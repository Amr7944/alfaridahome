from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from pathlib import Path
from db import init_db, get_session
from models import Salesman, Customer, Product, Invoice, InvoiceItem, StockMovement
from schemas import LoginRequest, TokenResponse, CustomerCreate, InvoiceCreate, StockAdjustment
from security import verify_password, create_token, salesman_id_from_token
import uuid
from datetime import datetime

app = FastAPI(title="Sales Invoice API", version="1.0.0")
security = HTTPBearer()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

def current_salesman(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    try:
        sid = salesman_id_from_token(credentials.credentials)
    except Exception:
        raise HTTPException(401, "Invalid token")

    salesman = session.get(Salesman, sid)

    if not salesman:
        raise HTTPException(401, "User not found")

    return salesman

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(Salesman).where(Salesman.username == body.username)).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    return TokenResponse(access_token=create_token(user.id), salesman_id=user.id, salesman_name=user.name)

@app.get("/customers")
def customers(q: str = "", session: Session = Depends(get_session), user=Depends(current_salesman)):
    stmt = select(Customer).order_by(Customer.name)
    rows = session.exec(stmt).all()
    q = q.strip().lower()
    if q:
        rows = [x for x in rows if q in x.name.lower() or q in str(x.code) or q in (x.phone or "").lower()]
    return rows[:100]

@app.post("/customers")
def add_customer(body: CustomerCreate, session: Session = Depends(get_session), user=Depends(current_salesman)):
    max_code = session.exec(select(Customer)).all()
    next_code = max([c.code for c in max_code], default=0) + 1
    c = Customer(code=next_code, name=body.name.strip(), phone=body.phone, address=body.address, created_by=user.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c

@app.get("/products")
def products(q: str = "", session: Session = Depends(get_session), user=Depends(current_salesman)):
    rows = session.exec(select(Product).order_by(Product.name)).all()
    q = q.strip().lower()
    if q:
        rows = [x for x in rows if q in x.name.lower() or q in str(x.code)]
    return rows[:100]

@app.post("/invoices")
def create_invoice(body: InvoiceCreate, session: Session = Depends(get_session), user=Depends(current_salesman)):
    customer = session.get(Customer, body.customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    if not body.items:
        raise HTTPException(400, "Invoice has no items")

    invoice = Invoice(
        invoice_no="INV-" + datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6].upper(),
        customer_id=customer.id,
        salesman_id=user.id,
        total=0,
        status="posted"
    )
    session.add(invoice)
    session.flush()

    total = 0
    for req in body.items:
        # البحث عن المنتج بواسطة id أو بواسطة code
        stmt = select(Product).where(
            (Product.id == req.product_id) | (Product.code == req.product_id)
        )
        product = session.exec(stmt).first()

        if not product:
            raise HTTPException(404, f"Product {req.product_id} not found")
        if req.quantity <= 0:
            raise HTTPException(400, "Quantity must be greater than zero")
        if product.stock < req.quantity:
            raise HTTPException(400, f"Insufficient stock for {product.name}")
        line = product.price * req.quantity
        total += line
        session.add(InvoiceItem(
            invoice_id=invoice.id, product_id=product.id, product_code=product.code,
            product_name=product.name, unit_price=product.price,
            quantity=req.quantity, line_total=line
        ))
        before = product.stock
        product.stock -= req.quantity
        session.add(StockMovement(
            product_id=product.id, quantity_before=before,
            quantity_change=-req.quantity, quantity_after=product.stock,
            movement_type="sale", reason=f"Invoice {invoice.invoice_no}",
            user_type="salesman", user_id=user.id
        ))
        session.add(product)

    invoice.total = total
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice

@app.get("/invoices")
def invoices(session: Session = Depends(get_session), user=Depends(current_salesman)):
    rows = session.exec(select(Invoice).where(Invoice.salesman_id == user.id).order_by(Invoice.created_at.desc())).all()
    return rows

@app.get("/admin/invoices")
def admin_invoices(session: Session = Depends(get_session)):
    return session.exec(select(Invoice).order_by(Invoice.created_at.desc())).all()

@app.get("/admin/stock")
def admin_stock(session: Session = Depends(get_session)):
    return session.exec(select(Product).order_by(Product.code)).all()

@app.post("/admin/stock/adjust")
def adjust_stock(body: StockAdjustment, session: Session = Depends(get_session)):
    product = session.get(Product, body.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    before = product.stock
    after = before + body.quantity_change
    if after < 0:
        raise HTTPException(400, "Stock cannot become negative")
    product.stock = after
    session.add(product)
    session.add(StockMovement(
        product_id=product.id, quantity_before=before,
        quantity_change=body.quantity_change, quantity_after=after,
        movement_type="manual", reason=body.reason, user_type="admin"
    ))
    session.commit()
    return product

@app.get("/admin", include_in_schema=False)
def admin_page():
    p = Path(__file__).resolve().parents[2] / "admin" / "index.html"
    return FileResponse(p)
