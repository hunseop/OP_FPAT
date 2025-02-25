from typing import Dict, List
import pandas as pd
from .report_generator import BaseReportGenerator

class PolicyReporter(BaseReportGenerator):
    """정책 보고서 생성을 담당하는 클래스"""

    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        
        # 컬럼 번역 매핑
        self.column_translations = {
            'Rule Name': '정책명',
            'Enable': '상태',
            'Action': '동작',
            'Source': '출발지',
            'User': '사용자',
            'Destination': '목적지',
            'Service': '서비스',
            'Application': '애플리케이션',
            'Security Profile': '보안 프로필',
            'Category': '카테고리',
            'Description': '설명',
            'Request Type': '신청유형',
            'REQUEST_ID': '신청번호',
            'Ruleset ID': 'RULESET ID',
            'MIS ID': 'MIS ID',
            'Request User': '신청자',
            'Start Date': '시작일',
            'End Date': '종료일'
        }

    def generate_reports(self, df: pd.DataFrame) -> Dict[str, str]:
        """모든 보고서 생성
        
        Args:
            df: 정책 데이터프레임
            
        Returns:
            보고서 파일 경로 딕셔너리
        """
        try:
            # 필수 컬럼 확인
            required_columns = ['Rule Name', '예외', '중복여부', '신청이력', '만료여부', '미사용여부']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.error(f"보고서 생성에 필요한 컬럼이 없습니다: {missing_columns}")
                
                # 누락된 컬럼 자동 추가 (빈 값으로)
                for col in missing_columns:
                    self.logger.warning(f"누락된 컬럼 '{col}'을 빈 값으로 추가합니다.")
                    df[col] = ''
            
            # 데이터 검증
            if df.empty:
                self.logger.error("보고서 생성을 위한 데이터가 비어 있습니다.")
                return {}
            
            # 값이 누락된 중요 컬럼 확인
            for col in required_columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    self.logger.warning(f"'{col}' 컬럼에 {null_count}개의 누락된 값이 있습니다.")
                    # 누락된 값을 빈 문자열로 대체
                    df[col].fillna('', inplace=True)
            
            reports = {}
            
            # 최종 분석 파일
            reports['final'] = self._save_report(
                self._prepare_final_report(df),
                'final_analysis'
            )
            
            # 만료/사용 정책 보고서
            expired_used_df = self._filter_expired_used(df)
            if not expired_used_df.empty:
                reports['expired_used'] = self._save_report(
                    expired_used_df,
                    'expired_used_policies'
                )
            else:
                self.logger.info("만료/사용 정책이 없습니다.")
            
            # 만료/미사용 정책 보고서
            expired_unused_df = self._filter_expired_unused(df)
            if not expired_unused_df.empty:
                reports['expired_unused'] = self._save_report(
                    expired_unused_df,
                    'expired_unused_policies'
                )
            else:
                self.logger.info("만료/미사용 정책이 없습니다.")
            
            # 미만료/미사용 정책 보고서
            unexpired_unused_df = self._filter_unexpired_unused(df)
            if not unexpired_unused_df.empty:
                reports['unexpired_unused'] = self._save_report(
                    unexpired_unused_df,
                    'unexpired_unused_policies'
                )
            else:
                self.logger.info("미만료/미사용 정책이 없습니다.")
            
            # 이력없는/미사용 정책 보고서
            no_history_unused_df = self._filter_no_history_unused(df)
            if not no_history_unused_df.empty:
                reports['no_history_unused'] = self._save_report(
                    no_history_unused_df,
                    'no_history_unused_policies'
                )
            else:
                self.logger.info("이력없는/미사용 정책이 없습니다.")
            
            # 중복/공지용 정책 보고서
            duplicate_notice_df = self._filter_duplicate_notice(df)
            if not duplicate_notice_df.empty:
                reports['duplicate_notice'] = self._save_report(
                    duplicate_notice_df,
                    'duplicate_notice_policies'
                )
            else:
                self.logger.info("중복/공지용 정책이 없습니다.")
            
            # 중복/삭제용 정책 보고서
            duplicate_delete_df = self._filter_duplicate_delete(df)
            if not duplicate_delete_df.empty:
                reports['duplicate_delete'] = self._save_report(
                    duplicate_delete_df,
                    'duplicate_delete_policies'
                )
            else:
                self.logger.info("중복/삭제용 정책이 없습니다.")
            
            return reports
            
        except Exception as e:
            self.logger.error(f"보고서 생성 중 오류 발생: {str(e)}")
            raise

    def _prepare_final_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """최종 분석 파일 준비"""
        df = df.copy()
        df = self._translate_columns(df, self.column_translations)
        df = self._fill_empty_values(df)
        return df

    def _filter_expired_used(self, df: pd.DataFrame) -> pd.DataFrame:
        """만료/사용 정책 필터링"""
        return df[
            (df['예외'].isin(['', '신규']))
            & (df['중복여부'] == '')
            & (df['신청이력'].isin(['GROUP', 'NORMAL']))
            & (df['만료여부'] == '만료')
            & (df['미사용여부'] == '사용')
        ].copy()

    def _filter_expired_unused(self, df: pd.DataFrame) -> pd.DataFrame:
        """만료/미사용 정책 필터링"""
        return df[
            (df['예외'].isin(['', '신규']))
            & (df['중복여부'] == '')
            & (df['신청이력'].isin(['GROUP', 'NORMAL']))
            & (df['만료여부'] == '만료')
            & (df['미사용여부'] == '미사용')
        ].copy()

    def _filter_unexpired_unused(self, df: pd.DataFrame) -> pd.DataFrame:
        """미만료/미사용 정책 필터링"""
        return df[
            (df['예외'] == '')
            & (df['중복여부'] == '')
            & (df['신청이력'].isin(['GROUP', 'NORMAL']))
            & (df['만료여부'] == '미만료')
            & (df['미사용여부'] == '미사용')
        ].copy()

    def _filter_no_history_unused(self, df: pd.DataFrame) -> pd.DataFrame:
        """이력없는/미사용 정책 필터링"""
        return df[
            (df['예외'] == '')
            & (df['중복여부'] == '')
            & (df['신청이력'] == 'Unknown')
            & (df['미사용여부'] == '미사용')
        ].copy()

    def _filter_duplicate_notice(self, df: pd.DataFrame) -> pd.DataFrame:
        """중복/공지용 정책 필터링"""
        return df[
            (df['중복여부'] == 'Upper')
        ].copy()

    def _filter_duplicate_delete(self, df: pd.DataFrame) -> pd.DataFrame:
        """중복/삭제용 정책 필터링"""
        return df[
            (df['중복여부'] == 'Lower')
        ].copy() 