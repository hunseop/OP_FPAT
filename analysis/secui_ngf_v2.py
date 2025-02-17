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

    @staticmethod
    def list_to_string(list_data) -> str:
        """
        리스트 데이터를 콤마로 구분된 문자열로 변환합니다.
        """
        if isinstance(list_data, list):
            return ','.join(str(s) for s in list_data)
        return list_data

    def download_ngf_rules(self) -> dict:
        """
        NGF 규칙 데이터를 로그인 후 조회하고 로그아웃하여 반환합니다.
        """
        token = self.login()
        if token:
            rules_data = self.get_fw4_rules()
            self.logout()
            return rules_data
        return None

    def export_security_rules(self) -> pd.DataFrame:
        """
        NGF 규칙 데이터를 파싱하여 pandas DataFrame으로 반환합니다.
        """
        rules_data = self.download_ngf_rules()
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