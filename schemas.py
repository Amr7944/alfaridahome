from typing import Optional, List, Union
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    salesman_id: int
    salesman_name: str

class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class InvoiceItemCreate(BaseModel):
    product_id: Union[int, str]  # يقبل المعرف الرقمي (id) أو الكود (code)
    quantity: float

class InvoiceCreate(BaseModel):
    customer_id: int
    items: List[InvoiceItemCreate]

class StockAdjustment(BaseModel):
    product_id: Union[int, str]  # يقبل المعرف الرقمي (id) أو الكود (code)
    quantity_change: float
    reason: str