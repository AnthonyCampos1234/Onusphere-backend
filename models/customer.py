from mongoengine import StringField, ReferenceField, ListField, Document
from models.order import Order

class Customer(Document):
  name = StringField(required=True)
  orders = ListField(ReferenceField(Order))