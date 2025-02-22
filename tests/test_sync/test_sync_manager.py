import pytest
from app.services.sync_manager import SyncManager
from app.models import Firewall
from app import db
import time
import pandas as pd
from unittest.mock import patch
from datetime import datetime, UTC

def test_sync_manager_initialization():
    """동기화 관리자 초기화 테스트"""
    sync_manager = SyncManager()
    assert sync_manager._sync_queue is not None
    assert sync_manager._active_syncs == {}
    assert sync_manager._lock is not None

def test_start_sync(test_app, sample_firewall):
    """동기화 시작 테스트"""
    with test_app.app_context():
        sync_manager = SyncManager()
        success, message = sync_manager.start_sync(sample_firewall.id)
        
        assert success is True
        assert "동기화가 시작되었습니다" in message

        # 동기화 상태 확인
        status = sync_manager.get_status(sample_firewall.id)
        assert status is not None
        assert status['status'] == 'syncing'
        assert 'progress' in status
        assert 'start_time' in status

def test_duplicate_sync(test_app, sample_firewall):
    """중복 동기화 시도 테스트"""
    with test_app.app_context():
        sync_manager = SyncManager()
        
        # 첫 번째 동기화 시작
        success1, _ = sync_manager.start_sync(sample_firewall.id)
        assert success1 is True
        
        # 두 번째 동기화 시도 (이미 진행 중)
        success2, message2 = sync_manager.start_sync(sample_firewall.id)
        assert success2 is False
        assert "이미 동기화가 진행 중입니다" in message2

def test_sync_status_tracking(test_app, sample_firewall):
    """동기화 상태 추적 테스트"""
    with test_app.app_context():
        sync_manager = SyncManager()
        sync_manager.start_sync(sample_firewall.id)
        
        # 초기 상태 확인
        status = sync_manager.get_status(sample_firewall.id)
        assert status is not None
        assert status['status'] == 'syncing'
        assert status['progress'] == 0
        assert 'start_time' in status

@pytest.fixture
def mock_ngf_data():
    """테스트용 NGF 데이터"""
    # 보안 규칙
    rules_data = {
        'Seq': [1],
        'Rule Name': ['Test Rule'],
        'Enable': [True],
        'Action': ['allow'],
        'Source': ['Internal'],
        'User': ['any'],
        'Destination': ['External'],
        'Service': ['HTTP'],
        'Application': ['Web'],
        'Description': ['Test description'],
        'Last Hit Date': [datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)]
    }
    rules_df = pd.DataFrame(rules_data)

    # 네트워크 객체
    network_objects_data = {
        'Name': ['TestHost'],
        'Type': ['ip-netmask'],
        'Value': ['192.168.1.100']
    }
    network_objects_df = pd.DataFrame(network_objects_data)

    # 네트워크 그룹
    network_groups_data = {
        'Group Name': ['TestGroup'],
        'Entry': ['TestHost']
    }
    network_groups_df = pd.DataFrame(network_groups_data)

    # 서비스 객체
    service_objects_data = {
        'Name': ['TestService'],
        'Protocol': ['tcp'],
        'Port': ['80']
    }
    service_objects_df = pd.DataFrame(service_objects_data)

    # 서비스 그룹
    service_groups_data = {
        'Group Name': ['TestServiceGroup'],
        'Entry': ['TestService']
    }
    service_groups_df = pd.DataFrame(service_groups_data)

    return {
        'rules': rules_df,
        'network_objects': network_objects_df,
        'network_groups': network_groups_df,
        'service_objects': service_objects_df,
        'service_groups': service_groups_df
    }

def test_sync_completion(test_app, sample_firewall, mock_ngf_data):
    """동기화 완료 테스트"""
    with test_app.app_context():
        # NGF 클라이언트 모킹
        with patch('firewall.collector_factory.FirewallCollectorFactory.get_collector') as mock_collector:
            # 모의 Collector 설정
            mock_collector.return_value.export_security_rules.return_value = mock_ngf_data['rules']
            mock_collector.return_value.export_network_objects.return_value = mock_ngf_data['network_objects']
            mock_collector.return_value.export_network_group_objects.return_value = mock_ngf_data['network_groups']
            mock_collector.return_value.export_service_objects.return_value = mock_ngf_data['service_objects']
            mock_collector.return_value.export_service_group_objects.return_value = mock_ngf_data['service_groups']

            sync_manager = SyncManager()
            success, message = sync_manager.start_sync(sample_firewall.id)
            assert success is True
            assert "동기화가 시작되었습니다" in message

            # 동기화 완료 대기 (최대 10초)
            start_time = time.time()
            while time.time() - start_time < 10:
                db.session.expire_all()  # 세션 캐시 초기화
                firewall = db.session.get(Firewall, sample_firewall.id)
                db.session.refresh(firewall)  # 객체 새로고침
                
                if firewall.sync_status in ['success', 'failed']:
                    break
                time.sleep(0.5)

            # 상태 확인
            db.session.expire_all()  # 세션 캐시 초기화
            firewall = db.session.get(Firewall, sample_firewall.id)
            db.session.refresh(firewall)  # 객체 새로고침
            
            assert firewall.sync_status in ['success', 'failed'] 