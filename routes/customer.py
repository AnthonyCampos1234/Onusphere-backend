from models import customer
from models.order import Order
from models.account import Account
from models.customer import Customer
from utils.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/")
def get_customers_on_account(current_user: Account = Depends(get_current_user)):
    customers = Customer.objects(account=current_user) # type: ignore

    return [{"id": str(c.id), "name": c.name, "email_domain": c.email_domain} for c in customers]


@router.get("/{id}")
def get_customer(id: str, current_user: Account = Depends(get_current_user)):
    customer = Customer.objects(id=id, account=current_user).first()  # type: ignore
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "id": str(customer.pk),
        "name": customer.name,
        "email_domain": customer.email_domain,
    }

@router.get("/{id}/orders")
def get_orders_from_customer(id: str, current_user: Account = Depends(get_current_user)):
    customer = Customer.objects(id=id, account=current_user).first() # type: ignore
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = Order.objects(customer=customer) # type: ignore
    
    def serialize_order(order):
        return {
            "id": str(order.id),
            "items": [
                {
                    "item_id": str(oi.item.id),
                    "number_pallets": oi.number_pallets
                } for oi in order.items
            ],
            "order_date": order.order_date.isoformat(),
            "upcoming_shipment_times": order.upcoming_shipment_times,
            "loading_instructions": order.loading_instructions
        }

    return [serialize_order(order) for order in orders]
