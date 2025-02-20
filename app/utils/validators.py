import re
from typing import Optional, Tuple

def validate_firewall_name(name: str) -> Tuple[bool, Optional[str]]:
    """방화벽 이름 검증
    - 2자 이상 50자 이하
    - 특수문자는 '-', '_'만 허용
    """
    if not 2 <= len(name) <= 50:
        return False, "방화벽 이름은 2자 이상 50자 이하여야 합니다."
    
    if not re.match(r'^[가-힣a-zA-Z0-9-_\s]+$', name):
        return False, "방화벽 이름에는 한글, 영문, 숫자, 하이픈(-), 언더스코어(_)만 사용할 수 있습니다."
    
    return True, None

def validate_firewall_type(type_: str) -> Tuple[bool, Optional[str]]:
    """방화벽 타입 검증"""
    valid_types = ['ngf', 'mf2', 'paloalto']
    if type_.lower() not in valid_types:
        return False, f"유효하지 않은 방화벽 타입입니다. 가능한 값: {', '.join(valid_types)}"
    
    return True, None

def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
    """IP 주소 검증"""
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if not re.match(ip_pattern, ip):
        return False, "유효하지 않은 IP 주소 형식입니다."
    
    return True, None

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """사용자 이름 검증
    - 4자 이상 32자 이하
    - 영문, 숫자만 허용
    """
    if not 4 <= len(username) <= 32:
        return False, "사용자 이름은 4자 이상 32자 이하여야 합니다."
    
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return False, "사용자 이름은 영문과 숫자만 사용할 수 있습니다."
    
    return True, None

def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """비밀번호 검증
    - 2자 이상
    """
    if len(password) < 2:
        return False, "비밀번호는 2자 이상이어야 합니다."
    
    return True, None

def validate_firewall_data(data: dict, is_edit: bool = False) -> Tuple[bool, list]:
    """방화벽 데이터 전체 검증"""
    errors = []
    
    # 필수 필드 확인
    required_fields = ['name', 'type', 'ip_address', 'username']
    if not is_edit:  # 신규 등록 시에만 비밀번호 필수
        required_fields.append('password')
        
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"'{field}' 필드는 필수입니다.")
    
    if errors:
        return False, errors
    
    # 각 필드 유효성 검사
    validators = {
        'name': validate_firewall_name,
        'type': validate_firewall_type,
        'ip_address': validate_ip_address,
        'username': validate_username
    }
    
    # 비밀번호가 입력된 경우에만 검증
    if data.get('password'):
        validators['password'] = validate_password
    
    for field, validator in validators.items():
        is_valid, error = validator(data[field])
        if not is_valid:
            errors.append(error)
    
    return len(errors) == 0, errors 