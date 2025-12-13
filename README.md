# Arcadium

A multiplayer online game project with wiki service, game server, and web client.

## Project Structure

- `services/` - All microservices (wiki, game-server, auth, presence, chat, leaderboard, assets, admin)
- `client/` - Web client application
- `shared/` - Shared code across services (protocols, auth, utils)
- `infrastructure/` - Infrastructure as code (docker, database, scripts)
- `docs/` - Project documentation

## Getting Started

See individual service READMEs for specific setup instructions.

## Development

```bash
# Start all services with Docker Compose
docker-compose up

# Start specific services
docker-compose up wiki game-server client
```

## Services

- **Wiki Service** (Python/Flask) - Documentation and planning wiki
- **Game Server** (Go) - Core game logic and multiplayer server
- **Auth Service** - Authentication and user management
- **Presence Service** - Online status and presence tracking
- **Chat Service** - Real-time messaging
- **Leaderboard Service** - Stats and rankings
- **Asset Service** - Asset/CDN management
- **Admin Service** - Administrative dashboard

## License

[To be determined]

