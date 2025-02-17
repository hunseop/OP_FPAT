# firewall/ngf/ngf_collector.py
import pandas as pd
from firewall.firewall_interface import FirewallCollector
from .ngf_module import NGFClient

class NGFCollector(FirewallCollector):
    def __init__(self, hostname: str, ext_clnt_id: str, ext_clnt_secret: str):
        self.client = NGFClient(hostname, ext_clnt_id, ext_clnt_secret)

    def get_system_info(self) -> pd.DataFrame:
        # NGF 모듈에 시스템 정보 기능이 없는 경우 빈 DataFrame 반환
        return pd.DataFrame()

    def export_security_rules(self) -> pd.DataFrame:
        return self.client.export_security_rules()