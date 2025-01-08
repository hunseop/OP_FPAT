import pandas as pd
import re
import paramiko
from scp import SCPClient
import os

POLICY_DIRECTORY = 'ls'
CONF_DIRECTORY = 'ls'
INFO_FILE = 'cat infofile'

# 객체 싱을 위한 정규식 패턴 정보
HOST_PATTERN = {
    'id': r'id = (\d+)',
    'name': r'name = "([^"]+)"',
    'zone': r'zone = "([^"]+)"',
    'user': r'user = "([^"]+)"',
    'date': r'date = "([^"]+)"',
    'ip': r'ip = "([^"]+)"',
    'description': r'd = "([^"]+)"',
}
MASK_PATTERN = {
    'id': r'id = (\d+)',
    'name': r'name = "([^"]+)"',
    'zone': r'zone = "([^"]+)"',
    'user': r'user = "([^"]+)"',
    'date': r'date = "([^"]+)"',
    'ip/start': r'ip="([^"]+)"',
    'mask/end': r'mask="([^"]+)"',
    'description': r'd = "([^"]+)"',
}
RANGE_PATTERN = {
    'id': r'id = (\d+)',
    'name': r'name = "([^"]+)"',
    'zone': r'zone = "([^"]+)"',
    'user': r'user = "([^"]+)"',
    'date': r'date = "([^"]+)"',
    'ip/start': r'rangestart="([^"]+)"',
    'mask/end': r'rangeend="([^"]+)"',
    'description': r'd = "([^"]+)"',
}
GROUP_PATTERN = {
    'id': r'id = (\d+)',
    'name': r'name = "([^"]+)"',
    'zone': r'zone = "([^"]+)"',
    'user': r'user = "([^"]+)"',
    'date': r'date = "([^"]+)"',
    'count': r'count = \{(.*?)\},',
    'hosts': r'hosts=\{(.*?)\},',
    'networks': r'networks=\{(.*?)\},',
    'description': r'd = "([^"]+)"',
}
SERVICE_PATTERN = {
    'id': r'id = (\d+)',
    'name': r'name = "([^"]+)"',
    'protocol': r'protocol="([^"]+),',
    'str_src_port': r'str_src_port="([^"]+)",',
    'str_svc_port': r'str_svc_port="([^"]+)",',
    'svc_type': r'svc_type="([^"]+)",',
    'description': r'd = "([^"]+)"',
}

def export_mf2_data(host, port, username, password, remote_directory, local_directory):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, port, username, password)

    try:
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_directory} && {POLICY_DIRECTORY}')
        file_lines_fwrules = stdout.readlines()

        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_directory} && {CONF_DIRECTORY}')
        file_lines_conf = stdout.readlines()

        downloaded_files = []
        with SCPClient(ssh.get_transport()) as scp:
            if file_lines_fwrules:
                latest_fwrules_file = file_lines_fwrules[0].split()[-1]
                remote_path = os.path.join(remote_directory, latest_fwrules_file)
                local_path = os.path.join(local_directory, f'{host}_{latest_fwrules_file}')
                scp.get(remote_path, local_path)
                downloaded_files.append(f'{host}_{latest_fwrules_file}')

            specified_conf_files = [
                'groupobject.conf',
                'hostobject.conf',
                'networkobject.conf',
                'serviceobject.conf',
            ]

            for line in file_lines_conf:
                conf_file = line.strip()
                if conf_file in specified_conf_files:
                    remote_path = os.path.join(remote_directory, conf_file)
                    download_name = f'{host}_{conf_file}'
                    local_path = os.path.join(local_directory, download_name)
                    scp.get(remote_path, local_path)
                    downloaded_files.append(str(download_name))
        
    except Exception as e:
        print(f'error: {e}')
    finally:
        ssh.close()
        return downloaded_files

def download_rule_file(host, port, username, password, remote_directory, local_directory):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, port, username, password)

    try:
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_directory} && {POLICY_DIRECTORY}')
        file_lines_fwrules = stdout.readlines()

        with SCPClient(ssh.get_transport()) as scp:
            if file_lines_fwrules:
                latest_fwrules_file = file_lines_fwrules[0].split()[-1]
                remote_path = os.path.join(remote_directory, latest_fwrules_file)
                local_path = os.path.join(local_directory, f'{host}_{latest_fwrules_file}')
                scp.get(remote_path, local_path)
        
    except Exception as e:
        print(f'error: {e}')
    finally:
        ssh.close()
        return f'{host}_{latest_fwrules_file}'

def show_system_info(host, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, port, username, password)

    try:
        stdin, stdout, stderr = ssh.exec_command(f'hostname')
        hostname = stdout.readline().rstrip()

        stdin, stdout, stderr = ssh.exec_command(f'uptime')
        uptime_data = stdout.readline().rstrip().split(' ')
        uptime = str(uptime_data[3]) + ' ' + str(uptime_data[4].rstrip(','))

        stdin, stdout, stderr = ssh.exec_command(f'{INFO_FILE}')
        info = stdout.readlines()

        stdin, stdout, stderr = ssh.exec_command(f'rpm -q mf2')
        version = stdout.readline().rstrip()

        model = info[0].split('=')[1].rstrip('\n').lstrip()
        mac_address = info[2].split('=')[1].rstrip('\n').lstrip()
        hw_serial = info[3].split('=')[1].rstrip('\n').lstrip()

        info = {
            "hostname": hostname,
            "ip_address": host,
            "mac_address": mac_address,
            "uptime": uptime,
            "model": model,
            "serial_number": hw_serial,
            "sw_version": version,
        }

        return pd.DataFrame(info, index=[0])
        
    except Exception as e:
        print(f'error: {e}')
    finally:
        ssh.close()

def download_object_files(host, port, username, password, remote_directory, local_directory):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(host, port, username, password)

    try:
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_directory} && {CONF_DIRECTORY}')
        file_lines_fwrules = stdout.readlines()

        downloaded_files = []
        with SCPClient(ssh.get_transport()) as scp:
            if file_lines_fwrules:
                latest_fwrules_file = file_lines_fwrules[0].split()[-1]
                remote_path = os.path.join(remote_directory, latest_fwrules_file)
                local_path = os.path.join(local_directory, f'{host}_{latest_fwrules_file}')
                scp.get(remote_path, local_path)
                downloaded_files.append(f'{host}_{latest_fwrules_file}')

            specified_conf_files = [
                'groupobject.conf',
                'hostobject.conf',
                'networkobject.conf',
                'serviceobject.conf',
            ]

            for line in file_lines_conf:
                conf_file = line.strip()
                if conf_file in specified_conf_files:
                    remote_path = os.path.join(remote_directory, conf_file)
                    download_name = f'{host}_{conf_file}'
                    local_path = os.path.join(local_directory, download_name)
                    scp.get(remote_path, local_path)
                    downloaded_files.append(str(download_name))
        
    except Exception as e:
        print(f'error: {e}')
    finally:
        ssh.close()
        return downloaded_files

# Config file 파싱
def remove_newlines_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            content = file.read()

        content_without_newlines = content.replace('\n', '')

        return content_without_newlines
    except Exception as e:
        return f"error: {e}"

def extract_braces_of_depth_1_or_more(content):
    depth = 0
    depth_1_or_more_content = []
    temp = ""

    for char in content:
        if char == '{':
            if depth == 0:
                temp = "" # 깊이 0에서 새로운 중괄호 시작
            temp += char
            depth += 1
        elif char == '}':
            temp += char
            depth -= 1
            if depth == 0:
                # 깊이가 0으로 돌아오면 현재까지의 내용을 결과 리스트에 추가
                depth_1_or_more_content.append(temp.strip())
        elif depth >= 1:
            temp += char # 깊이가 1 이상인 경우에만 temp에 문자 추가
    
    return depth_1_or_more_content

def extract_braces_of_depth_2_or_more_without_outer_braces(content):
    depth = 0
    depth_2_or_more_content = []
    temp = ""

    for char in content:
        if char == '{':
            if depth >= 1:
                temp += char # 깊이 1 이상에서 중괄호 시작 추가
            depth += 1
        elif char == '}':
            depth -= 1
            if depth >= 1:
                temp += char # 깊이 1 이상에서 중괄호 종료 추가
                if depth == 1:
                    # 첫 '{' 와 마지막 '}'를 제외하고 결과 리스트에 추가
                    depth_2_or_more_content.append(temp[1:-1].strip())
                    temp = ""
        elif depth >= 2:
            temp += char # 깊이가 2 이상인 경우에만 temp에 문자 추가
    
    return depth_2_or_more_content

def parse_object(object):
    parsed_objects = []

    object = object.replace('"', '')

    if "," in object:
        for entry in object.split(','):
            parsed_objects.append(entry.split(' ')[1])
    else:
        if " " in object:
            parsed_objects.append(object.split(' ')[1])
        else:
            parsed_objects.append(object)
    
    return ','.join(str(s) for s in parsed_objects)

def group_parsing(file_path):
    content = remove_newlines_from_file(file_path)
    depth_2_braces = extract_braces_of_depth_2_or_more_without_outer_braces(content)

    depth_2_braces.pop(0) # delete id info

    # Extracting and storing data in a list of dictionaries
    data_list = []
    for text in depth_2_braces:
        data = {}
        pattern = GROUP_PATTERN
        for key, pattern in pattern.items():
            match = re.search(pattern, text)
            if match and key in ['hosts', 'networks']:
                parsed_object = []
                object = match.group(1)
                if object:
                    object_list = object.split(',')
                    for host in object_list:
                        parsed_object.append(host.split('=')[0].replace('[', '').replace(']', ''))
                data[key] = ','.join(str(s) for s in parsed_object)
            elif match and key == 'count':
                parsed_object = []
                object = match.group(1)
                if object:
                    object_list = object.split(',')
                    for host in object_list:
                        parsed_object.append(host.split('=')[1])
                data[key] = ','.join(str(s) for s in parsed_object)
            elif match:
                data[key] = match.group(1)
        data_list.append(data)
    
    # converting the list of dictionaries to a dataframe
    df = pd.DataFrame(data_list)

    return df

def service_parsing(file_path):
    content = remove_newlines_from_file(file_path)
    depth_2_braces = extract_braces_of_depth_2_or_more_without_outer_braces(content)

    # delete id, second info
    depth_2_braces.pop(0)
    depth_2_braces.pop(0)

    # Extracting and storing data in a list of dictionaries
    data_list = []
    for text in depth_2_braces:
        data = {}

        pattern = SERVICE_PATTERN

        for key, pattern in pattern.items():
            match = re.search(pattern, text)
            if match:
                data[key] = match.group(1)
        data_list.append(data)
    
    return de

def network_parsing(file_path):
    content = remove_newlines_from_file(file_path)
    depth_2_braces = extract_braces_of_depth_2_or_more_without_outer_braces(content)

    depth_2_braces.pop(0)

    data_list = []
    for text in depth_2_braces:
        data = {}
        if "range" in text:
            pattern = RANGE_PATTERN
        else:
            pattern = MASK_PATTERN
        
        for key, pattern in pattern.items():
            match = re.search(pattern, text)
            if match:
                data[key] = match.group(1)
        data_list.append(data)
    
    df = pd.DataFrame(data_list)

    return df

def host_parsing(file_path):
    content = remove_newlines_from_file(file_path)
    depth_2_braces = extract_braces_of_depth_2_or_more_without_outer_braces(content)

    depth_2_braces.pop(0)

    data_list = []
    for text in depth_2_braces:
        data = {}
        pattern = HOST_PATTERN
        for key, pattern in pattern.items():
            match = re.search(pattern, text)
            if match:
                data[key] = match.group(1)
        data_list.append(data)
    
    df = pd.DataFrame(data_list)

    return df

def rule_parsing(file_path):
    content = remove_newlines_from_file(file_path)
    depth_2_braces = extract_braces_of_depth_2_or_more_without_outer_braces(content)
    rule_data = extract_braces_of_depth_1_or_more(depth_2_braces[0])

    # 정규표현식을 사용하여 데이터 추출
    rule_pattern = r"\{rid=(.*?), "
    description_pattern = r"description=\"(.*?)\", use="
    use_pattern = r"use=\"(.*?)\", action"
    action_pattern = r"action=\"(.*?)\", group"
    shaping_string_pattern = r"shaping_string=\"(.*?)\", bi_di"
    source_pattern = r"from=\{(.*?)\},  to"
    destination_pattern = r"to=\{(.*?)\},  service"
    service_pattern = r"service=\{(.*?)\},  vid"
    ua_pattern = r"ua=\{(.*?)\}, unuse"

    policy = []
    for idx, rule in enumerate(rule_data):
        rulename = re.findall(rule_pattern, rule)
        description = re.findall(description_pattern, rule)
        use = re.findall(use_pattern, rule)
        action = re.findall(action_pattern, rule)
        shaping_string = re.findall(shaping_string_pattern, rule)
        shaping_string = str(shaping_string[0])
        if "time=" in shaping_string:
            schedule = shaping_string.split('=')[1].lstrip('"')
        else:
            schedule = ''
        source = re.findall(source_pattern, rule)
        destination = re.findall(destination_pattern, rule)
        service = re.findall(service_pattern, rule)
        ua = re.findall(ua_pattern, rule)

        rule_info = {
            "Seq": idx + 1,
            "Rule Name": int(rulename[0]),
            "Enable": str(use[0]),
            "Action": str(action[0]),
            "Source": parse_object(source[0]),
            "User": parse_object(ua[0]),
            "Destination": parse_object(destination[0]),
            "Service": parse_object(service[0]),
            "Applicationn": "Any",
            "Security Profile": schedule,
            "Description": str(description[0]),
        }
        policy.append(rule_info)
    
    df = pd.DataFrame(policy)

    df[['Source', 'Destination', 'Service', 'User']] = df[['Source', 'Destination', 'Service', 'User']].replace({'': 'Any', ' ': 'Any'})

    return df

def delete_files(file_paths):
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
    
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)
        else:
            print(f"File not found: {path}")

def export_objects(device_ip, username, password):
    files = download_object_files(
        device_ip, 22, username, password, '/temp/', './'
    )
    group_file = f'{files[0]}'
    host_file = f'{files[1]}'
    network_file = f'{files[2]}'
    service_file = f'{files[3]}'

    address_df, address_group_df = export_address_objects(group_file, host_file, network_file)
    service_df = export_service_objects(service_file)
    
    delete_files(files)

    return [address_df, address_group_df, service_df]

def export_security_rules(device_ip, username, password):
    file = download_rule_file(device_ip, 22, username, password, '/temp/','./')
    rule_df = rule_parsing(f'{file}')
    delete_files(file)
    return rule_df

def combine_mask_end(row):
    # mask/end가 숫자로만 구성되어 있다면, cidr로 변환
    if row['mask/end'].isdigit():
        return f"{row['ip/start']}/{row['mask/end']}"
    else:
        return f"{row['ip/start']}-{row['mask/end']}"

def replace_values(ids, mapping):
    # 콤마로 구분된 문자열을 리스트로 변환하고 각 원소에 대응하는 값을 찾음
    return ','.join(mapping.get(id_str, '') for id_str in ids.split(','))

