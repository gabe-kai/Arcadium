# Development Conventions

This document outlines development conventions and standards for the Arcadium project. These conventions ensure consistency across the codebase and help maintain code quality.

## Database Naming

All Arcadium databases use a consistent naming convention with the `arcadium_` prefix.

### Production/Development Databases
- **Pattern**: `arcadium_<service_name>`
- **Examples**: `arcadium_wiki`, `arcadium_auth`, `arcadium_game_server`

### Test Databases
- **Pattern**: `arcadium_testing_<service_name>`
- **Examples**: `arcadium_testing_wiki`, `arcadium_testing_auth`, `arcadium_testing_game_server`

**See**: [Database Naming Convention](architecture/database-naming-convention.md) for complete details.

## Environment Variables

### Database Credentials
- Use `arcadium_user` and `arcadium_pass` for database credentials (recommended)
- Or use `DATABASE_URL` directly if preferred
- Services automatically construct `DATABASE_URL` from `arcadium_user` and `arcadium_pass` if not set

**See**: [Database Credentials](architecture/database-credentials.md) for complete details.

## Service Architecture

### Health Endpoints
All services must implement a standardized health check endpoint at `/health`.

**See**: [Health Endpoint Standard](services/health-endpoint-standard.md) for implementation details.

### Service Communication
- HTTP REST APIs for service-to-service communication
- JWT tokens for user authentication
- Service tokens for service-to-service calls
- Shared code libraries in `shared/` directory

**See**: [Service Architecture](services/service-architecture.md) for complete details.

## Code Quality

### Pre-commit Hooks
The project uses pre-commit hooks to ensure code quality:
- Trailing whitespace removal
- End of file fixer
- Code formatting (black, isort)
- Linting (ruff)
- Merge conflict detection
- YAML/JSON validation

**See**: [README.md](../README.md#pre-commit-hooks) for setup instructions.

### Testing
- All services should have comprehensive test coverage
- Tests use PostgreSQL (not SQLite) for accurate testing
- Test databases use `arcadium_testing_` prefix

**See**: [CI/CD Documentation](ci-cd.md) for testing standards.

## Project Structure

### Monorepo Organization
- Shared virtual environment for all Python services
- Service-specific dependencies in `services/<service>/requirements.txt`
- Shared code in `shared/` directory
- Documentation in `docs/` directory

**See**: [README.md](../README.md) for project structure details.

## Wiki Content Writing

When writing wiki pages or content:
1. Always refer to `docs/wiki-ai-content-management.md` for complete instructions
2. Write markdown files with YAML frontmatter to `services/wiki/data/pages/`
3. Use `parent_slug` (not `parent_id`) in frontmatter
4. Always set `created_by: "admin"` and `updated_by: "admin"`
5. After writing files, run: `python -m app.sync sync-all`

**See**: [Wiki AI Content Management](wiki-ai-content-management.md) for details.

## Related Documentation

- [Architecture Documentation](architecture/README.md) - Architecture decisions and infrastructure
- [Service Documentation](services/README.md) - Service specifications and standards
- [CI/CD Documentation](ci-cd.md) - Continuous integration and deployment standards
