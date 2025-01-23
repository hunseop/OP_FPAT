from flask import Flask, render_template, request, jsonify, send_file
import json
import time
import os
import pandas as pd
from datetime import datetime
from utils.crypto import HostsEncryption
from werkzeug.utils import secure_filename
import io
from config.commands import COMMANDS, SUBCOMMAND_FUNCTIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 호스트 암호화 객체 초기화
hosts_crypto = HostsEncryption()

# 명령어 구조 로드
with open('commands.json', 'r') as f:
    COMMANDS = json.load(f)

def load_hosts():
    return hosts_crypto.decrypt_hosts()

def save_hosts(hosts):
    hosts_crypto.encrypt_hosts(hosts)

# 결과 저장 디렉토리 설정
RESULTS_DIR = 'results'
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

@app.route('/')
def index():
    # 매 요청마다 hosts를 새로 읽어옴
    hosts = load_hosts()
    return render_template('index.html', commands=COMMANDS, hosts=hosts)

@app.route('/api/hosts', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_hosts():
    if request.method == 'GET':
        return jsonify(load_hosts())
    
    elif request.method == 'POST':
        hosts = load_hosts()
        new_host = request.json
        if new_host['hostname'] in hosts:
            return jsonify({'error': '이미 존재하는 호스트입니다.'}), 400
        hosts[new_host['hostname']] = {
            'alias': new_host['alias'],
            'username': new_host['username'],
            'password': new_host['password']
        }
        save_hosts(hosts)
        return jsonify({'message': '호스트가 추가되었습니다.'})
    
    elif request.method == 'PUT':
        hosts = load_hosts()
        updated_host = request.json
        
        # hostname 키 존재 여부 확인
        if 'hostname' not in updated_host:
            return jsonify({'error': 'hostname이 필요합니다.'}), 400
            
        if updated_host['hostname'] not in hosts:
            return jsonify({'error': '존재하지 않는 호스트입니다.'}), 404
            
        # 필수 필드 검증
        required_fields = ['alias', 'username', 'password']
        missing_fields = [field for field in required_fields if field not in updated_host]
        if missing_fields:
            return jsonify({'error': f'다음 필드가 필요합니다: {", ".join(missing_fields)}'}), 400
            
        hosts[updated_host['hostname']] = {
            'alias': updated_host['alias'],
            'username': updated_host['username'],
            'password': updated_host['password']
        }
        save_hosts(hosts)
        return jsonify({'message': '호스트가 수정되었습니다.'})
    
    elif request.method == 'DELETE':
        hosts = load_hosts()
        
        # hostname 키 존재 여부 확인
        if not request.json or 'hostname' not in request.json:
            return jsonify({'error': 'hostname이 필요합니다.'}), 400
            
        hostname = request.json['hostname']
        if hostname not in hosts:
            return jsonify({'error': '존재하지 않는 호스트입니다.'}), 404
            
        del hosts[hostname]
        save_hosts(hosts)
        return jsonify({'message': '호스트가 삭제되었습니다.'})

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    hostname = data.get('hostname')
    username = data.get('username')
    password = data.get('password')
    firewall_type = data.get('firewall_type')
    command = data.get('command')
    subcommand = data.get('subcommand')
    options = data.get('options', {})
    
    # 필수 파라미터 검증
    if not all([hostname, username, password, firewall_type, command, subcommand]):
        return jsonify({
            'status': 'error',
            'message': 'Missing required parameters'
        }), 400

    # commands 구조에 맞게 명령어 검증
    if firewall_type not in COMMANDS:
        return jsonify({
            'status': 'error',
            'message': f'Invalid firewall type: {firewall_type}'
        }), 400
        
    if command not in COMMANDS[firewall_type]:
        return jsonify({
            'status': 'error',
            'message': f'Invalid command: {command}'
        }), 400
        
    command_data = COMMANDS[firewall_type][command]
    if not command_data:
        return jsonify({
            'status': 'error',
            'message': f'Invalid command data for {command}'
        }), 400

    # subcommand가 직접 값을 가지는 경우 (options가 없는 경우)
    if not isinstance(command_data, dict):
        response = {
            'status': 'success',
            'message': f'Command executed: {firewall_type} {command} {subcommand}',
            'details': {
                'hostname': hostname,
                'options': options
            }
        }
        return jsonify(response)

    if subcommand not in command_data:
        return jsonify({
            'status': 'error',
            'message': f'Invalid subcommand: {subcommand}'
        }), 400
        
    # 옵션 검증
    subcommand_data = command_data[subcommand]
    command_options = {}
    
    if isinstance(subcommand_data, dict):
        command_options = subcommand_data.get('options', {})
    
    # 옵션이 있는 경우에만 검증
    if command_options and options:
        for key, value in options.items():
            if key not in command_options:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid option: {key}'
                }), 400
                
            # 필수 옵션 검증
            option_config = command_options[key]
            if isinstance(option_config, dict) and option_config.get('required', False) and not value:
                return jsonify({
                    'status': 'error',
                    'message': f'Required option missing: {key}'
                }), 400
    
    # subcommand 함수 호출
    try:
        command_fuction = SUBCOMMAND_FUNCTIONS[firewall_type][command][subcommand]
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid command or subcommand"}), 400

    try:
        # 명령어 함수 실행
        if callable(command_function):
            # 명령어 실행 후 결과받기
            result_data = command_fuction(hostname, username, password, subcommand, options) if "options" in command_fuction.__code__.co_varnames else command_fuction(hostname, username, password, subcommand)

            if isinstance(result_data, dict):
                return jsonify(result_data)
            elif isinstance(result_data, str):
                return jsonify({
                    'status': 'success',
                    'message': f'Analysis complete. Click download button to save the results.',
                    'details': {
                        'filename': result_data
                    }
                })
            else:
                return jsonify({"status": "error", "message": "Undified Return"}), 500
        else:
            return jsonify({"status": "error", "message": "Command not callable"}), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error during analysis: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(RESULTS_DIR, filename)
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error downloading file: {str(e)}'
        }), 404

# 주기적으로 오래된 임시 파일 정리 (선택사항)
def cleanup_temp_files():
    # 24시간 이상 된 파일 삭제
    current_time = time.time()
    for filename in os.listdir(RESULTS_DIR):
        filepath = os.path.join(RESULTS_DIR, filename)
        if os.path.getmtime(filepath) < current_time - 86400:  # 24시간
            os.remove(filepath)

@app.route('/api/hosts/template')
def download_template():
    """호스트 등록 템플릿 다운로드"""
    df = pd.DataFrame(columns=['hostname', 'alias', 'username', 'password'])
    
    # 예제 데이터 추가
    df.loc[0] = ['192.168.1.1', '방화벽1', 'admin', 'password123']
    df.loc[1] = ['192.168.1.2', '방화벽2', 'admin', 'password456']
    
    # 엑셀 파일로 변환
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='host_template.xlsx'
    )

@app.route('/api/hosts/bulk', methods=['POST'])
def bulk_add_hosts():
    """엑셀 파일로 호스트 일괄 등록"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400
        
    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Only Excel files are allowed.'}), 400

    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file)
        required_columns = ['hostname', 'alias', 'username', 'password']
        
        # 필수 컬럼 확인
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Required columns are missing.'}), 400
            
        # 현재 호스트 목록 로드
        hosts = load_hosts()
        results = {
            'success': [],
            'failed': []
        }
        
        # 각 행 처리
        for _, row in df.iterrows():
            try:
                hostname = str(row['hostname']).strip()
                # 기본 유효성 검사
                if not hostname or pd.isna(hostname):
                    results['failed'].append({
                        'hostname': hostname,
                        'reason': 'Hostname is empty.'
                    })
                    continue
                    
                # 이미 존재하는 호스트 확인
                if hostname in hosts:
                    results['failed'].append({
                        'hostname': hostname,
                        'reason': 'Host already exists.'
                    })
                    continue
                
                # 호스트 추가
                hosts[hostname] = {
                    'alias': str(row['alias']).strip(),
                    'username': str(row['username']).strip(),
                    'password': str(row['password']).strip()
                }
                results['success'].append(hostname)
                
            except Exception as e:
                results['failed'].append({
                    'hostname': hostname if 'hostname' in locals() else 'Unknown',
                    'reason': str(e)
                })
        
        # 변경사항 저장
        if results['success']:
            save_hosts(hosts)
        
        return jsonify({
            'message': f"{len(results['success'])} host(s) added successfully.",
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True) 