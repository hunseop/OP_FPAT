import os
import pandas as pd
from flask import jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models import Firewall
from app.utils.validators import validate_firewall_data

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_excel_upload(file):
    if not file:
        return jsonify({'success': False, 'error': '파일이 없습니다.'})
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '선택된 파일이 없습니다.'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': '허용되지 않는 파일 형식입니다.'})
    
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
            
            is_valid, validation_errors = validate_firewall_data(data)
            if not is_valid:
                errors.append(f"행 {index + 2}: {', '.join(validation_errors)}")
                continue
            
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