# main.py
from firewall.collector_factory import FirewallCollectorFactory

def main():
    # PaloAlto Collector 사용 예시
    palo_collector = FirewallCollectorFactory.get_collector(
        'paloalto',
        hostname='palo.example.com',
        username='palo_user',
        password='palo_pass'
    )
    palo_sys_info = palo_collector.get_system_info()
    palo_rules = palo_collector.export_security_rules()
    print("PaloAlto System Info:")
    print(palo_sys_info.head())
    print("PaloAlto Security Rules:")
    print(palo_rules.head())

    # MF2 Collector 사용 예시
    mf2_collector = FirewallCollectorFactory.get_collector(
        'mf2',
        device_ip='mf2.example.com',
        username='mf2_user',
        password='mf2_pass'
    )
    mf2_sys_info = mf2_collector.get_system_info()
    mf2_rules = mf2_collector.export_security_rules()
    print("MF2 System Info:")
    print(mf2_sys_info.head())
    print("MF2 Security Rules:")
    print(mf2_rules.head())

    # NGF Collector 사용 예시
    ngf_collector = FirewallCollectorFactory.get_collector(
        'ngf',
        hostname='ngf.example.com',
        ext_clnt_id='ngf_client_id',
        ext_clnt_secret='ngf_client_secret'
    )
    # NGF의 시스템 정보 기능이 없다면 보안 규칙만 조회
    ngf_rules = ngf_collector.export_security_rules()
    print("NGF Security Rules:")
    print(ngf_rules.head())

if __name__ == "__main__":
    main()