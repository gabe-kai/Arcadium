# Asset Service

Asset/CDN management service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables and run migrations

3. Start the service:
```bash
flask run --port 8004
```

## API Endpoints

- `GET /api/assets` - List all assets
- `GET /api/assets/<asset_id>` - Get asset metadata
- `POST /api/assets` - Upload a new asset
- `GET /api/assets/<asset_id>/download` - Download an asset
