# firewall/paloalto/paloalto_collector.py
import pandas as pd
from firewall.firewall_interface import FirewallCollector
from .paloalto_module import PaloAltoAPI

class PaloAltoCollector(FirewallCollector):
    def __init__(self, hostname: str, username: str, password: str):
        self.api = PaloAltoAPI(hostname, username, password)

    def get_system_info(self) -> pd.DataFrame:
        return self.api.get_system_info()

    def export_security_rules(self) -> pd.DataFrame:
        return self.api.export_security_rules()