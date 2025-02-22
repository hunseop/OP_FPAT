from firewall.firewall_interface import FirewallInterface
from .mock_module import MockFirewall
import pandas as pd

class MockCollector(FirewallInterface):
    """테스트용 가상 방화벽 Collector"""
    
    def __init__(self, hostname: str, username: str, password: str):
        self.client = MockFirewall(hostname, username, password)
    
    def export_security_rules(self):
        """보안 규칙 내보내기"""
        return self.client.export_security_rules()
    
    def export_network_objects(self):
        """네트워크 객체 내보내기"""
        return self.client.export_network_objects()
    
    def export_network_group_objects(self):
        """네트워크 그룹 내보내기"""
        return self.client.export_network_group_objects()
    
    def export_service_objects(self):
        """서비스 객체 내보내기"""
        return self.client.export_service_objects()
    
    def export_service_group_objects(self):
        """서비스 그룹 내보내기"""
        return self.client.export_service_group_objects()

    def get_system_info(self):
        """시스템 정보 조회 (Mock)"""
        return pd.DataFrame({
            'hostname': [self.client.hostname],
            'version': ['1.0.0'],
            'model': ['Mock Firewall'],
            'serial': ['MOCK-12345'],
            'uptime': ['365 days'],
            'status': ['running']
        }) 