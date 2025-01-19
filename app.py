from flask import Flask, render_template, request, jsonify
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# 명령어 구조 로드
with open('commands.json', 'r') as f:
    COMMANDS = json.load(f)

# 호스트 정보 로드
with open('hosts.json', 'r') as f:
    HOSTS = json.load(f)

@app.route('/')
def index():
    return render_template('index.html', commands=COMMANDS, hosts=HOSTS)

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