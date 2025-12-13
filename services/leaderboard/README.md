# Leaderboard Service

Stats and rankings service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables and run migrations

3. Start the service:
```bash
flask run --port 8003
```

## API Endpoints

- `GET /api/leaderboard/<leaderboard_type>` - Get leaderboard rankings
- `GET /api/leaderboard/<leaderboard_type>/<user_id>` - Get user's rank
- `POST /api/leaderboard/<leaderboard_type>/<user_id>` - Update user score

