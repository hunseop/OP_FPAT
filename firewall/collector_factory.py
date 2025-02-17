# firewall/collector_factory.py
from .paloalto.paloalto_collector import PaloAltoCollector
from .mf2.mf2_collector import MF2Collector
from .ngf.ngf_collector import NGFCollector

class FirewallCollectorFactory:
    @staticmethod
    def get_collector(source_type: str, **kwargs):
        """
        source_type: 'paloalto', 'mf2', 'ngf' 중 하나.
        kwargs: 각 모듈별 필요한 인자들.
            - paloalto: hostname, username, password
            - mf2: device_ip, username, password
            - ngf: hostname, ext_clnt_id, ext_clnt_secret
        """
        source_type = source_type.lower()
        if source_type == 'paloalto':
            return PaloAltoCollector(kwargs['hostname'], kwargs['username'], kwargs['password'])
        elif source_type == 'mf2':
            return MF2Collector(kwargs['device_ip'], kwargs['username'], kwargs['password'])
        elif source_type == 'ngf':
            return NGFCollector(kwargs['hostname'], kwargs['ext_clnt_id'], kwargs['ext_clnt_secret'])
        else:
            raise ValueError(f"알 수 없는 방화벽 모듈 타입: {source_type}")