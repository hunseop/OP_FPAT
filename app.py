from flask import Flask, render_template, request, jsonify
import json
import time

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
        if updated_host['hostname'] not in hosts:
            return jsonify({'error': '존재하지 않는 호스트입니다.'}), 404
        hosts[updated_host['hostname']] = {
            'alias': updated_host['alias'],
            'username': updated_host['username'],
            'password': updated_host['password']
        }
        save_hosts(hosts)
        return jsonify({'message': '호스트가 수정되었습니다.'})
    
    elif request.method == 'DELETE':
        hosts = load_hosts()
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
    
    print(data)
    time.sleep(10)
    # 여기에 실제 명령어 실행 로직 구현
    # 현재는 테스트용 응답만 반환
    response = {
        'status': 'success',
        'message': f'Command executed: {firewall_type} {command} {subcommand}',
        'details': {
            'hostname': hostname,
            'options': options
        }
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True) 