from mongoengine import Document, StringField, FloatField, IntField

class Item(Document):
    item_number = StringField(required=True, unique=True)
    height = FloatField() # in inches, ex: 30.75
    width = FloatField() # in inches
    length = FloatField() # in inches

