from . import db
from datetime import datetime
class Post(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    slug = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String)
    playlist_name = db.Column(db.String)
    playlist_id = db.Column(db.String)
    playlist_i = db.Column(db.Integer)
    playlist_n = db.Column(db.Integer)
    duration_s = db.Column(db.Integer)
    body = db.Column(db.String)
    audio = db.Column(db.String)
    created = db.Column(db.DateTime, default=datetime.utcnow)
