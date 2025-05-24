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
    notification_preferences = fields.DictField(default=dict)


# ===== Invitation =====
class Invitation(Document):
    date_created = fields.DateTimeField(default=datetime.datetime.utcnow, required=True)
    account = fields.ReferenceField(Account, required=True)
    email = fields.EmailField(required=True)
    role = fields.StringField(required=True, choices=("admin", "manager", "member"), default="member")
    message = fields.StringField()
    invitation_token = fields.StringField(required=True, unique=True)
    expires_at = fields.DateTimeField(required=True)
    status = fields.StringField(choices=("pending", "accepted", "expired"), default="pending")
    invited_by = fields.ReferenceField(Member, required=True)

    @staticmethod
    def generate_token():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def save(self, *args, **kwargs):
        if not self.invitation_token:
            self.invitation_token = self.generate_token()
        if not self.expires_at:
            # Set expiration to 7 days from now
            self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        return super().save(*args, **kwargs)


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
    status = fields.StringField(choices=("incomplete", "processing", "done"))
    loading_instructions = fields.ListField(fields.StringField(), null=True, default=None)


class Notification(Document):
    account = fields.ReferenceField(Account, required=True)
    member = fields.ReferenceField(Member, required=True)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField(required=True, max_length=500)
    type = fields.StringField(required=True, choices=['order', 'customer', 'team', 'system', 'security'])
    is_read = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=datetime.datetime.utcnow)
    read_at = fields.DateTimeField()
    metadata = fields.DictField()  # For storing additional data like order_id, etc.

    meta = {
        'collection': 'notifications',
        'indexes': [
            ('account', 'member', '-created_at'),
            ('account', 'member', 'is_read'),
        ]
    }


class UserSession(Document):
    member = fields.ReferenceField(Member, required=True)
    session_token = fields.StringField(required=True, unique=True)
    device_info = fields.StringField(max_length=200)
    ip_address = fields.StringField()
    location = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.datetime.utcnow)
    last_activity = fields.DateTimeField(default=datetime.datetime.utcnow)
    is_active = fields.BooleanField(default=True)

    meta = {
        'collection': 'user_sessions',
        'indexes': [
            'session_token',
            ('member', '-last_activity'),
        ]
    }

