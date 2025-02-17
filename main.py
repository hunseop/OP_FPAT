# main.py
from firewall.collector_factory import FirewallCollectorFactory
import pandas as pd

def print_dataframe(df: pd.DataFrame, title: str):
    """DataFrame을 예쁘게 출력하는 헬퍼 함수"""
    print(f"\n{'='*20} {title} {'='*20}")
    if df.empty:
        print("데이터가 없습니다.")
    else:
        print(df.head())
    print('='*50)

def main():
    # PaloAlto Collector 사용 예시
    print("\n[PaloAlto 방화벽 테스트]")
    palo_collector = FirewallCollectorFactory.get_collector(
        'paloalto',
        hostname='palo.example.com',
        username='palo_user',
        password='palo_pass'
    )
    
    # 시스템 정보 및 보안 규칙
    palo_sys_info = palo_collector.get_system_info()
    palo_rules = palo_collector.export_security_rules()
    print_dataframe(palo_sys_info, "PaloAlto 시스템 정보")
    print_dataframe(palo_rules, "PaloAlto 보안 규칙")

    # 객체 정보
    palo_net_objects = palo_collector.export_network_objects()
    palo_net_groups = palo_collector.export_network_group_objects()
    palo_svc_objects = palo_collector.export_service_objects()
    palo_svc_groups = palo_collector.export_service_group_objects()
    
    print_dataframe(palo_net_objects, "PaloAlto 네트워크 객체")
    print_dataframe(palo_net_groups, "PaloAlto 네트워크 그룹")
    print_dataframe(palo_svc_objects, "PaloAlto 서비스 객체")
    print_dataframe(palo_svc_groups, "PaloAlto 서비스 그룹")

    # MF2 Collector 사용 예시
    print("\n[MF2 방화벽 테스트]")
    mf2_collector = FirewallCollectorFactory.get_collector(
        'mf2',
        device_ip='mf2.example.com',
        username='mf2_user',
        password='mf2_pass'
    )
    
    # 시스템 정보 및 보안 규칙
    mf2_sys_info = mf2_collector.get_system_info()
    mf2_rules = mf2_collector.export_security_rules()
    print_dataframe(mf2_sys_info, "MF2 시스템 정보")
    print_dataframe(mf2_rules, "MF2 보안 규칙")

    # 객체 정보
    mf2_net_objects = mf2_collector.export_network_objects()
    mf2_net_groups = mf2_collector.export_network_group_objects()
    mf2_svc_objects = mf2_collector.export_service_objects()
    mf2_svc_groups = mf2_collector.export_service_group_objects()
    
    print_dataframe(mf2_net_objects, "MF2 네트워크 객체")
    print_dataframe(mf2_net_groups, "MF2 네트워크 그룹")
    print_dataframe(mf2_svc_objects, "MF2 서비스 객체")
    print_dataframe(mf2_svc_groups, "MF2 서비스 그룹")

    # NGF Collector 사용 예시
    print("\n[NGF 방화벽 테스트]")
    ngf_collector = FirewallCollectorFactory.get_collector(
        'ngf',
        hostname='ngf.example.com',
        ext_clnt_id='ngf_client_id',
        ext_clnt_secret='ngf_client_secret'
    )
    
    # 시스템 정보 및 보안 규칙
    ngf_sys_info = ngf_collector.get_system_info()
    ngf_rules = ngf_collector.export_security_rules()
    print_dataframe(ngf_sys_info, "NGF 시스템 정보")
    print_dataframe(ngf_rules, "NGF 보안 규칙")

    # 객체 정보
    ngf_net_objects = ngf_collector.export_network_objects()
    ngf_net_groups = ngf_collector.export_network_group_objects()
    ngf_svc_objects = ngf_collector.export_service_objects()
    ngf_svc_groups = ngf_collector.export_service_group_objects()
    
    print_dataframe(ngf_net_objects, "NGF 네트워크 객체")
    print_dataframe(ngf_net_groups, "NGF 네트워크 그룹")
    print_dataframe(ngf_svc_objects, "NGF 서비스 객체")
    print_dataframe(ngf_svc_groups, "NGF 서비스 그룹")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n오류 발생: {e}")