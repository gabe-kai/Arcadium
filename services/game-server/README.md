# Game Server

Core game logic and multiplayer server built with Go.

## Setup

1. Install dependencies:
```bash
go mod download
```

2. Set up environment variables:
```bash
export DATABASE_URL=postgresql://arcadium:arcadium_dev@localhost:5432/arcadium
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

