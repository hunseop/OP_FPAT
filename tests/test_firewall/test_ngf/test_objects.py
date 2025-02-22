import pytest
import requests_mock
import pandas as pd
from firewall.ngf.ngf_module import NGFClient

@pytest.fixture
def mock_host_response():
    """호스트 객체 응답 데이터 fixture"""
    return {
        "result": [
            {
                "addr_obj_id": "1",
                "name": "Server1",
                "ip": "192.168.1.100"
            }
        ]
    }

@pytest.fixture
def mock_network_response():
    """네트워크 객체 응답 데이터 fixture"""
    return {
        "result": [
            {
                "addr_obj_id": "2",
                "name": "Internal_Network",
                "ip": "192.168.0.0",
                "mask": "255.255.0.0"
            }
        ]
    }

@pytest.fixture
def mock_service_response():
    """서비스 객체 응답 데이터 fixture"""
    return {
        "result": [
            {
                "name": "HTTP",
                "port": "80",
                "protocol": "tcp",
                "srv_obj_id": "1"
            }
        ]
    }

def test_export_host_objects(mock_host_response):
    """호스트 객체 추출 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        # Mock host objects response
        m.get(
            'https://test_host/api/op/host/4/objects',
            json=mock_host_response
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        
        # 호스트 객체를 DataFrame으로 변환
        response = client.get_host_objects()
        df = pd.DataFrame(response['result'])
        
        assert not df.empty
        assert 'name' in df.columns
        assert 'ip' in df.columns
        assert df.iloc[0]['name'] == 'Server1'
        assert df.iloc[0]['ip'] == '192.168.1.100'

def test_export_network_objects(mock_network_response):
    """네트워크 객체 추출 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        # Mock network objects response
        m.get(
            'https://test_host/api/op/network/4/objects',
            json=mock_network_response
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        
        # 네트워크 객체를 DataFrame으로 변환
        response = client.get_network_objects()
        df = pd.DataFrame(response['result'])
        
        assert not df.empty
        assert 'name' in df.columns
        assert 'ip' in df.columns
        assert 'mask' in df.columns
        assert df.iloc[0]['name'] == 'Internal_Network'
        assert df.iloc[0]['ip'] == '192.168.0.0'
        assert df.iloc[0]['mask'] == '255.255.0.0'

def test_export_service_objects(mock_service_response):
    """서비스 객체 추출 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        # Mock service objects response
        m.get(
            'https://test_host/api/op/service/objects',
            json=mock_service_response
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        
        # 서비스 객체를 DataFrame으로 변환
        response = client.get_service_objects()
        df = pd.DataFrame(response['result'])
        
        assert not df.empty
        assert 'name' in df.columns
        assert 'protocol' in df.columns
        assert 'port' in df.columns
        assert df.iloc[0]['name'] == 'HTTP'
        assert df.iloc[0]['protocol'] == 'tcp'
        assert df.iloc[0]['port'] == '80' 