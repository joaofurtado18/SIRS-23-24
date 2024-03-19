from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    owner = db.relationship('User', back_populates='owns')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    format = db.Column(db.String(10))
    artist = db.Column(db.String(50))
    title = db.Column(db.String(100))
    genre = db.Column(db.ARRAY(db.String(50)))
    lyrics = db.Column(db.ARRAY(db.String(500)))
    audio_base64 = db.Column(db.Text)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16))
    password = db.Column(db.String(16))
    public_key = db.Column(db.Text)
    owns = db.relationship('Media', back_populates='owner')
    family = db.relationship('Family', back_populates='members')
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)

class Family(db.Model):
    __tablename__ = 'family'
    id = db.Column(db.Integer, primary_key=True)
    members = db.relationship('User', back_populates='family')
    key = db.Column(db.Text)