"""Pydantic request/response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]
MovementReason = Literal["restock", "sale", "return", "damaged", "correction"]


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=40, examples=["ELEC-1001"])
    name: str = Field(min_length=1, max_length=120, examples=["USB-C Charger 65W"])
    category: str = Field(min_length=1, max_length=60, examples=["Electronics"])
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)
    unit_price: float = Field(default=0, ge=0)
    supplier: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=60, examples=["Aisle 3 / Bin B"])


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """All fields optional: PUT accepts a partial or full update."""

    sku: str | None = Field(default=None, min_length=2, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    unit_price: float | None = Field(default=None, ge=0)
    supplier: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=60)


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_status: StockStatus
    created_at: datetime
    updated_at: datetime


class StockAdjustment(BaseModel):
    change: int = Field(description="Positive to add stock, negative to remove it")
    reason: MovementReason
    note: str | None = Field(default=None, max_length=200)


class MovementRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    change: int
    reason: str
    note: str | None
    created_at: datetime


class InventoryStats(BaseModel):
    total_products: int
    total_units: int
    inventory_value: float
    low_stock: int
    out_of_stock: int
    categories: dict[str, int]
