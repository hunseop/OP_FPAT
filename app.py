from flask import Flask, render_template, request, jsonify, send_file
import json
import time
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐시 비활성화

# 명령어 구조 로드
with open('commands.json', 'r') as f:
    COMMANDS = json.load(f)

def load_hosts():
    with open('hosts.json', 'r') as f:
        return json.load(f)

def save_hosts(hosts):
    with open('hosts.json', 'w', encoding='utf-8') as f:
        json.dump(hosts, f, ensure_ascii=False, indent=4)

# 임시 파일 저장 디렉토리
TEMP_DIR = 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/')
def index():
    # 매 요청마다 hosts.json을 새로 읽어옴
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

    # commands.json 구조에 맞게 명령어 검증
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
        print(data)
        time.sleep(5)
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
    
    print(data)
    time.sleep(5)
    
    try:
        # 임시 데이터프레임 생성 (예시)
        df = pd.DataFrame({
            'Command': [f"{firewall_type} {command} {subcommand}"],
            'Hostname': [hostname],
            'Timestamp': [datetime.now()]
        })
        
        # 파일명 생성
        filename = f"{time.strftime('%Y%m%d')}_{hostname}_{subcommand}.xlsx"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # 엑셀 파일로 저장
        df.to_excel(filepath, index=False)
        
        response = {
            'status': 'success',
            'message': f'Analysis complete. Click download button to save the results.',
            'details': {
                'filename': filename
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error during analysis: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(TEMP_DIR, filename)
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
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.getmtime(filepath) < current_time - 86400:  # 24시간
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True) 