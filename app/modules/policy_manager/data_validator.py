import logging
import pandas as pd
from typing import Tuple, List, Dict, Any, Optional


class DataValidator:
    """데이터 유효성 검증 클래스"""
    
    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(__name__)
    
    def validate_policy_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """정책 데이터 유효성 검증
        
        Args:
            df: 검증할 정책 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 빈 데이터프레임 검증
        if df is None or df.empty:
            return False, "정책 데이터가 비어 있습니다."
        
        # 필수 컬럼 검증
        required_columns = ['Rule Name', 'Enable', 'Action', 'Source', 'Destination', 'Service']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"필수 컬럼이 누락되었습니다: {missing_columns}"
        
        # Rule Name 중복 검증
        duplicate_rules = df[df.duplicated('Rule Name', keep=False)]
        if not duplicate_rules.empty:
            duplicate_count = len(duplicate_rules['Rule Name'].unique())
            return False, f"중복된 Rule Name이 {duplicate_count}개 있습니다."
        
        # 데이터 타입 검증
        try:
            # Enable 컬럼이 yes/no 또는 boolean 타입인지 확인
            if 'Enable' in df.columns:
                valid_values = ['yes', 'no', True, False]
                invalid_enables = df[~df['Enable'].isin(valid_values)]
                if not invalid_enables.empty:
                    return False, f"Enable 컬럼에 유효하지 않은 값이 있습니다: {invalid_enables['Enable'].unique()}"
            
            # Action 컬럼이 allow/deny 또는 permit/drop 타입인지 확인
            if 'Action' in df.columns:
                valid_actions = ['allow', 'deny', 'permit', 'drop']
                invalid_actions = df[~df['Action'].str.lower().isin(valid_actions)]
                if not invalid_actions.empty:
                    return False, f"Action 컬럼에 유효하지 않은 값이 있습니다: {invalid_actions['Action'].unique()}"
        
        except Exception as e:
            return False, f"데이터 타입 검증 중 오류 발생: {str(e)}"
        
        return True, "정책 데이터가 유효합니다."
    
    def validate_usage_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """사용 이력 데이터 유효성 검증
        
        Args:
            df: 검증할 사용 이력 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 빈 데이터프레임 검증
        if df is None or df.empty:
            return False, "사용 이력 데이터가 비어 있습니다."
        
        # 필수 컬럼 검증
        required_columns = ['Rule Name']
        alternative_columns = {
            'Rule Name': ['rule_name', 'rulename', 'name', '정책명'],
            'last_hit': ['last_hit_timestamp', 'last_used', '마지막사용일시', '마지막사용시간']
        }
        
        # 필수 컬럼 또는 대체 컬럼 확인
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                # 대체 컬럼 확인
                alternatives = alternative_columns.get(col, [])
                found = False
                for alt_col in alternatives:
                    if alt_col in df.columns:
                        found = True
                        break
                
                if not found:
                    missing_columns.append(col)
        
        if missing_columns:
            return False, f"필수 컬럼이 누락되었습니다: {missing_columns}"
        
        # Rule Name 중복 검증
        rule_name_col = 'Rule Name'
        for alt_col in alternative_columns['Rule Name']:
            if alt_col in df.columns:
                rule_name_col = alt_col
                break
        
        duplicate_rules = df[df.duplicated(rule_name_col, keep=False)]
        if not duplicate_rules.empty:
            duplicate_count = len(duplicate_rules[rule_name_col].unique())
            return False, f"중복된 {rule_name_col}이 {duplicate_count}개 있습니다."
        
        return True, "사용 이력 데이터가 유효합니다."
    
    def validate_request_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """신청 정보 데이터 유효성 검증
        
        Args:
            df: 검증할 신청 정보 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 빈 데이터프레임 검증
        if df is None or df.empty:
            return False, "신청 정보 데이터가 비어 있습니다."
        
        # 필수 컬럼 검증
        required_columns = ['Rule Name', '신청번호']
        alternative_columns = {
            'Rule Name': ['rule_name', 'rulename', 'name', '정책명'],
            '신청번호': ['request_id', 'request_number', '요청번호', '요청ID']
        }
        
        # 필수 컬럼 또는 대체 컬럼 확인
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                # 대체 컬럼 확인
                alternatives = alternative_columns.get(col, [])
                found = False
                for alt_col in alternatives:
                    if alt_col in df.columns:
                        found = True
                        break
                
                if not found:
                    missing_columns.append(col)
        
        if missing_columns:
            return False, f"필수 컬럼이 누락되었습니다: {missing_columns}"
        
        return True, "신청 정보 데이터가 유효합니다."
    
    def validate_duplicate_analysis_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """중복 분석 결과 데이터 유효성 검증
        
        Args:
            df: 검증할 중복 분석 결과 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 빈 데이터프레임 검증
        if df is None or df.empty:
            return False, "중복 분석 결과 데이터가 비어 있습니다."
        
        # 필수 컬럼 검증
        required_columns = ['Rule Name', '작업구분']
        alternative_columns = {
            'Rule Name': ['rule_name', 'rulename', 'name', '정책명'],
            '작업구분': ['duplicate_status', 'status', '중복여부', '중복상태']
        }
        
        # 필수 컬럼 또는 대체 컬럼 확인
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                # 대체 컬럼 확인
                alternatives = alternative_columns.get(col, [])
                found = False
                for alt_col in alternatives:
                    if alt_col in df.columns:
                        found = True
                        break
                
                if not found:
                    missing_columns.append(col)
        
        if missing_columns:
            return False, f"필수 컬럼이 누락되었습니다: {missing_columns}"
        
        return True, "중복 분석 결과 데이터가 유효합니다."
    
    def validate_report_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """보고서 데이터 유효성 검증
        
        Args:
            df: 검증할 보고서 데이터프레임
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 빈 데이터프레임 검증
        if df is None or df.empty:
            return False, "보고서 데이터가 비어 있습니다."
        
        # 필수 컬럼 검증
        required_columns = ['Rule Name', '중복여부', '미사용여부', '신청이력', '만료여부', '예외']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"필수 컬럼이 누락되었습니다: {missing_columns}"
        
        # 데이터 타입 검증
        try:
            # 중복여부 컬럼 검증
            if '중복여부' in df.columns:
                null_duplicates = df['중복여부'].isnull().sum()
                if null_duplicates > 0:
                    self.logger.warning(f"중복여부 컬럼에 {null_duplicates}개의 null 값이 있습니다.")
            
            # 미사용여부 컬럼 검증
            if '미사용여부' in df.columns:
                null_unused = df['미사용여부'].isnull().sum()
                if null_unused > 0:
                    self.logger.warning(f"미사용여부 컬럼에 {null_unused}개의 null 값이 있습니다.")
            
            # 신청이력 컬럼 검증
            if '신청이력' in df.columns:
                null_requests = df['신청이력'].isnull().sum()
                if null_requests > 0:
                    self.logger.warning(f"신청이력 컬럼에 {null_requests}개의 null 값이 있습니다.")
            
            # 만료여부 컬럼 검증
            if '만료여부' in df.columns:
                null_expired = df['만료여부'].isnull().sum()
                if null_expired > 0:
                    self.logger.warning(f"만료여부 컬럼에 {null_expired}개의 null 값이 있습니다.")
            
            # 예외 컬럼 검증
            if '예외' in df.columns:
                null_exceptions = df['예외'].isnull().sum()
                if null_exceptions > 0:
                    self.logger.warning(f"예외 컬럼에 {null_exceptions}개의 null 값이 있습니다.")
        
        except Exception as e:
            return False, f"데이터 타입 검증 중 오류 발생: {str(e)}"
        
        return True, "보고서 데이터가 유효합니다."
    
    def check_column_exists(self, df: pd.DataFrame, column: str, alternatives: List[str] = None) -> Tuple[bool, Optional[str]]:
        """컬럼 존재 여부 확인 및 대체 컬럼 반환
        
        Args:
            df: 확인할 데이터프레임
            column: 확인할 컬럼명
            alternatives: 대체 컬럼명 목록
            
        Returns:
            (존재 여부, 존재하는 컬럼명 또는 None)
        """
        if column in df.columns:
            return True, column
        
        if alternatives:
            for alt_col in alternatives:
                if alt_col in df.columns:
                    return True, alt_col
        
        return False, None
    
    def get_column_stats(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """컬럼 통계 정보 반환
        
        Args:
            df: 데이터프레임
            column: 통계를 계산할 컬럼명
            
        Returns:
            통계 정보 딕셔너리
        """
        if column not in df.columns:
            return {
                'exists': False,
                'error': f"컬럼이 존재하지 않습니다: {column}"
            }
        
        try:
            stats = {
                'exists': True,
                'count': len(df),
                'null_count': df[column].isnull().sum(),
                'null_percentage': round(df[column].isnull().sum() / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
            # 숫자형 컬럼인 경우 추가 통계
            if pd.api.types.is_numeric_dtype(df[column]):
                stats.update({
                    'min': df[column].min(),
                    'max': df[column].max(),
                    'mean': df[column].mean(),
                    'median': df[column].median()
                })
            # 문자열 컬럼인 경우 추가 통계
            elif pd.api.types.is_string_dtype(df[column]):
                value_counts = df[column].value_counts()
                stats.update({
                    'unique_count': df[column].nunique(),
                    'most_common': value_counts.index[0] if not value_counts.empty else None,
                    'most_common_count': value_counts.iloc[0] if not value_counts.empty else 0
                })
            
            return stats
        
        except Exception as e:
            return {
                'exists': True,
                'error': f"통계 계산 중 오류 발생: {str(e)}"
            } 