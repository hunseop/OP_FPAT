from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import models
from app.routes import init_app
from app.services.sync_manager import sync_manager

with app.app_context():
    db.create_all()
    init_app(app)
    sync_manager.init_app(app)