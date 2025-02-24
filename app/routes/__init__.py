from flask import Blueprint
from .main import bp as main_bp
from .firewall import bp as firewall_bp
from .api import bp as api_bp

def init_app(app):
    from app.routes import main
    from app.routes import firewall
    from app.routes import object  # object 블루프린트 import
    from app.routes.api import init_app as init_api

    app.register_blueprint(main.bp)
    app.register_blueprint(firewall.bp, url_prefix='/firewall')
    app.register_blueprint(object.bp, url_prefix='/object')  # object 블루프린트 등록
    init_api(app)
