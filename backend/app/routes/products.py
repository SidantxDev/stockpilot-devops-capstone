"""Inventory REST API: products CRUD, stock adjustments and stats."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from prometheus_client import Counter
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api", tags=["inventory"])

STOCK_MOVEMENTS = Counter(
    "stockpilot_stock_movements_total",
    "Stock adjustments recorded, by reason",
    ["reason"],
)
STOCK_UNITS_MOVED = Counter(
    "stockpilot_stock_units_moved_total",
    "Absolute number of units moved, by direction",
    ["direction"],
)


def _get_product_or_404(db: Session, product_id: int) -> models.Product:
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


def _commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with this SKU already exists")


@router.get("/products", response_model=list[schemas.ProductRead])
def list_products(
    q: str | None = Query(default=None, description="Search name, SKU or supplier"),
    category: str | None = None,
    stock_status: schemas.StockStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(models.Product).order_by(models.Product.updated_at.desc(), models.Product.id.desc())
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(models.Product.name).like(like),
                func.lower(models.Product.sku).like(like),
                func.lower(models.Product.supplier).like(like),
            )
        )
    if category:
        stmt = stmt.where(models.Product.category == category)
    if stock_status == "out_of_stock":
        stmt = stmt.where(models.Product.quantity <= 0)
    elif stock_status == "low_stock":
        stmt = stmt.where(
            models.Product.quantity > 0, models.Product.quantity <= models.Product.reorder_level
        )
    elif stock_status == "in_stock":
        stmt = stmt.where(models.Product.quantity > models.Product.reorder_level)
    return db.scalars(stmt).all()


# Declared before /products/{product_id} so "stats" is not parsed as an id.
@router.get("/products/stats", response_model=schemas.InventoryStats)
def inventory_stats(db: Session = Depends(get_db)):
    products = db.scalars(select(models.Product)).all()
    categories: dict[str, int] = {}
    for p in products:
        categories[p.category] = categories.get(p.category, 0) + 1
    return schemas.InventoryStats(
        total_products=len(products),
        total_units=sum(p.quantity for p in products),
        inventory_value=round(sum(p.quantity * float(p.unit_price) for p in products), 2),
        low_stock=sum(1 for p in products if p.stock_status == "low_stock"),
        out_of_stock=sum(1 for p in products if p.stock_status == "out_of_stock"),
        categories=dict(sorted(categories.items())),
    )


@router.get("/products/{product_id}", response_model=schemas.ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return _get_product_or_404(db, product_id)


@router.post("/products", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**payload.model_dump())
    db.add(product)
    _commit_or_conflict(db)
    db.refresh(product)
    if product.quantity:
        db.add(models.StockMovement(
            product_id=product.id, change=product.quantity, reason="restock", note="Initial stock"
        ))
        db.commit()
    return product


@router.put("/products/{product_id}", response_model=schemas.ProductRead)
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    product = _get_product_or_404(db, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    _commit_or_conflict(db)
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_product_or_404(db, product_id)
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/products/{product_id}/adjust", response_model=schemas.ProductRead)
def adjust_stock(product_id: int, payload: schemas.StockAdjustment, db: Session = Depends(get_db)):
    if payload.change == 0:
        raise HTTPException(status_code=422, detail="change must not be zero")
    product = _get_product_or_404(db, product_id)
    new_quantity = product.quantity + payload.change
    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock: {product.quantity} on hand, tried to remove {-payload.change}",
        )
    product.quantity = new_quantity
    db.add(models.StockMovement(
        product_id=product.id, change=payload.change, reason=payload.reason, note=payload.note
    ))
    db.commit()
    db.refresh(product)
    STOCK_MOVEMENTS.labels(reason=payload.reason).inc()
    STOCK_UNITS_MOVED.labels(direction="in" if payload.change > 0 else "out").inc(abs(payload.change))
    return product


@router.get("/movements", response_model=list[schemas.MovementRead])
def recent_movements(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.execute(
        select(models.StockMovement, models.Product.name)
        .join(models.Product)
        .order_by(models.StockMovement.created_at.desc(), models.StockMovement.id.desc())
        .limit(limit)
    ).all()
    return [
        schemas.MovementRead(
            id=m.id, product_id=m.product_id, product_name=name, change=m.change,
            reason=m.reason, note=m.note, created_at=m.created_at,
        )
        for m, name in rows
    ]
