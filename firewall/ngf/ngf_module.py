import json
import logging
import requests
import pandas as pd

# SSL 경고 비활성화
requests.packages.urllib3.disable_warnings()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class NGFClient:
    """
    NGF API와 연동하여 로그인, 데이터 조회, 규칙 파싱 등의 기능을 제공하는 클라이언트입니다.
    """

    def __init__(self, hostname: str, ext_clnt_id: str, ext_clnt_secret: str, timeout: int = 60):
        self.hostname = hostname
        self.ext_clnt_id = ext_clnt_id
        self.ext_clnt_secret = ext_clnt_secret
        self.timeout = timeout
        self.token = None
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/54.0.2840.99 Safari/537.6"
        )

    def _get_headers(self, token: str = None) -> dict:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
        }
        if token:
            headers['Authorization'] = str(token)
        return headers

    def login(self) -> str:
        """
        NGF에 로그인하여 api_token을 반환하고, 내부적으로 저장합니다.
        """
        url = f"https://{self.hostname}/api/au/external/login"
        data = {
            "ext_clnt_id": self.ext_clnt_id,
            "ext_clnt_secret": self.ext_clnt_secret,
            "lang": "ko",
            "force": 1
        }
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                data=json.dumps(data),
                verify=False,
                timeout=3
            )
            if response.status_code == 200:
                logging.info("Login Success")
                self.token = response.json().get("result", {}).get("api_token")
                return self.token
            else:
                logging.error("Login Failed, status code: %s", response.status_code)
                return None
        except Exception as e:
            logging.error("Exception during login: %s", e)
            return None

    def logout(self) -> bool:
        """
        NGF에서 로그아웃합니다.
        """
        if not self.token:
            logging.warning("No token available for logout")
            return False

        url = f"https://{self.hostname}/api/au/external/logout"
        try:
            response = requests.delete(
                url,
                headers=self._get_headers(token=self.token),
                verify=False,
                timeout=3
            )
            if response.status_code == 200:
                logging.info("Logout Success")
                self.token = None
                return True
            else:
                logging.error("Logout Failed, status code: %s", response.status_code)
                return False
        except Exception as e:
            logging.error("Exception during logout: %s", e)
            return False

    def _get(self, endpoint: str) -> dict:
        """
        내부적으로 GET 요청을 수행합니다.
        """
        url = f"https://{self.hostname}{endpoint}"
        try:
            response = requests.get(
                url,
                headers=self._get_headers(token=self.token),
                verify=False,
                timeout=self.timeout
            )
            if response.status_code == 200:
                logging.info("GET %s Success", endpoint)
                return response.json()
            else:
                logging.error("GET %s Failed, status code: %s", endpoint, response.status_code)
                return None
        except Exception as e:
            logging.error("Exception during GET %s: %s", endpoint, e)
            return None

    def _post_service_group_objects(self, endpoint: str, service_group_name: str) -> dict:
        """
        서비스 그룹 객체를 단독으로 추출하기 위한 POST 요청 수행.
        """
        url = f"https://{self.hostname}{endpoint}"
        try:
            response = requests.post(
                url,
                headers=self._get_headers(token=self.token),
                verify=False,
                timeout=self.timeout,
                json={'name': service_group_name}
            )
            if response.status_code == 200:
                logging.info("GET %s Success", endpoint)
                return response.json()
            else:
                logging.error("GET %s Failed, status code: %s", endpoint, response.status_code)
                return None
        except Exception as e:
            logging.error("Exception during GET %s: %s", endpoint, e)
            return None

    def get_fw4_rules(self) -> dict:
        """
        FW4 규칙 데이터를 조회합니다.
        """
        return self._get("/api/po/fw/4/rules")

    def get_host_objects(self) -> dict:
        """
        호스트 객체 데이터를 조회합니다.
        """
        return self._get("/api/op/host/4/objects")

    def get_network_objects(self) -> dict:
        """
        네트워크 객체 데이터를 조회합니다.
        """
        return self._get("/api/op/network/4/objects")

    def get_domain_objects(self) -> dict:
        """
        도메인 객체 데이터를 조회합니다.
        """
        return self._get("/api/op/domain/4/objects")

    def get_group_objects(self) -> dict:
        """
        그룹 객체 데이터를 조회합니다.
        """
        return self._get("/api/op/group/4/objects")

    def get_service_objects(self) -> dict:
        """
        서비스 객체 데이터를 조회합니다.
        """
        return self._get("/api/op/service/objects")

    def get_service_group_objects(self) -> dict:
        """
        서비스 그룹 객체 데이터를 조회합니다.
        """
        return self._get("/api/op/service-group/objects")
    
    def get_service_group_objects_information(self, service_group_name) -> dict:
        """
        단일 서비스 그룹 객체의 데이터를 조회합니다.
        """
        return self._post_service_group_objects("/api/op/service-group/get/objects", service_group_name)

    @staticmethod
    def list_to_string(list_data) -> str:
        """
        리스트 데이터를 콤마로 구분된 문자열로 변환합니다.
        """
        if isinstance(list_data, list):
            return ','.join(str(s) for s in list_data)
        return list_data

    def export_security_rules(self) -> pd.DataFrame:
        """
        NGF 규칙 데이터를 파싱하여 pandas DataFrame으로 반환합니다.
        """
        token = self.login()
        if token:
            rules_data = self.get_fw4_rules()
            self.logout()
        
        if not rules_data:
            logging.error("No rules data available")
            return pd.DataFrame()

        security_rules = []
        rules = rules_data.get("result", [])
        for rule in rules:
            seq = rule.get("seq")
            fw_rule_id = rule.get("fw_rule_id")
            name = rule.get("name")
            # default rule은 건너뜁니다.
            if name == "default":
                continue
            use = "Y" if rule.get("use") == 1 else "N"
            action = "allow" if rule.get("action") == 1 else "deny"

            src_list = rule.get("src")
            if not src_list:
                src_list = "any"
            else:
                src_list = [src.get("name") for src in src_list]

            user_list = rule.get("user")
            if not user_list:
                user_list = "any"
            else:
                user_list = [list(user.values())[0] for user in user_list]

            dst_list = rule.get("dst")
            if not dst_list:
                dst_list = "any"
            else:
                dst_list = [dst.get("name") for dst in dst_list]

            srv_list = rule.get("srv")
            if not srv_list:
                srv_list = "any"
            else:
                srv_list = [srv.get("name") for srv in srv_list]

            app_list = rule.get("app")
            if not app_list:
                app_list = "any"
            else:
                app_list = [app.get("name") for app in app_list]

            last_hit_time = rule.get("last_hit_time")
            desc = rule.get("desc")

            info = {
                "Seq": seq,
                "Rule Name": fw_rule_id,
                "Enable": use,
                "Action": action,
                "Source": self.list_to_string(src_list),
                "User": self.list_to_string(user_list),
                "Destination": self.list_to_string(dst_list),
                "Service": self.list_to_string(srv_list),
                "Application": self.list_to_string(app_list),
                "Last Hit Date": last_hit_time,
                "Description": desc
            }
            security_rules.append(info)

        return pd.DataFrame(security_rules)

    def export_objects(self, object_type: str) -> pd.DataFrame:
        """
        NGF 객체 데이터를 파싱하여 pandas DataFrame으로 반환합니다.

        내부적으로 로그인 후 조회하고, 로그아웃을 처리합니다.
        object_type 파라미터가 반드시 지정되어야 하며, 허용되는 값은
        "host", 'network", "domain", "group", "service", "service_group" 입니다.

        API 응답의 "result" 데이터를 사용하며, pd.json_normalize()를 이용해 중첩 딕셔너리를 평탄화하고,
        각 컬럼의 값이 리스트인 경우 쉼표(,)로 조인, 딕셔너인 경우에는 딕셔너리의 value들의 쉼표로 연결합니다.

        Parameters:
            object_type (str): 조회할 객체 타입. 예: "host", "network", "domain",
                                                "group", "service", "service_group"

        Returns:
            pd.DataFrame: 조회된 객체 데이터가 포함된 DataFrame. 데이터가 없으면 빈 DataFrame 반환.
        """
        # object_type 파라미터는 반드시 지정되어야 합니다.
        if not object_type:
            logging.error("object_type 파라미터를 지정해야 합니다.")
            return pd.DataFrame()
        
        token = self.login()
        if not token:
            logging.error("로그인 실패")
            return pd.DataFrame()
        
        # 객체 타입에 따른 API 호출 함수 매핑
        type_to_getter = {
            "host": self.get_host_objects,
            "network": self.get_network_objects,
            "domain": self.get_domain_objects,
            "group": self.get_group_objects,
            "service": self.get_service_objects,
            "service_group": self.get_service_group_objects,
        }

        getter = type_to_getter.get(object_type)
        if not getter:
            logging.error("유효하지 않은 객체 타입: %s", object_type)
            self.logout()
            return pd.DataFrame
        
        data = getter()
        self.logout()

        if not data:
            logging.error("데이터를 가져올 수 없습니다: %s", object_type)
            return pd.DataFrame()
        
        results = data.get("result", [])
        if not results:
            logging.error("결과 데이터가 없습니다: %s", object_type)
            return pd.DataFrame()
        
        # pd.json_normalize()를 사용해 중첩 딕셔너리를 평탄화합니다.
        df = pd.json_normalize(results, sep='_')

        # 각 컬럼의 값에 대해:
        # - 리스트인 경우: 쉼표로 조인하여 문자열로 변환
        # - 딕셔너리인 경우: 딕셔너리의 value들을 쉼표로 연결하여 문자열로 변환
        for col in df.columns:
            df[col] = df[col].apply(lambda x: self.list_to_string(x)
                                    if isinstance(x, list)
                                    else (','.join(map(str, x.values()))
                                            if isinstance(x, dict) else x))

        return df
        '''
        서비스그룹객체를 그냥 조회하면 멤버가 조회되지 않는다.
        서비스그룹명을 리스트에 넣어 아래 메소드를 이용하여 매핑시켜야 함. 최악임.
        '''
    def export_service_group_objects_info(self, service_group_name: str) -> pd.DataFrame:
        """
        단일 서비스 그룹 객체를 파싱하여 pandas DataFrame으로 반환합니다.
        """
        token = self.login()
        if token:
            object_data = self.get_service_objects_information(service_group_name)
            self.logout()
        
        if not object_data:
            logging.error("No rules data available")
            return pd.DataFrame()
        
        result_data = object_data.get('result', [])
        
        # pd.json_normalize()를 사용해 중첩 딕셔너리를 평탄화합니다.
        df = pd.json_normalize(result_data, sep='_')
        
        for col in df.columns:
            df[col] = df[col].apply(lambda x: self.list_to_string(x)
                                    if isinstance(x, list)
                                    else (','.join(map(str, x.values()))
                                            if isinstance(x, dict) else x))

        return df
    
def export_service_group_objects_with_members(self) -> pd.DataFrame:
    """
    서비스 그룹 객체와 해당 멤버들의 정보를 포함한 DataFrame을 반환합니다.
    """
    # 1. 먼저 모든 서비스 객체 정보를 가져옴 (캐싱용)
    service_df = self.export_objects('service')
    # srv_obj_id를 키로, name을 값으로 하는 매핑 딕셔너리 생성
    service_lookup = {}
    if not service_df.empty:
        for _, row in service_df.iterrows():
            if 'srv_obj_id' in row and 'name' in row:
                service_lookup[str(row['srv_obj_id'])] = row['name']
    
    # 2. 서비스 그룹 기본 정보 가져오기
    group_df = self.export_objects('service_group')
    if group_df.empty:
        return pd.DataFrame()
    
    # 3. 각 그룹의 상세 정보를 저장할 리스트
    group_details = []
    
    # 4. 각 서비스 그룹에 대해 멤버 정보 조회
    for _, group in group_df.iterrows():
        group_info = self.export_service_group_objects_info(group['name'])
        if not group_info.empty:
            detail = group_info.iloc[0] if len(group_info) > 0 else None
            if detail is not None:
                # mem_id 문자열을 ; 기준으로 분리하여 리스트로 변환
                member_ids = str(detail['mem_id']).split(';') if detail['mem_id'] else []
                # ID를 이름으로 변환 (매핑되는 이름이 없으면 'Unknown_{id}' 사용)
                member_names = []
                for member_id in member_ids:
                    member_id = member_id.strip()  # 공백 제거
                    if member_id:  # 빈 문자열이 아닌 경우만 처리
                        member_name = service_lookup.get(member_id)
                        if member_name:
                            member_names.append(member_name)
                        else:
                            member_names.append(f'Unknown_{member_id}')
                
                group_details.append({
                    'Group Name': group['name'],
                    'Entry': ','.join(member_names) if member_names else ''
                })
    
    return pd.DataFrame(group_details)

# ────────────── 모듈 테스트 예시 ──────────────
if __name__ == '__main__':
    # NGFClient 객체 생성 후 보안 규칙 DataFrame을 출력하는 예시
    device_ip = "your_device_ip"
    client = NGFClient(device_ip, "your_ext_clnt_id", "your_ext_clnt_secret")
    df_rules = client.export_security_rules()
    if not df_rules.empty:
        logging.info("Exported Security Rules:\n%s", df_rules.head())
    else:
        logging.error("Security Rules export 실패")