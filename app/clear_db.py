from models import db, Media
from create_app import create_app
import random
from faker import Faker 

fake = Faker()

app = create_app()

with app.app_context():
    db.drop_all()
    db.session.commit()
    print("Database tables dropped successfully.") 
