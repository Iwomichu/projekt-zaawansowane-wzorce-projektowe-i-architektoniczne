# Użyte wzorce projektowe
## Identity Map
### Użycie
SQLAlchemy używa tego wzorca dla obiektów zarządzanych w obrębie sesji. Więcej: https://docs.sqlalchemy.org/en/20/glossary.html#term-identity-map
### Klasy
Wszystkie klasy obsługiwane przez SQLAlchemy, tj. wszystkie dziedziczące z `BaseModel`.
### Uzasadnienie / Korzyści
Wszystkie odwołania do konkretnego obiektu w bazie zostają zaaplikowanego dla dokładnie jednej instancji reprezentacji tego obiektu w aplikacji (przynajmniej w obrębie jednej sesji).

## Data mapper
### Użycie
SQLAlchemy używa tego wzorca do tłumaczenia definicji klasy na SQL. Poza samym stworzeniem klas (tj. ukrytym tworzeniem mapowania), użytkownicy klasy nie muszą nic wiedzieć o tym gdzie i jak przechowywane są instancje (natomiast w tym kodzie jest ta wiedza wykorzystywana, tj. są często tworzone zapytania w języku SQL z użyciem konkretnych, unikalnie Postgresowych funkcji).
### Klasy
Wszystkie klasy obsługiwane przez SQLAlchemy, tj. wszystkie dziedziczące z `BaseModel`, np. `Supply`
### Uzasadnienie / Korzyści
W prostych sytuacjach brak narzutu związanego z pamiętaniem o strukturze obiektów w bazie (tj. używanie obiektów jakby były natywnym Pythonowymi obiektami zamiast encjami w bazie, np. iterowanie po "dzieciach" rodzica).

## Lazy load
### Użycie
SQLAlchemy używa tego wzorca dla pól składowych klas mapowanych do bazy danych będących osobnymi encjami w bazie. Więcej: https://docs.sqlalchemy.org/en/20/glossary.html#term-lazy-loading
### Klasy
Klasy obsługiwane przez SQLAlchemy, których pola składowe są również odrębnymi encjami w bazie, np. `Order`.
### Uzasadnienie / Korzyści
Często zdarza się, że pomimo zaczytania całej kolekcji z bazy, chcemy odwołać się tylko do niektórych atrybutów otrzymanych obiektów. Jednocześnie, czasami chcemy odwołać się do pól obiektów będących polami w tych obiektach (np. po zaczytaniu obiektu klasy `Order`, chcemy dowiedzieć się jaka jest wartość pola `last_name` dla `Order.order_personal_information`). Dzięki lazy loadingu tych pól są one doczytywane dopiero w momencie dostępu, co w przypadku dominacji pierwszego typu interakcji z obiektem, nie spowalnia działania oraz nie zwiększa zużycia pamięci programu.

## Query object
### Użycie
Wzorzec implementowany przez SQLAlchemy m.in. w klasie `select` oraz metodzie `Session.query`.
### Klasy
Używany w większości klas typu `Workflow`, np. `HandleArrivingRetailPackageWorkflow`.
### Uzasadnienie / Korzyści
Pozwala na wykonywanie zapytań odwołujących się do różnych encji w bazie przy użyciu klas na które są mapowane w aplikacji. Dzięki temu refactor tych klas jest łatwiejszy (np. w porządnym IDE można zmienić nazwę pola i zostanie ona odwzorowana we wszystkich zapytaniach w których jest użyte; jeśli byłby to plain SQL to konieczny byłby Find&Replace) oraz brak konieczności implementacji podstawowych ułatwień, takich jak obrona przez SQL Injection.
## Foreign Key Mapping
### Użycie
Wzorzec implementowany przez SQLAlchemy w klasach, gdzie występuje odwołanie do innej klasy odwzorowującej encję w bazie danych, np. `SupplyOffer.supply`.
### Klasy
Na przykład `SupplyOffer.supply`, `WarehouseProduct.product`, itd.
### Uzasadnienie / Korzyści
Pozwala na łatwy dostęp do pól obiektu będącej w rzeczywistości inną encją w bazie danych, tj. zamiast wykonywać nowe zapytanie explicit za każdym odwołaniem, można odnieść się jak do pola składowego obiektu.
## Association Table Mapping
Wszystkie cechy podobnie jak dla Foreign Key Mapping tylko w sytuacji, gdzie występuje relacja wiele do wielu, np. tabela `warehouse_time_windows_associate_table`.
## Template View
### Użycie
Wzorzec implementowany przez Jinja dla całej warstwy prezentacji.
### Klasy
Wszystkie instancje klasy `APIRouter`, np. `zwpa.routers.retail.router`.
### Uzasadnienie / Korzyści
Najbardziej podstawowy sposób serwowania dynamicznej treści, który nie wymaga znajomości JavaScriptu i pozwala skupiać się na warstwie logicznej.
## Server Session State
### Użycie
Wzorzec implementowany przez aplikacje w pakiecie `cart_manager`.
### Klasy
Dla głownego serwera jest on realizowany przez interfejs `CartManager` tj. przez jego implementacje `RestCartManager` wykorzystującą aplikację z pakietu `cart_manager`.
### Uzasadnienie / Korzyści
Ponieważ zaistniała konieczność przechowywania sesji użytkownika (w stopniu bardziej zaawansowanym niż domyślne zachowanie przeglądarki jak np. dla autentykacji), wybrałem ten wzorzec ponieważ dawał mi największą kontrolę nad tym jak ma się zachowywać sesja użytkownika oraz jaki dostęp jest do niej możliwy.
##  Transaction Script
### Użycie / Klasy
Wzorzec implementowany poprzez klasy typu `Workflow`, gdzie każda taka klasa implementuje każdą procedurę, np. `InitializeCartManagerWorkflow`.
### Uzasadnienie / Korzyści
Z powodu łatwego podziału przewidywanej funkcjonalności na autonomiczne procedury serwisu (synchronizowane dopiero przez bazę danych) zastosowałem najprostszy wzorzec, który jednocześnie pozwala na łatwą rozbudowę serwisu poprzez dodawanie kolejnych endpointów realizujących nowe procedury.