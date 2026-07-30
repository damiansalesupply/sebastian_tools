# SPEC — sebastian_tools

Specyfikacja produktowa. Tu opisujemy **CO** narzędzie robi (z perspektywy użytkownika i biznesu).
Operacyjne (stack, komendy, deploy) → `CLAUDE.md`.

> **Aktualizuj na koniec każdej sesji** jeśli zmieniła się funkcjonalność widoczna dla użytkownika (CLI, format outputu, format maila, zakres danych).

---

## 1. Cel produktu

**Problem, który rozwiązuje**: Każdego miesiąca trzeba dostarczyć klientom Salesupply komplet komentarzy z ticketów obsługi posprzedażowej, podzielony per sklep, w formie Excela do importu / archiwum klienta. Bez automatyzacji zajmowało to godziny operatora.

**Dla kogo**: zespół operacyjny Salesupply odpowiedzialny za raportowanie do klientów (BPO / Contact Center). Klienci końcowi (sklepy korzystające z usługi obsługi klienta) dostają zip-y mailem.

**Mierzalny efekt**:
- 1 polecenie zamiast godzin pracy.
- Comiesięczne raporty wychodzą przed 5. dniem miesiąca.
- Brak ręcznych pomyłek w mapowaniu sklep → odbiorcy.

---

## 2. Użytkownicy i role

| Rola | Kto to | Co może |
|---|---|---|
| **Operator BPO** | Pracownik Salesupply odpowiedzialny za miesięczne raporty | Edytuje `shops.yml` (recipienty), uruchamia skrypt, weryfikuje output przed wysyłką |
| **Klient (sklep)** | Odbiorca raportu | Dostaje mail z zip-em zawierającym XLSX-y dla swoich sklepów |
| **Admin techniczny** | Damian / dev | Zmienia kod, dodaje nowe pola w outpucie, debuguje błędy API |

---

## 3. Główne funkcje

### 3.1 Ekstrakcja danych

- **Pobieranie ticketów z Salesupply API** dla shop ID z `shops.yml` o ile sklep ma jakichkolwiek odbiorców.
  - Status: wdrożone
  - API: ShopCtrl `/Tickets` z `fromDateChanged`/`untilDateChanged` (exclusive)
- **Filtrowanie komentarzy do okresu raportowania** — okno ticketów jest szersze (×3 default) niż okno komentarzy.
  - Status: wdrożone
- **Per-shop podział** — jeden plik XLSX na shop ID.
  - Status: wdrożone

### 3.2 Output

- **Excel** w `data/<run-date>/comments_<ShopName>_<shopId>_<periodStart>_<periodEnd>.xlsx`
  - Status: wdrożone
- **Log per run** w `data/<run-date>/export_comments_<YYYY-MM-DD_HHMMSS>.log` (timestamp żeby kolejne runy tego samego dnia się nie nadpisywały).
  - Status: wdrożone

### 3.3 Mailing

- **Zip per recipient** zawierający tylko sklepy, do których odbiorca ma dostęp (z `shops.yml`).
  - Status: wdrożone
- **Domyślnie maile się wysyłają** — opcja `--no-sending` żeby tylko wygenerować pliki.
  - Status: wdrożone
- **Smoke-test** `--only-send-to <email>` — kierujemy zip-y tylko do podanego adresu.
  - Status: wdrożone

### 3.4 Konfiguracja okresu (CLI)

| Opcja | Co robi |
|---|---|
| `--period mtd` (default) | Month-to-date przez dzień bieżący |
| `--period last_month` | Poprzedni pełny miesiąc kalendarzowy |
| `--period last_n_days --n-days N` | Ostatnie N dni włącznie z dniem bieżącym |
| `--period time-range --from-date Y-M-D --to-date Y-M-D` | Sztywny zakres |
| `--ticket-window-factor N` | Mnożnik okna API (default 3) |

### 3.5 Filtrowanie zakresu (CLI)

- `--only-shops 1521 2040` — eksport wybranych shop ID
- `--only-send-to a@b.com c@d.com` — wysyłka tylko do wybranych odbiorców
- `--shops-yml PATH` — alternatywna lokalizacja pliku konfiguracji

---

## 4. Kluczowe user flows

### Flow 1 — comiesięczny raport

1. Operator wchodzi do venv: `.venv\Scripts\activate`
2. Sprawdza `shops.yml` — czy nie zmienili się recipienty
3. Uruchamia: `.venv\Scripts\python.exe export_comments.py --period last_month`
4. Skrypt iteruje po sklepach, generuje XLSX-y, zapisuje log, wysyła zip-y
5. Operator weryfikuje log + przykładowy plik

### Flow 2 — ad hoc raport dla 1 klienta

1. Operator znajduje shop ID w panelu CMS (lub w `shops.yml`)
2. Edytuje `shops.yml` jeśli trzeba dorzucić odbiorcę
3. `.venv\Scripts\python.exe export_comments.py --only-shops 1521 --period time-range --from-date 2026-04-01 --to-date 2026-04-15`
4. Sprawdza zip-a, ewentualnie ponawia z `--no-sending` żeby zobaczyć output bez wysłania.

---

## 5. Out-of-scope (świadomie NIE robimy)

- **Modyfikacja danych po stronie Salesupply** — skrypt jest read-only.
- **Generowanie PDF / dashboardu** — output to XLSX, koniec. Klienci sami sobie wizualizują.
- **Real-time / webhook** — to batch tool, nie service.
- **Zarządzanie subskrypcjami przez UI** — recipienty edytujesz ręcznie w `shops.yml` (świadoma decyzja: małe, stałe grono, nie warto budować panelu).

---

## 6. Domena / model biznesowy

| Pojęcie | Definicja | Atrybuty |
|---|---|---|
| **Shop** | Sklep klienta obsługiwany przez Salesupply BPO | `id` (numeryczne, ShopCtrl), `name`, `recipients[]` |
| **Recipient** | Email odbiorcy raportu dla danego sklepu (jeden recipient może być na wielu sklepach) | `email` |
| **Reporting period** | Okres (komentarze z tego okresu trafiają do raportu) | `start`, `end` (inclusive) |
| **Ticket window** | Okno API w którym szukamy ticketów (szersze niż reporting period) | `fromDateChanged`, `untilDateChanged` (exclusive po stronie API) |
| **Ticket** | Pojedyncze zgłoszenie obsługi klienta w ShopCtrl | `id`, `shopId`, `lastChange`, `comments[]` |
| **Comment** | Wpis na tickecie (z timestampem) | `ticketId`, `timestamp`, `text`, `author` |

Powiązania:
- `Recipient` (N) ↔ (N) `Shop` — każdy recipient może być na wielu sklepach, każdy sklep może mieć wielu recipientów. Konfiguracja w `shops.yml`.
- `Ticket` (1) → (N) `Comment`.

---

## 7. Powiązania zewnętrzne

| System | Po co | Auth |
|---|---|---|
| **Salesupply ShopCtrl API** (`api.salesupply.com/v1/*`) | Pobieranie listy sklepów + ticketów + komentarzy | `SHOPCTRL_BASIC_AUTH_HEADER` w `.env` |
| **SMTP (CyberFolks: `s113.cyber-folks.pl:587`)** | Wysyłka mailem | `EMAIL_PASSWORD` + ewent. `SMTP_HOST/PORT/USER` — konto: `ai_agent@salesupplyaiservices.website` (od 2026-07-30; poprzednie `support@salesupplyaiservices.com` padło) |
| **OpenAI** (opcjonalnie) | Eksperymenty z analizą tekstu komentarzy (extra `[openai]`) | `OPENAI_API_KEY` |

---

## 8. Roadmap / etapy

### Wdrożone _(produkcja)_

- Eksport per shop, mailing zip-ów
- Filtrowanie okresu (mtd / last_month / last_n_days / time-range)
- Smoke-test (`--only-send-to`)
- `--ticket-window-factor` jako tuning szerokości okna API

### Backlog / pomysły

- [ ] Wypełnić `base/aia_utils.py` (placeholder na utili AIA — nieokreślony jeszcze scope)
- [ ] Ekstrakcja kategorii / tagów ticketu do osobnej kolumny w XLSX (jeśli klienci proszą)
- [ ] Statystyki podsumowujące w mailu (liczba ticketów / komentarzy per shop)
- [ ] Dry-run mode pokazujący "co zostałoby wysłane do kogo" bez generowania plików
- [ ] Wyciągnięcie `base/` jako osobny pakiet `salesupply-py-utils` (re-use w `prospecting_lists`, `bpo-reporting`)

---

## 9. Decyzje produktowe (ADR-lite)

- **2026-04** — Format outputu: XLSX (nie CSV) — pozwala formatowanie + kilka arkuszy w przyszłości; klienci preferują Excel.
- **2026-04** — Recipienty per-shop konfigurowane w pliku YAML, nie w panelu — małe stałe grono, nie warto budować UI.
- **2026-04** — Ticket window ×3 default — wystarczy do wyłapania ticketów rozłożonych w czasie, bez ekstremalnego rate-limit'u API.
- **2026-04** — `untilDateChanged` exclusive po stronie API → skrypt dolicza +1 dzień w kodzie zamiast wymagać tego od użytkownika.

---

## 10. Ryzyka i otwarte pytania

- **Zmiana API ShopCtrl** — gdy Salesupply zmieni format odpowiedzi `/Tickets`, wrapper w `base/shopctrl_utils.py` może wymagać aktualizacji. Mamy testy?
- **Limity SMTP CyberFolks** — Hetzner blokuje 465, używamy 587. W razie zwiększonego volume sprawdzić rate-limity (CyberFolks ~100 maili/h domyślnie).
- **Otwarte pytanie**: czy nowe sklepy automatycznie pojawiają się z API CMS, czy operator musi ręcznie dorzucać do `shops.yml`?

---

## CHANGELOG (krótki)

- 2026-07-30 — migracja SMTP nadawcy: `support@salesupplyaiservices.com` → `ai_agent@salesupplyaiservices.website` (stare konto padło).
- 2026-05-06 — utworzenie `SPEC.md`, `CLAUDE.md`, `docs/HANDOFF.md`, `docs/END_OF_SESSION.md`.
- (wcześniejsze zmiany — patrz `git log` na main)
