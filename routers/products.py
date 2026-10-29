from fastapi import APIRouter
from dependencies import Paging

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/")
def list_products(paging: Paging):
    return {
        "skip": paging["skip"],
        "limit": paging["limit"],
        "products": [
            {"id": 1, "name": "Pen"},
            {"id": 2, "name": "Notebook"}
        ]
    }


@router.get("/{product_id}")
def get_product(product_id: int):
    return {
        "id": product_id,
        "name": "Sample product"
    }
