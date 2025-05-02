from mongoengine import Document, ReferenceField, ListField, DateTimeField
from models.customer import Customer
from models.item import Item
from datetime import datetime

class CustomerOrder(Document):
    customer = ReferenceField(Customer)
    item = ListField(ReferenceField(Item))
    order_date = DateTimeField(required=True)
