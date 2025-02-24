from flask import Blueprint, render_template
from app.models import Firewall

bp = Blueprint('object', __name__)

@bp.route('/')
def index():
    """객체 관리 페이지를 표시합니다."""
    firewalls = Firewall.query.all()
    return render_template('object/index.html', title='객체 관리', firewalls=firewalls) 