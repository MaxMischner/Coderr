# Coderr Backend (Django)

Backend‑API für das Coderr‑Frontend (Vanilla JS). Dieses Repository enthält sowohl Backend (Django/DRF) als auch das Frontend im Ordner `Coderr/`.

## Features

- Auth: Registrierung, Login (Token)
- Profile (Customer/Business)
- Offers + OfferDetails
- Orders
- Reviews
- Base‑Info Statistik
- Pagination & Filter

## Voraussetzungen

- Python 3.14
- Virtuelle Umgebung
- Abhängigkeiten aus `requirements.txt`

## Setup

```text
pip install -r requirements.txt
```

## Migrationen

```text
python Backend_Coderr/manage.py makemigrations
python Backend_Coderr/manage.py migrate
```

## Demo‑Daten

```text
python Backend_Coderr/manage.py seed_demo
```

Demo‑Logins:
- Business: `kevin / asdasd24`
- Customer: `andrey / asdasd`

## Backend starten

```text
python Backend_Coderr/manage.py runserver
```

API‑Base: `http://127.0.0.1:8000/api/`

## OpenAPI / Swagger

- Schema JSON: `http://127.0.0.1:8000/api/schema/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`

## Frontend starten

```text
python -m http.server 5500 --directory Coderr
```

Frontend: `http://127.0.0.1:5500/`

## Tests

```text
python Backend_Coderr/manage.py test
```

## Media / Uploads

- Uploads werden unter `media/` gespeichert
- Dev‑Serving ist aktiv

## CORS

Für lokale Entwicklung ist `http://127.0.0.1:5500` freigegeben.

## API‑Endpoints (Auszug)

- `POST /api/registration/`
- `POST /api/login/`
- `GET /api/base-info/`
- `GET /api/profile/{id}/`
- `PATCH /api/profile/{id}/`
- `GET /api/profiles/business/`
- `GET /api/profiles/customer/`
- `GET /api/offers/`
- `POST /api/offers/`
- `GET /api/offers/{id}/`
- `PATCH /api/offers/{id}/`
- `DELETE /api/offers/{id}/`
- `GET /api/offerdetails/{id}/`
- `GET /api/orders/`
- `POST /api/orders/`
- `PATCH /api/orders/{id}/`
- `DELETE /api/orders/{id}/`
- `GET /api/order-count/{business_user_id}/`
- `GET /api/completed-order-count/{business_user_id}/`
- `GET /api/reviews/`
- `POST /api/reviews/`
- `PATCH /api/reviews/{id}/`
- `DELETE /api/reviews/{id}/`
