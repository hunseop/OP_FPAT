# firewall/mf2/mf2_collector.py
import pandas as pd
from firewall.firewall_interface import FirewallInterface
from .mf2_module import show_system_info, export_security_rules, download_object_files, host_parsing, network_parsing, combine_mask_end, delete_files, export_address_objects, service_parsing
import os

class MF2Collector(FirewallInterface):
    def __init__(self, device_ip: str, username: str, password: str):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(module_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_system_info(self) -> pd.DataFrame:
        # 기본 포트 22 사용
        return show_system_info(self.device_ip, self.username, self.password)

    def export_security_rules(self) -> pd.DataFrame:
        return export_security_rules(self.device_ip, self.username, self.password)

    def export_network_objects(self) -> pd.DataFrame:
        """네트워크 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        conf_types = ['hostobject.conf', 'networkobject.conf']
        files = download_object_files(self.device_ip, 22, self.username, self.password, '/secui/etc/', self.temp_dir, conf_types)
        if len(files) < len(conf_types):
            return pd.DataFrame(columns=['Name', 'Type', 'Value'])

        host_file = os.path.join(self.temp_dir, f"{self.device_ip}_hostobject.conf")
        network_file = os.path.join(self.temp_dir, f"{self.device_ip}_networkobject.conf")

        # 호스트 객체 처리
        host_df = host_parsing(host_file)
        host_df = host_df[['name', 'ip']].rename(columns={'name': 'Name', 'ip': 'Value'})
        host_df['Type'] = 'ip-netmask'

        # 네트워크 객체 처리
        network_df = network_parsing(network_file)
        network_df['Value'] = network_df.apply(combine_mask_end, axis=1)
        network_df = network_df[['name', 'Value']].rename(columns={'name': 'Name'})
        network_df['Type'] = 'ip-netmask'

        # 결과 합치기
        result_df = pd.concat([host_df, network_df], ignore_index=True)
        # 'Value'에 '-'가 포함되어 있으면 ip-range, 그렇지 않으면 ip-netmask로 설정
        result_df['Type'] = result_df['Value'].apply(lambda v: 'ip-range' if '-' in str(v) else 'ip-netmask')

        delete_files(files)
        return result_df

    def export_network_group_objects(self) -> pd.DataFrame:
        """네트워크 그룹 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        conf_types = ['hostobject.conf', 'networkobject.conf', 'groupobject.conf']
        files = download_object_files(self.device_ip, 22, self.username, self.password, '/secui/etc/', self.temp_dir, conf_types)
        if len(files) < len(conf_types):
            return pd.DataFrame(columns=['Group Name', 'Entry'])

        group_file = os.path.join(self.temp_dir, f"{self.device_ip}_groupobject.conf")
        host_file = os.path.join(self.temp_dir, f"{self.device_ip}_hostobject.conf")
        network_file = os.path.join(self.temp_dir, f"{self.device_ip}_networkobject.conf")

        address_df, group_df = export_address_objects(group_file, host_file, network_file)
        delete_files(files)
        return group_df[['Group Name', 'Entry']]

    def export_service_objects(self) -> pd.DataFrame:
        """서비스 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        conf_types = ['serviceobject.conf']
        files = download_object_files(self.device_ip, 22, self.username, self.password, '/secui/etc/', self.temp_dir, conf_types)
        if len(files) < len(conf_types):
            return pd.DataFrame(columns=['Name', 'Protocol', 'Port'])

        service_file = os.path.join(self.temp_dir, f"{self.device_ip}_serviceobject.conf")
        service_df = service_parsing(service_file)
        service_df = service_df[['name', 'protocol', 'str_svc_port']].rename(
            columns={'name': 'Name', 'protocol': 'Protocol', 'str_svc_port': 'Port'}
        )
        delete_files(files)
        return service_df

    def export_service_group_objects(self) -> pd.DataFrame:
        """서비스 그룹 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        # MF2는 서비스 그룹 기능이 없으므로 빈 DataFrame 반환
        return pd.DataFrame(columns=['Group Name', 'Entry'])