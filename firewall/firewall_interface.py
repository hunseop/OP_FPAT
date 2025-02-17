# firewall/firewall_interface.py
from abc import ABC, abstractmethod
import pandas as pd

class FirewallInterface(ABC):
    @abstractmethod
    def get_system_info(self) -> pd.DataFrame:
        """시스템 정보를 DataFrame으로 반환합니다."""
        pass

    @abstractmethod
    def export_security_rules(self) -> pd.DataFrame:
        """보안 규칙 데이터를 DataFrame으로 반환합니다."""
        pass

    @abstractmethod
    def export_network_objects(self) -> pd.DataFrame:
        """네트워크 객체 정보를 DataFrame으로 반환합니다.
        Returns:
            pd.DataFrame: Name, Type, Value 컬럼을 가진 DataFrame
        """
        pass

    @abstractmethod
    def export_network_group_objects(self) -> pd.DataFrame:
        """네트워크 그룹 객체 정보를 DataFrame으로 반환합니다.
        Returns:
            pd.DataFrame: Group Name, Entry 컬럼을 가진 DataFrame
        """
        pass

    @abstractmethod
    def export_service_objects(self) -> pd.DataFrame:
        """서비스 객체 정보를 DataFrame으로 반환합니다.
        Returns:
            pd.DataFrame: Name, Protocol, Port 컬럼을 가진 DataFrame
        """
        pass

    @abstractmethod
    def export_service_group_objects(self) -> pd.DataFrame:
        """서비스 그룹 객체 정보를 DataFrame으로 반환합니다.
        Returns:
            pd.DataFrame: Group Name, Entry 컬럼을 가진 DataFrame
        """
        pass