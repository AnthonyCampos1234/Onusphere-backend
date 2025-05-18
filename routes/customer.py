from models.types import Account, Member, Customer, Order, Item
from utils.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

class CreateCustomerRequest(BaseModel):
    name: str
    email_domain: str

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
    customer = Customer.objects(id=id, account=current_user).first()  # type: ignore
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = Order.objects(customer=customer)  # type: ignore

    def serialize_order(order):
        return {
            "id": str(order.pk),
            "order_batches": [
                {
                    "order_batch_id": str(ob.id),
                    "number_pallets": ob.number_pallets,
                    "item": {
                        "item_id": str(ob.item_id.id),
                        "item_number": ob.item_id.item_number,
                        "description": ob.item_id.description,
                        "units_per_pallet": ob.item_id.units_per_pallet
                    } if ob.item_id else None
                }
                for ob in order.order_item_ids
            ],
            "order_date": order.order_date.isoformat(),
            "shipment_times": order.shipment_times,
            "status": order.status,
            "loading_instructions": order.loading_instructions or []
        }

    return [serialize_order(order) for order in orders]


@router.post("/")
def create_customer(customer_data: CreateCustomerRequest, current_user: Account = Depends(get_current_user)):
    customer = Customer(
        name=customer_data.name,
        email_domain=customer_data.email_domain,
        account=current_user
    ).save()
    
    return {
        "id": str(customer.id),
        "name": customer.name,
        "email_domain": customer.email_domain
    }
