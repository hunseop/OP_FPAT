from threading import Thread, Lock
from queue import Queue
import time
import logging
from datetime import datetime, UTC
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
        """서버 재시작 시 pending 상태의 동기화 복구"""
        with app.app_context():
            try:
                pending_firewalls = Firewall.query.filter_by(sync_status='pending').all()
                for firewall in pending_firewalls:
                    firewall.sync_status = 'failed'
                    firewall.last_sync_error = '서버 재시작으로 인한 동기화 중단'
                db.session.commit()
            except Exception as e:
                logger.error(f"pending 상태 복구 중 오류 발생: {str(e)}")
    
    def _process_queue(self):
        """동기화 큐 처리"""
        while True:
            try:
                firewall_id = self._sync_queue.get()
                self._do_sync(firewall_id)
            except Exception as e:
                logger.error(f"큐 처리 중 오류 발생: {str(e)}")
            finally:
                self._sync_queue.task_done()
    
    def _update_progress(self, firewall_id: int, progress: int):
        """동기화 진행률 업데이트"""
        with self._lock:
            if firewall_id in self._active_syncs:
                self._active_syncs[firewall_id]['progress'] = progress
                logger.debug(f"방화벽 {firewall_id} 동기화 진행률: {progress}%")
    
    def _do_sync(self, firewall_id: int):
        """동기화 실행"""
        logger.info(f"방화벽 {firewall_id} 동기화 시작")
        try:
            with app.app_context():
                firewall = db.session.get(Firewall, firewall_id)
                if not firewall:
                    logger.error(f"방화벽 {firewall_id}를 찾을 수 없음")
                    return

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

                try:
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
                        },
                        'mock': {
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

                    # 데이터 수집
                    logger.info(f"방화벽 {firewall_id} 보안 규칙 수집 시작")
                    rules_df = collector.export_security_rules()
                    self._update_progress(firewall_id, 20)

                    logger.info(f"방화벽 {firewall_id} 네트워크 객체 수집 시작")
                    network_df = collector.export_network_objects()
                    self._update_progress(firewall_id, 40)

                    logger.info(f"방화벽 {firewall_id} 네트워크 그룹 수집 시작")
                    group_df = collector.export_network_group_objects()
                    self._update_progress(firewall_id, 60)

                    logger.info(f"방화벽 {firewall_id} 서비스 객체 수집 시작")
                    service_df = collector.export_service_objects()
                    self._update_progress(firewall_id, 80)

                    logger.info(f"방화벽 {firewall_id} 서비스 그룹 수집 시작")
                    service_group_df = collector.export_service_group_objects()
                    self._update_progress(firewall_id, 90)

                    # 데이터베이스 업데이트
                    try:
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
                                enabled=row.get('Enable') == 'Y' if isinstance(row.get('Enable'), str) else bool(row.get('Enable')),
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
                        firewall.last_sync = datetime.now(UTC)
                        firewall.last_sync_error = None
                        db.session.commit()

                        logger.info(f"방화벽 {firewall_id} 동기화 성공")
                        self._update_progress(firewall_id, 100)

                    except Exception as e:
                        db.session.rollback()
                        raise Exception(f"데이터베이스 업데이트 중 오류 발생: {str(e)}")

                except Exception as e:
                    raise Exception(f"데이터 수집 중 오류 발생: {str(e)}")

        except Exception as e:
            logger.error(f"방화벽 {firewall_id} 동기화 실패: {str(e)}")
            try:
                with app.app_context():
                    firewall = db.session.get(Firewall, firewall_id)
                    if firewall:
                        firewall.sync_status = 'failed'
                        firewall.last_sync_error = str(e)
                        db.session.commit()
            except Exception as inner_e:
                logger.error(f"상태 업데이트 중 오류 발생: {str(inner_e)}")

        finally:
            with self._lock:
                if firewall_id in self._active_syncs:
                    del self._active_syncs[firewall_id]
    
    def start_sync(self, firewall_id: int) -> tuple:
        """동기화 시작"""
        with self._lock:
            if firewall_id in self._active_syncs:
                return False, "이미 동기화가 진행 중입니다."

        with app.app_context():
            firewall = db.session.get(Firewall, firewall_id)
            if not firewall:
                return False, "방화벽을 찾을 수 없습니다."

            firewall.sync_status = 'pending'
            db.session.commit()

        self._sync_queue.put(firewall_id)
        return True, "동기화가 시작되었습니다."
    
    def get_status(self, firewall_id: int) -> dict:
        """동기화 상태 조회"""
        with self._lock:
            if firewall_id in self._active_syncs:
                return self._active_syncs[firewall_id]
            
        with app.app_context():
            firewall = db.session.get(Firewall, firewall_id)
            if firewall:
                return {
                    'status': firewall.sync_status,
                    'last_sync': firewall.last_sync.strftime('%Y-%m-%d %H:%M:%S') if firewall.last_sync else None,
                    'error': firewall.last_sync_error
                }
        return None

# 전역 SyncManager 인스턴스 생성
sync_manager = SyncManager() 