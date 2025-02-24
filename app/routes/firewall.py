from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from app import db
from app.models import Firewall
from app.services.sync_manager import sync_manager
from app.services.audit_service import audit_service
from app.utils.validators import validate_firewall_data
from app.utils.file_handlers import allowed_file, handle_excel_upload
import os
import pandas as pd

bp = Blueprint('firewall', __name__)

@bp.route('/')
def index():
    firewalls = Firewall.query.all()
    return render_template('firewall/index.html', title='방화벽 관리', firewalls=firewalls)

@bp.route('/add', methods=['POST'])
def add_firewall():
    try:
        data = {
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'ip_address': request.form.get('ip'),
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        error = validate_firewall_data(data)
        if error:
            return jsonify({'success': False, 'error': error})
        
        firewall = Firewall(**data)
        db.session.add(firewall)
        db.session.commit()

        # 감사 로그 기록
        audit_service.log(
            action='add',
            target_type='firewall',
            target_id=firewall.id,
            target_name=firewall.name,
            status='success'
        )
        
        return jsonify({'success': True})
    except Exception as e:
        # 감사 로그 기록 (실패)
        audit_service.log(
            action='add',
            target_type='firewall',
            target_id=None,
            target_name=request.form.get('name'),
            status='failed',
            details=str(e)
        )
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        name = firewall.name  # 삭제 전에 이름 저장
        
        db.session.delete(firewall)
        db.session.commit()

        # 감사 로그 기록
        audit_service.log(
            action='delete',
            target_type='firewall',
            target_id=id,
            target_name=name,
            status='success'
        )
        
        return jsonify({'success': True})
    except Exception as e:
        # 감사 로그 기록 (실패)
        audit_service.log(
            action='delete',
            target_type='firewall',
            target_id=id,
            target_name=firewall.name if firewall else 'unknown',
            status='failed',
            details=str(e)
        )
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_firewall(id):
    firewall = Firewall.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify({
            'name': firewall.name,
            'type': firewall.type,
            'ip_address': firewall.ip_address,
            'username': firewall.username
        })
    
    try:
        data = {
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'ip_address': request.form.get('ip'),
            'username': request.form.get('username')
        }
        
        if request.form.get('password'):
            data['password'] = request.form.get('password')
        
        error = validate_firewall_data(data, id)
        if error:
            return jsonify({'success': False, 'error': error})
        
        for key, value in data.items():
            setattr(firewall, key, value)
        
        db.session.commit()

        # 감사 로그 기록
        audit_service.log(
            action='edit',
            target_type='firewall',
            target_id=firewall.id,
            target_name=firewall.name,
            status='success'
        )
        
        return jsonify({'success': True})
    except Exception as e:
        # 감사 로그 기록 (실패)
        audit_service.log(
            action='edit',
            target_type='firewall',
            target_id=id,
            target_name=firewall.name,
            status='failed',
            details=str(e)
        )
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/template')
def download_template():
    """방화벽 등록용 엑셀 템플릿 다운로드"""
    from app import app
    template_path = os.path.join(app.root_path, 'static', 'templates', 'firewall_template.xlsx')
    return send_file(template_path, as_attachment=True)

@bp.route('/upload', methods=['POST'])
def upload_firewalls():
    """엑셀 파일을 통한 방화벽 일괄 등록"""
    return handle_excel_upload(request.files.get('file')) 