from mongoengine import StringField, ReferenceField, Document
from models.account import Account

class Customer(Document):
  account = ReferenceField(Account)
  name = StringField() # Will be entered by User later
  email_domain = StringField(required=True)