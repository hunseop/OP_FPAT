import logging
import pandas as pd
from typing import Optional, List, Dict, Any

class DataValidator:
    """데이터 유효성 검증을 담당하는 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 필수 컬럼 정의
        self.required_columns = {
            'policy': [
                'Rule Name', 'Enable', 'Action', 'Source', 'User',
                'Destination', 'Service', 'Application', 'Security Profile',
                'Category', 'Description'
            ],
            'usage': ['Rule Name', 'last_hit'],
            'request': ['REQUEST_ID', 'REQEUST_STATUS']
        }

    def validate_policy_data(self, df: pd.DataFrame) -> tuple[bool, Optional[str]]:
        """정책 데이터 유효성 검증
        
        Args:
            df: 검증할 정책 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        try:
            # 필수 컬럼 확인
            missing_columns = self._check_required_columns(df, 'policy')
            if missing_columns:
                return False, f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
            
            # 데이터 타입 검증
            if not self._validate_policy_types(df):
                return False, "데이터 타입이 올바르지 않습니다."
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"정책 데이터 검증 중 오류 발생: {str(e)}")
            return False, str(e)

    def validate_usage_data(self, df: pd.DataFrame) -> tuple[bool, Optional[str]]:
        """사용 이력 데이터 유효성 검증
        
        Args:
            df: 검증할 사용 이력 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        try:
            # 필수 컬럼 확인
            missing_columns = self._check_required_columns(df, 'usage')
            if missing_columns:
                return False, f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
            
            # last_hit 컬럼 날짜 형식 검증
            if not self._validate_date_column(df, 'last_hit'):
                return False, "last_hit 컬럼의 날짜 형식이 올바르지 않습니다."
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"사용 이력 데이터 검증 중 오류 발생: {str(e)}")
            return False, str(e)

    def validate_request_data(self, df: pd.DataFrame) -> tuple[bool, Optional[str]]:
        """신청 정보 데이터 유효성 검증
        
        Args:
            df: 검증할 신청 정보 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        try:
            # 필수 컬럼 확인
            missing_columns = self._check_required_columns(df, 'request')
            if missing_columns:
                return False, f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
            
            # REQUEST_ID 형식 검증
            if not self._validate_request_id_format(df):
                return False, "REQUEST_ID 형식이 올바르지 않습니다."
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"신청 정보 데이터 검증 중 오류 발생: {str(e)}")
            return False, str(e)

    def _check_required_columns(self, df: pd.DataFrame, data_type: str) -> List[str]:
        """필수 컬럼 존재 여부 확인
        
        Args:
            df: 검증할 데이터프레임
            data_type: 데이터 유형 ('policy', 'usage', 'request')
            
        Returns:
            누락된 컬럼 목록
        """
        required = self.required_columns.get(data_type, [])
        return [col for col in required if col not in df.columns]

    def _validate_policy_types(self, df: pd.DataFrame) -> bool:
        """정책 데이터 타입 검증"""
        try:
            # Enable 컬럼이 bool 또는 int 타입인지 확인
            if 'Enable' in df.columns:
                if not df['Enable'].dtype in ['bool', 'int64']:
                    return False
            
            return True
            
        except Exception:
            return False

    def _validate_date_column(self, df: pd.DataFrame, column: str) -> bool:
        """날짜 컬럼 형식 검증"""
        try:
            if column not in df.columns:
                return False
                
            # null이 아닌 값들을 datetime으로 변환 시도
            pd.to_datetime(df[column].dropna())
            return True
            
        except Exception:
            return False

    def _validate_request_id_format(self, df: pd.DataFrame) -> bool:
        """REQUEST_ID 형식 검증"""
        try:
            if 'REQUEST_ID' not in df.columns:
                return False
            
            # REQUEST_ID가 숫자로만 구성되어 있는지 확인
            return df['REQUEST_ID'].astype(str).str.match(r'^\d+$').all()
            
        except Exception:
            return False 