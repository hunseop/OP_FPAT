import json
import os
from crypto import HostsEncryption

def migrate_hosts():
    """기존 hosts.json 파일을 암호화된 형태로 변환"""
    # hosts.json 파일 읽기
    try:
        with open('hosts.json', 'r', encoding='utf-8') as f:
            hosts_data = json.load(f)
    except FileNotFoundError:
        print("hosts.json 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print("hosts.json 파일 형식이 잘못되었습니다.")
        return

    # 암호화하여 저장
    crypto = HostsEncryption()
    crypto.encrypt_hosts(hosts_data)

    # 기존 파일 백업
    if os.path.exists('hosts.json'):
        os.rename('hosts.json', 'hosts.json.bak')
        print("기존 hosts.json 파일이 hosts.json.bak으로 백업되었습니다.")

    print("호스트 데이터가 성공적으로 암호화되었습니다.")
    print("암호화된 파일 위치: config/hosts.enc")
    print("암호화 키 위치: config/.key")

if __name__ == '__main__':
    migrate_hosts() 