# firewall/mf2/mf2_collector.py
import pandas as pd
from firewall.firewall_interface import FirewallCollector
from .mf2_module import show_system_info, export_security_rules

class MF2Collector(FirewallCollector):
    def __init__(self, device_ip: str, username: str, password: str):
        self.device_ip = device_ip
        self.username = username
        self.password = password

    def get_system_info(self) -> pd.DataFrame:
        # 기본 포트 22 사용
        return show_system_info(self.device_ip, 22, self.username, self.password)

    def export_security_rules(self) -> pd.DataFrame:
        return export_security_rules(self.device_ip, self.username, self.password)