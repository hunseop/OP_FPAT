# firewall/firewall_interface.py
from abc import ABC, abstractmethod
import pandas as pd

class FirewallCollector(ABC):
    @abstractmethod
    def get_system_info(self) -> pd.DataFrame:
        """시스템 정보를 DataFrame으로 반환합니다."""
        pass

    @abstractmethod
    def export_security_rules(self) -> pd.DataFrame:
        """보안 규칙 데이터를 DataFrame으로 반환합니다."""
        pass