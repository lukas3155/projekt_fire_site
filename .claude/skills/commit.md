# Commit Guidelines (Conventional Commits)

Ten projekt używa standardu **Conventional Commits**.
Każdy commit MUSI być logicznie spójny i dotyczyć jednego celu.

## 1. Ogólny cel
Twoim zadaniem jest:
- analizować zmiany w kodzie
- **wydzielać logiczne commity**
- nadawać im poprawne komunikaty zgodne z Conventional Commits

Nigdy nie łącz w jednym commicie zmian o różnych celach.

---

## 2. Struktura komunikatu commita

Format:
<type>(<scope>): <krótki opis>


### Przykłady:
- `feat(auth): add JWT refresh token`
- `fix(api): handle null user response`
- `refactor(ui): extract button component`
- `docs(readme): update installation steps`

---

## 3. Dozwolone typy commitów

- `feat` – nowa funkcjonalność
- `fix` – poprawka błędu
- `refactor` – zmiana kodu bez zmiany zachowania
- `perf` – poprawa wydajności
- `test` – testy (dodanie / poprawa)
- `docs` – dokumentacja
- `style` – formatowanie (bez zmiany logiki)
- `chore` – konfiguracja, narzędzia, build, CI
- `ci` – pipeline, GitHub Actions itp.
- `build` – zależności, bundling
- `revert` – cofnięcie commita

---

## 4. Scope (zakres)

Scope jest:
- nazwą modułu, folderu lub funkcjonalności
- opcjonalny, ale zalecany

### Przykłady:
- `auth`, `api`, `db`, `ui`, `config`, `deps`
- nazwa pakietu, folderu lub komponentu

---

## 5. Zasady wydzielania commitów

### ZAWSZE rozdzielaj commity, gdy:
- zmiany dotyczą **różnych funkcjonalności**
- jedna zmiana to `feat`, a inna to `fix`
- zmiany produkcyjne i testy nie są ściśle zależne
- refaktor dotyka kodu niezwiązanego bezpośrednio z featurem

### MOŻESZ łączyć zmiany, gdy:
- testy są bezpośrednio związane z featurem
- refaktor jest konieczny do działania feature’a
- zmiany dotyczą jednego, spójnego celu

---

## 6. Kolejność commitów

Jeśli to możliwe:
1. `refactor`
2. `feat`
3. `fix`
4. `test`
5. `docs`

Każdy commit powinien:
- przechodzić build
- nie łamać testów

---

## 7. Styl opisu

- czas teraźniejszy, tryb rozkazujący
- krótko i konkretnie
- bez kropki na końcu

❌ `added new validation`
✅ `add input validation`

---

## 8. Breaking changes

Breaking changes oznaczaj:
- `!` po typie: `feat(api)!: change auth flow`
- lub w treści commita (jeśli obsługiwane)

---

## 9. Czego NIE robić

- ❌ jeden commit „na wszystko”
- ❌ opisy typu „update”, „changes”, „fix stuff”
- ❌ mieszanie formatowania z logiką
- ❌ commitowanie niedziałającego kodu

---

## 10. Jeśli masz wątpliwości

Jeśli zmiany są niejednoznaczne:
- preferuj **więcej mniejszych commitów**
- każdy commit powinien dać się jasno opisać jednym zdaniem