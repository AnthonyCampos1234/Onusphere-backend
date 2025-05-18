from typing import Required
from mongoengine import Document, EmbeddedDocument, fields, connect
import datetime
import random
import string

# ===== Account =====
class Account(Document):
    date_created = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)
    email = fields.StringField(required=True)
    name = fields.StringField(required=True)
    company_code = fields.StringField(required=True, unique=True)


# ===== Member =====
class Member(Document):
    date_created = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)
    account = fields.ReferenceField(Account, required=True)
    name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    phone = fields.StringField()
    hashed_password = fields.StringField(required=True)
    role = fields.StringField(required=True, choices=("admin", "manager", "member"), default="member")


# ===== Customer =====
class Customer(Document):
    date_created = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)
    account = fields.ReferenceField(Account, required=True)
    name = fields.StringField()
    email_domain = fields.StringField(required=True)


# ===== Item =====
class Item(Document):
    item_number = fields.StringField(required=True)
    height = fields.FloatField(required=True)
    width = fields.FloatField(required=True)
    length = fields.FloatField(required=True)
    special_instructions = fields.StringField(required=True)
    description = fields.StringField()
    units_per_pallet = fields.IntField(required=True)


# ===== OrderBatch =====
class OrderBatch(Document):
    date_created = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)
    item_id = fields.ReferenceField(Item, required=True)
    number_pallets = fields.IntField(required=True)

    @staticmethod
    def calculate_pallets(order_quantity, units_per_pallet):
        if units_per_pallet <= 0:
            raise ValueError("Units per pallet must be greater than zero.")
        return max(1, -(-order_quantity // units_per_pallet))  # Ceiling division
    
    def set_pallets(self, order_quantity, units_per_pallet):
        self.number_pallets = self.calculate_pallets(order_quantity, units_per_pallet)

# ===== Order =====
class Order(Document):
    date_created = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)
    customer = fields.ReferenceField(Customer, required=True)
    order_item_ids = fields.ListField(fields.ReferenceField(OrderBatch), required=True)
    order_date = fields.DateField(required=True)
    shipment_times = fields.ListField(fields.StringField(), required=True)
    status = fields.StringField(choices=("processing", "done"))
    loading_instructions = fields.ListField(fields.StringField())  # nullable, default None

