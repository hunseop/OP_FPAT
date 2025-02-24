from datetime import datetime
from flask import request
from app import db
from app.models import AuditLog

class AuditService:
    @staticmethod
    def log(action, target_type, target_id, target_name, status, details=None):
        """감사 로그를 기록합니다."""
        try:
            # 현재 사용자 ID (로그인 기능 구현 시 추가)
            user_id = None
            
            # 클라이언트 IP 주소
            ip_address = request.remote_addr
            
            audit_log = AuditLog(
                timestamp=datetime.utcnow(),
                action=action,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                status=status,
                details=details,
                user_id=user_id,
                ip_address=ip_address
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"감사 로그 기록 중 오류 발생: {str(e)}")
            return False

audit_service = AuditService() 