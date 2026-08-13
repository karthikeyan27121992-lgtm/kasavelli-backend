# Kasavelli — Backend (Django)

Django REST API for the Kasavelli silver jewellery e-commerce platform.

## Tech Stack
- Python 3.10+ / Django 5.1
- Django REST Framework + SimpleJWT
- PostgreSQL
- Razorpay payment gateway
- Gunicorn + WhiteNoise (production)

## Local Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv myenv
source myenv/bin/activate   # Windows: myenv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start server
python manage.py runserver
```

API available at `http://localhost:8000`  
Admin panel at `http://localhost:8000/admin`

## Deploy to Render (free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New → Blueprint** → connect your repo
3. Render reads `render.yaml` and auto-creates the web service + PostgreSQL database
4. Add these environment variables in the Render dashboard:
   | Key | Value |
   |---|---|
   | `RAZORPAY_KEY_ID` | Your Razorpay key |
   | `RAZORPAY_KEY_SECRET` | Your Razorpay secret |
   | `FRONTEND_URL` | Your Cloudflare Pages URL (e.g. `https://kasavelli.pages.dev`) |

> `SECRET_KEY` and `DATABASE_URL` are auto-generated/linked by Render via `render.yaml`.

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | `True` for dev, `False` for prod | ✅ |
| `ALLOWED_HOSTS` | Comma-separated hostnames | ✅ |
| `DATABASE_URL` | Full PostgreSQL connection URL (production) | ✅ prod |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Individual DB vars (local dev) | ✅ local |
| `FRONTEND_URL` | Frontend origin added to CORS | prod |
| `RAZORPAY_KEY_ID` | Razorpay key ID | ✅ |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret | ✅ |

## API Endpoints

| Method | URL | Description |
|---|---|---|
| POST | `/api/users/users/` | Register |
| POST | `/api/users/users/login/` | Login |
| GET | `/api/products/products/` | List products |
| GET | `/api/users/cart/` | Get cart |
| POST | `/api/users/cart/` | Add to cart |
| POST | `/api/payments/create_order/` | Create Razorpay order |
| POST | `/api/payments/verify_payment/` | Verify payment |
# kasavelli-backend
