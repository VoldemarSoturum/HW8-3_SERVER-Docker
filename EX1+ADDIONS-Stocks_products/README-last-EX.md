# Stocks & Products API (DRF)

REST API для управления продуктами и складами с вложенными позициями (через промежуточную модель). Реализованы CRUD, поиск, фильтрация и пагинация. Покрыто автотестами.

## Содержание
- [Технологии](#технологии)
- [Запуск проекта](#запуск-проекта)
- [Конфигурация DRF](#конфигурация-drf)
- [Модели и диаграмма БД](#модели-и-диаграмма-бд)
- [Эндпоинты](#эндпоинты)
- [Примеры запросов (HTTP file)](#примеры-запросов-http-file)
- [Скриншоты выполнения запросов](#скриншоты-выполнения-запросов)
- [Скриншоты БД (после запросов)](#скриншоты-бд-после-запросов)
- [Тесты](#тесты)
- [Полезные команды](#полезные-команды)
- [!!!!Дополнительная функциональность по заданию!!!!!](#ДОПОЛНИТЕЛЬНАЯ-ФУНКЦИОНАЛЬНОСТЬ-ПО-ЗАДАНИЮ)

---

## Технологии
- Python 3.11+
- Django 3.2+ / 4.x
- Django REST Framework
- django-filter
- SQLite / PostgreSQL (на выбор)

---

## Запуск проекта

```bash
# создать и активировать venv (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# установить зависимости
pip install -r requirements.txt

#Создать БД и раздать права

psql -U postgres -h 127.0.0.1 -p 5432  


CREATE DATABASE netology_stocks_products;CREATE ROLE netology_stocks LOGIN PASSWORD 'netology_stocks'; GRANT ALL PRIVILEGES ON DATABASE netology_stocks_products TO netology_stocks;ALTER ROLE netology_stocks WITH CREATEDB;

\c netology_stocks_products

GRANT USAGE, CREATE ON SCHEMA public TO netology_stocks; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO netology_stocks; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO netology_stocks; GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO netology_stocks; ALTER DEFAULT PRIVILEGES FOR ROLE netology_stocks IN SCHEMA public GRANT ALL ON TABLES TO netology_stocks; ALTER DEFAULT PRIVILEGES FOR ROLE netology_stocks IN SCHEMA public GRANT ALL ON SEQUENCES TO netology_stocks; ALTER DEFAULT PRIVILEGES FOR ROLE netology_stocks IN SCHEMA public GRANT ALL ON FUNCTIONS TO netology_stocks;



# применить миграции
python manage.py migrate

# (опционально) создать суперпользователя
python manage.py createsuperuser

# запустить сервер
python manage.py runserver
```

Базовый URL в примерах ниже:
```
http://localhost:8000/api/v1
```

---

## Конфигурация DRF

В `settings.py`:
```python
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
```

---

## Модели и диаграмма БД

- `Product(id, title, description?)`
- `Stock(id, address)`
- `StockProduct(stock -> Stock, product -> Product, quantity, price)` — промежуточная модель (позиции на складе)

**Диаграмма БД:**

> ![DB Diagram](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/netology_stocks_products%20-%20public.png)

---

## Эндпоинты

### Products
- `GET /products/` — список (поиск `?search=` по `title`, `description`, пагинация `?page=`)
- `POST /products/` — создать
- `GET /products/{id}/` — получить
- `PATCH /products/{id}/` — частично обновить
- `DELETE /products/{id}/` — удалить

### Stocks
- `GET /stocks/` — список складов (фильтр: `?products=<id>` — показать только склады, где есть этот продукт; в ответе товары/позиции «режутся» под этот фильтр)
- `POST /stocks/` — создать склад с вложенными `positions`
- `GET /stocks/{id}/` — получить склад
- `PATCH /stocks/{id}/` — обновить склад и его позиции (upsert + удаление отсутствующих)
- `DELETE /stocks/{id}/` — удалить

---

## Примеры запросов (HTTP file)

Сохраните как `requests-examples.http` (поддерживается в VS Code / IntelliJ / HTTP Client):

```http
# примеры API-запросов

@baseUrl = http://localhost:8000/api/v1

# создание продукта
POST {{baseUrl}}/products/
Content-Type: application/json

{
  "title": "Помидор",
  "description": "Лучшие помидоры на рынке"
}

###

# получение продуктов
GET {{baseUrl}}/products/
Content-Type: application/json

###

# обновление продукта
PATCH {{baseUrl}}/products/1/
Content-Type: application/json

{
  "description": "Самые сочные и ароматные помидорки"
}

###

# удаление продукта
DELETE {{baseUrl}}/products/1/
Content-Type: application/json


#================================


### Создадим несколько продуктов для наглядности
POST {{baseUrl}}/products/
Content-Type: application/json

{
  "title": "Помидор черри",
  "description": "Свежие мини-помидоры для салатов"
}

###
POST {{baseUrl}}/products/
Content-Type: application/json

{
  "title": "Огурец длинный",
  "description": "Хрустящий, отличный для салатов с помидорами"
}

###
POST {{baseUrl}}/products/
Content-Type: application/json

{
  "title": "Базилик",
  "description": "Травяной аромат, сочетается с томатами (помидорами)"
}


#=========================================



###

# поиск продуктов по названию и описанию
GET {{baseUrl}}/products/?search=помидор
Content-Type: application/json

#===========================================

### Поиск продуктов по названию И описанию (SearchFilter ищет во всех указанных полях)
GET {{baseUrl}}/products/?search=помидор
Content-Type: application/json

### Пример: поиск по нескольким словам (ищутся по отдельности, регистр не важен)
GET {{baseUrl}}/products/?search=помидор%20салат
Content-Type: application/json

### Пример: пагинация результатов (если PAGE_SIZE=10, это покажет вторую страницу)
GET {{baseUrl}}/products/?search=помидор&page=2
Content-Type: application/json

#===========================================



###

# создание склада
POST {{baseUrl}}/stocks/
Content-Type: application/json

{
  "address": "мой адрес не дом и не улица, мой адрес сегодня такой: www.ленинград-спб.ru3",
  "positions": [
    {
      "product": 2,
      "quantity": 250,
      "price": 120.50
    },
    {
      "product": 3,
      "quantity": 100,
      "price": 180
    }
  ]
}

###
# Вывести список складов 
GET {{baseUrl}}/stocks/

###
# обновляем записи на складе
PATCH {{baseUrl}}/stocks/1/
Content-Type: application/json

{
  "positions": [
    {
      "product": 2,
      "quantity": 100,
      "price": 130.80
    },
    {
      "product": 3,
      "quantity": 243,
      "price": 145
    }
  ]
}

###

# поиск складов, где есть определенный продукт
GET {{baseUrl}}/stocks/?products=2
Content-Type: application/json
```

---

## Скриншоты выполнения запросов

> Положите изображения в `docs/` и вставьте сюда ссылки.  
> Можно добавить краткое описание под каждым скрином.

- Создание продукта:  
 > ![create-product](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195311.png)

- Список продуктов:  
  > ![list-products](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195311.png)

- Список обновление продуктов:  
  > ![update-products](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195400.png)

- Удаление продукта:  
  > ![delete-products](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195419.png)

- Создание продуктов:  
  > ![create-products-1](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195440.png)
  > ![create-products-2](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195457.png)
  > ![create-products-3](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20195513.png)

- Поиск по названию и описанию продукта `?search=помидор`:  
  > ![search-products](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20200003.png)


- Поиск по нескольким словам`?search=помидор`:  
  > ![search-products-someWrd](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20200151.png)

- Пагенация:  
  > ![pagination-products](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20200219.png)
  
- Создание склада с позициями:  
  > ![create-stock](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20200310.png)
- Вывод склада с позициями:  
  > ![view-stock](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20201054.png)
  
- Обновление позиций на складе (PATCH):  
  > ![patch-stock-positions](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20201225.png)

- Фильтр складов `?products=2`:  
  > ![filter-stocks-by-product](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20203022.png)

---

## Скриншоты БД (после запросов)

- Диаграмма БД:  
  > ![db-diagram](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/netology_stocks_products%20-%20public.png)

- Таблица `product` (после заполнения):  
  > ![db-products-table](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20210829.png)

- Таблица `stock`:  
  > ![db-stocks-table](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20210847.png)

- Таблица `stockproduct` (позиции):  
  > ![db-stockproducts-table](https://github.com/VoldemarSoturum/HW7-6_DJANGO-CRUD_in_DRF/blob/main/EX1%2BADDIONS-Stocks_products/FOR_README/2025-10-26%20210907.png)

---

## Тесты

Запуск всех тестов:
```bash
python manage.py test
```

Что покрыто:
- CRUD для `Product`;
- поиск `?search=`;
- создание `Stock` с вложенными `positions`;
- обновление (upsert) позиций и удаление отсутствующих;
- фильтрация `GET /stocks/?products=<id>` и «сужение» вложенных `products/positions` под фильтр.

---

## Полезные команды

- Очистить данные (dev):
  ```bash
  python manage.py flush --no-input
  ```
- Создать суперпользователя:
  ```bash
  python manage.py createsuperuser
  ```
- Просроченные сессии:
  ```bash
  python manage.py clearsessions
  ```

## ДОПОЛНИТЕЛЬНАЯ ФУНКЦИОНАЛЬНОСТЬ ПО ЗАДАНИЮ

### Поиск складов по названию/описанию продукта 

Реализован расширенный поиск складов через параметр `?search=`, который ищет не только по адресу склада, но и по **названию** и **описанию** связанных продуктов.

**Пример:**
```
GET /stocks/?search=помид
```
Вернёт все склады, где:
- присутствует товар, у которого `title` **или** `description` содержит «помид».

> Примечание: фильтр `?search=` **не обрезает** вложенные поля `products/positions` в ответе. Сужение вложенных данных включается только для запроса вида `?products=<id>`.

### Поведение поиска продуктов (`/products/?search=`)

Поиск по продуктам с `SearchFilter` выполняется по полям `title` **и** `description` (подстрочное, без учёта регистра). Поэтому запрос вида:
```
GET /products/?search=помидор
```
вернёт как товары с «помидор» в **названии**, так и товары, где «помидор» встречается в **описании**.

