from flask import Blueprint, jsonify, request
from app import db
from app.models import Firewall
from app.services.sync_manager import sync_manager
from app.services.audit_service import audit_service
from app.utils.validators import validate_firewall_data
from app.utils.file_handlers import allowed_file, handle_excel_upload
import os
import pandas as pd

bp = Blueprint('firewall', __name__)

@bp.route('/sync/<int:id>', methods=['POST'])
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

@bp.route('/sync/status/<int:id>')
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

@bp.route('/status/<int:id>', methods=['POST'])
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

@bp.route('/edit/<int:id>', methods=['POST'])
def edit_firewall(id):
    """방화벽 정보를 수정합니다."""
    try:
        firewall = Firewall.query.get_or_404(id)
        
        # 폼 데이터 검증
        if not request.form.get('name'):
            return jsonify({'success': False, 'error': '방화벽 이름은 필수입니다.'})
        if not request.form.get('type'):
            return jsonify({'success': False, 'error': '방화벽 종류는 필수입니다.'})
        if not request.form.get('ip'):
            return jsonify({'success': False, 'error': 'IP 주소는 필수입니다.'})
        if not request.form.get('username'):
            return jsonify({'success': False, 'error': '사용자 이름은 필수입니다.'})
        
        # 데이터 업데이트
        firewall.name = request.form.get('name')
        firewall.type = request.form.get('type')
        firewall.ip_address = request.form.get('ip')
        firewall.username = request.form.get('username')
        
        # 비밀번호가 입력된 경우에만 업데이트
        if request.form.get('password'):
            firewall.password = request.form.get('password')
        
        db.session.commit()

        # 감사 로그 기록
        audit_service.log(
            action='edit',
            target_type='firewall',
            target_id=firewall.id,
            target_name=firewall.name,
            status='success'
        )
        
        return jsonify({'success': True, 'message': '방화벽 정보가 수정되었습니다.'})
    except Exception as e:
        db.session.rollback()
        # 감사 로그 기록 (실패)
        audit_service.log(
            action='edit',
            target_type='firewall',
            target_id=id,
            target_name=firewall.name if firewall else 'unknown',
            status='failed',
            details=str(e)
        )
        return jsonify({
            'success': False,
            'error': f'방화벽 수정 중 오류가 발생했습니다: {str(e)}'
        })

@bp.route('/edit/<int:id>', methods=['GET'])
def get_firewall(id):
    """방화벽 정보를 조회합니다."""
    try:
        firewall = Firewall.query.get_or_404(id)
        return jsonify({
            'success': True,
            'name': firewall.name,
            'type': firewall.type,
            'ip_address': firewall.ip_address,
            'username': firewall.username
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'방화벽 정보를 불러오는 중 오류가 발생했습니다: {str(e)}'
        }), 500 