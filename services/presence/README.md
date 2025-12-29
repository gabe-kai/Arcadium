# Presence Service

Online status and presence tracking service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables and run migrations

3. Start the service:
```bash
flask run --port 8001
```

## API Endpoints

- `GET /api/presence/<user_id>` - Get user presence status
- `POST /api/presence/<user_id>` - Update user presence status
