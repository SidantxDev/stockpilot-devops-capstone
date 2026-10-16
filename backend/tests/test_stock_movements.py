def test_adjust_stock_records_movement(client, created_product):
    pid = created_product["id"]
    response = client.post(f"/api/products/{pid}/adjust", json={"change": -5, "reason": "sale", "note": "Order #42"})
    assert response.status_code == 200
    assert response.json()["quantity"] == 15

    movements = client.get("/api/movements").json()
    assert movements[0]["change"] == -5
    assert movements[0]["reason"] == "sale"
    assert movements[0]["product_name"] == "Barcode Scanner"


def test_adjust_stock_cannot_go_negative(client, created_product):
    response = client.post(
        f"/api/products/{created_product['id']}/adjust", json={"change": -999, "reason": "sale"}
    )
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_adjust_stock_rejects_unknown_reason(client, created_product):
    response = client.post(
        f"/api/products/{created_product['id']}/adjust", json={"change": 1, "reason": "magic"}
    )
    assert response.status_code == 422


def test_adjust_stock_increments_business_metric(client, created_product):
    client.post(f"/api/products/{created_product['id']}/adjust", json={"change": 7, "reason": "restock"})
    metrics = client.get("/metrics").text
    assert 'stockpilot_stock_movements_total{reason="restock"}' in metrics


def test_deleting_product_removes_its_movements(client, created_product):
    pid = created_product["id"]
    client.post(f"/api/products/{pid}/adjust", json={"change": 1, "reason": "return"})
    client.delete(f"/api/products/{pid}")
    assert client.get("/api/movements").json() == []
