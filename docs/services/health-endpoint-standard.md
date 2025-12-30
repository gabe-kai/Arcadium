# Health Endpoint Standard

All Arcadium services must implement a standardized health check endpoint that provides consistent metadata for service monitoring and management.

## Endpoint

**Path:** `GET /health`
**Response Code:** `200 OK` (when service is healthy)

## Response Format

All health endpoints must return a JSON response with the following structure:

```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "service": "service-name",
  "version": "1.0.0",
  "process_info": {
    "pid": 12345,
    "uptime_seconds": 3600.0,
    "cpu_percent": 2.5,
    "memory_mb": 150.0,
    "memory_percent": 1.2,
    "threads": 8,
    "open_files": 5
  },
  "dependencies": {
    "auth_service": {
      "status": "reachable" | "unreachable",
      "url": "http://localhost:8000"
    }
  },
  "additional_info": {}
}
```

## Required Fields

### Core Fields

- **`status`** (string, required): Service health status
  - `"healthy"`: Service is fully operational
  - `"degraded"`: Service is operational but with reduced functionality
  - `"unhealthy"`: Service is not operational

- **`service`** (string, required): Service identifier (e.g., "wiki", "auth", "game-server")

- **`version`** (string, required): Service version (e.g., "1.0.0")

### Process Information

- **`process_info`** (object, required): Process metadata
  - **`pid`** (integer): Process ID
  - **`uptime_seconds`** (float): Process uptime in seconds
  - **`cpu_percent`** (float): CPU usage percentage
  - **`memory_mb`** (float): Memory usage in megabytes
  - **`memory_percent`** (float): Memory usage as percentage of system memory
  - **`threads`** (integer): Number of threads
  - **`open_files`** (integer): Number of open file descriptors (0 on Windows)

### Optional Fields

- **`dependencies`** (object, optional): Status of service dependencies
  - Each dependency should have a `status` field indicating reachability
  - May include additional metadata (URL, response codes, etc.)

- **`additional_info`** (object, optional): Service-specific information
  - Database connection status
  - Cache status
  - Queue status
  - Other service-specific metrics

## Implementation

### Using the Standard Utility

All Python services should use the `health_check` utility module:

```python
from app.utils.health_check import get_health_status
from flask import jsonify

@app.route("/health")
def health():
    """Health check endpoint"""
    health_status = get_health_status(
        service_name="your-service-name",
        version="1.0.0",
        additional_info={
            "database": "connected",
            "cache": "operational"
        },
        include_process_info=True
    )
    return jsonify(health_status), 200
```

### Manual Implementation

If you cannot use the utility (e.g., non-Python services), ensure your implementation matches the standard format:

1. **Include all required fields**
2. **Use `psutil` for process information** (Python) or equivalent for other languages
3. **Keep response time < 500ms** - health checks should be fast
4. **Don't block on external services** - use short timeouts
5. **Always return 200 OK** - even if degraded/unhealthy (status is in the response body)

## Performance Requirements

- **Response Time:** < 500ms (target: < 200ms)
- **Timeout:** Health checks should not block on external services
- **Resource Usage:** Minimal CPU/memory overhead
- **Windows Compatibility:** Skip `open_files()` on Windows (it's extremely slow)

## Example Implementations

### Python (Flask) - Using Utility

```python
from flask import Blueprint, jsonify
from app.utils.health_check import get_health_status

bp = Blueprint("health", __name__)

@bp.route("/health")
def health():
    health_status = get_health_status(
        service_name="my-service",
        version="1.0.0",
        include_process_info=True
    )
    return jsonify(health_status), 200
```

### Python (Flask) - Manual

```python
import os
import time
import platform
from flask import jsonify

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

@app.route("/health")
def health():
    health_status = {
        "status": "healthy",
        "service": "my-service",
        "version": "1.0.0"
    }

    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            with process.oneshot():
                create_time = process.create_time()
                uptime_seconds = time.time() - create_time
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                cpu_percent = process.cpu_percent(interval=None)
                memory_percent = process.memory_percent()
                threads = process.num_threads()

                # Skip open_files() on Windows
                if platform.system() == "Windows":
                    open_files = 0
                else:
                    open_files = len(process.open_files())

            health_status["process_info"] = {
                "pid": process.pid,
                "uptime_seconds": round(uptime_seconds, 2),
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2),
                "threads": threads,
                "open_files": open_files,
            }
        except Exception:
            health_status["process_info"] = {
                "pid": os.getpid(),
                "uptime_seconds": 0.0,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "memory_percent": 0.0,
                "threads": 0,
                "open_files": 0,
            }

    return jsonify(health_status), 200
```

### Node.js/Express

```javascript
const express = require('express');
const router = express.Router();
const os = require('os');
const process = require('process');

router.get('/health', (req, res) => {
  const uptime = process.uptime();
  const memoryUsage = process.memoryUsage();
  const cpuUsage = process.cpuUsage();

  const healthStatus = {
    status: 'healthy',
    service: 'my-service',
    version: '1.0.0',
    process_info: {
      pid: process.pid,
      uptime_seconds: uptime,
      cpu_percent: 0.0, // Node.js doesn't provide easy CPU % - may need external library
      memory_mb: memoryUsage.heapUsed / (1024 * 1024),
      memory_percent: (memoryUsage.heapUsed / os.totalmem()) * 100,
      threads: 0, // Node.js is single-threaded (worker threads not counted here)
      open_files: 0, // Would need external library
    }
  };

  res.status(200).json(healthStatus);
});
```

## Testing

Health endpoints should be tested to ensure:

1. **Response format matches standard**
2. **All required fields are present**
3. **Process information is accurate**
4. **Response time is acceptable**
5. **Works correctly when psutil is unavailable**

Example test:

```python
def test_health_endpoint(client):
    """Test health endpoint returns standard format"""
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.get_json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "process_info" in data
    assert "pid" in data["process_info"]
    assert "uptime_seconds" in data["process_info"]
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
```

## Migration Guide

### For Existing Services

1. **Install `psutil`** (if not already installed):
   ```bash
   pip install psutil
   ```

2. **Copy the health check utility** to your service:
   ```bash
   cp services/wiki/app/utils/health_check.py services/your-service/app/utils/
   ```

3. **Update your health endpoint** to use the utility:
   ```python
   from app.utils.health_check import get_health_status

   @app.route("/health")
   def health():
       return jsonify(get_health_status("your-service", "1.0.0")), 200
   ```

4. **Test the endpoint**:
   ```bash
   curl http://localhost:PORT/health | jq
   ```

5. **Verify in Service Management page** - the service should now show process information

## Checklist

When implementing or updating a health endpoint, ensure:

- [ ] Endpoint path is `/health`
- [ ] Returns JSON with all required fields
- [ ] Includes `process_info` with all fields
- [ ] Response time < 500ms
- [ ] Doesn't block on external services
- [ ] Handles psutil unavailability gracefully
- [ ] Skips `open_files()` on Windows
- [ ] Returns 200 OK status code
- [ ] Includes service name and version
- [ ] Tested and verified in Service Management page

## References

- **Service Management Page:** `/services` (admin only)
- **Service Status Service:** `services/wiki/app/services/service_status_service.py`
- **Health Check Utility:** `services/wiki/app/utils/health_check.py`
- **Example Implementation:** `services/auth/app/__init__.py` (health endpoint)
