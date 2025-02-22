import pytest
import pandas as pd
from firewall.ngf.ngf_module import NGFClient
import requests_mock

@pytest.fixture
def mock_rules_response():
    """규칙 응답 데이터 fixture"""
    return {
        "result": [
            {
                "seq": 1,
                "fw_rule_id": "rule1",
                "name": "Allow Web",
                "use": 1,
                "action": 1,
                "src": [{"name": "Internal"}],
                "user": [{"name": "any"}],
                "dst": [{"name": "External"}],
                "srv": [{"name": "HTTP"}],
                "app": [{"name": "Web"}],
                "last_hit_time": "2024-03-15 10:00:00",
                "desc": "Allow web traffic"
            }
        ]
    }

def test_export_security_rules(mock_rules_response):
    """보안 규칙 추출 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        # Mock rules response
        m.get(
            'https://test_host/api/po/fw/4/rules',
            json=mock_rules_response
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        
        df = client.export_security_rules()
        
        assert not df.empty
        assert "Rule Name" in df.columns
        assert "Enable" in df.columns
        assert "Action" in df.columns
        assert len(df) == 1
        assert df.iloc[0]["Rule Name"] == "rule1"
        assert df.iloc[0]["Enable"] == "Y"
        assert df.iloc[0]["Action"] == "allow"

def test_empty_rules_response():
    """빈 규칙 응답 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        # Mock empty rules response
        m.get(
            'https://test_host/api/po/fw/4/rules',
            json={"result": []}
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        
        df = client.export_security_rules()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

def test_invalid_rules_response():
    """잘못된 규칙 응답 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        # Mock invalid rules response
        m.get(
            'https://test_host/api/po/fw/4/rules',
            status_code=500
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        
        with pytest.raises(Exception):
            client.export_security_rules() 