
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Salesman(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: int = Field(index=True, unique=True)
    name: str
    username: str = Field(index=True, unique=True)
    password_hash: str

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: int = Field(index=True, unique=True)
    name: str = Field(index=True)
    phone: Optional[str] = None
    address: Optional[str] = None
    created_by: Optional[int] = None

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: int = Field(index=True, unique=True)
    name: str = Field(index=True)
    price: float
    stock: float = 0

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_no: str = Field(index=True, unique=True)
    customer_id: int = Field(index=True)
    salesman_id: int = Field(index=True)
    total: float = 0
    status: str = "posted"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InvoiceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(index=True)
    product_id: int = Field(index=True)
    product_code: int
    product_name: str
    unit_price: float
    quantity: float
    line_total: float

class StockMovement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(index=True)
    quantity_before: float
    quantity_change: float
    quantity_after: float
    movement_type: str
    reason: Optional[str] = None
    user_type: str = "system"
    user_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
