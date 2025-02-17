# firewall/ngf/ngf_collector.py
import pandas as pd
from firewall.firewall_interface import FirewallInterface
from .ngf_module import NGFClient

class NGFCollector(FirewallInterface):
    def __init__(self, hostname: str, ext_clnt_id: str, ext_clnt_secret: str):
        self.client = NGFClient(hostname, ext_clnt_id, ext_clnt_secret)

    def get_system_info(self) -> pd.DataFrame:
        """시스템 정보를 반환합니다."""
        # NGF는 시스템 정보 기능이 없으므로 빈 DataFrame 반환
        return pd.DataFrame()

    def export_security_rules(self) -> pd.DataFrame:
        """보안 규칙을 반환합니다."""
        return self.client.export_security_rules()

    def export_network_objects(self) -> pd.DataFrame:
        """네트워크 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        # 호스트 객체
        host_objects = self.client.get_host_objects()
        if host_objects and 'result' in host_objects:
            host_df = pd.DataFrame(host_objects['result'])
            if not host_df.empty:
                host_df = host_df[['name', 'ip']].rename(columns={'name': 'Name', 'ip': 'Value'})
                host_df['Type'] = 'ip-netmask'
            else:
                host_df = pd.DataFrame(columns=['Name', 'Type', 'Value'])
        else:
            host_df = pd.DataFrame(columns=['Name', 'Type', 'Value'])

        # 네트워크 객체
        network_objects = self.client.get_network_objects()
        if network_objects and 'result' in network_objects:
            network_df = pd.DataFrame(network_objects['result'])
            if not network_df.empty:
                network_df['Value'] = network_df.apply(lambda x: f"{x['ip']}/{x['mask']}", axis=1)
                network_df = network_df[['name', 'Value']].rename(columns={'name': 'Name'})
                network_df['Type'] = 'ip-netmask'
            else:
                network_df = pd.DataFrame(columns=['Name', 'Type', 'Value'])
        else:
            network_df = pd.DataFrame(columns=['Name', 'Type', 'Value'])

        # 도메인 객체
        domain_objects = self.client.get_domain_objects()
        if domain_objects and 'result' in domain_objects:
            domain_df = pd.DataFrame(domain_objects['result'])
            if not domain_df.empty:
                domain_df = domain_df[['name']].rename(columns={'name': 'Name'})
                domain_df['Type'] = 'fqdn'
                domain_df['Value'] = domain_df['Name']
            else:
                domain_df = pd.DataFrame(columns=['Name', 'Type', 'Value'])
        else:
            domain_df = pd.DataFrame(columns=['Name', 'Type', 'Value'])

        # 결과 합치기
        result_df = pd.concat([host_df, network_df, domain_df], ignore_index=True)
        return result_df

    def export_network_group_objects(self) -> pd.DataFrame:
        """네트워크 그룹 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        group_objects = self.client.get_group_objects()
        if group_objects and 'result' in group_objects:
            group_df = pd.DataFrame(group_objects['result'])
            if not group_df.empty:
                # hosts와 networks를 합쳐서 Entry로 만들기
                group_df['Entry'] = group_df.apply(
                    lambda x: ','.join(filter(None, [
                        x.get('hosts', ''),
                        x.get('networks', '')
                    ])), axis=1
                )
                return group_df[['name', 'Entry']].rename(columns={'name': 'Group Name'})
        return pd.DataFrame(columns=['Group Name', 'Entry'])

    def export_service_objects(self) -> pd.DataFrame:
        """서비스 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        service_objects = self.client.get_service_objects()
        if service_objects and 'result' in service_objects:
            service_df = pd.DataFrame(service_objects['result'])
            if not service_df.empty:
                service_df = service_df[['name', 'protocol', 'str_svc_port']].rename(
                    columns={'name': 'Name', 'protocol': 'Protocol', 'str_svc_port': 'Port'}
                )
                return service_df
        return pd.DataFrame(columns=['Name', 'Protocol', 'Port'])

    def export_service_group_objects(self) -> pd.DataFrame:
        """서비스 그룹 객체 정보를 PaloAlto 형식으로 변환하여 반환합니다."""
        service_group_objects = self.client.get_service_group_objects()
        if service_group_objects and 'result' in service_group_objects:
            group_df = pd.DataFrame(service_group_objects['result'])
            if not group_df.empty:
                return group_df[['name', 'members']].rename(
                    columns={'name': 'Group Name', 'members': 'Entry'}
                )
        return pd.DataFrame(columns=['Group Name', 'Entry'])