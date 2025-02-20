from flask import render_template, request, jsonify, redirect, url_for, send_file
from app import app, db
from app.models import Firewall, SecurityRule, NetworkObject, NetworkGroup, ServiceObject, ServiceGroup
from app.utils.validators import validate_firewall_data
from datetime import datetime
import os
import pandas as pd
from werkzeug.utils import secure_filename
from threading import Thread, Lock
from queue import Queue
import time
import logging
from firewall.collector_factory import FirewallCollectorFactory

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class SyncManager:
    def __init__(self):
        self._sync_queue = Queue()
        self._active_syncs = {}
        self._lock = Lock()
        self._worker = Thread(target=self._process_queue, daemon=True)
        self._worker.start()
        self._recover_pending_syncs()
    
    def _recover_pending_syncs(self):
        """서버 재시작 시 'syncing' 상태의 방화벽을 'failed'로 변경"""
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
        """Thread-safe한 진행률 업데이트"""
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
                
                # 상태 초기화
                with self._lock:
                    self._active_syncs[firewall_id] = {
                        'status': 'syncing',
                        'progress': 0,
                        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                
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
            logger.error(f"방화벽 {firewall_id} 동기화 실패: {str(e)}")
            with app.app_context():
                firewall.sync_status = 'failed'
                firewall.last_sync_error = str(e)
                db.session.commit()
            with self._lock:
                if firewall_id in self._active_syncs:
                    self._active_syncs[firewall_id]['error'] = str(e)
        
        finally:
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # 방화벽 개수
    firewall_count = Firewall.query.count()
    
    # 전체 정책 수
    policy_count = SecurityRule.query.count()
    
    # 활성화된 정책 수
    active_policy_count = SecurityRule.query.filter_by(enabled=True).count()
    
    # 전체 객체 수 (네트워크 객체 + 네트워크 그룹 + 서비스 객체 + 서비스 그룹)
    object_count = (
        NetworkObject.query.count() +
        NetworkGroup.query.count() +
        ServiceObject.query.count() +
        ServiceGroup.query.count()
    )
    
    return render_template('index.html', 
                         title='FPAT',
                         firewall_count=firewall_count,
                         policy_count=policy_count,
                         active_policy_count=active_policy_count,
                         inactive_policy_count=policy_count - active_policy_count,
                         object_count=object_count)

@app.route('/policy')
def policy():
    return render_template('policy/index.html', title='정책 관리')

@app.route('/analysis')
def analysis():
    return render_template('analysis/index.html', title='정책 분석')

@app.route('/firewall')
def firewall():
    firewalls = Firewall.query.all()
    return render_template('firewall/index.html', title='방화벽 관리', firewalls=firewalls)

@app.route('/firewall/add', methods=['POST'])
def add_firewall():
    try:
        data = {
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'ip_address': request.form.get('ip'),
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        # 입력값 검증
        is_valid, errors = validate_firewall_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '입력값 검증 실패',
                'details': errors
            })

        # 중복 검사
        existing_firewall = Firewall.query.filter(
            (Firewall.name == data['name']) | 
            (Firewall.ip_address == data['ip_address'])
        ).first()
        
        if existing_firewall:
            return jsonify({
                'success': False,
                'error': '중복된 방화벽',
                'details': ['동일한 이름 또는 IP 주소를 가진 방화벽이 이미 존재합니다.']
            })

        new_firewall = Firewall(
            name=data['name'],
            type=data['type'].lower(),
            ip_address=data['ip_address'],
            username=data['username'],
            password=data['password']
        )
        db.session.add(new_firewall)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/firewall/delete/<int:id>', methods=['POST'])
def delete_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        db.session.delete(firewall)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/firewall/sync/<int:id>', methods=['POST'])
def sync_firewall(id):
    try:
        firewall = Firewall.query.get_or_404(id)
        
        # 이미 동기화 중인 경우
        if firewall.sync_status == 'syncing':
            return jsonify({
                'success': False,
                'error': '이미 동기화가 진행 중입니다.'
            })

        # 동기화 상태 업데이트
        firewall.sync_status = 'syncing'
        db.session.commit()

        # 동기화 시작
        success, message = sync_manager.start_sync(id)
        
        return jsonify({
            'success': success,
            'message': message
        })

    except Exception as e:
        # 오류 발생 시 sync_status를 'failed'로 업데이트
        firewall.sync_status = 'failed'
        firewall.last_sync_error = str(e)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'error': f'동기화 시작 중 오류가 발생했습니다: {str(e)}'
        })

@app.route('/firewall/sync/status/<int:id>')
def sync_status(id):
    status = sync_manager.get_status(id)
    if status:
        return jsonify(status)
    
    # 동기화가 진행 중이 아닌 경우, DB에서 상태 확인
    firewall = Firewall.query.get_or_404(id)
    return jsonify({
        'status': firewall.sync_status,
        'last_sync': firewall.last_sync.strftime('%Y-%m-%d %H:%M:%S') if firewall.last_sync else None,
        'error': firewall.last_sync_error
    })

@app.route('/firewall/template')
def download_template():
    """방화벽 등록용 엑셀 템플릿 다운로드"""
    template_path = os.path.join(app.root_path, 'static', 'templates', 'firewall_template.xlsx')
    return send_file(template_path, as_attachment=True)

@app.route('/firewall/upload', methods=['POST'])
def upload_firewalls():
    """엑셀 파일을 통한 방화벽 일괄 등록"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '파일이 없습니다.'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '선택된 파일이 없습니다.'})
    
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            required_columns = ['name', 'type', 'ip_address', 'username', 'password']
            
            if not all(col in df.columns for col in required_columns):
                return jsonify({'success': False, 'error': '필수 컬럼이 누락되었습니다.'})
            
            errors = []
            success_count = 0
            
            for index, row in df.iterrows():
                data = {
                    'name': str(row['name']).strip(),
                    'type': str(row['type']).strip(),
                    'ip_address': str(row['ip_address']).strip(),
                    'username': str(row['username']).strip(),
                    'password': str(row['password']).strip()
                }
                
                # 입력값 검증
                is_valid, validation_errors = validate_firewall_data(data)
                if not is_valid:
                    errors.append(f"행 {index + 2}: {', '.join(validation_errors)}")
                    continue
                
                # 중복 검사
                existing_firewall = Firewall.query.filter(
                    (Firewall.name == data['name']) | 
                    (Firewall.ip_address == data['ip_address'])
                ).first()
                
                if existing_firewall:
                    errors.append(f"행 {index + 2}: 동일한 이름 또는 IP 주소를 가진 방화벽이 이미 존재합니다.")
                    continue
                
                firewall = Firewall(
                    name=data['name'],
                    type=data['type'].lower(),
                    ip_address=data['ip_address'],
                    username=data['username'],
                    password=data['password']
                )
                db.session.add(firewall)
                success_count += 1
            
            if success_count > 0:
                db.session.commit()
            
            result = {
                'success': True,
                'message': f'{success_count}개의 방화벽이 등록되었습니다.'
            }
            if errors:
                result['warnings'] = errors
            
            return jsonify(result)
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': '허용되지 않는 파일 형식입니다.'})

@app.route('/firewall/edit/<int:id>', methods=['GET', 'POST'])
def edit_firewall(id):
    firewall = Firewall.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify({
            'name': firewall.name,
            'type': firewall.type,
            'ip_address': firewall.ip_address,
            'username': firewall.username,
            'password': firewall.password
        })
    
    try:
        data = {
            'name': request.form.get('name'),
            'type': request.form.get('type'),
            'ip_address': request.form.get('ip'),
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        # 입력값 검증 (수정 모드)
        is_valid, errors = validate_firewall_data(data, is_edit=True)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': '입력값 검증 실패',
                'details': errors
            })

        # 중복 검사 (현재 편집 중인 방화벽 제외)
        existing_firewall = Firewall.query.filter(
            Firewall.id != id,
            (Firewall.name == data['name']) | 
            (Firewall.ip_address == data['ip_address'])
        ).first()
        
        if existing_firewall:
            return jsonify({
                'success': False,
                'error': '중복된 방화벽',
                'details': ['동일한 이름 또는 IP 주소를 가진 방화벽이 이미 존재합니다.']
            })

        # 데이터 업데이트
        firewall.name = data['name']
        firewall.type = data['type'].lower()
        firewall.ip_address = data['ip_address']
        firewall.username = data['username']
        if data['password']:  # 비밀번호가 입력된 경우에만 업데이트
            firewall.password = data['password']
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})