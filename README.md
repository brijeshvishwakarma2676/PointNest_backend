# PointNest

**Developed by Brijesh Vishwakarma**

A robust, production-ready FastAPI backend designed to manage customer loyalty programs, purchases, and point systems for small-to-medium businesses.

## Features

- **User Authentication**: Secure registration and login flow using direct `bcrypt` hashing and JWT tokens.
- **Customer Management**: Add and look up customers instantly by phone or email.
- **Loyalty Points System**: Programmatically issue reward points based on purchase amounts (1 point per 10 currency units).
- **Scalable Database Strategy**: Built with `SQLAlchemy` ORM, safely supporting connections with AWS TiDB Serverless (MySQL).
- **Standardized API Error Handling**: Global exception handler providing a uniformly flattened JSON response shape.
- **Dynamic Worker Support**: Runs smoothly under `Uvicorn` for local development or heavily optimized `Gunicorn` workers on Linux environments.

## Quickstart

### Prerequisites

- Python 3.10+
- A running MySQL/TiDB database instance.

### Installation

1. **Clone & Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
pip install gunicorn  # (Required if running on Linux)
```

3. **Environment Variables**
   Create a `.env` file in the root directory by copying the example:

```bash
cp .env.example .env
```

Update `.env` with your secure database credentials.

4. **Run the Application**

```bash
python main.py
```

### Automatic API Documentation

Once the server is running, the interactive interactive OpenAPI UI will be available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```text
.
├── app
│   ├── api/v1/endpoints/  # Route definitions
│   ├── config/            # DB Session and Environment config
│   ├── core/              # Global constants and Exception handlers
│   ├── models/            # SQLAlchemy Database Models
│   ├── repositories/      # Database logic and Queries
│   ├── schemas/           # Pydantic Schemas (Request/Response models)
│   ├── services/          # Pure Business Logic
├── main.py                # Server Entrypoint
└── requirements.txt
```
