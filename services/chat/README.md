# Chat Service

Real-time messaging service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables and run migrations

3. Start the service:
```bash
flask run --port 8002
```

## API Endpoints

- `GET /api/chat/channels` - List all chat channels
- `GET /api/chat/channels/<channel_id>/messages` - Get messages from a channel
- `POST /api/chat/channels/<channel_id>/messages` - Send a message to a channel

