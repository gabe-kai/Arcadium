"""Test health check endpoint"""


def test_health_check(client):
    """Test that health check endpoint works and conforms to standard format"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()

    # Required fields
    assert data["status"] == "healthy"
    assert data["service"] == "wiki"
    assert "version" in data

    # Process info (required by standard)
    assert "process_info" in data
    process_info = data["process_info"]
    assert "pid" in process_info
    assert "uptime_seconds" in process_info
    assert "cpu_percent" in process_info
    assert "memory_mb" in process_info
    assert "memory_percent" in process_info
    assert "threads" in process_info
    assert "open_files" in process_info

    # Optional dependencies field (wiki checks auth service)
    if "dependencies" in data:
        assert isinstance(data["dependencies"], dict)


def test_health_check_response_format(client):
    """Test that health check response matches standard format exactly"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()

    # Verify all required fields are present
    required_fields = ["status", "service", "version", "process_info"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Verify process_info structure
    process_info = data["process_info"]
    required_process_fields = [
        "pid",
        "uptime_seconds",
        "cpu_percent",
        "memory_mb",
        "memory_percent",
        "threads",
        "open_files",
    ]
    for field in required_process_fields:
        assert field in process_info, f"Missing required process_info field: {field}"

    # Verify status is valid
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
