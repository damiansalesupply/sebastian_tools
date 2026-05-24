"""
Search game-account marketplaces for Brawl Stars listings and filter the ones advertising the
Challenger Colt skin. Results are written as JSON under data/<run-date>/.

Run from the project root with the project venv, e.g.:
    .venv/bin/python brawl_stars_scraper.py --max-pages 5
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from base.logger import logger
from brawl_scraper.matcher import ColtChallengerMatcher
from brawl_scraper.pipeline import run_scrape
from brawl_scraper.sites import SITE_REGISTRY

DEFAULT_CONFIG = "brawl_config.yml"


def load_config(path: Path) -> dict:
    if not path.exists():
        logger.warning("Config %s not found; using built-in defaults.", path)
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--sites",
        nargs="+",
        choices=sorted(SITE_REGISTRY),
        help="Sites to scrape (default: the enabled sites from config, or all known sites).",
    )
    p.add_argument("--query", default="brawl stars account", help="Search query / term (default: %(default)r).")
    p.add_argument("--max-pages", type=int, default=3, help="Max result pages per site (default: %(default)s).")
    p.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG), help="Path to config YAML (default: %(default)s).")
    p.add_argument("--output", type=Path, default=None, help="Output JSON path (default: data/<date>/brawl_colt_<ts>.json).")
    p.add_argument("--save-all", action="store_true", help="Also include every scanned listing, not just matches.")
    p.add_argument("--no-browser", action="store_true", help="Disable the Playwright browser fallback (requests only).")
    p.add_argument("-q", "--quiet", action="store_true", help="Only log warnings and errors.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.quiet:
        logger.setLevel(logging.WARNING)

    config = load_config(args.config)
    sites = args.sites or config.get("enabled_sites") or sorted(SITE_REGISTRY)

    run_started = datetime.now()
    out_path = args.output or (
        Path("data") / run_started.strftime("%Y-%m-%d") / f"brawl_colt_{run_started.strftime('%Y-%m-%d_%H%M%S')}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(out_path.with_suffix(".log"), encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    matcher = ColtChallengerMatcher(config.get("filter_patterns"))
    report = run_scrape(
        sites=sites,
        query=args.query,
        max_pages=args.max_pages,
        config=config,
        matcher=matcher,
        allow_browser=not args.no_browser,
        save_all=args.save_all,
    )

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = report["stats"]
    logger.info("Done. Scanned %s offers, %s matched Challenger Colt.", stats["scanned"], stats["matched"])
    for name, s in stats["per_site"].items():
        logger.info("  %-16s scanned=%-5s matched=%s", name, s["scanned"], s["matched"])
    logger.info("Results written to %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
