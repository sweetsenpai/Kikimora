from unittest.mock import MagicMock

import pytest

from ..api_views.products.products_views import sort_products


@pytest.mark.parametrize(
    "sort_by,expected_order_by",
    [
        ("price_asc", "price"),
        ("price_des", "-price"),
        ("weight_asc", "weight"),
        ("weight_des", "-weight"),
    ],
)
def test_sort_producst_applies_correct_ordering(sort_by, expected_order_by):
    mock_qs = MagicMock()
    mock_qs.order_by.return_value = f"Ordered by {expected_order_by}"

    result = sort_products(mock_qs, sort_by)

    mock_qs.order_by.assert_called_once_with(expected_order_by)
    assert result == f"Ordered by {expected_order_by}"


def test_sort_producst_does_nothing_for_invalid_param():
    mock_qs = MagicMock()
    mock_qs.order_by.return_value = mock_qs  # на случай если случайно вызовется

    result = sort_products(mock_qs, "invalid_param")

    mock_qs.order_by.assert_not_called()
    assert result == mock_qs
