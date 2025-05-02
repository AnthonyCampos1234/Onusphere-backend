from typing import List
from datetime import datetime
from models.customer import Customer
from models.customer_order import CustomerOrder
from models.item import Item

def find_new_items(df) -> List:
    """
    Returns a list of item_numbers that exist in the database
    but are NOT present in the given DataFrame.
    """
    current_items = set(df["Item"].astype(str).unique())
    all_db_items = set(Item.objects.scalar("item_number"))

    missing_items = list(all_db_items - current_items)

    return missing_items

def store_customer_order_in_db(receipt):
    """
    Saves a customer order to the database using the order receipt object.
    """

    # 1. Get or create the customer
    customer = Customer.objects(name=receipt.customer_id).first()
    if not customer:
        customer = Customer(name=receipt.customer_id, email="unknown@example.com")
        customer.save()

    item_ids = receipt.order_details["Item"].astype(str).unique()
    items = list(Item.objects(item_number__in=item_ids))

    order = CustomerOrder(
        customer=customer,
        item=items,
        order_date=datetime.strptime(receipt.date_ordered, "%m/%d/%y")
    )
    order.save()
    return order