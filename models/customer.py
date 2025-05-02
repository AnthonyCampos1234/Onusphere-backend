from mongoengine import Document, StringField

class Customer(Document):
    name = StringField(required=True)
    email = StringField()
