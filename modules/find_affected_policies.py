import sqlite3
import pandas as pd

# 캐시 설정
expansion_cache = {
    "address": {},
    "service": {},
    "application": {},
    "user": {},
}

# 범위 겹침 확인 함수
def get_range_overlap(start1, end1, start2, end2):
    """두 범위의 겹치는 부분을 반환. 겹치는 부분이 없으면 None을 반환"""
    if start1 <= end2 and start2 <= end1:
        return max(start1, start2), min(end1, end2)
    return None

# 객체 범위를 조회하는 함수들
def get_address_ranges(cursor, address_ids):
    """ address_id 집합에 대한 각 start_int와 end_int 범위를 가져옴 """
    ranges = []
    for address_id in address_ids:
        cursor.execute("SELECT start_int, end_int FROM Address WHERE address_id = ?", (address_id,))
        result = cursor.fetchone()
        if result:
            ranges.append(result)   
    return ranges

def get_service_ranges(cursor, service_ids):
    """ service_id 집합에 대한 각 start_port와 end_port 범위를 가져옴 """
    ranges = []
    for service_id in service_ids:
        cursor.execute("SELECT start_port, end_port FROM Service WHERE service_id = ?", (service_id,))
        result = cursor.fetchone()
        if result:
            ranges.append(result)   
    return ranges

# 객체 확장 함수들
def expand_address(cursor, address_id, visited=None):
    if visited is None:
        visited = set()
    
    if address_id == "any":
        return {"any"}

    if address_id in visited:
        return set()
    
    visited.add(address_id)

    if address_id in expansion_cache["address"]:
        return expansion_cache["address"][address_id]

    addresses = {address_id}
    cursor.execute("SELECT address_id FROM Address_Group_Members WHERE address_group_id = ?", (address_id,))
    group_members = cursor.fetchall()

    for member_id in group_members:
        addresses.update(expand_address(cursor, member_id, visited))

    expansion_cache["address"][address_id] = addresses
    return addresses

def expand_service(cursor, service_id, visited=None):
    if visited is None:
        visited = set()

    if service_id in visited:
        return set()
    
    visited.add(service_id)

    if service_id in expansion_cache["service"]:
        return expansion_cache["service"][service_id]

    services = {service_id}
    cursor.execute("SELECT service_id FROM Service_Group_Members WHERE service_group_id = ?", (service_id,))
    group_members = cursor.fetchall()

    for member_id in group_members:
        services.update(expand_service(cursor, member_id, visited))

    expansion_cache["service"][service_id] = services
    return services

def expand_application(cursor, application_id, visited=None):
    if visited is None:
        visited = set()

    if application_id in visited:
        return set()

    visited.add(application_id)

    if application_id in expansion_cache["application"]:
        return expansion_cache["application"][application_id]

    applications = {application_id}
    cursor.execute("SELECT application_id FROM Application_Group_Members WHERE application_group_id = ?", (application_id,))
    group_members = cursor.fetchall()

    for member_id in group_members:
        applications.update(expand_application(cursor, member_id))

    expansion_cache["application"][application_id] = applications
    return applications

def expand_user(user_id):
    if user_id in expansion_cache["user"]:
        return expansion_cache["user"][user_id]

    users = {user_id}

    expansion_cache["user"][user_id] = users
    return users

# 허용 정책 추출
def get_allow_policies_below_block(cursor, block_policy_id):
    cursor.execute("SELECT seq FROM Policies WHERE policy_id = ?", (block_policy_id,))
    block_seq = cursor.fetchone()[0]

    cursor.execute("SELECT policy_id FROM Policies WHERE action = 'allow' AND seq > ?", (block_seq,))

    return [row[0] for row in cursor.fetchall()]

# 겹치는 객체 추출을 포함한 비교 함수들
def compare_address(cursor, block_address_ids, allow_address_ids):
    block_ranges = get_address_ranges(cursor, block_address_ids)
    allow_ranges = get_address_ranges(cursor, allow_address_ids)

    overlapping_ranges = []
    for block_start, block_end in block_ranges:
        for allow_start, allow_end in allow_ranges:
            overlap = get_range_overlap(block_start, block_end, allow_start, allow_end)
            if overlap:
                overlapping_ranges.append(overlap)
    
    return overlapping_ranges if overlapping_ranges else None

def compare_service(cursor, block_service_ids, allow_service_ids):
    block_ranges = get_service_ranges(cursor, block_service_ids)
    allow_ranges = get_service_ranges(cursor, allow_service_ids)

    overlapping_ranges = []
    for block_start, block_end in block_ranges:
        for allow_start, allow_end in allow_ranges:
            overlap = get_range_overlap(block_start, block_end, allow_start, allow_end)
            if overlap:
                overlapping_ranges.append(overlap)
    
    return overlapping_ranges if overlapping_ranges else None

def compare_user(block_user_list, allow_user_list):
    if "any" in block_user_list:
        return allow_user_list
    if "any" in allow_user_list:
        return block_user_list
    return list(set(block_user_list) & set(allow_user_list))

def compare_application(block_app_list, allow_app_list):
    if "any" in block_app_list:
        return allow_app_list
    if "any" in allow_app_list:
        return block_app_list
    return list(set(block_app_list) & set(allow_app_list))

# 차단 정책과 허용 정책 간 겹치는 객체 추출 함수
def find_overlapping_objects(cursor, block_objects, allow_objects):
    overlapping_objects = {
        "sources": compare_address(cursor, block_objects["sources"], allow_objects["sources"]),
        "destinations": compare_address(cursor, block_objects["destinations"], allow_objects["destinations"]),
        "services": compare_service(cursor, block_objects["services"], allow_objects["services"]),
        "users": compare_user(block_objects["users"], allow_objects["users"]),
        "applications": compare_application(block_objects["applications"], allow_objects["applications"]),
    }

    overlapping_objects = {k: v for k, v in overlapping_objects.items() if v}
    return overlapping_objects

# 영향받는 정책 조회 및 매핑
def find_affected_policies(cursor, overlapping_objects):
    """ 차단 정책 이동 시 영향받는 허용 정책을 조회하고 매핑합니다. """
    affected_policies = []

    # 각 객체 필드별로 겹치는 객체 조회
    for field, ids in overlapping_objects.items():
        if not ids:
            continue

        table_name = {
            "sources": "Policy_Source",
            "users": "Policy_User",
            "destinations": "Policy_Destination",
            "services": "Policy_Service",
            "applications": "Policy_Application",
        }.get(field)

        if table_name:
            for obj_id in ids:
                cursor.execute(f"""
                    SELECT p.policy_id, p.rule_name
                    FROM {table_name} po ON p.policy_id = po.policy_id
                    WHERE po.object_id = ?
                """, (obj_id,))

                results = cursor.fetchall()
                for policy_id, rule_name in results:
                    affected_policies.append({
                        "policy_id": policy_id,
                        "rule_name": rule_name,
                        "affected_field": field,
                        "object_id": obj_id,
                    })
    
    # 모든 필드에서 겹치는 정책을 최종적으로 판별
    final_affected_policies = {}
    for policy in affected_policies:
        policy_id = policy["policy_id"]
        if policy_id not in final_affected_policies:
            final_affected_policies[policy_id] = {
                "policy_id": policy_id,
                "rule_name": policy["rule_name"],
                "affected_fields": set(),
                "object_ids": set(),
            }
        
        # 영향을 받는 필드 및 객체 ID 추가
        final_affected_policies[policy_id]["affected_fields"].add(policy["affected_field"])
        final_affected_policies[policy_id]["object_ids"].add(policy["object_id"])
    
    # 모든 필드에서 겹치는 정책만 필터링
    fully_affected_policies = [p for p in final_affected_policies.values() if len(p["affected_fields"]) == 5]

    return fully_affected_policies

# 허용 정책 객체 확장 및 중복 제거
def expand_and_merge_allow_policy_objects(cursor, allow_policy_ids):
    merged_sources = set()
    merged_destinations = set()
    merged_services = set()
    merged_users = set()
    merged_applications = set()

    for policy_id in allow_policy_ids:
        merged_sources.update(expand_address(cursor, policy_id))
        merged_destinations.update(expand_address(cursor, policy_id))
        merged_services.update(expand_service(cursor, policy_id))
        merged_users.update(expand_user(policy_id))
        merged_applications.update(expand_application(cursor, policy_id))
    
    return {
        "sources": merged_sources,
        "users": merged_users,
        "destinations": merged_destinations,
        "services": merged_services,
        "applications": merged_applications,
    }

# 엑셀 파일로 결과 출력
def export_to_excel(block_policy, affected_policies, filename="impact_analysis.xlsx"):
    block_policy_df = pd.DataFrame([{
        "policy_id": block_policy["policy_id"],
        "rule_name": block_policy["rule_name"],
        "source": ",".join(map(str, block_policy["sources"])),
        "user": ",".join(map(str, block_policy["users"])),
        "destination": ",".join(map(str, block_policy["destinations"])),
        "service": ",".join(map(str, block_policy["services"])),
        "application": ",".join(map(str, block_policy["applications"])),
        "affected_object": "Blocking Policy"
    }])

    affected_policies_data = []
    for policy in affected_policies:
        affected_policies_data.append({
            "policy_id": policy["policy_id"],
            "rule_name": policy["rule_name"],
            "source": ",".join(map(str, policy["object_ids"] if "sources" in policy["affected_fields"] else [])),
            "user": ",".join(map(str, policy["object_ids"] if "users" in policy["affected_fields"] else [])),
            "destination": ",".join(map(str, policy["object_ids"] if "destinations" in policy["affected_fields"] else [])),
            "service": ",".join(map(str, policy["object_ids"] if "services" in policy["affected_fields"] else [])),
            "application": ",".join(map(str, policy["object_ids"] if "applications" in policy["affected_fields"] else [])),
            "affected_object": "Affected"
        })
    
    affected_policies_df = pd.DataFrame(affected_policies_data)
    result_df = pd.concat([block_policy_df, affected_policies_df], ignore_index=True)
    result_df.to_excel(filename, index=False, engine='xlsxwriter')

# 메인 함수
def main(db_name, block_policy_name, output_filename="impact_analysis.xlsx"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 차단 정책 조회
    cursor.execute("SELECT policy_id FROM Policies WHERE rule_name = ? AND action = 'deny'", (block_policy_name,))
    block_policy_data = cursor.fetchone()
    if not block_policy_data:
        print(f"차단 정책 {block_policy_name}을 찾을 수 없습니다.")
        conn.close()
        return
    block_policy_id = block_policy_data[0]

    def get_policy_objects(policy_id, table_name):
        cursor.execute(f"SELECT object_id FROM {table_name} WHERE policy_id = ?", (policy_id,))
        return {row[0] for row in cursor.fetchall()}

    block_objects = {
        "sources": get_policy_objects(block_policy_id, "Policy_Source"),
        "users": get_policy_objects(block_policy_id, "Policy_User"),
        "destinations": get_policy_objects(block_policy_id, "Policy_Destination"),
        "services": get_policy_objects(block_policy_id, "Policy_Service"),
        "applications": get_policy_objects(block_policy_id, "Policy_Application"),
    }

    allow_policies = get_allow_policies_below_block(cursor, block_policy_id)
    allow_objects = expand_and_merge_allow_policy_objects(cursor, allow_policies)
    overlapping_objects = find_overlapping_objects(cursor, block_objects, allow_objects)
    affected_policies = find_affected_policies(cursor, overlapping_objects)

    block_policy = {
        "policy_id": block_policy_id,
        "rule_name": block_policy_name,
        "sources": block_objects["sources"],
        "users": block_objects["users"],
        "destinations": block_objects["destinations"],
        "services": block_objects["services"],
        "applications": block_objects["applications"],
    }
    export_to_excel(block_policy, affected_policies, output_filename)

    conn.close()
    print(f"{block_policy_name} 정책의 영향 분석 결과이 {output_filename} 파일로 저장되었습니다.")

if __name__ == "__main__":
    main("firewall.db", "Block_All_Web_Traffic")