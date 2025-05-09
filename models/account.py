from mongoengine import Document, StringField, ListField, ReferenceField

class Account(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    hashed_password = StringField(required=True)
    company_name = StringField()
    phone = StringField()
    job_title = StringField()
    timezone = StringField(default="America/New_York")
