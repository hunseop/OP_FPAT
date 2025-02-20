from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

from app import models
from app.routes import init_app

with app.app_context():
    db.create_all()
    init_app(app)