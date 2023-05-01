from . import db
from datetime import datetime
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    slug = db.Column(db.String, unique=True, nullable=False)
    voice = db.Column(db.ForeignKey('voices.id'), nullable=False)
    body = db.Column(db.String)
    audio = db.Column(db.String)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    audio_size = db.Column(db.Integer)

class Voices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voice_name = db.Column(db.String, unique=True, nullable=False)