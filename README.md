# Hospital Management System API

A production-ready, highly structured RESTful API for managing hospital operations, built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, **Stripe Integration**, and **Automated Email Verification**.

---

## 🌟 Key Features

* **User Management & Auth**: JWT-based authentication, role-based access control (Admin, Doctor, Patient, Staff), and secure automated email account verification via **FastMail**.
* **Appointments & Scheduling**: Dynamic doctor availability, appointment booking, and status tracking.
* **Medical Records**: Comprehensive patient medical histories, clinical diagnoses, and prescriptions.
* **Billing & Payments**: Invoice generation, Stripe Checkout integration, and webhook payment reconciliation.
* **Database Migrations**: Version-controlled relational schema migrations using Alembic.

---

## 📁 Project Architecture

```text
housphtel/
│
├── alembic/                # Database migration scripts
├── app/
│   ├── models/             # Domain modules
│   │   ├── appointments/   # Models, Schemas, Router, Services
│   │   ├── billing/        # Invoices and billing management
│   │   ├── medical_records/# Medical charts & records
│   │   ├── scheduling/     # Doctor slots & shift management
│   │   └── users/          # Authentication & User profiles
│   │
│   ├── payment/            # Stripe API & Webhook service layer
│   ├── config.py           # Centralized Pydantic Settings
│   ├── database.py         # SQLAlchemy engine & session setup
│   ├── main.py             # FastAPI entrypoint & middleware
│   └── security.py         # Password hashing & JWT token handling
│
├── .env                    # Environment variables (Ignored by Git)
├── .gitignore              # Git exclusion configuration
├── alembic.ini             # Alembic setup configuration
├── README.md               # Project documentation
└── requirements.txt        # Project dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10+
* PostgreSQL Database instance

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone <repository-url>
cd housphtel

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory based on the following template:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/hospital_db

# Security & JWT
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# System Initial Admin Credentials
FIRST_ADMIN_EMAIL=admin@hospital.com
FIRST_ADMIN_PASSWORD=AdminPassword123!

# Email Service Configuration
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

# Payment Gateway (Stripe)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
BASE_URL=http://127.0.0.1:8000
```

### 4. Database Migration

Run Alembic migrations to construct the database tables:

```bash
alembic upgrade head
```

### 5. Running the Application

Start the development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

Access the interactive API documentation at:
* **Swagger UI**: `http://127.0.0.1:8000/docs`
* **ReDoc**: `http://127.0.0.1:8000/redoc`
```
eof

I have generated the entire `README.md` file in a single file block. You can copy the raw markdown directly or view it in the editor. Is there anything else you need to finalize before committing to Git?