from fastapi import APIRouter, UploadFile, File, Form, Depends
from models.request_bodies import TriggerRequest
from threading import Event
from models.types import Member, Customer, Order, OrderBatch, Item
from shared_state import pipeline_trigger_event, email_data
from utils.dependencies import get_current_user
from datetime import datetime
from bson import ObjectId
import shared_state

router = APIRouter()

@router.post("/email-trigger")
async def trigger_pipeline(
    csv_file: UploadFile = File(...),
    pdf_file: UploadFile = File(...),
    subject: str = Form(...),
    email_body: str = Form(...)
):
    csv_bytes = await csv_file.read()
    pdf_bytes = await pdf_file.read()

    email_data = {
        "csv_file": csv_bytes,
        "pdf_file": pdf_bytes,
        "subject": subject,
        "email_body": email_body
    }

    shared_state.email_data = email_data
    shared_state.order_id_holder["id"] = None
    shared_state.pipeline_trigger_event.set()

    return {"status": "Pipeline triggered"}


@router.post("/pipeline-trigger")
def email_trigger(payload: TriggerRequest):
    pipeline_trigger_event = Event()
    return {"status": "Email event triggered", "order_id": payload.order_id}

@router.post("/create-test-order")
def create_test_order(current_user: Member = Depends(get_current_user)):
    # Create a test customer if it doesn't exist
    customer = Customer.objects(account=current_user.account).first()
    if not customer:
        customer = Customer(
            name="Test Customer",
            email_domain="test.com",
            account=current_user.account
        ).save()

    # Generate unique item numbers using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create test items with complete dimensions
    item1 = Item(
        item_number=f"TEST001_{timestamp}",
        description="Premium Widget Set",
        height=12.5,
        width=8.0,
        length=6.0,
        special_instructions="Handle with care - fragile components",
        units_per_pallet=24
    ).save()

    item2 = Item(
        item_number=f"TEST002_{timestamp}",
        description="Heavy Duty Components",
        height=18.0,
        width=12.0,
        length=10.0,
        special_instructions="Requires forklift - heavy item",
        units_per_pallet=12
    ).save()

    item3 = Item(
        item_number=f"TEST003_{timestamp}",
        description="Standard Parts Kit",
        height=6.0,
        width=4.0,
        length=8.0,
        special_instructions="Standard handling",
        units_per_pallet=48
    ).save()

    # Create order batches (using correct field name)
    order_batches = [
        OrderBatch(item_id=item1, number_pallets=4).save(),
        OrderBatch(item_id=item2, number_pallets=2).save(),
        OrderBatch(item_id=item3, number_pallets=6).save()
    ]

    # Create the order with loading instructions (using correct field names)
    order = Order(
        customer=customer,
        order_item_ids=order_batches,  # Correct field name
        order_date=datetime.now().date(),  # Use date() not datetime
        shipment_times=["7:00 AM", "9:00 AM", "11:00 AM"],  # Correct field name
        status="done",  # Set to "done" so it shows as complete with loading instructions
        loading_instructions=[  # List of strings, not dict
            f"1. Load {item1.item_number} (4 pallets) at the front of the truck - handle with care due to fragile components",
            f"2. Load {item2.item_number} (2 pallets) in the middle section using forklift - heavy items require secure positioning",
            f"3. Load {item3.item_number} (6 pallets) at the rear of the truck - standard handling",
            "4. Secure all pallets with heavy-duty straps and corner protectors",
            "5. Double-check weight distribution and ensure proper load balance",
            "6. Verify all items are properly secured before departure",
            "7. Complete final inspection and document any concerns"
        ]
    ).save()

    return {
        "id": str(order.id),
        "customer_id": str(customer.id),
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
                }
            } for ob in order_batches
        ],
        "order_date": order.order_date.isoformat(),
        "shipment_times": order.shipment_times,
        "status": order.status,
        "loading_instructions": order.loading_instructions
    }
