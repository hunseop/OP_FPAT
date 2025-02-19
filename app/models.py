from datetime import datetime
from app import db

class Firewall(db.Model):
    """방화벽 정보를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'ngf', 'mf2', 'paloalto'
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
            'paloalto': 'PALOALTO'
        }
        return type_map.get(self.type, self.type.upper())

class SecurityRule(db.Model):
    """방화벽 보안 규칙을 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    vsys = db.Column(db.String(50), nullable=True)  # PALOALTO용, 다른 방화벽은 기본값
    seq = db.Column(db.Integer)
    name = db.Column(db.String(200))
    enabled = db.Column(db.Boolean, default=True)
    action = db.Column(db.String(50))
    source = db.Column(db.Text)
    user = db.Column(db.Text)
    destination = db.Column(db.Text)
    service = db.Column(db.Text)
    application = db.Column(db.Text)
    security_profile = db.Column(db.Text, nullable=True)  # PALOALTO의 url_filtering, MF2의 schedule
    category = db.Column(db.String(200), nullable=True)  # PALOALTO 전용
    description = db.Column(db.Text, nullable=True)
    last_hit = db.Column(db.DateTime, nullable=True)  # NGF 전용
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NetworkObject(db.Model):
    """네트워크 객체를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # ip-netmask, ip-range, fqdn
    value = db.Column(db.Text)
    start_ip = db.Column(db.BigInteger, nullable=True)  # IP 주소를 정수로 변환
    end_ip = db.Column(db.BigInteger, nullable=True)    # IP 범위 끝 주소
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NetworkGroup(db.Model):
    """네트워크 그룹 객체를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    members = db.Column(db.Text)  # 쉼표로 구분된 멤버 목록
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceObject(db.Model):
    """서비스 객체를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    protocol = db.Column(db.String(50))
    port = db.Column(db.Text)
    start_port = db.Column(db.Integer, nullable=True)  # 포트 번호 시작
    end_port = db.Column(db.Integer, nullable=True)    # 포트 번호 끝
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceGroup(db.Model):
    """서비스 그룹 객체를 저장하는 모델"""
    id = db.Column(db.Integer, primary_key=True)
    firewall_id = db.Column(db.Integer, db.ForeignKey('firewall.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    members = db.Column(db.Text)  # 쉼표로 구분된 멤버 목록
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 