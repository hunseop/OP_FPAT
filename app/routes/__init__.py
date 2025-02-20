from flask import Blueprint
from .main import bp as main_bp
from .firewall import bp as firewall_bp
from .api import bp as api_bp

def init_app(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(firewall_bp, url_prefix='/firewall')
    app.register_blueprint(api_bp, url_prefix='/api')
