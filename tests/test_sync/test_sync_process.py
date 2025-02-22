import pytest
from app.services.sync_manager import SyncManager
from app.models import (
    Firewall, SecurityRule, NetworkObject,
    NetworkGroup, ServiceObject, ServiceGroup
)
from app import db
import pandas as pd
from datetime import datetime, UTC

@pytest.fixture
def mock_sync_data():
    """테스트용 동기화 데이터"""
    # 보안 규칙
    rules_data = {
        'Seq': [1],
        'Rule Name': ['Test Rule'],
        'Enable': ['Y'],
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

def test_sync_process_data_insertion(test_app, sample_firewall, mock_sync_data):
    """동기화 프로세스 데이터 삽입 테스트"""
    with test_app.app_context():
        # 기존 데이터 삭제
        SecurityRule.query.filter_by(firewall_id=sample_firewall.id).delete()
        NetworkObject.query.filter_by(firewall_id=sample_firewall.id).delete()
        NetworkGroup.query.filter_by(firewall_id=sample_firewall.id).delete()
        ServiceObject.query.filter_by(firewall_id=sample_firewall.id).delete()
        ServiceGroup.query.filter_by(firewall_id=sample_firewall.id).delete()
        db.session.commit()
        
        # 새 데이터 삽입
        # 보안 규칙
        for _, row in mock_sync_data['rules'].iterrows():
            rule = SecurityRule(
                firewall_id=sample_firewall.id,
                seq=row['Seq'],
                name=row['Rule Name'],
                enabled=row['Enable'] == 'Y',
                action=row['Action'],
                source=row['Source'],
                user=row['User'],
                destination=row['Destination'],
                service=row['Service'],
                application=row['Application'],
                description=row['Description'],
                last_hit=row['Last Hit Date']
            )
            db.session.add(rule)
        
        # 네트워크 객체
        for _, row in mock_sync_data['network_objects'].iterrows():
            obj = NetworkObject(
                firewall_id=sample_firewall.id,
                name=row['Name'],
                type=row['Type'],
                value=row['Value']
            )
            db.session.add(obj)
        
        # 네트워크 그룹
        for _, row in mock_sync_data['network_groups'].iterrows():
            group = NetworkGroup(
                firewall_id=sample_firewall.id,
                name=row['Group Name'],
                members=row['Entry']
            )
            db.session.add(group)
        
        # 서비스 객체
        for _, row in mock_sync_data['service_objects'].iterrows():
            obj = ServiceObject(
                firewall_id=sample_firewall.id,
                name=row['Name'],
                protocol=row['Protocol'],
                port=row['Port']
            )
            db.session.add(obj)
        
        # 서비스 그룹
        for _, row in mock_sync_data['service_groups'].iterrows():
            group = ServiceGroup(
                firewall_id=sample_firewall.id,
                name=row['Group Name'],
                members=row['Entry']
            )
            db.session.add(group)
        
        db.session.commit()
        
        # 데이터 검증
        assert SecurityRule.query.filter_by(firewall_id=sample_firewall.id).count() == len(mock_sync_data['rules'])
        assert NetworkObject.query.filter_by(firewall_id=sample_firewall.id).count() == len(mock_sync_data['network_objects'])
        assert NetworkGroup.query.filter_by(firewall_id=sample_firewall.id).count() == len(mock_sync_data['network_groups'])
        assert ServiceObject.query.filter_by(firewall_id=sample_firewall.id).count() == len(mock_sync_data['service_objects'])
        assert ServiceGroup.query.filter_by(firewall_id=sample_firewall.id).count() == len(mock_sync_data['service_groups'])

def test_sync_process_data_update(test_app, sample_firewall, mock_sync_data):
    """동기화 프로세스 데이터 업데이트 테스트"""
    with test_app.app_context():
        # 첫 번째 동기화
        test_sync_process_data_insertion(test_app, sample_firewall, mock_sync_data)
        
        # 데이터 수정
        mock_sync_data['rules'].at[0, 'Description'] = 'Updated description'
        mock_sync_data['network_objects'].at[0, 'Value'] = '192.168.1.200'
        mock_sync_data['service_objects'].at[0, 'Port'] = '443'
        
        # 두 번째 동기화
        test_sync_process_data_insertion(test_app, sample_firewall, mock_sync_data)
        
        # 업데이트 검증
        rule = SecurityRule.query.filter_by(firewall_id=sample_firewall.id).first()
        assert rule.description == 'Updated description'
        
        net_obj = NetworkObject.query.filter_by(firewall_id=sample_firewall.id).first()
        assert net_obj.value == '192.168.1.200'
        
        svc_obj = ServiceObject.query.filter_by(firewall_id=sample_firewall.id).first()
        assert svc_obj.port == '443'

def test_sync_process_error_handling(test_app, sample_firewall):
    """동기화 프로세스 에러 처리 테스트"""
    with test_app.app_context():
        # 잘못된 데이터로 동기화 시도
        invalid_rule = SecurityRule(
            firewall_id=sample_firewall.id,
            seq=None,  # 필수 필드 누락
            name=None  # 필수 필드 누락
        )
        db.session.add(invalid_rule)
        
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()
        
        # 방화벽 상태 확인
        firewall = db.session.get(Firewall, sample_firewall.id)
        assert firewall.sync_status != 'success' 