from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_route():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scan_dashboard_and_pdf_routes():
    payload = {
        "domain": "finance",
        "autonomy_level": "high",
        "human_oversight": False,
        "decision_impacts_persons": True,
        "logging_present": True,
    }
    response = client.post("/scan", json=payload)
    assert response.status_code == 200
    scan_id = response.json()["scan_id"]
    assert response.json()["tier"] == "high-risk"

    dashboard = client.get(f"/dashboard/{scan_id}")
    assert dashboard.status_code == 200
    assert "text/html" in dashboard.headers["content-type"]
    assert "HIGH-RISK" in dashboard.text

    pdf = client.get(f"/report/{scan_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
