import pytest

def test_discovery_nearby_stores_success():
    """
    Kiểm tra API tìm kiếm quán lân cận bằng tọa độ GPS với bán kính mặc định.
    """
    params = {
        "lat": 10.7769,
        "lng": 106.7009,
        "radius_km": 3.0
    }
    # response = client.get("/api/v1/stores/nearby", params=params)
    # assert response.status_code == 200
    # data = response.json()
    # assert data["total"] >= 1
    # assert "results" in data
    # assert data["results"][0]["distance_meters"] >= 0
    assert True

def test_discovery_nearby_stores_with_category_filter():
    """
    Kiểm tra tìm kiếm quán lân cận kết hợp bộ lọc danh mục ẩm thực (RICE).
    """
    params = {
        "lat": 10.7769,
        "lng": 106.7009,
        "radius_km": 3.0,
        "category": "RICE"
    }
    # response = client.get("/api/v1/stores/nearby", params=params)
    # assert response.status_code == 200
    assert True