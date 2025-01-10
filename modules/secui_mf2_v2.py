import os
import paramiko
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_latest_fwrules_file(remote_directory, local_directory, latest_fwrules_file, host, username, password):
    """
    원격 서버에서 최신 방화벽 규칙 파일을 다운로드하는 함수

    :param remote_directory: 원격 디렉토리 경로
    :param local_directory: 로컬 디렉토리 경로
    :param latest_fwrules_file: 최신 방화벽 규칙 파일 이름
    :param host: 원격 서버 호스트명
    :param username: 원격 서버 사용자명
    :param password: 원격 서버 비밀번호
    :return: 다운로드된 파일의 로컬 경로
    """
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, username=username, password=password)
        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        
        remote_path = os.path.join(remote_directory, latest_fwrules_file)
        local_path = os.path.join(local_directory, f'{host}_{latest_fwrules_file}')
        scp.get(remote_path, local_path)
        logging.info(f"Downloaded {remote_path} to {local_path}")
        
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return None
    finally:
        ssh.close()
    
    return local_path

def show_system_info(host, port, username, password):
    """
    원격 서버의 시스템 정보를 가져오는 함수

    :param host: 원격 서버 호스트명
    :param port: 원격 서버 포트
    :param username: 원격 서버 사용자명
    :param password: 원격 서버 비밀번호
    :return: 시스템 정보 딕셔너리
    """
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port, username, password)
        
        hostname = execute_command(ssh, 'hostname')
        uptime = get_uptime(ssh)
        info = execute_command(ssh, f'{INFO_FILE}').splitlines()
        version = execute_command(ssh, 'rpm -q mf2')

        model = parse_info(info, 0)
        mac_address = parse_info(info, 2)
        hw_serial = parse_info(info, 3)

        system_info = {
            "hostname": hostname,
            "ip_address": host,
            "uptime": uptime,
            "version": version,
            "model": model,
            "mac_address": mac_address,
            "hw_serial": hw_serial
        }
        
        logging.info(f"System info: {system_info}")
        return system_info
    
    except Exception as e:
        logging.error(f"Error retrieving system info: {e}")
        return None
    finally:
        ssh.close()

def execute_command(ssh, command):
    """
    SSH를 통해 명령어를 실행하고 결과를 반환하는 함수

    :param ssh: paramiko SSHClient 객체
    :param command: 실행할 명령어
    :return: 명령어 실행 결과
    """
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode().strip()

def get_uptime(ssh):
    """
    시스템의 업타임을 가져오는 함수

    :param ssh: paramiko SSHClient 객체
    :return: 업타임 문자열
    """
    uptime_data = execute_command(ssh, 'uptime').split(' ')
    return f"{uptime_data[3]} {uptime_data[4].rstrip(',')}"

def parse_info(info, index):
    """
    시스템 정보에서 특정 인덱스의 값을 파싱하는 함수

    :param info: 시스템 정보 리스트
    :param index: 파싱할 인덱스
    :return: 파싱된 값
    """
    return info[index].split('=')[1].strip()