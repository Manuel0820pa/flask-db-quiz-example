def test_health_endpoint(app):
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_endpoint_content_type(app):
    client = app.test_client()
    response = client.get("/api/health")
    assert response.content_type == "application/json"