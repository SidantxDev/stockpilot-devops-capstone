def test_list_products_starts_empty(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.json() == []


def test_create_product(client, sample_product):
    response = client.post("/api/products", json=sample_product)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["sku"] == "TEST-0001"
    assert body["stock_status"] == "in_stock"


def test_create_product_rejects_duplicate_sku(client, created_product, sample_product):
    response = client.post("/api/products", json=sample_product)
    assert response.status_code == 409


def test_create_product_validates_input(client):
    response = client.post("/api/products", json={"sku": "X", "name": "", "category": "A", "quantity": -1})
    assert response.status_code == 422


def test_get_product_by_id(client, created_product):
    response = client.get(f"/api/products/{created_product['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Barcode Scanner"


def test_get_missing_product_returns_404(client):
    response = client.get("/api/products/9999")
    assert response.status_code == 404


def test_update_product(client, created_product):
    response = client.put(
        f"/api/products/{created_product['id']}",
        json={"quantity": 3, "unit_price": 1999.5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 3
    assert body["unit_price"] == 1999.5
    assert body["stock_status"] == "low_stock"
    assert body["name"] == "Barcode Scanner"  # untouched fields are preserved


def test_delete_product(client, created_product):
    response = client.delete(f"/api/products/{created_product['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/products/{created_product['id']}").status_code == 404


def test_filter_products_by_status_and_search(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.post("/api/products", json={**sample_product, "sku": "TEST-0002", "name": "Label Printer", "quantity": 0})

    out = client.get("/api/products", params={"status": "out_of_stock"}).json()
    assert [p["sku"] for p in out] == ["TEST-0002"]

    found = client.get("/api/products", params={"q": "label"}).json()
    assert [p["name"] for p in found] == ["Label Printer"]


def test_inventory_stats(client, sample_product):
    client.post("/api/products", json=sample_product)  # 20 x 2499
    client.post("/api/products", json={**sample_product, "sku": "TEST-0002", "category": "Packaging",
                                       "quantity": 2, "reorder_level": 5, "unit_price": 10})
    stats = client.get("/api/products/stats").json()
    assert stats["total_products"] == 2
    assert stats["total_units"] == 22
    assert stats["inventory_value"] == 20 * 2499 + 2 * 10
    assert stats["low_stock"] == 1
    assert stats["out_of_stock"] == 0
    assert stats["categories"] == {"Electronics": 1, "Packaging": 1}
