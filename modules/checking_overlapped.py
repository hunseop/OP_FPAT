import ipaddress
import re

def ip_to_range(ip):
    if ip == 'any':
        return 0, 2**32 - 1
    elif '-' in ip:
        start, end = ip.split('-')
        return int(ipaddress.IPv4Address(start)), int(ipaddress.IPv4Address(end))
    else:
        net = ipaddress.ip_network(ip, strict=False)
        return int(net.network_address), int(net.broadcast_address)

def check_indiviual_ip_overlap(ip_a, ip_b):
    start_a, end_a = ip_to_range(ip_a)
    start_b, end_b = ip_to_range(ip_b)
    return not(end_a < start_b or start_a > end_b)

def is_valid_ip_format(ip):
    try:
        if ip == 'any':
            return True
        if '-' in ip:
            start, end = ip.split('-')
            ipaddress.IPv4Address(start)
            ipaddress.IPv4Address(end)
        else:
            ipaddress.ip_network(ip, strict=False)
        return True
    except ValueError:
        return False

def is_ip_overlap(ips1, ips2):
    ips1, ips2 = str(ips1), str(ips2)
    ip_list1 = [ip.strip() for ip in ips1.split(',') if is_valid_ip_format(ip.strip())]
    ip_list2 = [ip.strip() for ip in ips2.split(',') if is_valid_ip_format(ip.strip())]

    for ip1 in ip_list1:
        for ip2 in ip_list2:
            if check_indiviual_ip_overlap(ip1, ip2):
                return True
    
    return False

def split_port_range(port_range):
    if port_range and '-' in port_range:
        return map(int, port_range.split('-'))
    elif port_range:
        return int(port_range), int(port_range)
    else:
        return None, None

def check_individual_service_overlap(service_a, service_b):
    protocol1, port_range1 = re.match(r"(\w+)(?:/(\d+(?:-\d+)?))?", service_a).groups()
    protocol2, port_range2 = re.match(r"(\w+)(?:/(\d+(?:-\d+)?))?", service_b).groups()

    if protocol1 != protocol2:
        return False
    
    start_port1, end_port1 = split_port_range(port_range1)
    start_port2, end_port2 = split_port_range(port_range2)

    if start_port1 is not None and start_port2 is not None:
        return not (end_port1 < start_port2 or start_port1 > end_port2)
    
    return True

def is_service_overlap(service1, service2):
    if service1 == 'any' or service2 == 'any':
        return True
    
    services1 = service1.split(',')
    services2 = service2.split(',')

    for serv1 in services1:
        for serv2 in services2:
            if check_individual_service_overlap(serv1.strip(), serv2.strip()):
                return True
    
    return False

def is_application_overlap(app1, app2):
    if app1 == 'any' or app2 == 'any':
        return True
    
    set1, set2 = set(app1.split(',')), set(app2.split(','))
    return not set1.isdisjoint(set2)

def check_overlaps(data1, data2):
    if not is_application_overlap(data1['Application'], data2['Application']):
        return False
    
    if not is_service_overlap(data1['Extracted Service'], data2['Extracted Service']):
        return False
    
    if not (is_ip_overlap(data1['Extracted Source'], data2['Extracted Source']) and is_ip_overlap(data1['Extracted Destination'], data2['Extracted Destination'])):
        return False
    
    return True

def analyze_impact(moved_policy_name, df):
    impacted_rules = []
    matched_rules = []

    target_index = df[df['Rule Name'] == moved_policy_name].index[0]
    reference_index = df.index[-1]

    if target_index >= reference_index:
        print("이동 대상의 위치가 이동할 위치보다 같거나 상단에 있습니다.")
        return False
    
    start_index = min(target_index, reference_index)
    end_index = max(target_index, reference_index)

    for i in range(start_index, end_index + 1):
        if df.iloc[i]['Action'] == 'deny':
            impacted_rules.append(i)
    
    if impacted_rules:
        for index in impacted_rules:
            if check_overlaps(df.iloc[start_index], df.iloc[index]):
                matched_rules.append(index)
    
    result = {target_index: matched_rules}

    return result

def analyze_impact_2(moved_policy_name, df):
    impacted_rules = []
    matched_rules = []

    moved_index = df[df['Rule Name'] == moved_policy_name].index[0]
    reference_index = df.index[-2]

    if moved_index >= reference_index:
        print("이동 대상의 위치가 이동할 위치보다 같거나 상단에 있습니다.")
        return False
    
    start_index = min(moved_index, reference_index)
    end_index = max(moved_index, reference_index)

    for i in range(start_index, end_index + 1):
        if df.iloc[i]['Action'] == 'deny':
            impacted_rules.append(df.iloc[i])
    
    if impacted_rules:
        for rule in impacted_rules:
            if check_overlaps(df.iloc[start_index], rule):
                matched_rules.append(rule)
                print(rule['Rule Name', 'Source', 'Destination', 'Service', 'Application', 'Description'])
    else:
        print("영향받는 정책이 없습니다.")

def validate_policy_name(policy_name, df):
    return policy_name in df['Rule Name'].values

def main():
    target_list_file = 'target.txt'
    result_file_name = 'result.xlsx'
    device_ip = '1.1.1.1'
    username = 'admin'
    password = '1234'

    with open(target_list_file, 'r') as file:
        targets = [line.strip() for line in file]
    
    api_key = get_api_key(device_ip, username, password)
    config = get_config(device_ip, api_key)
    rules_df = rule_converting(config)
    result = []
    total_target = len(targets)
    for i, target_policy_name in enumerate(targets):
        print(f'진행률: {i+1}/{total_target}')
        try:
            result.append(analyze_impact(target_policy_name, rules_df))
        except:
            print(f'error - {target_policy_name}')
    
    output_columns = ['#', 'Type', 'Related Counts', 'Host Name', 'Seq', 'Rule Name', 'Enable', 'Action', 'Source', 'User', 'Destination', 'Service', 'Application', 'Description']
    output = []

    for idx, i in enumerate(result):
        if not i:
            print(idx, i)
            continue
        target_index = list(i.keys())[0]
        related_index = list(i.values())[0]
        related_count = len(related_index)
        target_rule = rules_df.iloc[target_index].tolist()

        indexes_to_remove = [1, 11, 13, 14, 15]

        target_rule = [item for idx, item in enumerate(target_rule) if idx not in indexes_to_remove]
        target_rule.insert(0, related_count)
        target_rule.insert(0, 'Target Rule')
        target_rule.insert(0, idx + 1)
        output.append(target_rule)
        if related_count >= 1:
            for j in related_index:
                related_rule = rules_df.iloc[j].tolist()
                indexes_to_remove = [1, 11, 13, 14, 15]

                related_rule = [item for idx, item in enumerate(related_rule) if idx not in indexes_to_remove]
                related_rule.insert(0, '-')
                related_rule.insert(0, 'Related Rule')
                related_rule.insert(0, idx + 1)
                output.append(related_rule)
        
    output_df = pd.DataFrame(output, columns=output_columns)
    output_df.to_excel(result_file_name, index=False)