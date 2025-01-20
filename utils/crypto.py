import os
import json
from cryptography.fernet import Fernet
from pathlib import Path

class HostsEncryption:
    def __init__(self):
        self.key_file = 'config/.key'
        self.encrypted_hosts_file = 'config/hosts.enc'
        self._ensure_key()

    def _ensure_key(self):
        """키 파일이 없으면 생성"""
        if not os.path.exists('config'):
            os.makedirs('config')
            
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)

    def _get_cipher(self):
        """Fernet 암호화 객체 반환"""
        with open(self.key_file, 'rb') as f:
            key = f.read()
        return Fernet(key)

    def encrypt_hosts(self, hosts_data):
        """호스트 데이터 암호화"""
        cipher = self._get_cipher()
        encrypted_data = cipher.encrypt(json.dumps(hosts_data).encode())
        with open(self.encrypted_hosts_file, 'wb') as f:
            f.write(encrypted_data)

    def decrypt_hosts(self):
        """호스트 데이터 복호화"""
        if not os.path.exists(self.encrypted_hosts_file):
            return {}
            
        cipher = self._get_cipher()
        with open(self.encrypted_hosts_file, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"복호화 중 오류 발생: {e}")
            return {} 