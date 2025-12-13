# Wiki Service

Documentation and planning wiki service built with Python/Flask.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run migrations:
```bash
flask db upgrade
```

4. Start the service:
```bash
flask run
```

## API Endpoints

- `GET /` - Wiki homepage
- `GET /api/pages` - List all pages
- `GET /api/pages/<page_id>` - Get a specific page
- `POST /api/pages` - Create a new page

