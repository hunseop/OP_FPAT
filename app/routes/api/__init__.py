from flask import Blueprint

# 메인 API Blueprint 생성
bp = Blueprint('api', __name__)

# 하위 모듈 import
from .firewall import bp as firewall_bp
from .policy import bp as policy_bp
from .notification import bp as notification_bp
from .object import bp as object_bp  # object API 블루프린트 import

# 하위 Blueprint 등록
bp.register_blueprint(firewall_bp, url_prefix='/firewall')
bp.register_blueprint(policy_bp, url_prefix='/policy')
bp.register_blueprint(notification_bp, url_prefix='/notification')
bp.register_blueprint(object_bp, url_prefix='/object')  # object API 블루프린트 등록

def init_app(app):
    app.register_blueprint(bp, url_prefix='/api') 