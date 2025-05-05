from mongoengine import Document, StringField, ListField, ReferenceField
from models.customer import Customer

class Account(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    hashed_password = StringField(required=True)
    customers = ListField(ReferenceField(Customer))

    def addCustomer(self, customer: Customer):
        self.customers = self.customers.append(customer)