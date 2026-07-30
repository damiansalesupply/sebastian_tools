# End-of-Session Prompt — sebastian_tools

Trigger: użytkownik pisze "kończymy sesję", "koniec sesji", "end session" lub podobnie.

---

## Prompt do wykonania (Claude robi to bez pytania, bez skrótu):

Kończymy tę sesję. Przygotuj handoff do wznowienia pracy bez tłumaczenia wszystkiego od nowa.

Zrób teraz:

1. **Zaktualizuj `docs/HANDOFF.md`**:
   - aktualny branch / ostatni commit (`git log -1 --oneline`),
   - cel bieżącej pracy,
   - co zostało zrobione w tej sesji (zmiany pogrupowane po featurach),
   - jakie pliki zostały zmienione (tabela),
   - co jest następne (TODO, najlepiej z priorytetami),
   - jakie testy / scenariusze zostały wykonane (`pytest`, `ruff`, smoke run z `--no-sending`),
   - ryzyka / blokery,
   - czego brakuje do Definition of Done (z `CLAUDE.md`).

2. **Zaktualizuj `SPEC.md`** jeśli zmieniła się funkcjonalność widoczna dla użytkownika:
   - dorzuć / zmień wpis w "Główne funkcje" (3.1-3.5),
   - dorzuć linijkę do `CHANGELOG (krótki)` na dole,
   - jeśli zapadła decyzja produktowa — dorzuć wpis ADR-lite w sekcji "Decyzje produktowe".

3. **Zaktualizuj `README.md`** jeśli zmienił się CLI:
   - sekcja "Command-line options" — nowa flaga / zmiana zachowania,
   - sekcja "Examples" — przykład użycia.

4. **Zaktualizuj `CLAUDE.md`** jeśli pojawiły się nowe stałe ustalenia (np. nowa zmienna `.env`, nowy known issue, zmiana w workflow).

5. **Commit lokalny** jeśli zmiany są spójne:
   - sensowny message (Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`),
   - commit tylko gdy stan repo jest do zapisania (nie WIP).

6. **NIE pushuj** automatycznie na origin/main — chyba że to wyraźnie poleciłem.

7. Jeśli nie commitujesz — wyjaśnij krótko dlaczego.

---

## Nowe kroki (dodane 2026-07-08)

- **Project map**: zaktualizuj wpis TEGO projektu w memory "Project Map" (Claude) — status, ostatni commit, jedno zdanie zmian. Nie rób pełnego rescanu wszystkich projektów.
- **Moja Firma / oferty**: zapytaj czy praca z tej sesji dotyczy oferty lub konkretnego klienta i powinna mieć wpis w `Moja firma/00_DASHBOARD.md`. Jeśli tak — dopisz wiersz (nazwa, 1-2 zdania, link).
- **Backup (jeśli projekt ma bazę/dane na VPS)**: sprawdź czy ostatni backup jest aktualny (<7 dni, patrz `C:\projects\backups\`). Jeśli nie — zaflaguj w handoffie i zasugeruj odpalenie dumpa (nie rób tego automatycznie bez potwierdzenia).

---

## Output dla użytkownika (na końcu pokaż):

- 📍 **Gdzie jesteśmy**: branch + ostatni commit
- ✅ **Co działa**: 1-3 punkty (testy zielone, smoke run zielony)
- ⏳ **Co nie jest domknięte**: 1-3 punkty
- 💾 **Czy powstał commit**: tak/nie + hash
- 🚧 **Czy coś blokuje push**: tak/nie + co
- ▶️ **Od czego zacząć następną sesję**: 1 zdanie
