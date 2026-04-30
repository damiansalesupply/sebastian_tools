"""
Export ticket comments per shop to Excel, then email zips to recipients from shops.yml.
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import re
import smtplib
import sys
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

from base.shopctrl_utils import (
    ShopCtrlInstance,
    get_list_of_tickets_ids_and_codes,
    get_ticket_comments,
)


def load_shops_config(path: Path | None = None) -> dict[int, dict]:
    """Load shops.yml: shop_id -> {name: str, recipients: list[str]}. CWD must be project root."""
    p = path or (Path.cwd() / "shops.yml")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: dict[int, dict] = {}
    for k, v in raw.items():
        sid = int(k) if not isinstance(k, int) else k
        out[sid] = v
    return out


def _normalized_recipients(cfg: dict) -> list[str]:
    raw = cfg.get("recipients") or []
    seen: set[str] = set()
    out: list[str] = []
    for r in raw:
        e = str(r).strip()
        if e and e not in seen:
            seen.add(e)
            out.append(e)
    return out


def build_shops_with_recipients(shops_by_id: dict[int, dict]) -> dict[int, dict]:
    """shop_id -> cfg with recipients stripped/deduped; only shops with at least one email."""
    out: dict[int, dict] = {}
    for sid, cfg in shops_by_id.items():
        recs = _normalized_recipients(cfg)
        if recs:
            out[sid] = {**cfg, "recipients": recs}
    return out


def build_email_to_shops(shops_by_id: dict[int, dict]) -> dict[str, list[dict]]:
    """email -> [{"shop_id": int, "name": str}, ...] (one entry per shop per email)."""
    inv: dict[str, list[dict]] = {}
    for sid, cfg in shops_by_id.items():
        recs = _normalized_recipients(cfg)
        if not recs:
            continue
        name = cfg.get("name", "")
        entry = {"shop_id": sid, "name": name}
        for email in recs:
            inv.setdefault(email, []).append(entry)
    return inv


def clean_invisible_chars(text: str) -> str:
    pattern = r"[\uFEFF\u200B\u200C\u200D\u200E\u200F\u2060\u202A-\u202E]"
    return re.sub(pattern, "", text)


def html2txt(html: str) -> str:
    import bs4

    soup = bs4.BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return clean_invisible_chars(text)


def _fold_accents_for_filename(s: str) -> str:
    """Map letters like ü, é, ö to plain ASCII letters (NFD + drop combining marks)."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("ß", "ss").replace("ẞ", "SS")


def sanitize_filename_part(s: str, max_len: int = 80) -> str:
    """Fold accented Latin chars; strip whitespace, dots, parentheses; replace invalid path chars."""
    if s is None:
        return ""
    s = _fold_accents_for_filename(str(s))
    s = re.sub(r"\s+", "", s)
    s = s.replace(".", "")
    s = re.sub(r"[()\uff08\uff09]", "", s)  # () and fullwidth （）
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = s.strip("._")
    return s[:max_len] if len(s) > max_len else s


def _comment_timestamp_in_period(ts: datetime | None, start: date, end: date) -> bool:
    if ts is None:
        return False
    if ts.tzinfo is not None:
        ts = ts.astimezone().replace(tzinfo=None)
    d = ts.date()
    return start <= d <= end


@dataclass(frozen=True)
class PeriodBounds:
    start: date
    end: date


def resolve_period(
    period: str,
    *,
    today: date,
    n_days: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> PeriodBounds:
    p = period.lower().replace("-", "_")
    if p == "mtd":
        start = today.replace(day=1)
        return PeriodBounds(start=start, end=today)
    if p == "last_month":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        start = last_prev.replace(day=1)
        return PeriodBounds(start=start, end=last_prev)
    if p == "last_n_days":
        if n_days is None or n_days < 1:
            raise ValueError("last_n_days requires --n-days >= 1")
        start = today - timedelta(days=n_days - 1)
        return PeriodBounds(start=start, end=today)
    if p == "time_range":
        if from_date is None or to_date is None:
            raise ValueError("time-range requires --from-date and --to-date")
        if from_date > to_date:
            raise ValueError("--from-date must be on or before --to-date")
        return PeriodBounds(start=from_date, end=to_date)
    raise ValueError(f"Unknown period: {period!r}")


def ticket_api_date_range(period: PeriodBounds, ticket_window_factor: int) -> tuple[date, date]:
    """Inclusive calendar bounds for which we want ticket *changes* (fromDateChanged inclusive).

    The API's untilDateChanged is exclusive; callers must pass api_until + 1 day as until_date_changed.
    """
    if ticket_window_factor < 1:
        raise ValueError("ticket_window_factor must be >= 1")
    period_days = (period.end - period.start).days + 1
    extended_days = period_days * ticket_window_factor
    api_until = period.end
    api_from = api_until - timedelta(days=extended_days - 1)
    return api_from, api_until


def format_api_date(d: date) -> str:
    return d.isoformat()


def comments_to_dataframe(comments: list, ticket_id2code: dict[int, str]) -> pd.DataFrame:
    columns = [
        "CommentId",
        "TimeStamp",
        "Comment",
        "TicketCode",
        "EmployeeName",
        "EmployeeId",
        "OrderId",
        "OfferId",
        "TicketId",
        "CommentType",
    ]
    if not comments:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame([c.model_dump() for c in comments])
    df["Comment"] = df["Comment"].apply(html2txt)
    df["TicketCode"] = df["TicketId"].map(ticket_id2code)
    df = df[
        [
            "Id",
            "TimeStamp",
            "Comment",
            "TicketCode",
            "EmployeeName",
            "EmployeeId",
            "OrderId",
            "OfferId",
            "TicketId",
            "CommentType",
        ]
    ].rename(columns={"Id": "CommentId"})
    return df.sort_values("TimeStamp")


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s %(levelname)s %(message)s"
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(fmt))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(fmt))
    root.addHandler(fh)
    root.addHandler(sh)


def zip_excel_files(paths: Iterable[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            if p.is_file():
                zf.write(p, arcname=p.name)
    return buf.getvalue()


def _smtp_socket_timeout() -> float | None:
    """Seconds for SMTP socket operations (connect, TLS, login, send). None = no explicit timeout."""
    raw = (os.getenv("SMTP_TIMEOUT") or "180").strip()
    if raw.lower() in ("none", "off", "unlimited"):
        return None
    try:
        v = float(raw)
    except ValueError:
        return 180.0
    if v <= 0:
        return None
    return v


def send_zip_email(
    *,
    to_email: str,
    zip_bytes: bytes,
    subject: str,
    body: str,
    zip_filename: str,
) -> None:
    load_dotenv()
    msg = EmailMessage()
    from_addr = os.getenv("EMAIL_FROM", "BPO Reporting <support@salesupplyaiservices.com>")
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    msg.add_attachment(
        zip_bytes,
        maintype="application",
        subtype="zip",
        filename=zip_filename,
    )
    host = os.getenv("SMTP_HOST", "s113.cyber-folks.pl")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "support@salesupplyaiservices.com")
    password = os.getenv("EMAIL_PASSWORD")
    if not password:
        raise RuntimeError("EMAIL_PASSWORD is not set in environment")

    timeout = _smtp_socket_timeout()
    with smtplib.SMTP(host, port, timeout=timeout) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)


def _parse_iso_date(s: str) -> date:
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export ticket comments to Excel and email zips to recipients.")
    p.add_argument("--no-sending", action="store_true", help="Skip SMTP; only write Excel files.")
    p.add_argument(
        "--only-shops",
        type=int,
        nargs="*",
        default=None,
        metavar="SHOP_ID",
        help="Restrict export to these shop IDs (must have recipients in shops.yml).",
    )
    p.add_argument(
        "--only-send-to",
        type=str,
        nargs="*",
        default=None,
        metavar="EMAIL",
        help="Only send zip emails to these addresses (export still runs for selected shops).",
    )
    p.add_argument(
        "--period",
        choices=("mtd", "last_month", "last_n_days", "time-range"),
        default="mtd",
        help="Reporting period for comment timestamps (default: mtd).",
    )
    p.add_argument(
        "--n-days",
        type=int,
        default=None,
        help="With --period last_n_days: number of calendar days ending on run day (inclusive).",
    )
    p.add_argument(
        "--from-date",
        type=str,
        default=None,
        help="With --period time-range: start date YYYY-MM-DD (inclusive).",
    )
    p.add_argument(
        "--to-date",
        type=str,
        default=None,
        help="With --period time-range: end date YYYY-MM-DD (inclusive).",
    )
    p.add_argument(
        "--ticket-window-factor",
        type=int,
        default=3,
        metavar="N",
        help="Ticket API date span = period length in days * N (default: 3).",
    )
    p.add_argument(
        "--shops-yml",
        type=Path,
        default=None,
        help="Path to shops.yml (default: ./shops.yml).",
    )
    return p.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    run_start = datetime.now()
    run_calendar_date = run_start.date()
    out_dir = Path("data") / run_calendar_date.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_stem = run_start.strftime("%Y-%m-%d_%H%M%S")
    setup_logging(out_dir / f"export_comments_{log_stem}.log")
    log = logging.getLogger(__name__)

    from_d = _parse_iso_date(args.from_date) if args.from_date else None
    to_d = _parse_iso_date(args.to_date) if args.to_date else None

    try:
        period = resolve_period(
            args.period,
            today=run_calendar_date,
            n_days=args.n_days,
            from_date=from_d,
            to_date=to_d,
        )
    except ValueError as e:
        log.error("%s", e)
        sys.exit(2)

    api_from, api_until = ticket_api_date_range(period, args.ticket_window_factor)
    from_s = format_api_date(api_from)
    # API untilDateChanged is exclusive — include changes through api_until by sending the next day.
    until_s = format_api_date(api_until + timedelta(days=1))
    period_tag = f"{format_api_date(period.start)}_{format_api_date(period.end)}"

    shops_by_id = load_shops_config(args.shops_yml)
    shops_with = build_shops_with_recipients(shops_by_id)
    email_to_shops = build_email_to_shops(shops_by_id)

    shop_ids = sorted(shops_with.keys())
    if args.only_shops is not None:
        want = set(args.only_shops)
        shop_ids = [sid for sid in shop_ids if sid in want]
        missing = want - set(shop_ids)
        if missing:
            log.warning("Shop IDs not in SHOPS_WITH_RECIPIENTS (skipped): %s", sorted(missing))

    instance = ShopCtrlInstance.Cms
    exported_paths: dict[int, Path] = {}

    log.info(
        "Run started run_calendar_date=%s run_start=%s period=%s..%s ticket_changes_inclusive=%s..%s untilDateChanged_param=%s factor=%s shops=%s",
        run_calendar_date,
        run_start.isoformat(timespec="seconds"),
        period.start,
        period.end,
        api_from,
        api_until,
        until_s,
        args.ticket_window_factor,
        len(shop_ids),
    )

    for shop_id in shop_ids:
        cfg = shops_with[shop_id]
        name = str(cfg.get("name", "") or f"shop_{shop_id}")
        t0 = time.perf_counter()
        log.info("Shop start id=%s name=%r", shop_id, name)
        err: str | None = None
        n_tickets = 0
        n_comments_raw = 0
        n_comments_kept = 0
        out_path: Path | None = None
        try:
            tickets_ids_and_codes = get_list_of_tickets_ids_and_codes(
                shop_id=shop_id,
                from_date_changed=from_s,
                until_date_changed=until_s,
                shopctrl_instance=instance,
            )
            n_tickets = len(tickets_ids_and_codes)
            ticket_id2code = {tid: code for tid, code in tickets_ids_and_codes}
            comments_all: list = []
            for tid, _code in tqdm(tickets_ids_and_codes, desc=f"tickets {shop_id}", leave=False):
                comments_all.extend(get_ticket_comments(tid, shopctrl_instance=instance))
            n_comments_raw = len(comments_all)
            comments_filtered = [
                c
                for c in comments_all
                if _comment_timestamp_in_period(c.TimeStamp, period.start, period.end)
            ]
            n_comments_kept = len(comments_filtered)
            df = comments_to_dataframe(comments_filtered, ticket_id2code)
            safe_name = sanitize_filename_part(name)
            fname = f"comments_{safe_name}_{shop_id}_{period_tag}.xlsx"
            out_path = out_dir / fname
            df.to_excel(out_path, index=False)
            exported_paths[shop_id] = out_path
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            log.exception("Shop failed id=%s", shop_id)
        elapsed = time.perf_counter() - t0
        if err:
            log.info(
                "Shop end id=%s duration_s=%.2f tickets=%s comments_raw=%s comments_in_period=%s ERROR=%s",
                shop_id,
                elapsed,
                n_tickets,
                n_comments_raw,
                n_comments_kept,
                err,
            )
        else:
            log.info(
                "Shop end id=%s duration_s=%.2f tickets=%s comments_raw=%s comments_in_period=%s file=%s",
                shop_id,
                elapsed,
                n_tickets,
                n_comments_raw,
                n_comments_kept,
                out_path,
            )

    if args.no_sending:
        log.info("Skipping email (--no-sending). Done.")
        return

    send_filter = None
    if args.only_send_to:
        send_filter = {e.strip().lower() for e in args.only_send_to if e.strip()}

    recipients = sorted(email_to_shops.keys())
    if send_filter is not None:
        recipients = [r for r in recipients if r.lower() in send_filter]
        unknown = send_filter - {r.lower() for r in email_to_shops}
        if unknown:
            log.warning("--only-send-to addresses not in shops.yml: %s", sorted(unknown))

    run_label = f"{args.period} {period.start} .. {period.end}"
    for to_email in recipients:
        paths: list[Path] = []
        for entry in email_to_shops[to_email]:
            sid = entry["shop_id"]
            if sid in exported_paths:
                paths.append(exported_paths[sid])
        if not paths:
            log.info("No exported files for recipient %s; skip email.", to_email)
            continue
        zip_name = f"comments_export_{run_calendar_date.isoformat()}_{to_email.replace('@', '_at_')}.zip"
        zip_bytes = zip_excel_files(paths)
        subj = f"Ticket comments export — {run_label}"
        body = (
            f"Comments for period {period.start} through {period.end} (inclusive).\n"
            f"Attached: {len(paths)} Excel file(s).\n"
        )
        try:
            send_zip_email(
                to_email=to_email,
                zip_bytes=zip_bytes,
                subject=subj,
                body=body,
                zip_filename=zip_name,
            )
            log.info("Sent zip to %s (%s files)", to_email, len(paths))
        except Exception:
            log.exception("Failed to send email to %s", to_email)

    log.info("Run finished.")


if __name__ == "__main__":
    main()
