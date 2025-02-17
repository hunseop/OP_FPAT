# firewall/paloalto/paloalto_collector.py
import pandas as pd
from firewall.firewall_interface import FirewallInterface
from .paloalto_module import PaloAltoAPI

class PaloAltoCollector(FirewallInterface):
    def __init__(self, hostname: str, username: str, password: str):
        self.api = PaloAltoAPI(hostname, username, password)

    def get_system_info(self) -> pd.DataFrame:
        """시스템 정보를 반환합니다."""
        return self.api.get_system_info()

    def export_security_rules(self) -> pd.DataFrame:
        """보안 규칙을 반환합니다."""
        return self.api.export_security_rules()

    def export_network_objects(self) -> pd.DataFrame:
        """네트워크 객체 정보를 반환합니다."""
        return self.api.export_network_objects()

    def export_network_group_objects(self) -> pd.DataFrame:
        """네트워크 그룹 객체 정보를 반환합니다."""
        return self.api.export_network_group_objects()

    def export_service_objects(self) -> pd.DataFrame:
        """서비스 객체 정보를 반환합니다."""
        return self.api.export_service_objects()

    def export_service_group_objects(self) -> pd.DataFrame:
        """서비스 그룹 객체 정보를 반환합니다."""
        return self.api.export_service_group_objects()