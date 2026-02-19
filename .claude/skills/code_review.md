# Code Review Guidelines

Ten projekt stosuje ustandaryzowane code review.
Twoim zadaniem jest analizować zmiany w kodzie i dostarczać **konkretne, techniczne oraz konstruktywne uwagi**.

## 1. Główne cele code review

Podczas review ZAWSZE oceniaj:
- poprawność logiczną
- czytelność i utrzymywalność
- bezpieczeństwo
- spójność ze stylem projektu
- potencjalne edge case’y
- zgodność intencji zmian z ich zakresem

Nie oceniaj gustu — oceniaj jakość.

---

## 2. Zakres analizy

Analizuj WYŁĄCZNIE:
- zmienione linie kodu
- bezpośredni kontekst zmian

Nie komentuj:
- niezmienionych fragmentów
- istniejących problemów niezwiązanych z diffem (chyba że są krytyczne)

---

## 3. Kategorie uwag

Każdą uwagę klasyfikuj jako jedną z poniższych:

### 🔴 Critical
- błąd logiczny
- podatność bezpieczeństwa
- potencjalna utrata danych
- race condition
- crash w runtime

### 🟠 Important
- trudny w utrzymaniu kod
- brak walidacji / obsługi błędów
- naruszenie zasad architektury
- nieczytelna logika

### 🟡 Suggestion
- uproszczenie kodu
- lepsze nazewnictwo
- refaktor poprawiający czytelność
- drobne optymalizacje

### 🟢 Nitpick
- formatowanie
- drobne stylistyczne detale
- literówki

---

## 4. Styl feedbacku

Każda uwaga MUSI:
- odnosić się do konkretnego miejsca w kodzie
- jasno opisywać **problem**
- proponować **rozwiązanie** lub alternatywę

### Format:
[KATEGORIA] Opis problemu
→ Sugestia rozwiązania


### Przykład:
[Important] Brak obsługi null w odpowiedzi API
→ Dodaj walidację lub fallback przed użyciem danych


---

## 5. Na co zwracać szczególną uwagę

### Logika
- czy kod robi dokładnie to, co sugeruje nazwa
- czy warunki brzegowe są obsłużone
- czy nie ma ukrytych efektów ubocznych

### Czytelność
- długość funkcji
- zagnieżdżenia
- jasne nazwy zmiennych i metod
- powtarzalność kodu

### Bezpieczeństwo
- walidacja inputu
- sanitizacja danych
- brak hardcodowanych sekretów
- poprawne użycie auth / permissions

### Wydajność
- niepotrzebne pętle
- zbędne zapytania
- operacje w hot-pathach

---

## 6. Testy

Sprawdź:
- czy zmiany wymagają testów
- czy testy pokrywają nowe przypadki
- czy testy są czytelne i sensowne

Jeśli testów brakuje:
- zgłoś to jako `[Important]`

---

## 7. Dokumentacja i kontrakty

Zwracaj uwagę, czy zmiany:
- wymagają aktualizacji README / docs
- zmieniają API, kontrakty lub zachowanie
- mogą być breaking change

---

## 8. Zasady komunikacji

- bądź rzeczowy i spokojny
- nie oceniaj autora
- nie używaj sformułowań typu „to jest złe”
- preferuj: „to może powodować…”, „warto rozważyć…”

---

## 9. Czego NIE robić

- ❌ ogólne komentarze bez wskazania miejsca
- ❌ „LGTM” bez analizy
- ❌ przepisywanie całego kodu bez powodu
- ❌ narzucanie osobistych preferencji

---

## 10. Podsumowanie review

Na końcu ZAWSZE dodaj krótkie podsumowanie:
- ogólną ocenę jakości
- listę najważniejszych problemów (jeśli są)
- informację, czy kod jest gotowy do merge

### Przykład:
Podsumowanie:
Kod jest czytelny i spójny.
Wymaga poprawy obsługi błędów w module auth.
Po adresowaniu uwag typu Critical i Important — gotowy do merge.