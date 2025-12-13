# Auth Service

Authentication and user management service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables and run migrations

3. Start the service:
```bash
flask run --port 8000
```

## API Endpoints

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get token
- `POST /api/auth/verify` - Verify authentication token

