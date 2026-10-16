def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "READY"


def test_root_describes_service(client):
    body = client.get("/").json()
    assert body["service"] == "StockPilot API"
    assert body["docs"] == "/docs"


def test_metrics_exposes_prometheus_format(client):
    client.get("/api/products")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
