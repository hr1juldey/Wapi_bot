"""Unit tests for transform atomic node."""

import pytest
from nodes.atomic import transform


@pytest.mark.asyncio
async def test_transform_filter_data():
    """Test transform with simple filter transformer."""
    state = {
        "all_services": [
            {"name": "Car Wash", "vehicle_type": "Hatchback"},
            {"name": "SUV Wash", "vehicle_type": "SUV"},
            {"name": "Basic Wash", "vehicle_type": "Hatchback"}
        ],
        "vehicle": {"vehicle_type": "Hatchback"}
    }

    # Filter transformer
    def filter_by_type(services, state):
        vtype = state.get("vehicle", {}).get("vehicle_type")
        return [s for s in services if s["vehicle_type"] == vtype]

    result = await transform.node(state, filter_by_type, "all_services", "filtered_services")

    # Should have 2 Hatchback services
    assert "filtered_services" in result
    assert len(result["filtered_services"]) == 2
    assert all(s["vehicle_type"] == "Hatchback" for s in result["filtered_services"])


@pytest.mark.asyncio
async def test_transform_format_data():
    """Test transform with formatter."""
    state = {
        "services": [
            {"product_name": "Premium Wash", "base_price": 499},
            {"product_name": "Basic Wash", "base_price": 299}
        ]
    }

    # Format transformer
    def format_catalog(services, state):
        lines = []
        for svc in services:
            lines.append(f"{svc['product_name']} - ₹{svc['base_price']}")
        return "\n".join(lines)

    result = await transform.node(state, format_catalog, "services", "formatted_catalog")

    assert "formatted_catalog" in result
    assert "Premium Wash - ₹499" in result["formatted_catalog"]
    assert "Basic Wash - ₹299" in result["formatted_catalog"]


@pytest.mark.asyncio
async def test_transform_calculate_data():
    """Test transform with calculator."""
    state = {
        "booking_data": {
            "base_price": 500,
            "addons": [{"price": 100}, {"price": 200}]
        }
    }

    # Calculate transformer
    def calculate_total(data, state):
        base = data.get("base_price", 0)
        addons_total = sum(a["price"] for a in data.get("addons", []))
        return base + addons_total

    result = await transform.node(state, calculate_total, "booking_data", "total_price")

    assert result["total_price"] == 800


@pytest.mark.asyncio
async def test_transform_empty_source_skip():
    """Test transform with empty source and skip mode."""
    state = {
        "customer": {"first_name": "Rahul"}
    }

    def noop_transformer(data, s):
        return data

    # Source path doesn't exist, should skip
    result = await transform.node(
        state,
        noop_transformer,
        "missing_field",
        "target",
        on_empty="skip"
    )

    # Target should not be created
    assert "target" not in result
    # No errors
    assert "errors" not in result


@pytest.mark.asyncio
async def test_transform_empty_source_default():
    """Test transform with empty source and default mode."""
    state = {"customer": {"first_name": "Rahul"}}

    def noop_transformer(data, s):
        return data

    result = await transform.node(
        state,
        noop_transformer,
        "missing_field",
        "target",
        on_empty="default"
    )

    # Target should be set to None
    assert "target" in result
    assert result["target"] is None


@pytest.mark.asyncio
async def test_transform_empty_source_raise():
    """Test transform with empty source and raise mode."""
    state = {}

    def noop_transformer(data, s):
        return data

    # Should raise ValueError
    with pytest.raises(ValueError, match="Source path 'missing_field' is empty"):
        await transform.node(
            state,
            noop_transformer,
            "missing_field",
            "target",
            on_empty="raise"
        )


@pytest.mark.asyncio
async def test_transform_transformer_error():
    """Test error handling when transformer fails."""
    state = {
        "data": [1, 2, 3]
    }

    def failing_transformer(data, s):
        raise ValueError("Transformation failed intentionally")

    result = await transform.node(state, failing_transformer, "data", "result")

    # Should log error in state
    assert "transform_error_result" in result.get("errors", [])
    # Result should not be set
    assert "result" not in result


@pytest.mark.asyncio
async def test_transform_nested_source_target():
    """Test transform with nested field paths."""
    state = {
        "api_responses": {
            "services": {
                "data": [
                    {"id": 1, "name": "Service 1"},
                    {"id": 2, "name": "Service 2"}
                ]
            }
        }
    }

    def extract_names(data, s):
        return [item["name"] for item in data]

    result = await transform.node(
        state,
        extract_names,
        "api_responses.services.data",
        "service_names"
    )

    assert result["service_names"] == ["Service 1", "Service 2"]
