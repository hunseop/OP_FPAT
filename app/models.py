from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Firewall(db.Model):
    """방화벽 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'ngf', 'mf2', 'paloalto', 'mock'
    ip_address = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    sync_status = db.Column(db.String(20), default='pending')  # pending, syncing, success, failed
    last_sync = db.Column(db.DateTime, default=datetime.utcnow)
    last_sync_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    security_rules = db.relationship('SecurityRule', backref='firewall', lazy=True, cascade='all, delete-orphan')
    network_objects = db.relationship('NetworkObject', backref='firewall', lazy=True, cascade='all, delete-orphan')
    network_groups = db.relationship('NetworkGroup', backref='firewall', lazy=True, cascade='all, delete-orphan')
    service_objects = db.relationship('ServiceObject', backref='firewall', lazy=True, cascade='all, delete-orphan')
    service_groups = db.relationship('ServiceGroup', backref='firewall', lazy=True, cascade='all, delete-orphan')

    @property
    def type_display(self):
        """방화벽 타입 표시용 프로퍼티"""
        type_map = {
            'ngf': 'NGF',
            'mf2': 'MF2',
            'paloalto': 'PALOALTO',
            'mock': 'MOCK'
        }
        return type_map.get(self.type, self.type.upper())

class SecurityRule(db.Model):
    """보안 규칙 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False, index=True)
    vsys = db.Column(db.String(50), index=True)
    seq = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    enabled = db.Column(db.Boolean, default=True, index=True)
    action = db.Column(db.String(20), index=True)
    source = db.Column(db.Text)
    user = db.Column(db.Text)
    destination = db.Column(db.Text)
    service = db.Column(db.Text)
    application = db.Column(db.Text)
    security_profile = db.Column(db.Text)
    category = db.Column(db.Text)
    description = db.Column(db.Text)
    last_hit = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NetworkObject(db.Model):
    """네트워크 객체 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20))  # ip-netmask, ip-range, fqdn
    value = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NetworkGroup(db.Model):
    """네트워크 그룹 객체 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    members = db.Column(db.Text)  # 콤마로 구분된 멤버 목록
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceObject(db.Model):
    """서비스 객체 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    protocol = db.Column(db.String(20))  # tcp, udp
    port = db.Column(db.String(100))  # 포트 범위 또는 단일 포트
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceGroup(db.Model):
    """서비스 그룹 객체 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    members = db.Column(db.Text)  # 콤마로 구분된 멤버 목록
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    """감사 로그를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # sync, add, edit, delete
    target_type = db.Column(db.String(50), nullable=False, index=True)  # firewall, policy, object
    target_id = db.Column(db.Integer, index=True)
    target_name = db.Column(db.String(100))
    status = db.Column(db.String(20), index=True)  # success, failed
    details = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

class Notification(db.Model):
    """알림을 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    type = db.Column(db.String(20), nullable=False)  # success, error, info, warning
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True)) 