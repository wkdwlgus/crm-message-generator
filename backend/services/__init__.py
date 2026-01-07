"""
Services module
비즈니스 로직 및 외부 서비스 연동
"""
from .mock_data import get_mock_customer, get_mock_product

__all__ = [
    "get_mock_customer",
    "get_mock_product",
]
