from flask import Blueprint, jsonify, request
from app import db
from app.models import Firewall
from app.services.sync_manager import sync_manager

bp = Blueprint('api', __name__)

@bp.route('/firewall/sync/<int:id>', methods=['POST'])
def sync_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        
        if firewall.sync_status == 'syncing':
            return jsonify({
                'success': False,
                'error': '이미 동기화가 진행 중입니다.'
            })

        firewall.sync_status = 'syncing'
        db.session.commit()

        success, message = sync_manager.start_sync(id)
        
        return jsonify({
            'success': success,
            'message': message
        })

    except Exception as e:
        firewall.sync_status = 'failed'
        firewall.last_sync_error = str(e)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'error': f'동기화 시작 중 오류가 발생했습니다: {str(e)}'
        })

@bp.route('/firewall/sync/status/<int:id>')
def sync_status(id):
    status = sync_manager.get_status(id)
    if status:
        return jsonify(status)
    
    firewall = Firewall.query.get_or_404(id)
    return jsonify({
        'status': firewall.sync_status,
        'last_sync': firewall.last_sync.strftime('%Y-%m-%d %H:%M:%S') if firewall.last_sync else None,
        'error': firewall.last_sync_error
    })

@bp.route('/firewall/status/<int:id>', methods=['POST'])
def update_firewall_status(id):
    try:
        data = request.get_json()
        if 'status' not in data:
            return jsonify({
                'success': False,
                'error': '상태 값이 누락되었습니다.'
            })

        firewall = Firewall.query.get_or_404(id)
        firewall.status = data['status']
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '상태가 업데이트되었습니다.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'상태 업데이트 중 오류가 발생했습니다: {str(e)}'
        }) 