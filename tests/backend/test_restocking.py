"""
Tests for restocking API endpoints (recommendations and submitted orders).
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_submitted_orders():
    """Submitted orders live in a module-level list, so reset it around each test."""
    main.submitted_orders.clear()
    yield
    main.submitted_orders.clear()


def get_forecasts(client):
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


def gap(forecast):
    return max(forecast["forecasted_demand"] - forecast["current_demand"], 0)


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_zero_budget_returns_no_items(self, client):
        """Test that a zero budget recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining"] == 0
        assert data["max_useful_budget"] > 0

    def test_response_structure(self, client):
        """Test that recommendations have the expected fields and types."""
        data = client.get("/api/restocking/recommendations?budget=5000").json()
        for key in ["budget", "total_cost", "remaining", "max_useful_budget", "items"]:
            assert key in data

        assert len(data["items"]) > 0
        for item in data["items"]:
            for key in ["sku", "name", "trend", "current_demand", "forecasted_demand",
                        "quantity", "unit_cost", "line_total", "lead_time_days"]:
                assert key in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] > 0
            assert item["line_total"] == pytest.approx(item["quantity"] * item["unit_cost"])

    def test_large_budget_covers_every_gap(self, client):
        """Test that a budget above the max recommends every positive-gap item in full."""
        forecasts = get_forecasts(client)
        data = client.get("/api/restocking/recommendations?budget=1000000").json()

        expected = {sku for sku, f in forecasts.items() if gap(f) > 0}
        assert {i["sku"] for i in data["items"]} == expected
        for item in data["items"]:
            assert item["quantity"] == gap(forecasts[item["sku"]])

        assert data["total_cost"] == pytest.approx(data["max_useful_budget"])

    def test_items_without_gap_are_excluded(self, client):
        """Test that items whose demand is flat or falling are never recommended."""
        forecasts = get_forecasts(client)
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        for item in data["items"]:
            assert gap(forecasts[item["sku"]]) > 0

    def test_increasing_trend_ranks_first(self, client):
        """Test that all increasing-trend items come before any other trend."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        trends = [i["trend"] for i in data["items"]]
        first_other = next((n for n, t in enumerate(trends) if t != "increasing"), len(trends))
        assert all(t != "increasing" for t in trends[first_other:])

    @pytest.mark.parametrize("budget", [1, 100, 500, 2500, 7000, 11000])
    def test_total_never_exceeds_budget(self, client, budget):
        """Test that partial fills keep the total within the budget."""
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        assert data["total_cost"] <= budget
        assert data["remaining"] == pytest.approx(budget - data["total_cost"])

    def test_partial_fill_of_top_item(self, client):
        """Test that a small budget buys as many units of the top item as it can afford."""
        data = client.get("/api/restocking/recommendations?budget=1000000").json()
        top = data["items"][0]

        budget = top["unit_cost"] * 3 + 1
        small = client.get(f"/api/restocking/recommendations?budget={budget}").json()
        assert small["items"][0]["sku"] == top["sku"]
        assert small["items"][0]["quantity"] == 3

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=-5")
        assert response.status_code == 400
        assert "detail" in response.json()


class TestRestockOrders:
    """Test suite for POST and GET /api/restocking/orders."""

    def test_no_orders_initially(self, client):
        """Test that the submitted orders list starts empty."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_submit_order_and_list_it(self, client):
        """Test that a submitted order is returned and then listed."""
        rec = client.get("/api/restocking/recommendations?budget=3000").json()
        payload = {
            "budget": 3000,
            "items": [{"sku": i["sku"], "quantity": i["quantity"]} for i in rec["items"]],
        }

        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["total_value"] == pytest.approx(rec["total_cost"])
        assert len(order["items"]) == len(rec["items"])

        listed = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in listed] == [order["id"]]

    def test_orders_listed_newest_first(self, client):
        """Test that the most recently submitted order is listed first."""
        payload = {"budget": 1000, "items": [{"sku": "GSK-203", "quantity": 1}]}
        first = client.post("/api/restocking/orders", json=payload).json()
        second = client.post("/api/restocking/orders", json=payload).json()

        listed = client.get("/api/restocking/orders").json()
        assert [o["id"] for o in listed] == [second["id"], first["id"]]

    def test_lead_time_is_longest_item(self, client):
        """Test that order lead time equals the slowest item's lead time."""
        forecasts = get_forecasts(client)
        skus = ["GSK-203", "CTL-330"]
        payload = {"budget": 10000, "items": [{"sku": s, "quantity": 1} for s in skus]}

        order = client.post("/api/restocking/orders", json=payload).json()
        assert order["lead_time_days"] == max(forecasts[s]["lead_time_days"] for s in skus)

    def test_expected_delivery_matches_lead_time(self, client):
        """Test that expected delivery is the submit date plus the lead time."""
        from datetime import datetime

        payload = {"budget": 1000, "items": [{"sku": "GSK-203", "quantity": 1}]}
        order = client.post("/api/restocking/orders", json=payload).json()

        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert (expected - submitted).days == order["lead_time_days"]

    def test_server_prices_are_used(self, client):
        """Test that line totals use server-side unit costs."""
        forecasts = get_forecasts(client)
        payload = {"budget": 10000, "items": [{"sku": "WDG-001", "quantity": 10}]}
        order = client.post("/api/restocking/orders", json=payload).json()
        assert order["items"][0]["unit_cost"] == forecasts["WDG-001"]["unit_cost"]
        assert order["total_value"] == pytest.approx(10 * forecasts["WDG-001"]["unit_cost"])

    def test_over_budget_rejected(self, client):
        """Test that an order costing more than the budget returns 400."""
        payload = {"budget": 10, "items": [{"sku": "CTL-330", "quantity": 1}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking/orders").json() == []

    def test_unknown_sku_rejected(self, client):
        """Test that an unknown SKU returns 400."""
        payload = {"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    def test_empty_order_rejected(self, client):
        """Test that an order with no items returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client):
        """Test that a zero quantity returns 400."""
        payload = {"budget": 1000, "items": [{"sku": "GSK-203", "quantity": 0}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

    def test_duplicate_sku_rejected(self, client):
        """Test that listing the same SKU twice returns 400."""
        payload = {"budget": 1000, "items": [{"sku": "GSK-203", "quantity": 1},
                                             {"sku": "GSK-203", "quantity": 1}]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400
