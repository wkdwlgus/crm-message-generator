"""
Pydantic models for the CRM message generation system
"""
from .user import CustomerProfile, LastPurchase, ShoppingBehavior, CouponProfile, LastEngagement, CartItem, PurchaseHistoryItem
from .product import Product, ProductCategory, ProductPrice, ProductReview, ProductAnalytics
from .persona import Persona
from .brand import BrandProfile
from .message import GeneratedMessage, MessageResponse, ErrorResponse

__all__ = [
    # User models
    "CustomerProfile",
    "LastPurchase",
    "ShoppingBehavior",
    "CouponProfile",
    "LastEngagement",
    "CartItem",
    "PurchaseHistoryItem",
    # Product models
    "Product",
    "ProductCategory",
    "ProductPrice",
    "ProductReview",
    "ProductAnalytics",
    # Persona
    "Persona",
    # Brand
    "BrandProfile",
    # Message
    "GeneratedMessage",
    "MessageResponse",
    "ErrorResponse",
]
