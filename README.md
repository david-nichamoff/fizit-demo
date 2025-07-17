# FIZIT Demo

FIZIT is a blockchain-based settlement platform designed for the industrial energy sector. It enables secure, auditable, and automated B2B payments using smart contracts, IoT integrations, and API-driven workflows.

This repository contains a Django-based implementation of the FIZIT platform architecture, showcasing core components such as:

- Smart contract interaction via Avalanche C-Chain  
- Encrypted data management and contract logic execution  
- RESTful API with Swagger documentation  
- Admin dashboard for contract management  
- Modular Django app structure for scalability  

---

## 🛠️ Getting Started

Follow these instructions to set up your local development environment.

### 1. Set Up Python & Virtual Environment

Install Python:  
https://www.python.org/downloads/

```bash
# Create and enter project directory
mkdir FIZIT_DEV && cd FIZIT_DEV

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Edit the following file to include your PYTHONPATH
nano .venv/bin/activate
# Add this line (update path as needed):
# export PYTHONPATH=/Users/yourname/Projects/FIZIT_DEV/packages
```

### 2. Install Dependencies

```bash
pip install django
pip install -r requirements.txt
```

### 3. Set Up the Project

```bash
django-admin startproject project .
python manage.py startapp api
python manage.py startapp frontend
```

Project structure:

```
FIZIT_DEV/
├── .venv/
├── project/
├── api/
└── frontend/
```

### 4. Run Migrations and Create Superuser

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start the Server

```bash
python manage.py runserver
```

Access the app at:  
http://127.0.0.1:8000/

---

## 🔍 Live Demo

A live instance of the FIZIT Demo is available:

- **API (Swagger UI)**  
  https://sandbox.fizit.biz/api/schema/swagger-ui/#/  
  _Read-only access is available without credentials. An API key is required for full access._

- **Admin Dashboard**  
  https://sandbox.fizit.biz/admin/
  
  _Login required._

To request an API key or admin login for demo purposes, please contact:  
📧 **david.nichamoff@gmail.com**
