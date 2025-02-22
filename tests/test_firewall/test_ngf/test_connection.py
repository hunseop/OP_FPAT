import pytest
from firewall.ngf.ngf_module import NGFClient
import requests_mock
import requests

def test_ngf_connection():
    """NGF 연결 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login response
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        token = client.login()
        assert token == 'test_token'

def test_connection_timeout():
    """타임아웃 상황 테스트"""
    with requests_mock.Mocker() as m:
        m.post(
            'https://invalid_host/api/au/external/login',
            exc=requests.exceptions.ConnectTimeout
        )
        
        client = NGFClient(
            hostname="invalid_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret",
            timeout=1
        )
        assert client.login() is None

def test_invalid_credentials():
    """잘못된 인증 정보 테스트"""
    with requests_mock.Mocker() as m:
        m.post(
            'https://test_host/api/au/external/login',
            status_code=401
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="invalid_id",
            ext_clnt_secret="invalid_secret"
        )
        assert client.login() is None

def test_successful_logout():
    """로그아웃 성공 테스트"""
    with requests_mock.Mocker() as m:
        # Mock login and logout responses
        m.post(
            'https://test_host/api/au/external/login',
            json={'result': {'api_token': 'test_token'}}
        )
        m.delete(
            'https://test_host/api/au/external/logout',
            status_code=200
        )
        
        client = NGFClient(
            hostname="test_host",
            ext_clnt_id="test_id",
            ext_clnt_secret="test_secret"
        )
        client.login()
        assert client.logout() is True 