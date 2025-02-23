from flask import Blueprint

# 메인 API Blueprint 생성
bp = Blueprint('api', __name__)

# 하위 Blueprint 생성
from flask import Blueprint
firewall_bp = Blueprint('firewall', __name__, url_prefix='/firewall')
policy_bp = Blueprint('policy', __name__, url_prefix='/policy')

# 하위 모듈 import
from . import firewall, policy

# Blueprint 등록
bp.register_blueprint(firewall_bp)
bp.register_blueprint(policy_bp)

def init_app(app):
    app.register_blueprint(bp, url_prefix='/api') 