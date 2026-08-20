# CLAUDE.md — sebastian_tools

Stała pamięć projektu (operacyjna). Czytaj na początku każdej sesji.

> **Trigger "kończymy sesję"**: gdy użytkownik napisze "kończymy sesję", "koniec sesji", "end session" lub podobnie — wykonaj procedurę z `docs/END_OF_SESSION.md`.

> **Co innego trzymać tu, a co w `SPEC.md`?**
> - **CLAUDE.md** (ten plik) = jak pracować z projektem: stack, komendy, workflow, definition of done, pułapki.
> - **`SPEC.md`** = co aplikacja robi: cel, użytkownicy, funkcje, user flows, out-of-scope, roadmap.

---

## Projekt — minimum kontekstu

- **Czym jest** (1 zdanie): CLI w Pythonie do eksportu komentarzy z ticketów Salesupply API per shop, z mailingiem zip-ów do skonfigurowanych odbiorców.
- **Pełny opis biznesowy**: zobacz `SPEC.md`.
- **GitHub**: https://github.com/damiansalesupply/sebastian_tools (publiczne)
- **Lokalizacja lokalna**: `C:\projects\sebastian_tools`
- **Branch domyślny**: `main`

---

## Stack techniczny

- **Język/runtime**: Python ≥ 3.12 (`pyproject.toml` `requires-python = ">=3.12"`)
- **Główne paczki**: `pandas≥3.0`, `openpyxl≥3.1.5`, `pydantic≥2.11`, `python-dotenv`, `pyyaml`, `requests`, `tqdm`, `beautifulsoup4`
- **Optional**: `openai` (extra `[openai]`), `ipykernel/jupyter` (extra `[notebook]`)
- **Dev**: `pytest≥8.4`
- **Lint**: `ruff` (line-length=130)
- **Storage / persistence**: brak DB — output to pliki XLSX + logi w `data/<run-date>/`
- **Auth zewnętrzny**: `SHOPCTRL_BASIC_AUTH_HEADER` (Salesupply API), `EMAIL_PASSWORD` + opcjonalnie `SMTP_HOST/PORT/USER/EMAIL_FROM/SMTP_TIMEOUT` (mailer)

---

## Struktura katalogów

```
.
├── README.md            — szczegółowy opis CLI + przykłady (czytaj przy zmianach UX)
├── pyproject.toml       — deps + ruff config
├── shops.yml            — konfiguracja sklepów + recipientów (klucz = shopId)
├── export_comments.py   — główny skrypt CLI
├── base/                — wewnętrzny pakiet utili (re-usable utilities)
│   ├── shopctrl_utils.py    — wrapper Salesupply ShopCtrl API
│   ├── requests_utils.py    — retry + rate limiting
│   ├── order_utils.py
│   ├── text_utils.py
│   ├── oai_utils.py         — opcjonalny wrapper OpenAI
│   ├── engaige_utils.py
│   ├── logger.py            — konfiguracja logowania
│   ├── aia_utils.py         — placeholder (pusty plik)
│   └── models/              — Pydantic modele
└── data/                — output (gitignored): XLSX-y per shop + logi per run
    └── <run-date>/
```

---

## Komendy

```bash
# Setup (jednorazowo)
cd C:\projects\sebastian_tools
python -m venv .venv
.venv\Scripts\activate            # PowerShell
pip install -e .                  # albo: pip install -e ".[notebook,openai]"

# Domyślny run — month-to-date, eksport + mailing
.venv\Scripts\python.exe export_comments.py

# Tylko eksport (bez maili)
.venv\Scripts\python.exe export_comments.py --no-sending

# Konkretny okres
.venv\Scripts\python.exe export_comments.py --period last_month
.venv\Scripts\python.exe export_comments.py --period last_n_days --n-days 14
.venv\Scripts\python.exe export_comments.py --period time-range --from-date 2026-04-01 --to-date 2026-04-15

# Tylko wybrane sklepy (muszą mieć recipientów w shops.yml)
.venv\Scripts\python.exe export_comments.py --only-shops 1521 2040

# Smoke-test mailingu (wyślij tylko do mnie)
.venv\Scripts\python.exe export_comments.py --only-send-to test@example.com

# Lint
ruff check .

# Testy
pytest
```

> Zawsze odpalaj przez `.venv\Scripts\python.exe` (lub `.venv/bin/python` na Linuksie), nie globalny Python — żeby imports zgadzały się z deps z venv.

---

## Workflow sesji

1. **Plan** — opisz co chcesz zrobić zanim zaczniesz pisać kod
2. **Implement** — zmiany w `export_comments.py` lub `base/`
3. **Test** — `ruff check .` + `pytest` + smoke run z `--no-sending` na 1 sklepie
4. **Commit + push** — push na origin/main jeśli stan stabilny
5. **Handoff** — zaktualizuj `docs/HANDOFF.md`

---

## Podział ról: Claude vs Codex

| Zadanie | Kto |
|---|---|
| Architektura, decyzje (np. nowy parser API), debug nietrywialny | **Claude** |
| Aktualizacja `SPEC.md`, `HANDOFF.md`, `CLAUDE.md` | **Claude** |
| Generowanie testów pytest, parsing odpowiedzi API, mała refaktorka | **Codex** |
| Ad-hoc skrypty importu / eksportu (jednorazowe) | **Codex** (review przez Claude przed mergem) |
| Real run produkcyjny (mailing) | **użytkownik** (świadoma decyzja, nie automat) |

**Zasada:** kod od Codexa idzie na branch roboczy → review Claude → merge do main świadomie.
**Logi Codexa** (`codex-*.log`): dorzuć do `.gitignore`, nie commituj.

---

## Konwencje

- **Naming Python**: snake_case, type hints (Python 3.12+ syntax: `list[int]`, `dict[str, Any]` bez importu `typing`).
- **Error handling**: log + dalej (`base/logger.py`). Nie cichego `except: pass`.
- **Ruff**: `line-length=130`. Nie wyłączamy reguł bez wpisu w PR-zie.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- **Branche**: `main` = stable; pojedyncze tematy → branch `feature/<slug>` lub `fix/<slug>`.

---

## Definition of Done

- [ ] Kod uruchamia się z `.venv` lokalnie (smoke `export_comments.py --no-sending --only-shops <jeden_id>`)
- [ ] `ruff check .` przechodzi
- [ ] `pytest` przechodzi (jeśli dotyczy zmiany — nowe testy obowiązkowe dla nowych funkcji w `base/`)
- [ ] Jeśli zmieniał się CLI: `README.md` zaktualizowane (sekcja "Command-line options" lub "Examples")
- [ ] Jeśli zmieniła się logika biznesowa (filtrowanie okresu, format outputu): `SPEC.md` zaktualizowane
- [ ] Commit z sensownym message
- [ ] `docs/HANDOFF.md` zaktualizowany

---

## Sekrety i konfiguracja

- `.env` na VPS: `/home/sebastian/comments_export/.env` — produkcyjne creds.
- `.env` lokalnie — **nie commituj**. Klucze:
  - `SHOPCTRL_BASIC_AUTH_HEADER` — auth do Salesupply API (Basic, zakodowane creds `d.kuczynski@salesupply.com`)
  - `EMAIL_PASSWORD` — hasło do skrzynki nadawcy
  - `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `EMAIL_FROM` — opcjonalne overrides
  - `SMTP_TIMEOUT` — sekundy timeoutu socketu (default 180; `none` = brak)

**Aktualny nadawca SMTP (od 2026-07-30)**:
- `SMTP_USER=ai_agent@salesupplyaiservices.website`
- `SMTP_HOST=s113.cyber-folks.pl`, `SMTP_PORT=587` (STARTTLS)
- ⚠️ Poprzednie konto `support@salesupplyaiservices.com` padło 2026-07-27 — nie używaj go.
- `shops.yml` jest commitowany — to **konfiguracja**, nie sekret. Recipienty są wewnętrzne.

---

## Pułapki i known issues

- **`untilDateChanged` w API jest exclusive** — skrypt sam dolicza dzień, ale przy ręcznym debugowaniu pamiętaj.
- **`--ticket-window-factor`** domyślnie ×3 — szukamy ticketów dla ticketów których ostatnia zmiana mieści się w szerszym oknie, potem filtrujemy komentarze. Mała wartość = możesz przegapić ticket którego ostatnia zmiana wypadła poza okresem ale komentarz w okresie.
- **`base/aia_utils.py` jest pusty** (0 B) — placeholder. Jak zaczniesz dodawać util, zaktualizuj tu.
- **`pandas≥3.0`** — w 3.0 zmieniły się niektóre defaulty (np. `infer_objects`). Pamiętaj, że nie wszyscy mają jeszcze 3.0.
- **SMTP konto `support@salesupplyaiservices.com` padło 2026-07-27** — 535 auth error. Aktualny nadawca: `ai_agent@salesupplyaiservices.website`. Jeśli mail przestanie chodzić — pierwsze podejrzenie to rotacja hasła SMTP lub padnięcie konta.
- **`SHOPCTRL_BASIC_AUTH_HEADER` = creds Damiana** — jeśli zmieni hasło w ShopCtrl, token wygaśnie (HTTP 401 przy pobieraniu ticketów). Wtedy wyciągnąć nowy przez F12 → Network → `Authorization` header.

---

## Healthcheck monitor

- URL: `https://hc-ping.com/6fbcff81-d29a-445a-81ef-1ee6b03d001b`
- Pingowany przez `run_daily.sh` na VPS po każdym udanym runie (dodane 2026-08-20).
- Jeśli monitor pokazuje "Down" → sprawdź `/tmp/export_daily.log` na VPS.

## Jak ręcznie wysłać raport (przy awarii crona)

```bash
# 1. Eksport za konkretny dzień (np. wczoraj = 2026-08-19)
ssh -i ~/.ssh/id_ed25519_vps claude-agent@62.238.2.26 \
  "sudo -u sebastian bash -c 'cd /home/sebastian/comments_export && .venv/bin/python export_comments.py --only-shops 1305 1308 1328 --period time-range --from-date 2026-08-19 --to-date 2026-08-19 --no-sending'"

# 2. Wysyłka do odbiorców
ssh -i ~/.ssh/id_ed25519_vps claude-agent@62.238.2.26 \
  "sudo -u sebastian bash -c 'cd /home/sebastian/comments_export && .venv/bin/python send_combined.py d.kuczynski@salesupply.com && .venv/bin/python send_combined.py s.adamczak@salesupply.com'"
```

## Kończenie sesji — checklist

Gdy użytkownik napisze "kończymy sesję":

1. Wykonaj pełną procedurę z `docs/END_OF_SESSION.md`
2. Zaktualizuj `docs/HANDOFF.md`
3. Zaktualizuj `SPEC.md` jeśli zmieniła się funkcjonalność CLI / output / mailing
4. Dopisz do `CLAUDE.md` nowe stałe ustalenia (jeśli są)
5. Zrób lokalny commit (push tylko gdy wyraźnie poleciłem)
6. Pokaż krótki handoff: gdzie jesteśmy, co działa, co otwarte
