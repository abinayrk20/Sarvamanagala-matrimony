# Sarvamangala Matrimony - Production Django REST Framework Backend

This is the production backend for **Sarvamangala Matrimony (Kanchipuram & Tamil Nadu)**, built with Django 4.2+, Django REST Framework, PostgreSQL, and WhiteNoise.

---

## 1. Features & Architecture

- **Mandatory ₹2,000 Registration Fee**:
  - GPay Payee Mobile: `9942006877` | UPI: `9942006877@upi`
  - Candidate registration sets user and profile to pending state.
  - Candidate submits 12-digit UTR (`/api/auth/submit-payment`).
  - Admin verifies payment in `/admin/` or `/sm-admin` -> sets status `PAID`, activates account, approves profile, and generates `RCP-2026-XXXX` receipt.
- **Strict Contact Helplines**:
  - Primary Contact: `8248853928` and `9942006877`
  - Official WhatsApp: `8248853928`
  - Zero presence of obsolete contact numbers.
- **Isolated Admin Management**:
  - No public links to the admin portal.
  - Accessible via Django standard admin `/admin/` and dedicated API endpoints under `/api/admin/`.
- **Database Flexibility**:
  - Automatically connects to PostgreSQL when `DATABASE_URL` is configured.
  - Falls back gracefully to SQLite for local development.

---

## 2. Quickstart & Local Setup

### Step 1: Install Requirements
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Step 3: Run Database Migrations
```bash
python manage.py makemigrations matrimony
python manage.py migrate
```

### Step 4: Seed Initial Data
Populate default membership plans, success stories, authentic testimonials, verified profiles, and admin credentials:
```bash
python manage.py seed_data
```
Default Administrator:
- **Email / Username**: `admin@sarvamangala.com`
- **Password**: `KanchiMangala@2026`

### Step 5: Start Development Server
```bash
python manage.py runserver 8000
```
- API Base: `http://localhost:8000/api/`
- Django Admin: `http://localhost:8000/admin/`

---

## 3. Production Deployment with PostgreSQL

### Render / Railway / Fly.io:
1. Set the following environment variables:
   - `DEBUG=False`
   - `SECRET_KEY=<your-secret-production-key>`
   - `DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DB_NAME`
   - `ALLOWED_HOSTS=your-domain.com,*.onrender.com`
   - `CORS_ALLOWED_ORIGINS=https://your-domain.com`
2. Build command:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py seed_data
   ```
3. Start command:
   ```bash
   gunicorn sarvamangala.wsgi:application --bind 0.0.0.0:$PORT
   ```

### Ubuntu VPS with Systemd + Nginx:
```ini
# /etc/systemd/system/sarvamangala.service
[Unit]
Description=Sarvamangala Matrimony Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sarvamangala/django_backend
EnvironmentFile=/var/www/sarvamangala/django_backend/.env
ExecStart=/var/www/sarvamangala/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 sarvamangala.wsgi:application

[Install]
WantedBy=multi-user.target
```
