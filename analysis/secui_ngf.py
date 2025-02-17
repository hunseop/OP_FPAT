import requests
import pandas as pd
import json
requests.packages.urllib3.disable_warnings()

# Login to the NGF
def login(hostname, ext_clnt_id, ext_clnt_secret):
    url = f"https://{hostname}/api/au/external/login"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6'
    }

    data = {
        "ext_clnt_id": ext_clnt_id,
        "ext_clnt_secret": ext_clnt_secret,
        "lang": "ko",
        "force": 1
    }

    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False, timeout=3)
    if response.status_code == 200:
        print("Login Success")
        return response.json().get("result").get("api_token")
    else:
        print("Login Failed")
        print(response.status_code)
        return None

# Logout from the NGF
def logout(hostname, token):
    url = f"https://{hostname}/api/au/external/logout"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.delete(url, headers=headers, verify=False, timeout=3)
    if response.status_code == 200:
        print("Logout Success")
        return True
    else:
        print("Logout Failed")
        print(response.status_code)
        return False

def get_fw4_rules(hostname, token):
    url = f"https://{hostname}/api/po/fw/4/rules"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get FW4 Rules Success")
        return response.json()
    else:
        print("Get FW4 Rules Failed")
        print(response.status_code)
        return None

def get_host_objects(hostname, token):
    url = f"https://{hostname}/api/op/host/4/objects"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get Host Objects Success")
        return response.json()
    else:
        print("Get Host Objects Failed")
        print(response.status_code)
        return None

def get_network_objects(hostname, token):
    url = f"https://{hostname}/api/op/network/4/objects"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get Network Objects Success")
        return response.json()
    else:
        print("Get Network Objects Failed")
        print(response.status_code)
        return None

def get_domain_objects(hostname, token):
    url = f"https://{hostname}/api/op/domain/4/objects"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get Domain Objects Success")
        return response.json()
    else:
        print("Get Domain Objects Failed")
        print(response.status_code)
        return None

def get_group_objects(hostname, token):
    url = f"https://{hostname}/api/op/group/4/objects"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get Group Objects Success")
        return response.json()
    else:
        print("Get Group Objects Failed")
        print(response.status_code)
        return None

def get_service_objects(hostname, token):
    url = f"https://{hostname}/api/op/service/objects"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get Service Objects Success")
        return response.json()
    else:
        print("Get Service Objects Failed")
        print(response.status_code)
        return None

def get_service_group_objects(hostname, token):
    url = f"https://{hostname}/api/op/service-group/objects"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.6',
        'Authorization': str(token)
    }

    response = requests.get(url, headers=headers, verify=False, timeout=60)
    if response.status_code == 200:
        print("Get Service Group Objects Success")
        return response.json()
    else:
        print("Get Service Group Objects Failed")
        print(response.status_code)
        return None

def list_to_string(list_data):
    if isinstance(list_data, list):
        return ','.join(str(s) for s in list_data)
    else:
        return list_data

def download_ngf_rules(device_ip, ext_clnt_id, ext_clnt_secret):
    token = login(device_ip, ext_clnt_id, ext_clnt_secret)
    if token:
        rules_data = get_fw4_rules(device_ip, token)
        logout(device_ip, token)
    
    return rules_data

def export_security_rules(device_ip, ext_clnt_id, ext_clnt_secret):
    rules_data = download_ngf_rules(device_ip, ext_clnt_id, ext_clnt_secret)
    security_rules = []
    rules = rules_data.get("result")
    for rule in rules:
        seq = rule.get("seq")
        fw_rule_id = rule.get("fw_rule_id")
        name = rule.get("name")
        if name == "default":
            continue
        use = "Y" if rule.get("use") == 1 else "N"
        action = "allow" if rule.get("action") == 1 else "deny"

        src_list = rule.get("src")
        src_list = "any" if not src_list else [src.get("name") for src in src_list]

        user_list = rule.get("user")
        user_list = "any" if not user_list else [list(user.values())[0] for user in user_list]

        dst_list = rule.get("dst")
        dst_list = "any" if not dst_list else [dst.get("name") for dst in dst_list]

        srv_list = rule.get("srv")
        srv_list = "any" if not srv_list else [srv.get("name") for srv in srv_list]

        app_list = rule.get("app")
        app_list = "any" if not app_list else [app.get("name") for app in app_list]

        last_hit_time = rule.get("last_hit_time")
        desc = rule.get("desc")

        info = {
            "Seq": seq,
            "Rule Name": fw_rule_id,
            # "Rule Name": name,
            "Enable": use,
            "Action": action,
            "Source": list_to_string(src_list),
            "User": list_to_string(user_list),
            "Destination": list_to_string(dst_list),
            "Service": list_to_string(srv_list),
            "Application": list_to_string(app_list),
            "Last Hit Date": last_hit_time,
            "Description": desc
        }
        security_rules.append(info)
    
    return pd.DataFrame(security_rules)