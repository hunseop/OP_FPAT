from flask import Blueprint, render_template, request, jsonify, send_file
from app import db
from app.models import Firewall
from app.services.sync_manager import sync_manager
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
        
        is_valid, errors = validate_firewall_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '입력값 검증 실패',
                'details': errors
            })

        existing_firewall = Firewall.query.filter(
            (Firewall.name == data['name']) | 
            (Firewall.ip_address == data['ip_address'])
        ).first()
        
        if existing_firewall:
            return jsonify({
                'success': False,
                'error': '중복된 방화벽',
                'details': ['동일한 이름 또는 IP 주소를 가진 방화벽이 이미 존재합니다.']
            })

        new_firewall = Firewall(
            name=data['name'],
            type=data['type'].lower(),
            ip_address=data['ip_address'],
            username=data['username'],
            password=data['password']
        )
        db.session.add(new_firewall)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        db.session.delete(firewall)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_firewall(id):
    firewall = Firewall.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify({
            'name': firewall.name,
            'type': firewall.type,
            'ip_address': firewall.ip_address,
            'username': firewall.username,
            'password': firewall.password
        })
    
    try:
        data = {
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'ip_address': request.form.get('ip'),
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        is_valid, errors = validate_firewall_data(data, is_edit=True)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '입력값 검증 실패',
                'details': errors
            })

        existing_firewall = Firewall.query.filter(
            Firewall.id != id,
            (Firewall.name == data['name']) | 
            (Firewall.ip_address == data['ip_address'])
        ).first()
        
        if existing_firewall:
            return jsonify({
                'success': False,
                'error': '중복된 방화벽',
                'details': ['동일한 이름 또는 IP 주소를 가진 방화벽이 이미 존재합니다.']
            })

        firewall.name = data['name']
        firewall.type = data['type'].lower()
        firewall.ip_address = data['ip_address']
        firewall.username = data['username']
        if data['password']:
            firewall.password = data['password']
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
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