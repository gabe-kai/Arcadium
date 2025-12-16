"""Test health check endpoint"""
def test_health_check(client):
    """Test that health check endpoint works"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'wiki'

