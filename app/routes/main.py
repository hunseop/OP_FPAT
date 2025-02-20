from flask import Blueprint, render_template
from app.models import Firewall, SecurityRule, NetworkObject, NetworkGroup, ServiceObject, ServiceGroup

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # 방화벽 개수
    firewall_count = Firewall.query.count()
    
    # 전체 정책 수
    policy_count = SecurityRule.query.count()
    
    # 활성화된 정책 수
    active_policy_count = SecurityRule.query.filter_by(enabled=True).count()
    
    # 전체 객체 수
    object_count = (
        NetworkObject.query.count() +
        NetworkGroup.query.count() +
        ServiceObject.query.count() +
        ServiceGroup.query.count()
    )
    
    return render_template('index.html', 
                         title='FPAT',
                         firewall_count=firewall_count,
                         policy_count=policy_count,
                         active_policy_count=active_policy_count,
                         inactive_policy_count=policy_count - active_policy_count,
                         object_count=object_count)

@bp.route('/policy')
def policy():
    return render_template('policy/index.html', title='정책 관리')

@bp.route('/analysis')
def analysis():
    return render_template('analysis/index.html', title='정책 분석') 