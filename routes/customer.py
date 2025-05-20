from models.types import Account, Member, Customer, Order, Item
from utils.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime

class CreateCustomerRequest(BaseModel):
    name: str
    email_domain: str

router = APIRouter()

@router.get("/")
def get_customers_on_account(current_user: Member = Depends(get_current_user)):
    account = current_user.account  # Extract account from member
    customers = Customer.objects(account=account)  # type: ignore

    return [{"id": str(c.id), "name": c.name, "email_domain": c.email_domain} for c in customers]

@router.get("/{id}")
def get_customer(id: str, current_user: Member = Depends(get_current_user)):
    account = current_user.account
    customer = Customer.objects(id=id, account=account).first()  # type: ignore
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "id": str(customer.pk),
        "name": customer.name,
        "email_domain": customer.email_domain,
    }

@router.get("/{id}/orders")
def get_orders_from_customer(id: str, current_user: Member = Depends(get_current_user)):
    account = current_user.account
    customer = Customer.objects(id=id, account=account).first()  # type: ignore
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
                        "units_per_pallet": ob.item_id.units_per_pallet,
                        "height": ob.item_id.height,
                        "width": ob.item_id.width,
                        "length": ob.item_id.length
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


@router.get("/{id}/unique-items")
def get_unique_items_for_customer(id: str, current_user: Member = Depends(get_current_user)):
    account = current_user.account
    customer = Customer.objects(id=id, account=account).first()  # type: ignore
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = Order.objects(customer=customer)  # type: ignore

    unique_items = {}
    for order in orders:
        for ob in order.order_item_ids:
            item = ob.item_id
            if item and str(item.id) not in unique_items:
                unique_items[str(item.id)] = {
                    "item_id": str(item.id),
                    "item_number": item.item_number,
                    "description": item.description,
                    "units_per_pallet": item.units_per_pallet,
                }

    return list(unique_items.values())

@router.post("/")
def create_customer(customer_data: CreateCustomerRequest, current_user: Member = Depends(get_current_user)):
    account = current_user.account
    customer = Customer(
        name=customer_data.name,
        email_domain=customer_data.email_domain,
        account=account
    ).save()

    return {
        "id": str(customer.id),
        "name": customer.name,
        "email_domain": customer.email_domain,
    }

@router.post("/{id}/update-name")
def update_customer_name(
    id: str,
    new_name: str = Body(...),
    current_user: Member = Depends(get_current_user)
):
    customer = Customer.objects(id=id, account=current_user.account).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.name = new_name
    customer.save()

    return {"id": str(customer.id), "name": customer.name}
