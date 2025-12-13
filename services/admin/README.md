# Admin Service

Administrative dashboard service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables and run migrations

3. Start the service:
```bash
flask run --port 8005
```

## API Endpoints

- `GET /` - Admin dashboard
- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/users` - List all users

