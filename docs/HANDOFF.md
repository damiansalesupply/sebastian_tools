# HANDOFF — sebastian_tools

Aktualizuj na końcu każdej sesji. Sekcja "Aktualny stan" zawsze odzwierciedla "tu i teraz", historia sesji idzie na dół.

---

## Aktualny stan

- **Branch**: `main`
- **Remote**: https://github.com/damiansalesupply/sebastian_tools.git (publiczne)
- **Ostatni commit**: 421d003 docs: add END_OF_SESSION.md procedure (lokalnie; VPS ma run_daily.sh z pingiem — nie commitowane)
- **Ostatnia aktualizacja tego pliku**: 2026-08-20
- **Środowisko produkcyjne**: VPS `62.238.2.26` → `/home/sebastian/comments_export/` (user: `sebastian`)
- **Healthcheck monitor**: https://hc-ping.com/6fbcff81-d29a-445a-81ef-1ee6b03d001b (ping wysyłany przez `run_daily.sh` po udanym runie)

---

## Co jest następne (TODO — żywa lista)

> Skrypt `weekly_digest.py` zlicza pozycje z `- [ ]` z tej sekcji jako otwarte zaległości projektu.

### Priorytet wysoki

- [ ] Sprawdzić czy nowe sklepy z CMS automatycznie pojawiają się czy trzeba ręcznie aktualizować `shops.yml`

### Priorytet średni

- [ ] Wypełnić `base/aia_utils.py` (placeholder 0 B) lub usunąć jeśli niepotrzebny
- [ ] Dorzucić testy `pytest` dla parsera odpowiedzi `/Tickets` w `base/shopctrl_utils.py` (na razie brak coverage)

### Backlog / pomysły

- [ ] Dry-run mode pokazujący "co zostałoby wysłane do kogo" bez generowania plików
- [ ] Statystyki podsumowujące w mailu (liczba ticketów / komentarzy per shop)
- [ ] Wyciągnąć `base/` jako pakiet `salesupply-py-utils` (re-use w `prospecting_lists`, `bpo-reporting`)
- [ ] Dorzucić ekstrakcję kategorii / tagów ticketu do XLSX-a (jeśli klienci poproszą)

---

## Ryzyka / blokery / decyzje do podjęcia

- **API ShopCtrl 500** — 2026-08-13 i prawdopodobnie 2026-08-20 API padało o 01:00 UTC. Cron nie ponawia próby — wymagana ręczna interwencja przy kolejnej awarii (patrz sekcja "Jak ręcznie wysłać raport" niżej).
- **API ShopCtrl** może zmienić format odpowiedzi — brak testów na to, ryzyko cichej regresji.
- **Limity SMTP CyberFolks** — przy wzroście volume mailingu sprawdzić rate-limity.
- **Rotacja hasła SMTP** — konto `support@salesupplyaiservices.com` padło 2026-07-27 (535 auth). Obecne konto `ai_agent@salesupplyaiservices.website` działa, ale jak następnym razem padnie — patrz `CLAUDE.md` sekcja Sekrety.
- **Token ShopCtrl** (`SHOPCTRL_BASIC_AUTH_HEADER`) — zakodowane są creds `d.kuczynski@salesupply.com`. Jeśli Damian zmieni hasło w ShopCtrl, token wygaśnie i eksport przestanie działać bez 401.

---

## Definition of Done — status (dla bieżącego cyklu)

- [ ] `ruff check .` przechodzi
- [ ] `pytest` przechodzi (jeśli zmiany dotyczą logiki)
- [ ] Smoke run `--no-sending --only-shops <id>` zielony
- [ ] `README.md` zaktualizowany jeśli zmienił się CLI
- [ ] `SPEC.md` zaktualizowany jeśli zmieniła się funkcjonalność
- [ ] Commit z sensownym message
- [ ] HANDOFF.md zaktualizowany

---

## Historia sesji

> Każdy wpis = podsumowanie jednej sesji. Nowsze na górze.

### Sesja 2026-08-20 — Healthcheck monitor + ręczne wysyłki po awariach API

**Cel**: przywrócić raport za 2026-08-13 (API 500 w nocy) + podłączyć healthcheck monitor.

**Co zrobiono**:
- Zdiagnozowano awarię ShopCtrl API z 2026-08-13 (HTTP 500 dla sklepów 1305/1308/1328 o 01:00 UTC) — ręcznie odparto eksport i wysłano do d.kuczynski + s.adamczak.
- Zidentyfikowano healthcheck monitor (hc-ping.com) — `run_daily.sh` nie pingował go wcale, stąd status "Down".
- Dodano `curl -fsS --retry 3 https://hc-ping.com/6fbcff81-d29a-445a-81ef-1ee6b03d001b` na końcu `run_daily.sh` na VPS.
- Przetestowano ping ręcznie z VPS → `OK` ✅.
- Wysłano raport za 2026-08-19 (wczoraj) do d.kuczynski i s.adamczak ✅.

**Pliki zmienione**:

| Plik | Gdzie | Zmiana |
|---|---|---|
| `run_daily.sh` | VPS `/home/sebastian/comments_export/` | Dodano curl ping healthchecka na końcu |
| `docs/HANDOFF.md` | lokalnie | ta sesja |

**Testy / weryfikacja**:
- `curl` ping z VPS → `OK` ✅
- Kod skryptu nie zmieniony — brak potrzeby ruff/pytest.

**Uwaga**: `run_daily.sh` na VPS **różni się od wersji w git** — git nie ma tej zmiany. Rozważyć czy commitować `run_daily.sh` do repo (aktualnie go tam nie ma).

---

### Sesja 2026-07-30 — Naprawa SMTP (konto nadawcy padło)

**Cel**: przywrócić działanie automatycznych raportów komentarzy (mailingi przestały dochodzić).

**Diagnoza**:
- Cron na VPS działa poprawnie (`0 1 * * *` daily + `0 3 1 * *` monthly) — eksport Exceli OK.
- Błąd: `SMTPAuthenticationError: (535, b'Incorrect authentication data')` w `send_combined.py`.
- Przyczyna: konto `support@salesupplyaiservices.com` padło 2026-07-27 (znany problem z innych projektów).

**Co zrobiono**:
- Zaktualizowano `.env` na VPS (`/home/sebastian/comments_export/.env`) — podmiana SMTP na `ai_agent@salesupplyaiservices.website`.
- Przetestowano wysyłkę — `Sent to d.kuczynski@salesupply.com` ✅
- Wysłano catch-up raport za 2026-07-29 do Sary (`s.adamczak@salesupply.com`) ✅.

**Pliki zmienione**:

| Plik | Gdzie | Zmiana |
|---|---|---|
| `.env` | VPS `/home/sebastian/comments_export/` | Nowe creds SMTP (`ai_agent@salesupplyaiservices.website`) |
| `docs/HANDOFF.md` | lokalnie | ta sesja |
| `SPEC.md` | lokalnie | sekcja 7 + CHANGELOG |
| `CLAUDE.md` | lokalnie | sekcja Sekrety + Pułapki |

**Testy / weryfikacja**:
- `send_combined.py d.kuczynski@salesupply.com` → `Sent` ✅
- `send_combined.py s.adamczak@salesupply.com` → `Sent` ✅
- Kod skryptu nie zmieniony — brak potrzeby ruff/pytest.

**Commit**: docs fix (HANDOFF + SPEC + CLAUDE) — bez push, zmiany tylko w dokumentacji i config na VPS.

---

### Sesja 2026-05-06 — Wprowadzenie procedur sesyjnych

**Cel**: dorzucić wzorzec dokumentacji z bpo-reporting (CLAUDE.md, SPEC.md, HANDOFF.md, END_OF_SESSION.md) do tego projektu.

**Co zrobiono**:

- Utworzono `CLAUDE.md` (operacyjny: stack, komendy, workflow, Definition of Done, pułapki, sekcja Claude vs Codex).
- Utworzono `SPEC.md` (produktowy: cel, użytkownicy, funkcje, user flows, decyzje produktowe, CHANGELOG).
- Utworzono `docs/HANDOFF.md` (ten plik).
- Utworzono `docs/END_OF_SESSION.md` (prompt do wykonania na "kończymy sesję").

**Pliki zmienione**:

| Plik | Zmiana |
|---|---|
| `CLAUDE.md` | nowy |
| `SPEC.md` | nowy |
| `docs/HANDOFF.md` | nowy |
| `docs/END_OF_SESSION.md` | nowy |

**Testy / weryfikacja**: nie dotyczy (zmiany tylko w dokumentacji).

**Commit**: do zrobienia ręcznie albo przy następnej sesji.

---

## Jak wznowić pracę (cheat-sheet)

1. `git pull && git status`
2. Aktywuj venv: `.venv\Scripts\activate`
3. Sprawdź sekcję "Aktualny stan" + ostatnią sesję wyżej.
4. Wybierz pierwszy punkt z TODO "Priorytet wysoki".
5. Komendy startowe → `CLAUDE.md` → sekcja "Komendy".
