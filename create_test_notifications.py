from app import app, db
from app.models import Notification
from datetime import datetime

def create_test_notifications():
    with app.app_context():
        # 테스트 알림 생성
        notifications = [
            Notification(
                type='info',
                title='시스템 알림',
                message='FPAT 시스템이 시작되었습니다.',
                timestamp=datetime.utcnow()
            ),
            Notification(
                type='success',
                title='동기화 완료',
                message='방화벽 정책 동기화가 완료되었습니다.',
                timestamp=datetime.utcnow()
            ),
            Notification(
                type='warning',
                title='주의',
                message='일부 방화벽 연결이 지연되고 있습니다.',
                timestamp=datetime.utcnow()
            )
        ]

        # 데이터베이스에 저장
        for notification in notifications:
            db.session.add(notification)
        db.session.commit()
        print('테스트 알림이 생성되었습니다.')

if __name__ == '__main__':
    create_test_notifications() 