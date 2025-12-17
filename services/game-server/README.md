# Game Server

Core game logic and multiplayer server built with Go.

## Setup

1. Install dependencies:
```bash
go mod download
```

2. Set up environment variables:
```bash
# Option 1: Using arcadium_user and arcadium_pass (recommended)
export arcadium_user=arcadium
export arcadium_pass=your-secure-password
export DB_NAME=arcadium_game_server

# Option 2: Using DATABASE_URL directly
export DATABASE_URL=postgresql://arcadium:your-secure-password@localhost:5432/arcadium_game_server
export AUTH_SERVICE_URL=http://localhost:8000
export PORT=8080
```

3. Run the server:
```bash
go run cmd/server/main.go
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/game/status` - Game server status
- `WS /ws` - WebSocket connection for real-time game communication

