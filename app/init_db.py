from models import db, Media
from create_app import create_app
import random
from faker import Faker
import base64

fake = Faker()

def create_random_media():
    random_media = Media(
        format=random.choice(['MP3', 'WAV', 'OGG']),
        artist=fake.name(),
        title=fake.catch_phrase(),
        genre=[fake.word() for _ in range(4)],
        lyrics=[fake.sentence() for _ in range(6)],
        audio_base64=base64.b64encode(fake.binary(length=64)).decode('utf-8')
    )

    return random_media


app = create_app()

with app.app_context():
    print("db.create_all()...")
    db.create_all()

    for i in range(10):
        print("creating fake media... {}/10".format(i+1))
        random_media = create_random_media()
        db.session.add(random_media)

    db.session.commit()

    print("Database tables created successfully.")
