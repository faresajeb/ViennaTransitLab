
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_all_stops():
    response = client.get("/api/v1/stops")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_filter_metro_stops():
    response = client.get("/api/v1/stops?mode=metro")

    assert response.status_code == 200

    stops = response.json()

    assert len(stops) == 2
    assert all("metro" in stop["modes"] for stop in stops)


def test_filter_tram_stops():
    response = client.get("/api/v1/stops?mode=tram")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_bus_stops():
    response = client.get("/api/v1/stops?mode=bus")

    assert response.status_code == 200
    assert response.json() == []


def test_search_stops():
    response = client.get("/api/v1/stops?search=karlsplatz")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Karlsplatz"


def test_combined_filters():
    response = client.get(
        "/api/v1/stops?mode=metro&search=karlsplatz"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_stop_by_id():
    response = client.get("/api/v1/stops/mock-001")

    assert response.status_code == 200
    assert response.json()["name"] == "Stephansplatz"


def test_stop_not_found():
    response = client.get("/api/v1/stops/nonexistent")

    assert response.status_code == 404


def test_stop_response_schema():
    response = client.get("/api/v1/stops")

    assert response.status_code == 200

    required_fields = {
        "stop_id",
        "station_id",
        "name",
        "latitude",
        "longitude",
        "modes",
        "route_ids",
    }

    for stop in response.json():
        assert required_fields.issubset(stop)
        assert isinstance(stop["modes"], list)
        assert isinstance(stop["route_ids"], list)


def test_invalid_search_length():
    response = client.get(
        "/api/v1/stops",
        params={"search": "a" * 101},
    )

    assert response.status_code == 422
