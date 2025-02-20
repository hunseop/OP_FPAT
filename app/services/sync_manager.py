from threading import Thread, Lock
from queue import Queue
import time
import logging
from datetime import datetime
import pandas as pd
from app import app, db
from app.models import (
    Firewall, SecurityRule, NetworkObject, 
    NetworkGroup, ServiceObject, ServiceGroup
)
from firewall.collector_factory import FirewallCollectorFactory

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self):
        self._sync_queue = Queue()
        self._active_syncs = {}
        self._lock = Lock()
        self._worker = Thread(target=self._process_queue, daemon=True)
        self._worker.start()
        self._recover_pending_syncs()
    
    def _recover_pending_syncs(self):
        try:
            with app.app_context():
                pending_firewalls = Firewall.query.filter_by(sync_status='syncing').all()
                for firewall in pending_firewalls:
                    firewall.sync_status = 'failed'
                    firewall.last_sync_error = '서버 재시작으로 인한 동기화 중단'
                db.session.commit()
                if pending_firewalls:
                    logger.info(f"{len(pending_firewalls)}개의 중단된 동기화 작업 복구 완료")
        except Exception as e:
            logger.error(f"중단된 동기화 작업 복구 중 오류 발생: {str(e)}")
    
    def _process_queue(self):
        while True:
            if not self._sync_queue.empty():
                firewall_id = self._sync_queue.get()
                self._do_sync(firewall_id)
            time.sleep(0.1)
    
    def _update_progress(self, firewall_id: int, progress: int):
        with self._lock:
            if firewall_id in self._active_syncs:
                self._active_syncs[firewall_id]['progress'] = progress
                logger.debug(f"방화벽 {firewall_id} 동기화 진행률: {progress}%")
    
    def _do_sync(self, firewall_id: int):
        logger.info(f"방화벽 {firewall_id} 동기화 시작")
        try:
            with app.app_context():
                firewall = Firewall.query.get(firewall_id)
                if not firewall:
                    logger.error(f"방화벽 {firewall_id}를 찾을 수 없음")
                    return

                try:
                    # 상태 초기화
                    with self._lock:
                        self._active_syncs[firewall_id] = {
                            'status': 'syncing',
                            'progress': 0,
                            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                    # 방화벽 상태 업데이트
                    firewall.sync_status = 'syncing'
                    db.session.commit()

                    # Collector 생성
                    collector_params = {
                        'ngf': {
                            'hostname': firewall.ip_address,
                            'ext_clnt_id': firewall.username,
                            'ext_clnt_secret': firewall.password
                        },
                        'mf2': {
                            'device_ip': firewall.ip_address,
                            'username': firewall.username,
                            'password': firewall.password
                        },
                        'paloalto': {
                            'hostname': firewall.ip_address,
                            'username': firewall.username,
                            'password': firewall.password
                        }
                    }

                    if firewall.type not in collector_params:
                        raise ValueError(f"지원하지 않는 방화벽 타입입니다: {firewall.type}")

                    collector = FirewallCollectorFactory.get_collector(
                        firewall.type,
                        **collector_params[firewall.type]
                    )
                    self._update_progress(firewall_id, 20)

                    # 데이터 수집
                    try:
                        rules_df = collector.export_security_rules()
                        self._update_progress(firewall_id, 40)
                        
                        network_df = collector.export_network_objects()
                        self._update_progress(firewall_id, 60)
                        
                        group_df = collector.export_network_group_objects()
                        service_df = collector.export_service_objects()
                        service_group_df = collector.export_service_group_objects()
                        self._update_progress(firewall_id, 80)

                        # 데이터가 정상적으로 수집된 경우에만 기존 데이터 삭제 및 새 데이터 추가
                        if all(not df.empty for df in [rules_df, network_df, group_df, service_df, service_group_df]):
                            try:
                                # 트랜잭션 시작
                                db.session.begin_nested()

                                # 기존 데이터 삭제
                                SecurityRule.query.filter_by(firewall_id=firewall.id).delete()
                                NetworkObject.query.filter_by(firewall_id=firewall.id).delete()
                                NetworkGroup.query.filter_by(firewall_id=firewall.id).delete()
                                ServiceObject.query.filter_by(firewall_id=firewall.id).delete()
                                ServiceGroup.query.filter_by(firewall_id=firewall.id).delete()

                                # 새 데이터 추가
                                for _, row in rules_df.iterrows():
                                    rule = SecurityRule(
                                        firewall_id=firewall.id,
                                        seq=row.get('Seq'),
                                        name=row.get('Rule Name'),
                                        enabled=row.get('Enable'),
                                        action=row.get('Action'),
                                        source=row.get('Source'),
                                        user=row.get('User'),
                                        destination=row.get('Destination'),
                                        service=row.get('Service'),
                                        application=row.get('Application'),
                                        description=row.get('Description'),
                                        last_hit=row.get('Last Hit Date') if pd.notna(row.get('Last Hit Date')) else None
                                    )
                                    db.session.add(rule)

                                for _, row in network_df.iterrows():
                                    obj = NetworkObject(
                                        firewall_id=firewall.id,
                                        name=row['Name'],
                                        type=row.get('Type'),
                                        value=row['Value']
                                    )
                                    db.session.add(obj)
                                
                                for _, row in group_df.iterrows():
                                    group = NetworkGroup(
                                        firewall_id=firewall.id,
                                        name=row['Group Name'],
                                        members=row.get('Entry')
                                    )
                                    db.session.add(group)
                                
                                for _, row in service_df.iterrows():
                                    obj = ServiceObject(
                                        firewall_id=firewall.id,
                                        name=row['Name'],
                                        protocol=row.get('Protocol'),
                                        port=row.get('Port')
                                    )
                                    db.session.add(obj)
                                
                                for _, row in service_group_df.iterrows():
                                    group = ServiceGroup(
                                        firewall_id=firewall.id,
                                        name=row['Group Name'],
                                        members=row.get('Entry')
                                    )
                                    db.session.add(group)

                                # 동기화 상태 업데이트
                                firewall.sync_status = 'success'
                                firewall.last_sync = datetime.utcnow()
                                firewall.last_sync_error = None
                                
                                # 트랜잭션 커밋
                                db.session.commit()
                                logger.info(f"방화벽 {firewall_id} 동기화 성공")
                                self._update_progress(firewall_id, 100)

                            except Exception as e:
                                db.session.rollback()
                                raise Exception(f"데이터베이스 업데이트 중 오류 발생: {str(e)}")
                        else:
                            raise Exception("일부 데이터를 수집할 수 없습니다.")

                    except Exception as e:
                        raise Exception(f"데이터 수집 중 오류 발생: {str(e)}")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"방화벽 {firewall_id} 동기화 실패: {error_msg}")
                    
                    # 방화벽 상태 업데이트
                    firewall.sync_status = 'failed'
                    firewall.last_sync_error = error_msg
                    db.session.commit()
                    
                    # active_syncs에서 제거
                    with self._lock:
                        if firewall_id in self._active_syncs:
                            del self._active_syncs[firewall_id]
                    
                    return  # 실패 시 즉시 반환

        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
        finally:
            # 마지막 안전장치: active_syncs에서 항상 제거
            with self._lock:
                if firewall_id in self._active_syncs:
                    del self._active_syncs[firewall_id]
    
    def start_sync(self, firewall_id: int) -> tuple:
        """단일 방화벽 동기화 시작"""
        with self._lock:
            if firewall_id in self._active_syncs:
                return False, "이미 동기화가 진행 중입니다."
        self._sync_queue.put(firewall_id)
        return True, "동기화가 시작되었습니다."
    
    def get_status(self, firewall_id: int) -> dict:
        """동기화 상태 조회"""
        with self._lock:
            return self._active_syncs.get(firewall_id)

# 전역 SyncManager 인스턴스 생성
sync_manager = SyncManager() 