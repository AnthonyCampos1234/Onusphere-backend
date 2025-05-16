from fastapi import APIRouter, HTTPException, Request, Depends
from models.request_bodies import TriggerRequest
from threading import Event
from models.types import Account, Member, Customer, Order, OrderBatch, Item
from shared_state import pipeline_trigger_event, email_data
from utils.dependencies import get_current_user
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/email-trigger")
async def trigger_pipeline(request: Request):
    payload = await request.json()
    email = request.headers.get("email")
    if email:
        account = Account.objects(email=email).first()  # type: ignore
        if account:
            email_data = payload
            return {"status": "Pipeline triggered"}
    raise HTTPException(status_code=400, detail="Email header missing or invalid")

@router.post("/pipeline-trigger")
def email_trigger(payload: TriggerRequest):
    pipeline_trigger_event = Event()
    return {"status": "Email event triggered", "order_id": payload.order_id}

@router.post("/create-test-order")
def create_test_order(current_user: Account = Depends(get_current_user)):
    # Create a test customer if it doesn't exist
    customer = Customer.objects(account=current_user).first()
    if not customer:
        customer = Customer(
            name="Test Customer",
            email_domain="test.com",
            account=current_user
        ).save()

    # Generate unique item numbers using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create test items
    item1 = Item(
        item_number=f"TEST001_{timestamp}",
        description="Test Item 1",
        height=1.0,
        width=1.0,
        length=1.0,
        units_per_pallet=12
    ).save()

    item2 = Item(
        item_number=f"TEST002_{timestamp}",
        description="Test Item 2",
        height=2.0,
        width=2.0,
        length=2.0,
        units_per_pallet=8
    ).save()

    # Create order items
    order_items = [
        OrderBatch(item=item1, number_pallets=3),
        OrderBatch(item=item2, number_pallets=2)
    ]

    # Create the order with loading instructions
    order = Order(
        customer=customer,
        items=order_items,
        order_date=datetime.now(),
        upcoming_shipment_times=["7:00 AM", "9:00 AM", "11:00 AM"],
        status="pending",
        loading_instructions={
            "sequence": [
                f"Load Item {item1.item_number} (3 pallets) at the front of the truck",
                f"Load Item {item2.item_number} (2 pallets) behind {item1.item_number}",
                "Secure all pallets with straps",
                "Double-check weight distribution"
            ],
            "notes": "Handle TEST002 with care due to larger dimensions",
            "vehicleType": "Standard Box Truck",
            "estimatedTime": "45 minutes"
        }
    ).save()

    return {
        "id": str(order.id),
        "customer_id": str(customer.id),
        "items": [
            {
                "item_id": str(oi.item.id),
                "number_pallets": oi.number_pallets
            } for oi in order.items
        ],
        "order_date": order.order_date.isoformat(),
        "upcoming_shipment_times": order.upcoming_shipment_times,
        "status": order.status,
        "loading_instructions": order.loading_instructions
    }
