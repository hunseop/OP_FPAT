from flask import Blueprint, jsonify, request
from app import db
from app.models import Notification
from datetime import datetime, timedelta

bp = Blueprint('notification', __name__)

@bp.route('/list', methods=['GET'])
def get_notifications():
    """최근 알림 목록을 반환합니다."""
    # 기본적으로 최근 30일 이내의 알림만 표시
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    notifications = Notification.query\
        .filter(Notification.timestamp >= thirty_days_ago)\
        .order_by(Notification.timestamp.desc())\
        .limit(50)\
        .all()
    
    return jsonify({
        'success': True,
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'timestamp': n.timestamp.isoformat(),
            'is_read': n.is_read
        } for n in notifications]
    })

@bp.route('/new', methods=['GET'])
def get_new_notifications():
    """마지막 알림 ID 이후의 새로운 알림을 반환합니다."""
    last_id = request.args.get('last_id', type=int, default=0)
    notifications = Notification.query.filter(Notification.id > last_id)\
        .order_by(Notification.timestamp.desc()).all()
    return jsonify({
        'success': True,
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'timestamp': n.timestamp.isoformat(),
            'is_read': n.is_read
        } for n in notifications]
    })

@bp.route('/add', methods=['POST'])
def add_notification():
    """새로운 알림을 추가합니다."""
    data = request.get_json()
    
    notification = Notification(
        type=data['type'],
        title=data['title'],
        message=data['message'],
        timestamp=datetime.utcnow(),
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'notification': {
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat(),
            'is_read': notification.is_read
        }
    })

@bp.route('/<int:id>/read', methods=['POST'])
def mark_as_read(id):
    """알림을 읽음 처리합니다."""
    try:
        notification = Notification.query.get_or_404(id)
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'알림 읽음 처리 중 오류가 발생했습니다: {str(e)}'
        })

@bp.route('/cleanup', methods=['POST'])
def cleanup_notifications():
    """90일 이상 지난 알림을 삭제합니다."""
    try:
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        Notification.query\
            .filter(Notification.timestamp < ninety_days_ago)\
            .delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'알림 정리 중 오류가 발생했습니다: {str(e)}'
        })

@bp.route('/clear', methods=['POST'])
def clear_notifications():
    """모든 알림을 읽음 처리합니다."""
    try:
        Notification.query.update({Notification.is_read: True})
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'알림 읽음 처리 중 오류가 발생했습니다: {str(e)}'
        }) 