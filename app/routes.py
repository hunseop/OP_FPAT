from flask import render_template, request, jsonify, redirect, url_for, send_file
from app import app, db
from app.models import Firewall
from app.utils.validators import validate_firewall_data
from datetime import datetime
import os
import pandas as pd
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', title='FPAT')

@app.route('/policy')
def policy():
    return render_template('policy/index.html', title='정책 관리')

@app.route('/analysis')
def analysis():
    return render_template('analysis/index.html', title='정책 분석')

@app.route('/firewall')
def firewall():
    firewalls = Firewall.query.all()
    return render_template('firewall/index.html', title='방화벽 관리', firewalls=firewalls)

@app.route('/firewall/add', methods=['POST'])
def add_firewall():
    try:
        data = {
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'ip_address': request.form.get('ip'),
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        # 입력값 검증
        is_valid, errors = validate_firewall_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '입력값 검증 실패',
                'details': errors
            })

        # 중복 검사
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

@app.route('/firewall/delete/<int:id>', methods=['POST'])
def delete_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        db.session.delete(firewall)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/firewall/sync/<int:id>', methods=['POST'])
def sync_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        # TODO: 실제 방화벽 동기화 로직 구현
        firewall.last_sync = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/firewall/template')
def download_template():
    """방화벽 등록용 엑셀 템플릿 다운로드"""
    template_path = os.path.join(app.root_path, 'static', 'templates', 'firewall_template.xlsx')
    return send_file(template_path, as_attachment=True)

@app.route('/firewall/upload', methods=['POST'])
def upload_firewalls():
    """엑셀 파일을 통한 방화벽 일괄 등록"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '파일이 없습니다.'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '선택된 파일이 없습니다.'})
    
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            required_columns = ['name', 'type', 'ip_address', 'username', 'password']
            
            if not all(col in df.columns for col in required_columns):
                return jsonify({'success': False, 'error': '필수 컬럼이 누락되었습니다.'})
            
            errors = []
            success_count = 0
            
            for index, row in df.iterrows():
                data = {
                    'name': str(row['name']).strip(),
                    'type': str(row['type']).strip(),
                    'ip_address': str(row['ip_address']).strip(),
                    'username': str(row['username']).strip(),
                    'password': str(row['password']).strip()
                }
                
                # 입력값 검증
                is_valid, validation_errors = validate_firewall_data(data)
                if not is_valid:
                    errors.append(f"행 {index + 2}: {', '.join(validation_errors)}")
                    continue
                
                # 중복 검사
                existing_firewall = Firewall.query.filter(
                    (Firewall.name == data['name']) | 
                    (Firewall.ip_address == data['ip_address'])
                ).first()
                
                if existing_firewall:
                    errors.append(f"행 {index + 2}: 동일한 이름 또는 IP 주소를 가진 방화벽이 이미 존재합니다.")
                    continue
                
                firewall = Firewall(
                    name=data['name'],
                    type=data['type'].lower(),
                    ip_address=data['ip_address'],
                    username=data['username'],
                    password=data['password']
                )
                db.session.add(firewall)
                success_count += 1
            
            if success_count > 0:
                db.session.commit()
            
            result = {
                'success': True,
                'message': f'{success_count}개의 방화벽이 등록되었습니다.'
            }
            if errors:
                result['warnings'] = errors
            
            return jsonify(result)
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': '허용되지 않는 파일 형식입니다.'})

@app.route('/firewall/edit/<int:id>', methods=['GET', 'POST'])
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
        
        # 입력값 검증 (수정 모드)
        is_valid, errors = validate_firewall_data(data, is_edit=True)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '입력값 검증 실패',
                'details': errors
            })

        # 중복 검사 (현재 편집 중인 방화벽 제외)
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

        # 데이터 업데이트
        firewall.name = data['name']
        firewall.type = data['type'].lower()
        firewall.ip_address = data['ip_address']
        firewall.username = data['username']
        if data['password']:  # 비밀번호가 입력된 경우에만 업데이트
            firewall.password = data['password']
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})