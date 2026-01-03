# Token Validation Utilities

Shared JWT token validation utilities for use across all services.

## Installation

These utilities require the `PyJWT` package:

```bash
pip install PyJWT
```

## Usage

### Basic Token Validation

```python
from shared.auth.tokens import validate_jwt_token

# Validate a JWT token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
secret = "your-jwt-secret-key"

payload = validate_jwt_token(token, secret)
if payload:
    print(f"Token is valid. User ID: {payload['user_id']}")
else:
    print("Token is invalid or expired")
```

### Extract User Information

```python
from shared.auth.tokens import validate_jwt_token, get_token_user_id, get_token_role

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
secret = "your-jwt-secret-key"

payload = validate_jwt_token(token, secret)
if payload:
    user_id = get_token_user_id(payload)
    role = get_token_role(payload)
    print(f"User ID: {user_id}, Role: {role}")
```

### Check Token Expiration

```python
from shared.auth.tokens import validate_jwt_token, is_token_expired

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
secret = "your-jwt-secret-key"

payload = validate_jwt_token(token, secret)
if payload and not is_token_expired(payload):
    print("Token is valid and not expired")
```

### Service Token Validation

```python
from shared.auth.tokens import validate_service_token, get_service_name

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
secret = "your-jwt-secret-key"

payload = validate_service_token(token, secret)
if payload:
    service_name = get_service_name(payload)
    print(f"Valid service token from: {service_name}")
```

## Functions

### `validate_jwt_token(token: str, secret: str, algorithm: str = "HS256") -> dict | None`

Validate and decode a JWT token. Returns the decoded payload if valid, None otherwise.

### `decode_token(token: str, secret: str, algorithm: str = "HS256") -> dict | None`

Decode a JWT token without validation (for debugging only). **WARNING**: Does not validate signature or expiration.

### `is_token_expired(token_payload: dict) -> bool`

Check if a token payload indicates the token is expired.

### `get_token_user_id(token_payload: dict) -> UUID | None`

Extract user ID from token payload as a UUID.

### `get_token_role(token_payload: dict) -> str | None`

Extract role from token payload.

### `validate_service_token(token: str, secret: str, algorithm: str = "HS256") -> dict | None`

Validate a service token for service-to-service authentication.

### `get_service_name(token_payload: dict) -> str | None`

Extract service name from service token payload.

### `get_service_id(token_payload: dict) -> str | None`

Extract service ID from service token payload.

### `is_service_token(token_payload: dict) -> bool`

Check if a token payload represents a service token.
