import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from .analyzer import PolicyAnalyzer
import re
from typing import Optional, Dict, Any

from .processor import PolicyProcessor
from .reporters.policy_reporter import PolicyReporter
from .utils.file_manager import FileManager
from .utils.data_validator import DataValidator

class DeletionWorkflow:
    """정책 삭제 워크플로우를 관리하는 클래스"""
    
    # 컬럼 설정
    COLUMNS = [
        'Rule Name', 'Enable', 'Action', 'Source', 'User', 'Destination',
        'Service', 'Application', 'Security Profile', 'Category', 'Description',
        'Request Type', 'Request ID', 'Ruleset ID', 'MIS ID', 'Request User',
        'Start Date', 'End Date'
    ]

    COLUMNS_NO_HISTORY = [
        'Rule Name', 'Enable', 'Action', 'Source', 'User', 'Destination',
        'Service', 'Application', 'Security Profile', 'Category', 'Description'
    ]

    DATE_COLUMNS = ['Start Date', 'End Date']

    TRANSLATED_COLUMNS = {
        'REQUEST_ID': 'GSAMS 신청번호',
        'REQUEST_START_DATE': '시작일',
        'REQUEST_END_DATE': '종료일',
        'TITLE': '제목',
        'REQUESTER_ID': '신청자 ID',
        'REQUESTER_EMAIL': '신청자 이메일',
        'REQUESTER_NAME': '신청자명',
        'REQUEST_DEPT': '신청자 부서',
        'WRITE_PERSON_ID': '기안자 ID',
        'WRITE_PERSON_EMAIL': '기안자 이메일',
        'WRITE_PERSON_NAME': '기안자명',
        'WRITE_PERSON_DEPT': '기안자 부서',
        'APPROVAL_PERSON_ID': '결재자 ID',
        'APPROVAL_PERSON_EMAIL': '결재자 이메일',
        'APPROVAL_PERSON_NAME': '결재자명',
        'APPROVAL_PERSON_DEPT': '결재자 부서',
    }

    # 예외 신청번호 리스트
    EXCEPTION_REQUEST_IDS = ['1', '2', '3']

    def __init__(self, output_dir: str = None):
        """
        Args:
            output_dir: 결과 파일을 저장할 디렉토리 경로
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir or Path.cwd() / 'output'
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        self.processor = PolicyProcessor()
        self.analyzer = PolicyAnalyzer()
        self.reporter = PolicyReporter(self.output_dir)
        self.file_manager = FileManager(self.output_dir)
        self.validator = DataValidator()
        
        self.policies_df = None
        self.vendor = None
        self.duplicate_analysis_file = None
        
        # 워크플로우 상태 관리
        self.progress = {
            'initialized': False,
            'request_processed': False,
            'usage_processed': False,
            'vendor_processed': False,
            'duplicates_analyzed': False,
            'reports_generated': False
        }
        
        # 상세 상태 및 오류 정보
        self.status = {
            'initialized': {'status': 'pending', 'message': '', 'timestamp': None},
            'request_processed': {'status': 'pending', 'message': '', 'timestamp': None},
            'usage_processed': {'status': 'pending', 'message': '', 'timestamp': None},
            'vendor_processed': {'status': 'pending', 'message': '', 'timestamp': None},
            'duplicates_analyzed': {'status': 'pending', 'message': '', 'timestamp': None},
            'reports_generated': {'status': 'pending', 'message': '', 'timestamp': None}
        }
        
        # 중간 결과물 저장 경로
        self.intermediate_files = {
            'initialized': None,
            'request_processed': None,
            'usage_processed': None,
            'vendor_processed': None,
            'duplicates_analyzed': None
        }
        
        self.initialized = False

    def initialize(self, policy_file: str, vendor: str) -> str:
        """워크플로우 초기화
        
        Args:
            policy_file: 정책 파일 경로
            vendor: 방화벽 벤더 ('paloalto' or 'secui')
            
        Returns:
            초기화된 정책 파일 경로
        """
        try:
            self._update_status('initialized', 'processing', '워크플로우 초기화 중...')
            
            # 벤더 유효성 검사
            if vendor.lower() not in ['paloalto', 'secui']:
                raise ValueError(f"지원되지 않는 벤더입니다: {vendor}")
            
            # 정책 파일 로드
            self.policies_df = pd.read_excel(policy_file)
            self.vendor = vendor.lower()
            
            # 필수 컬럼 확인
            required_columns = ['Rule Name', 'Enable', 'Action', 'Source', 'Destination', 'Service']
            missing_columns = [col for col in required_columns if col not in self.policies_df.columns]
            
            if missing_columns:
                error_msg = f"정책 파일에 필수 컬럼이 없습니다: {missing_columns}"
                self._update_status('initialized', 'failed', error_msg)
                raise ValueError(error_msg)
            
            # 초기화 완료
            self.initialized = True
            self.progress['initialized'] = True
            
            # 중간 결과물 저장
            output_file = self.file_manager.save_dataframe(
                self.policies_df,
                f"{self.vendor}_policies_initialized"
            )
            self.intermediate_files['initialized'] = output_file
            
            self._update_status('initialized', 'completed', '워크플로우 초기화 완료')
            return output_file
            
        except Exception as e:
            error_msg = f"워크플로우 초기화 중 오류 발생: {str(e)}"
            self._update_status('initialized', 'failed', error_msg)
            self.logger.error(error_msg)
            raise

    def process_request_info(self, request_info: Optional[pd.DataFrame] = None) -> str:
        """신청 정보 처리
        
        Args:
            request_info: 신청 정보 데이터프레임
            
        Returns:
            처리된 정책 파일 경로
        """
        try:
            if not self.initialized:
                error_msg = "워크플로우가 초기화되지 않았습니다."
                self._update_status('request_processed', 'failed', error_msg)
                raise ValueError(error_msg)
            
            self._update_status('request_processed', 'processing', '신청 정보 처리 중...')
            
            # 신청 정보 처리
            self.policies_df = self.processor.process_request_info(self.policies_df, request_info)
            
            # 상태 업데이트
            self.progress['request_processed'] = True
            
            # 중간 결과물 저장
            output_file = self.file_manager.save_dataframe(
                self.policies_df,
                f"{self.vendor}_policies_request_processed"
            )
            self.intermediate_files['request_processed'] = output_file
            
            self._update_status('request_processed', 'completed', '신청 정보 처리 완료')
            return output_file
            
        except Exception as e:
            error_msg = f"신청 정보 처리 중 오류 발생: {str(e)}"
            self._update_status('request_processed', 'failed', error_msg)
            self.logger.error(error_msg)
            raise

    def process_usage_data(self, usage_data: Optional[pd.DataFrame] = None) -> str:
        """사용 데이터 처리
        
        Args:
            usage_data: 사용 이력 데이터프레임
            
        Returns:
            처리된 정책 파일 경로
        """
        try:
            if not self.initialized:
                error_msg = "워크플로우가 초기화되지 않았습니다."
                self._update_status('usage_processed', 'failed', error_msg)
                raise ValueError(error_msg)
            
            self._update_status('usage_processed', 'processing', '사용 데이터 처리 중...')
            
            # 사용 데이터 처리
            self.policies_df = self.processor.process_usage_data(self.policies_df, usage_data)
            
            # 상태 업데이트
            self.progress['usage_processed'] = True
            
            # 중간 결과물 저장
            output_file = self.file_manager.save_dataframe(
                self.policies_df,
                f"{self.vendor}_policies_usage_processed"
            )
            self.intermediate_files['usage_processed'] = output_file
            
            self._update_status('usage_processed', 'completed', '사용 데이터 처리 완료')
            return output_file
            
        except Exception as e:
            error_msg = f"사용 데이터 처리 중 오류 발생: {str(e)}"
            self._update_status('usage_processed', 'failed', error_msg)
            self.logger.error(error_msg)
            raise

    def process_vendor_specific(self) -> str:
        """벤더별 처리
        
        Returns:
            처리된 정책 파일 경로
        """
        try:
            if not self.initialized:
                error_msg = "워크플로우가 초기화되지 않았습니다."
                self._update_status('vendor_processed', 'failed', error_msg)
                raise ValueError(error_msg)
            
            self._update_status('vendor_processed', 'processing', f'{self.vendor} 벤더별 처리 중...')
            
            # 벤더별 처리
            if self.vendor == 'paloalto':
                self.policies_df = self._process_paloalto(self.policies_df)
            elif self.vendor == 'secui':
                self.policies_df = self._process_secui(self.policies_df)
            else:
                error_msg = f"지원되지 않는 벤더입니다: {self.vendor}"
                self._update_status('vendor_processed', 'failed', error_msg)
                raise ValueError(error_msg)
            
            # 상태 업데이트
            self.progress['vendor_processed'] = True
            
            # 중간 결과물 저장
            output_file = self.file_manager.save_dataframe(
                self.policies_df,
                f"{self.vendor}_policies_vendor_processed"
            )
            self.intermediate_files['vendor_processed'] = output_file
            
            self._update_status('vendor_processed', 'completed', f'{self.vendor} 벤더별 처리 완료')
            return output_file
            
        except Exception as e:
            error_msg = f"벤더별 처리 중 오류 발생: {str(e)}"
            self._update_status('vendor_processed', 'failed', error_msg)
            self.logger.error(error_msg)
            raise

    def analyze_duplicates(self) -> str:
        """중복 정책 분석
        
        Returns:
            중복 정책 분석 결과 파일 경로
        """
        try:
            if not self.initialized:
                error_msg = "워크플로우가 초기화되지 않았습니다."
                self._update_status('duplicates_analyzed', 'failed', error_msg)
                raise ValueError(error_msg)
            
            self._update_status('duplicates_analyzed', 'processing', '중복 정책 분석 중...')
            
            # 중복 정책 분석
            duplicate_analysis_file = self.analyzer.analyze_duplicates(
                self.policies_df,
                self.vendor,
                self.output_dir
            )
            
            if not duplicate_analysis_file:
                error_msg = "중복 정책 분석 결과 파일이 생성되지 않았습니다."
                self._update_status('duplicates_analyzed', 'failed', error_msg)
                raise ValueError(error_msg)
            
            self.duplicate_analysis_file = duplicate_analysis_file
            
            # 중복여부 업데이트
            self.policies_df = self._update_duplicate_status(self.policies_df, duplicate_analysis_file)
            
            # 상태 업데이트
            self.progress['duplicates_analyzed'] = True
            
            # 중간 결과물 저장
            output_file = self.file_manager.save_dataframe(
                self.policies_df,
                f"{self.vendor}_policies_duplicates_analyzed"
            )
            self.intermediate_files['duplicates_analyzed'] = output_file
            
            self._update_status('duplicates_analyzed', 'completed', '중복 정책 분석 완료')
            return duplicate_analysis_file
            
        except Exception as e:
            error_msg = f"중복 정책 분석 중 오류 발생: {str(e)}"
            self._update_status('duplicates_analyzed', 'failed', error_msg)
            self.logger.error(error_msg)
            raise

    def generate_reports(self) -> Dict[str, str]:
        """최종 보고서 생성
        
        Returns:
            보고서 파일 경로 딕셔너리
        """
        try:
            if not self.initialized:
                error_msg = "워크플로우가 초기화되지 않았습니다."
                self._update_status('reports_generated', 'failed', error_msg)
                raise ValueError(error_msg)
            
            self._update_status('reports_generated', 'processing', '보고서 생성 중...')
            
            # 필수 단계 확인
            required_steps = ['usage_processed', 'request_processed', 'vendor_processed', 'duplicates_analyzed']
            missing_steps = [step for step in required_steps if not self.progress[step]]
            
            if missing_steps:
                error_msg = f"보고서 생성 전 필요한 단계가 완료되지 않았습니다: {missing_steps}"
                self._update_status('reports_generated', 'failed', error_msg)
                raise ValueError(error_msg)
            
            # 보고서 생성
            reports = self.reporter.generate_reports(self.policies_df)
            
            if not reports:
                error_msg = "보고서가 생성되지 않았습니다."
                self._update_status('reports_generated', 'failed', error_msg)
                raise ValueError(error_msg)
            
            # 상태 업데이트
            self.progress['reports_generated'] = True
            
            self._update_status('reports_generated', 'completed', '보고서 생성 완료')
            return reports
            
        except Exception as e:
            error_msg = f"보고서 생성 중 오류 발생: {str(e)}"
            self._update_status('reports_generated', 'failed', error_msg)
            self.logger.error(error_msg)
            return {}

    def get_progress(self) -> Dict[str, bool]:
        """현재 진행 상태 반환"""
        return self.progress.copy()
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """현재 상세 상태 반환"""
        return self.status.copy()
    
    def get_intermediate_files(self) -> Dict[str, str]:
        """중간 결과물 파일 경로 반환"""
        return self.intermediate_files.copy()
    
    def _update_status(self, step: str, status: str, message: str):
        """상태 업데이트
        
        Args:
            step: 업데이트할 단계
            status: 상태 ('pending', 'processing', 'completed', 'failed')
            message: 상태 메시지
        """
        self.status[step] = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if status == 'completed':
            self.logger.info(message)
        elif status == 'failed':
            self.logger.error(message)
        else:
            self.logger.debug(message)

    def _parse_request_numbers(self, df):
        """신청번호 파싱 로직
        
        Args:
            df (pd.DataFrame): 파싱할 정책 데이터프레임
        
        Returns:
            pd.DataFrame: 파싱된 데이터프레임
        """
        try:
            # Description에서 신청번호 추출을 위한 정규식 패턴
            patterns = {
                'REQUEST_ID': r'(?:신청번호|Request ID|REQ)[:\s]*([A-Z0-9-]+)',
                'MIS_ID': r'(?:MIS ID|MIS)[:\s]*([A-Z0-9-]+)',
                'RULESET_ID': r'(?:정책셋|Ruleset)[:\s]*([A-Z0-9-]+)'
            }

            # 각 패턴에 대해 추출 시도
            for column, pattern in patterns.items():
                df[column] = df['Description'].str.extract(pattern, expand=False)

            # 신청 유형 분류
            def determine_request_type(row):
                if pd.isna(row['REQUEST_ID']) and pd.isna(row['MIS_ID']):
                    return 'Unknown'
                elif not pd.isna(row['REQUEST_ID']):
                    return 'NORMAL'
                elif not pd.isna(row['MIS_ID']):
                    return 'GROUP'
                else:
                    return 'Unknown'

            df['Request Type'] = df.apply(determine_request_type, axis=1)

            return df

        except Exception as e:
            self.logger.error(f"신청번호 파싱 중 오류 발생: {str(e)}")
            raise

    def _process_paloalto(self, df):
        """팔로알토 정책 처리
        
        Args:
            df (pd.DataFrame): 처리할 정책 데이터프레임
        
        Returns:
            pd.DataFrame: 처리된 데이터프레임
        """
        try:
            current_date = datetime.now()
            three_months_ago = current_date - timedelta(days=90)

            df["예외"] = ''

            # 1. 예외 신청정책 처리
            df['REQUEST_ID'] = df['REQUEST_ID'].fillna('')
            for id in self.except_list:
                df.loc[df['REQUEST_ID'].str.startswith(id, na=False), '예외'] = '예외신청정책'
            
            # 2. 자동연장정책 처리
            df.loc[df['REQUEST_STATUS'] == 99, '예외'] = '자동연장정책'

            # 3. 신규정책 처리
            df['날짜'] = df['Rule Name'].str.extract(r'(\d{8})', expand=False)
            df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d', errors='coerce')
            df.loc[(df['날짜'] >= three_months_ago) & (df['날짜'] <= current_date), '예외'] = '신규정책'

            # 4. 인프라정책 처리
            deny_std_rule_index = df[df['Rule Name'] == 'deny_rule'].index[0]
            df.loc[df.index < deny_std_rule_index, '예외'] = '인프라정책'

            # 5. 테스트 그룹 정책 처리
            df.loc[df['Rule Name'].str.startswith(('sample_', 'test_')), '예외'] = 'test_group_정책'

            # 6. 비활성화정책 처리
            df.loc[df['Enable'] == 'N', '예외'] = '비활성화정책'

            # 7. 기준정책 처리
            df.loc[(df['Rule Name'].str.endswith('_Rule')) & (df['Enable'] == 'N'), '예외'] = '기준정책'

            # 8. 차단정책 처리
            df.loc[df['Action'] == 'deny', '예외'] = '차단정책'

            df['예외'].fillna('', inplace=True)

            # 컬럼 순서 조정
            cols = list(df.columns)
            cols = ['예외'] + [col for col in cols if col != '예외']
            df = df[cols]

            # 만료여부 체크
            def check_date(row):
                try:
                    end_date = pd.to_datetime(row['REQUEST_END_DATE'])
                    return '미만료' if end_date > current_date else '만료'
                except:
                    return '만료'
            
            df['만료여부'] = df.apply(check_date, axis=1)
            df.drop(columns=['날짜'], inplace=True)
            df.rename(columns={'Request Type': '신청이력'}, inplace=True)

            return df

        except Exception as e:
            self.logger.error(f"팔로알토 정책 처리 중 오류 발생: {str(e)}")
            raise

    def _process_secui(self, df):
        """시큐아이 정책 처리
        
        Args:
            df (pd.DataFrame): 처리할 정책 데이터프레임
        
        Returns:
            pd.DataFrame: 처리된 데이터프레임
        """
        try:
            current_date = datetime.now()
            three_months_ago = current_date - timedelta(days=90)

            df["예외"] = ''

            # 1. 예외 신청정책 처리
            df['Request ID'].fillna('-', inplace=True)
            for id in self.except_list:
                df.loc[df['Request ID'].str.startswith(id), '예외'] = '예외신청정책'
            
            # 2. 자동연장정책 처리
            df.loc[df['REQUEST_STATUS'] == 99, '예외'] = '자동연장정책'

            # 4. 인프라정책 처리
            deny_std_rule_index = df[df['Description'].str.contains('deny_rule') == True].index[0]
            df.loc[df.index < deny_std_rule_index, '예외'] = '인프라정책'

            # 5. 테스트 그룹 정책 처리
            df.loc[df['Description'].str.contains(('sample_', 'test_')) == True, '예외'] = 'test_group_정책'

            # 6. 비활성화정책 처리
            df.loc[df['Enable'] == 'N', '예외'] = '비활성화정책'

            # 7. 기준정책 처리
            df.loc[(df['Description'].str.contains('기준룰')) & (df['Enable'] == 'N'), '예외'] = '기준정책'

            # 8. 차단정책 처리
            df.loc[df['Action'] == 'deny', '예외'] = '차단정책'

            df['예외'].fillna('', inplace=True)

            # 컬럼 순서 조정
            cols = list(df.columns)
            cols = ['예외'] + [col for col in cols if col != '예외']
            df = df[cols]

            # 만료여부 체크
            def check_date(row):
                try:
                    end_date = pd.to_datetime(row['REQUEST_END_DATE'])
                    return '미만료' if end_date > current_date else '만료'
                except:
                    return '만료'
            
            df['만료여부'] = df.apply(check_date, axis=1)
            df.rename(columns={'Request Type': '신청이력'}, inplace=True)

            # 불필요한 컬럼 제거
            df.drop(columns=['Request ID', 'Ruleset ID', 'MIS ID', 'Request User', 'Start Date', 'End Date'], inplace=True)

            # 컬럼 순서 재조정
            cols = list(df.columns)
            cols.insert(cols.index('예외') + 1, cols.pop(cols.index('만료여부')))
            df = df[cols]
            cols.insert(cols.index('예외') + 1, cols.pop(cols.index('신청이력')))
            df = df[cols]

            return df

        except Exception as e:
            self.logger.error(f"시큐아이 정책 처리 중 오류 발생: {str(e)}")
            raise

    def _update_usage_status(self, df):
        """90일 기준으로 미사용 여부 업데이트"""
        try:
            current_date = datetime.now()
            ninety_days_ago = current_date - timedelta(days=90)
            
            # last_hit 컬럼이 있는 경우
            if 'last_hit' in df.columns:
                df['미사용여부'] = df['last_hit'].apply(
                    lambda x: '미사용' if pd.isnull(x) or pd.to_datetime(x) < ninety_days_ago else '사용'
                )
            else:
                df['미사용여부'] = '미사용'
            
            return df
        except Exception as e:
            self.logger.error(f"사용여부 업데이트 중 오류 발생: {str(e)}")
            raise

    def _update_duplicate_status(self, df, duplicate_analysis_file):
        """중복 정책 분석 결과를 기반으로 중복여부 업데이트"""
        try:
            # 중복여부 컬럼이 없으면 추가
            if '중복여부' not in df.columns:
                df['중복여부'] = ''
            
            # 중복 정책 분석 결과 파일 읽기
            duplicate_df = pd.read_excel(duplicate_analysis_file)
            
            # 필요한 컬럼이 있는지 확인
            required_columns = ['Rule Name', '작업구분']
            missing_columns = [col for col in required_columns if col not in duplicate_df.columns]
            
            if missing_columns:
                self.logger.warning(f"중복 정책 분석 결과 파일에 필요한 컬럼이 없습니다: {missing_columns}")
                
                # 대체 컬럼명 확인
                if 'Rule Name' in missing_columns:
                    # 가능한 대체 컬럼명 목록
                    rule_name_alternatives = ['정책명', 'RuleName', 'Policy Name', 'Name']
                    for alt in rule_name_alternatives:
                        if alt in duplicate_df.columns:
                            self.logger.info(f"'Rule Name' 대신 '{alt}' 컬럼을 사용합니다.")
                            duplicate_df.rename(columns={alt: 'Rule Name'}, inplace=True)
                            missing_columns.remove('Rule Name')
                            break
                
                if '작업구분' in missing_columns:
                    # 가능한 대체 컬럼명 목록
                    work_type_alternatives = ['작업 구분', 'WorkType', 'Type', '구분']
                    for alt in work_type_alternatives:
                        if alt in duplicate_df.columns:
                            self.logger.info(f"'작업구분' 대신 '{alt}' 컬럼을 사용합니다.")
                            duplicate_df.rename(columns={alt: '작업구분'}, inplace=True)
                            missing_columns.remove('작업구분')
                            break
            
            # 여전히 필요한 컬럼이 없으면 오류 발생
            if missing_columns:
                self.logger.error(f"중복 정책 분석 결과 파일에 필요한 컬럼을 찾을 수 없습니다: {missing_columns}")
                self.logger.info(f"사용 가능한 컬럼: {duplicate_df.columns.tolist()}")
                raise ValueError(f"중복 정책 분석 결과 파일에 필요한 컬럼이 없습니다: {missing_columns}")
            
            # 작업구분 데이터 매핑
            duplicate_map = duplicate_df[['Rule Name', '작업구분']].set_index('Rule Name').to_dict()['작업구분']
            
            # 정책 파일에 작업구분 데이터 추가
            updated_count = 0
            for idx, row in df.iterrows():
                rule_name = row['Rule Name']
                if rule_name in duplicate_map:
                    df.at[idx, '중복여부'] = duplicate_map[rule_name]
                    updated_count += 1
            
            self.logger.info(f"총 {updated_count}개의 정책에 중복여부 정보가 추가되었습니다.")
            return df
            
        except Exception as e:
            self.logger.error(f"중복여부 업데이트 중 오류 발생: {str(e)}")
            raise

    def _get_auto_extension_ids(self, request_info_df):
        """자동연장 대상 신청번호 추출"""
        try:
            if 'REQUEST_STATUS' in request_info_df.columns:
                auto_extension_ids = request_info_df[
                    request_info_df['REQUEST_STATUS'].isin([98, 99])
                ]['REQUEST_ID'].drop_duplicates()
                return auto_extension_ids.tolist()
            return []
        except Exception as e:
            self.logger.error(f"자동연장 신청번호 추출 중 오류 발생: {str(e)}")
            raise

    def _update_file_version(self, file_path, final_version=False):
        """파일 버전 관리"""
        try:
            base_name = file_path.stem
            ext = file_path.suffix
            
            match = re.search(r'_v(\d+)$', base_name)
            final_match = re.search(r'_vf$', base_name)
            
            if final_match:
                return file_path
            
            if final_version:
                if match:
                    new_base_name = re.sub(r'_v\d+$', '_vf', base_name)
                else:
                    new_base_name = f"{base_name}_vf"
            else:
                if match:
                    version = int(match.group(1))
                    new_version = version + 1
                    new_base_name = re.sub(r'_v\d+$', f'_v{new_version}', base_name)
                else:
                    new_base_name = f"{base_name}_v1"
            
            return Path(file_path.parent) / f"{new_base_name}{ext}"
        except Exception as e:
            self.logger.error(f"파일 버전 업데이트 중 오류 발생: {str(e)}")
            raise 