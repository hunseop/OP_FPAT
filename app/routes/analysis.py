from flask import Blueprint, render_template, request, jsonify, send_file, current_app
import os
import uuid
import json
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
import zipfile
from io import BytesIO

from app.modules.policy_manager.workflow import DeletionWorkflow
from app.modules.policy_manager.processor import PolicyProcessor
from app.modules.policy_manager.analyzer import PolicyAnalyzer

bp = Blueprint('analysis', __name__, url_prefix='/analysis')

# 워크플로우 저장소
workflows = {}

# 임시 파일 저장 경로
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# 워크플로우 디렉토리 생성
def create_workflow_dir(workflow_id):
    workflow_dir = os.path.join(TEMP_DIR, workflow_id)
    os.makedirs(workflow_dir, exist_ok=True)
    return workflow_dir

# 파일 확장자 확인
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls', 'csv'}

@bp.route('/')
def index():
    return render_template('analysis/index.html', title='분석')

@bp.route('/policy_manager')
def policy_manager():
    """정책 관리자 페이지를 렌더링합니다."""
    return render_template('analysis/policy_manager.html', title='정책 관리자')

# API 엔드포인트: 워크플로우 생성
@bp.route('/api/policy_manager/create_workflow', methods=['POST'])
def create_workflow():
    try:
        workflow_id = str(uuid.uuid4())
        workflow_dir = create_workflow_dir(workflow_id)
        
        # 워크플로우 객체 생성 및 저장
        workflows[workflow_id] = {
            'id': workflow_id,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'workflow_dir': workflow_dir,
            'files': {
                'intermediate': [],
                'reports': []
            }
        }
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id
        })
    except Exception as e:
        current_app.logger.error(f"워크플로우 생성 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 워크플로우 초기화
@bp.route('/api/policy_manager/initialize', methods=['POST'])
def initialize_workflow():
    try:
        workflow_id = request.form.get('workflow_id')
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        
        # 정책 파일 저장
        if 'policy_file' not in request.files:
            return jsonify({
                'success': False,
                'message': '정책 파일이 제공되지 않았습니다.'
            }), 400
        
        policy_file = request.files['policy_file']
        if policy_file.filename == '':
            return jsonify({
                'success': False,
                'message': '선택된 파일이 없습니다.'
            }), 400
        
        if not allowed_file(policy_file.filename):
            return jsonify({
                'success': False,
                'message': '지원되지 않는 파일 형식입니다.'
            }), 400
        
        # 파일 저장
        policy_filename = secure_filename(policy_file.filename)
        policy_path = os.path.join(workflow_dir, policy_filename)
        policy_file.save(policy_path)
        
        # 벤더 정보 저장
        vendor = request.form.get('vendor', 'unknown')
        
        # 워크플로우 상태 업데이트
        workflow['status'] = 'initialized'
        workflow['policy_path'] = policy_path
        workflow['vendor'] = vendor
        
        # 워크플로우 객체 생성
        workflow['workflow_obj'] = DeletionWorkflow(policy_path, vendor)
        
        # 중간 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['intermediate'].append({
            'id': file_id,
            'name': policy_filename,
            'path': policy_path,
            'type': 'policy'
        })
        
        return jsonify({
            'success': True,
            'message': '워크플로우가 초기화되었습니다.',
            'files': workflow['files']
        })
    except Exception as e:
        current_app.logger.error(f"워크플로우 초기화 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 신청 정보 처리
@bp.route('/api/policy_manager/process_request', methods=['POST'])
def process_request():
    try:
        workflow_id = request.form.get('workflow_id')
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        workflow_obj = workflow.get('workflow_obj')
        
        if not workflow_obj:
            return jsonify({
                'success': False,
                'message': '워크플로우가 초기화되지 않았습니다.'
            }), 400
        
        # 신청 정보 파일 처리 (선택 사항)
        request_file_path = None
        if 'request_file' in request.files and request.files['request_file'].filename != '':
            request_file = request.files['request_file']
            
            if not allowed_file(request_file.filename):
                return jsonify({
                    'success': False,
                    'message': '지원되지 않는 파일 형식입니다.'
                }), 400
            
            # 파일 저장
            request_filename = secure_filename(request_file.filename)
            request_file_path = os.path.join(workflow_dir, request_filename)
            request_file.save(request_file_path)
            
            # 중간 파일 목록 업데이트
            file_id = str(uuid.uuid4())
            workflow['files']['intermediate'].append({
                'id': file_id,
                'name': request_filename,
                'path': request_file_path,
                'type': 'request'
            })
        
        # 신청 정보 처리
        processor = PolicyProcessor(workflow_obj.policy_df)
        if request_file_path:
            request_df = pd.read_excel(request_file_path) if request_file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(request_file_path)
            processor.process_request_data(request_df)
        
        # 처리된 데이터 저장
        processed_path = os.path.join(workflow_dir, 'processed_policy.xlsx')
        processor.policy_df.to_excel(processed_path, index=False)
        
        # 워크플로우 객체 업데이트
        workflow_obj.policy_df = processor.policy_df
        workflow['status'] = 'request_processed'
        
        # 중간 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['intermediate'].append({
            'id': file_id,
            'name': 'processed_policy.xlsx',
            'path': processed_path,
            'type': 'processed'
        })
        
        return jsonify({
            'success': True,
            'message': '신청 정보가 처리되었습니다.',
            'files': workflow['files']
        })
    except Exception as e:
        current_app.logger.error(f"신청 정보 처리 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 사용 데이터 처리
@bp.route('/api/policy_manager/process_usage', methods=['POST'])
def process_usage():
    try:
        workflow_id = request.form.get('workflow_id')
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        workflow_obj = workflow.get('workflow_obj')
        
        if not workflow_obj:
            return jsonify({
                'success': False,
                'message': '워크플로우가 초기화되지 않았습니다.'
            }), 400
        
        # 사용 데이터 파일 처리 (선택 사항)
        usage_file_path = None
        if 'usage_file' in request.files and request.files['usage_file'].filename != '':
            usage_file = request.files['usage_file']
            
            if not allowed_file(usage_file.filename):
                return jsonify({
                    'success': False,
                    'message': '지원되지 않는 파일 형식입니다.'
                }), 400
            
            # 파일 저장
            usage_filename = secure_filename(usage_file.filename)
            usage_file_path = os.path.join(workflow_dir, usage_filename)
            usage_file.save(usage_file_path)
            
            # 중간 파일 목록 업데이트
            file_id = str(uuid.uuid4())
            workflow['files']['intermediate'].append({
                'id': file_id,
                'name': usage_filename,
                'path': usage_file_path,
                'type': 'usage'
            })
        
        # 사용 데이터 처리
        processor = PolicyProcessor(workflow_obj.policy_df)
        if usage_file_path:
            usage_df = pd.read_excel(usage_file_path) if usage_file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(usage_file_path)
            processor.process_usage_data(usage_df)
        else:
            # 사용 데이터가 없는 경우 기본 처리
            processor.process_usage_data(None)
        
        # 처리된 데이터 저장
        processed_path = os.path.join(workflow_dir, 'usage_processed_policy.xlsx')
        processor.policy_df.to_excel(processed_path, index=False)
        
        # 워크플로우 객체 업데이트
        workflow_obj.policy_df = processor.policy_df
        workflow['status'] = 'usage_processed'
        
        # 중간 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['intermediate'].append({
            'id': file_id,
            'name': 'usage_processed_policy.xlsx',
            'path': processed_path,
            'type': 'processed'
        })
        
        return jsonify({
            'success': True,
            'message': '사용 데이터가 처리되었습니다.',
            'files': workflow['files']
        })
    except Exception as e:
        current_app.logger.error(f"사용 데이터 처리 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 벤더별 처리
@bp.route('/api/policy_manager/process_vendor', methods=['POST'])
def process_vendor():
    try:
        data = request.json
        workflow_id = data.get('workflow_id')
        
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        workflow_obj = workflow.get('workflow_obj')
        
        if not workflow_obj:
            return jsonify({
                'success': False,
                'message': '워크플로우가 초기화되지 않았습니다.'
            }), 400
        
        # 벤더별 처리
        vendor = workflow.get('vendor', 'unknown')
        processor = PolicyProcessor(workflow_obj.policy_df)
        processor.process_vendor_data(vendor)
        
        # 처리된 데이터 저장
        processed_path = os.path.join(workflow_dir, 'vendor_processed_policy.xlsx')
        processor.policy_df.to_excel(processed_path, index=False)
        
        # 워크플로우 객체 업데이트
        workflow_obj.policy_df = processor.policy_df
        workflow['status'] = 'vendor_processed'
        
        # 중간 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['intermediate'].append({
            'id': file_id,
            'name': 'vendor_processed_policy.xlsx',
            'path': processed_path,
            'type': 'processed'
        })
        
        return jsonify({
            'success': True,
            'message': '벤더별 처리가 완료되었습니다.',
            'files': workflow['files']
        })
    except Exception as e:
        current_app.logger.error(f"벤더별 처리 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 중복 정책 분석
@bp.route('/api/policy_manager/analyze_duplicates', methods=['POST'])
def analyze_duplicates():
    try:
        data = request.json
        workflow_id = data.get('workflow_id')
        
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        workflow_obj = workflow.get('workflow_obj')
        
        if not workflow_obj:
            return jsonify({
                'success': False,
                'message': '워크플로우가 초기화되지 않았습니다.'
            }), 400
        
        # 중복 정책 분석
        analyzer = PolicyAnalyzer(workflow_obj.policy_df)
        analyzer.analyze_duplicates()
        
        # 처리된 데이터 저장
        analyzed_path = os.path.join(workflow_dir, 'duplicate_analyzed_policy.xlsx')
        analyzer.policy_df.to_excel(analyzed_path, index=False)
        
        # 워크플로우 객체 업데이트
        workflow_obj.policy_df = analyzer.policy_df
        workflow['status'] = 'duplicates_analyzed'
        
        # 중간 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['intermediate'].append({
            'id': file_id,
            'name': 'duplicate_analyzed_policy.xlsx',
            'path': analyzed_path,
            'type': 'processed'
        })
        
        # 중복 정책 목록 저장
        if hasattr(analyzer, 'duplicate_groups') and analyzer.duplicate_groups:
            duplicates_path = os.path.join(workflow_dir, 'duplicate_policies.xlsx')
            
            # 중복 그룹을 DataFrame으로 변환
            duplicate_rows = []
            for group_id, policies in analyzer.duplicate_groups.items():
                for policy in policies:
                    duplicate_rows.append({
                        'Group ID': group_id,
                        'Rule Name': policy.get('Rule Name', ''),
                        'Source': policy.get('Source', ''),
                        'Destination': policy.get('Destination', ''),
                        'Service': policy.get('Service', ''),
                        'Action': policy.get('Action', '')
                    })
            
            if duplicate_rows:
                duplicates_df = pd.DataFrame(duplicate_rows)
                duplicates_df.to_excel(duplicates_path, index=False)
                
                # 중간 파일 목록 업데이트
                file_id = str(uuid.uuid4())
                workflow['files']['intermediate'].append({
                    'id': file_id,
                    'name': 'duplicate_policies.xlsx',
                    'path': duplicates_path,
                    'type': 'report'
                })
        
        return jsonify({
            'success': True,
            'message': '중복 정책 분석이 완료되었습니다.',
            'files': workflow['files']
        })
    except Exception as e:
        current_app.logger.error(f"중복 정책 분석 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 보고서 생성
@bp.route('/api/policy_manager/generate_reports', methods=['POST'])
def generate_reports():
    try:
        data = request.json
        workflow_id = data.get('workflow_id')
        
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        workflow_obj = workflow.get('workflow_obj')
        
        if not workflow_obj:
            return jsonify({
                'success': False,
                'message': '워크플로우가 초기화되지 않았습니다.'
            }), 400
        
        # 보고서 디렉토리 생성
        reports_dir = os.path.join(workflow_dir, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # 최종 정책 파일 저장
        final_policy_path = os.path.join(reports_dir, 'final_policy.xlsx')
        workflow_obj.policy_df.to_excel(final_policy_path, index=False)
        
        # 보고서 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['reports'].append({
            'id': file_id,
            'name': 'final_policy.xlsx',
            'path': final_policy_path,
            'type': 'report'
        })
        
        # 미사용 정책 보고서 생성
        unused_policies = workflow_obj.policy_df[workflow_obj.policy_df['미사용여부'] == '미사용']
        if not unused_policies.empty:
            unused_path = os.path.join(reports_dir, 'unused_policies.xlsx')
            unused_policies.to_excel(unused_path, index=False)
            
            # 보고서 파일 목록 업데이트
            file_id = str(uuid.uuid4())
            workflow['files']['reports'].append({
                'id': file_id,
                'name': 'unused_policies.xlsx',
                'path': unused_path,
                'type': 'report'
            })
        
        # 중복 정책 보고서 생성
        duplicate_policies = workflow_obj.policy_df[workflow_obj.policy_df['중복여부'] == '중복']
        if not duplicate_policies.empty:
            duplicate_path = os.path.join(reports_dir, 'duplicate_policies_report.xlsx')
            duplicate_policies.to_excel(duplicate_path, index=False)
            
            # 보고서 파일 목록 업데이트
            file_id = str(uuid.uuid4())
            workflow['files']['reports'].append({
                'id': file_id,
                'name': 'duplicate_policies_report.xlsx',
                'path': duplicate_path,
                'type': 'report'
            })
        
        # 요약 보고서 생성
        summary = {
            '총 정책 수': len(workflow_obj.policy_df),
            '미사용 정책 수': len(unused_policies) if '미사용여부' in workflow_obj.policy_df.columns else 0,
            '중복 정책 수': len(duplicate_policies) if '중복여부' in workflow_obj.policy_df.columns else 0,
            '분석 일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '벤더': workflow.get('vendor', 'unknown')
        }
        
        summary_path = os.path.join(reports_dir, 'summary_report.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
        
        # 보고서 파일 목록 업데이트
        file_id = str(uuid.uuid4())
        workflow['files']['reports'].append({
            'id': file_id,
            'name': 'summary_report.json',
            'path': summary_path,
            'type': 'report'
        })
        
        # 워크플로우 상태 업데이트
        workflow['status'] = 'reports_generated'
        
        return jsonify({
            'success': True,
            'message': '보고서가 생성되었습니다.',
            'files': workflow['files'],
            'summary': summary
        })
    except Exception as e:
        current_app.logger.error(f"보고서 생성 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 모든 파일 다운로드
@bp.route('/api/policy_manager/download_all', methods=['POST'])
def download_all():
    try:
        data = request.json
        workflow_id = data.get('workflow_id')
        
        if not workflow_id or workflow_id not in workflows:
            return jsonify({
                'success': False,
                'message': '유효하지 않은 워크플로우 ID입니다.'
            }), 400
        
        workflow = workflows[workflow_id]
        workflow_dir = workflow['workflow_dir']
        
        # ZIP 파일 생성
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 중간 파일 추가
            for file_info in workflow['files']['intermediate']:
                file_path = file_info['path']
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.join('intermediate', os.path.basename(file_path)))
            
            # 보고서 파일 추가
            for file_info in workflow['files']['reports']:
                file_path = file_info['path']
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.join('reports', os.path.basename(file_path)))
        
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'policy_analysis_{workflow_id}.zip'
        )
    except Exception as e:
        current_app.logger.error(f"파일 다운로드 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API 엔드포인트: 단일 파일 다운로드
@bp.route('/api/policy_manager/download_file/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        # 모든 워크플로우에서 파일 검색
        for workflow_id, workflow in workflows.items():
            # 중간 파일 검색
            for file_info in workflow['files']['intermediate']:
                if file_info['id'] == file_id:
                    file_path = file_info['path']
                    if os.path.exists(file_path):
                        return send_file(
                            file_path,
                            as_attachment=True,
                            download_name=os.path.basename(file_path)
                        )
            
            # 보고서 파일 검색
            for file_info in workflow['files']['reports']:
                if file_info['id'] == file_id:
                    file_path = file_info['path']
                    if os.path.exists(file_path):
                        return send_file(
                            file_path,
                            as_attachment=True,
                            download_name=os.path.basename(file_path)
                        )
        
        return jsonify({
            'success': False,
            'message': '파일을 찾을 수 없습니다.'
        }), 404
    except Exception as e:
        current_app.logger.error(f"파일 다운로드 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 주기적인 임시 파일 정리 (실제 구현에서는 스케줄러 사용)
def cleanup_temp_files():
    try:
        # 24시간 이상 지난 워크플로우 디렉토리 삭제
        current_time = datetime.now()
        for workflow_id, workflow in list(workflows.items()):
            created_at = datetime.fromisoformat(workflow['created_at'])
            if (current_time - created_at).total_seconds() > 86400:  # 24시간
                workflow_dir = workflow['workflow_dir']
                if os.path.exists(workflow_dir):
                    shutil.rmtree(workflow_dir)
                del workflows[workflow_id]
    except Exception as e:
        current_app.logger.error(f"임시 파일 정리 오류: {str(e)}") 