import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import re

class PolicyProcessor:
    """정책 데이터 처리를 담당하는 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_request_info(self, df: pd.DataFrame, request_info: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """신청 정보 처리
        
        Args:
            df: 처리할 정책 데이터프레임
            request_info: 신청 정보 데이터프레임
        """
        try:
            if request_info is None:
                return df

            # 신청 정보 데이터 처리
            request_info['REQUEST_ID'] = request_info['REQUEST_ID'].astype(str)
            
            # 자동 연장 ID 추출
            auto_extension_ids = self._get_auto_extension_ids(request_info)
            
            # 정책 데이터에서 신청 정보 파싱
            df = self._parse_request_numbers(df)
            
            # 신청 정보 매칭 및 업데이트
            df = self._match_and_update_request_info(df, request_info, auto_extension_ids)
            
            return df
            
        except Exception as e:
            self.logger.error(f"신청 정보 처리 중 오류 발생: {str(e)}")
            raise

    def process_usage_data(self, df: pd.DataFrame, usage_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """사용 데이터 처리
        
        Args:
            df: 처리할 정책 데이터프레임
            usage_data: 사용 이력 데이터프레임
        """
        try:
            if '미사용여부' not in df.columns:
                df['미사용여부'] = ''
            
            # 1. 외부 사용 데이터가 제공된 경우
            if usage_data is not None:
                # 'Rule Name'과 '미사용여부' 컬럼이 있는지 확인
                if 'Rule Name' in usage_data.columns and '미사용여부' in usage_data.columns:
                    # 미사용여부 데이터 매핑
                    usage_map = usage_data[['Rule Name', '미사용여부']].set_index('Rule Name').to_dict()['미사용여부']
                    
                    # 정책 파일에 미사용여부 데이터 추가
                    updated_count = 0
                    for idx, row in df.iterrows():
                        rule_name = row['Rule Name']
                        if rule_name in usage_map:
                            df.at[idx, '미사용여부'] = usage_map[rule_name]
                            updated_count += 1
                    
                    self.logger.info(f"외부 파일에서 {updated_count}개의 정책에 미사용여부 정보가 추가되었습니다.")
                    return df
                
                # 'last_hit' 컬럼이 있는 경우
                elif 'Rule Name' in usage_data.columns and 'last_hit' in usage_data.columns:
                    current_date = datetime.now()
                    ninety_days_ago = current_date - timedelta(days=90)
                    
                    # Rule Name을 기준으로 last_hit 매핑
                    last_hit_map = usage_data[['Rule Name', 'last_hit']].set_index('Rule Name').to_dict()['last_hit']
                    
                    # 정책 파일에 미사용여부 데이터 추가
                    updated_count = 0
                    for idx, row in df.iterrows():
                        rule_name = row['Rule Name']
                        if rule_name in last_hit_map:
                            last_hit = last_hit_map[rule_name]
                            try:
                                last_hit_date = pd.to_datetime(last_hit)
                                df.at[idx, '미사용여부'] = '미사용' if pd.isnull(last_hit) or last_hit_date < ninety_days_ago else '사용'
                            except:
                                df.at[idx, '미사용여부'] = '미사용' if pd.isnull(last_hit) else '사용'
                            updated_count += 1
                    
                    self.logger.info(f"외부 파일의 last_hit 정보를 기반으로 {updated_count}개의 정책에 미사용여부 정보가 추가되었습니다.")
                    return df
                
                # 사용 데이터 파일에 필요한 컬럼이 없는 경우
                else:
                    self.logger.warning("사용 데이터 파일에 필요한 컬럼(Rule Name과 미사용여부 또는 last_hit)이 없습니다.")
                    self.logger.info("기본 로직으로 미사용여부를 처리합니다.")
            
            # 2. df에 last_hit 컬럼이 있는 경우
            if 'last_hit' in df.columns:
                current_date = datetime.now()
                ninety_days_ago = current_date - timedelta(days=90)
                
                df['미사용여부'] = df['last_hit'].apply(
                    lambda x: '미사용' if pd.isnull(x) or pd.to_datetime(x, errors='coerce') < ninety_days_ago else '사용'
                )
                self.logger.info("정책 데이터의 last_hit 정보를 기반으로 미사용여부 정보가 추가되었습니다.")
            # 3. 기본값 설정 (모든 정책을 '미사용'으로 표시)
            else:
                self.logger.warning("사용 데이터가 없어 모든 정책을 '미사용'으로 표시합니다.")
                df['미사용여부'] = '미사용'
            
            return df
            
        except Exception as e:
            self.logger.error(f"사용 데이터 처리 중 오류 발생: {str(e)}")
            raise

    def process_vendor_specific(self, df: pd.DataFrame, vendor: str) -> pd.DataFrame:
        """벤더별 특화 처리
        
        Args:
            df: 처리할 정책 데이터프레임
            vendor: 벤더명 ('paloalto' 또는 'secui')
        """
        try:
            if vendor == 'paloalto':
                return self._process_paloalto(df)
            elif vendor == 'secui':
                return self._process_secui(df)
            else:
                raise ValueError(f"지원하지 않는 벤더입니다: {vendor}")
                
        except Exception as e:
            self.logger.error(f"벤더별 처리 중 오류 발생: {str(e)}")
            raise

    def _parse_request_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """정책 설명에서 신청 번호 파싱"""
        try:
            def convert_to_date(date_str):
                try:
                    if pd.isna(date_str):
                        return None
                    date_obj = datetime.strptime(str(date_str), '%Y%m%d')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    return date_str
            
            def parse_request_info(rulename, description):
                data_dict = {
                    "Request Type": "Unknown",
                    "REQUEST_ID": None,
                    "Ruleset ID": None,
                    "MIS ID": None,
                    "Request User": None,
                    "Start Date": convert_to_date('19000101'),
                    "End Date": convert_to_date('19000101'),
                }

                if pd.isnull(description):
                    return data_dict
                
                # 정규식 패턴 정의
                req_id_pattern = r'신청번호[:\s]*(\d{8,})'
                mis_id_pattern = r'MIS[:\s]*(\d{8,})'
                ruleset_pattern = r'RULESET[:\s]*(\d{8,})'
                user_pattern = r'신청자[:\s]*([^\s,;]+)'
                date_pattern = r'(\d{8})[\s~-]+(\d{8})'
                
                # 패턴 매칭
                req_id_match = re.search(req_id_pattern, str(description))
                mis_id_match = re.search(mis_id_pattern, str(description))
                ruleset_match = re.search(ruleset_pattern, str(description))
                user_match = re.search(user_pattern, str(description))
                date_match = re.search(date_pattern, str(description))
                
                # 결과 저장
                if req_id_match:
                    data_dict["REQUEST_ID"] = req_id_match.group(1)
                    data_dict["Request Type"] = "NORMAL"
                
                if mis_id_match:
                    data_dict["MIS ID"] = mis_id_match.group(1)
                    if data_dict["Request Type"] == "NORMAL":
                        data_dict["Request Type"] = "GROUP"
                
                if ruleset_match:
                    data_dict["Ruleset ID"] = ruleset_match.group(1)
                
                if user_match:
                    data_dict["Request User"] = user_match.group(1)
                
                if date_match:
                    data_dict["Start Date"] = convert_to_date(date_match.group(1))
                    data_dict["End Date"] = convert_to_date(date_match.group(2))
                
                return data_dict
            
            # 각 행에 대해 파싱 수행
            result_df = df.copy()
            for idx, row in result_df.iterrows():
                data = parse_request_info(row['Rule Name'], row['Description'])
                for key, value in data.items():
                    if pd.notna(value):  # None이 아닌 값만 업데이트
                        result_df.at[idx, key] = value
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"신청 번호 파싱 중 오류 발생: {str(e)}")
            raise

    def _get_auto_extension_ids(self, request_info_df: pd.DataFrame) -> pd.Series:
        """자동 연장 ID 추출"""
        try:
            return request_info_df[
                request_info_df['REQEUST_STATUS'].isin([98, 99])
            ]['REQUEST_ID'].drop_duplicates()
        except Exception as e:
            self.logger.error(f"자동 연장 ID 추출 중 오류 발생: {str(e)}")
            raise

    def _match_and_update_request_info(self, df: pd.DataFrame, 
                                     request_info: pd.DataFrame,
                                     auto_extension_ids: pd.Series) -> pd.DataFrame:
        """신청 정보 매칭 및 업데이트"""
        try:
            # 결과를 저장할 새 데이터프레임 생성
            result_df = df.copy()
            
            # 각 행에 대해 매칭 수행
            for idx, row in result_df.iterrows():
                if row['Request Type'] == 'GROUP':
                    # GROUP 타입에 대한 복잡한 매칭 로직
                    matched_row = request_info[
                        ((request_info['REQUEST_ID'] == row['REQUEST_ID']) & (request_info['MIS_ID'] == row['MIS ID'])) |
                        ((request_info['REQUEST_ID'] == row['REQUEST_ID']) & (request_info['REQUEST_END_DATE'] == row['End Date']) & (request_info['WRITE_PERSON_ID'] == row['Request User'])) |
                        ((request_info['REQUEST_ID'] == row['REQUEST_ID']) & (request_info['REQUEST_END_DATE'] == row['End Date']) & (request_info['REQUESTER_ID'] == row['Request User']))
                    ]
                else:
                    # 일반 타입에 대한 단순 매칭
                    matched_row = request_info[request_info['REQUEST_ID'] == row['REQUEST_ID']]
                
                # 매칭된 행이 있으면 해당 정보로 업데이트
                if not matched_row.empty:
                    for col in matched_row.columns:
                        if col in ['REQUEST_START_DATE', 'REQUEST_END_DATE', 'Start Date', 'End Date']:
                            result_df.at[idx, col] = pd.to_datetime(matched_row[col].values[0], errors='coerce')
                        else:
                            result_df.at[idx, col] = matched_row[col].values[0]
                # 매칭된 행이 없지만 Request Type이 있는 경우 기본값 설정
                elif row['Request Type'] not in ['nan', 'Unknown', None]:
                    result_df.at[idx, 'REQUEST_ID'] = row['REQUEST_ID']
                    result_df.at[idx, 'REQUEST_START_DATE'] = row['Start Date']
                    result_df.at[idx, 'REQUEST_END_DATE'] = row['End Date']
                    result_df.at[idx, 'REQUESTER_ID'] = row['Request User']
                    result_df.at[idx, 'REQUESTER_EMAIL'] = row['Request User'] + '@gmail.com' if pd.notna(row['Request User']) else None

            # 자동 연장 표시
            result_df.loc[result_df['REQUEST_ID'].isin(auto_extension_ids), 'REQUEST_STATUS'] = '99'
            result_df['자동연장'] = result_df['REQUEST_ID'].isin(auto_extension_ids)

            return result_df
            
        except Exception as e:
            self.logger.error(f"신청 정보 매칭 중 오류 발생: {str(e)}")
            raise

    def _update_usage_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """90일 기준으로 미사용 여부 업데이트"""
        try:
            current_date = datetime.now()
            ninety_days_ago = current_date - timedelta(days=90)
            
            df['미사용여부'] = df['last_hit'].apply(
                lambda x: '미사용' if pd.isnull(x) or pd.to_datetime(x) < ninety_days_ago else '사용'
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"사용 상태 업데이트 중 오류 발생: {str(e)}")
            raise

    def _process_paloalto(self, df: pd.DataFrame) -> pd.DataFrame:
        """팔로알토 정책 처리"""
        try:
            current_date = datetime.now()
            three_months_ago = current_date - timedelta(days=90)

            df["예외"] = ''

            # 1. 예외 신청정책 처리
            df['REQUEST_ID'] = df['REQUEST_ID'].fillna('')
            except_list = ['1', '2', '3']  # 예외 신청번호 리스트
            for id in except_list:
                df.loc[df['REQUEST_ID'].str.startswith(id, na=False), '예외'] = '예외신청정책'
            
            # 2. 자동연장정책 처리
            df.loc[df['REQUEST_STATUS'] == '99', '예외'] = '자동연장정책'

            # 3. 신규정책 처리
            df['날짜'] = df['Rule Name'].str.extract(r'(\d{8})', expand=False)
            df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d', errors='coerce')
            df.loc[(df['날짜'] >= three_months_ago) & (df['날짜'] <= current_date), '예외'] = '신규정책'

            # 4. 인프라정책 처리
            try:
                deny_std_rule_index = df[df['Rule Name'] == 'deny_rule'].index[0]
                df.loc[df.index < deny_std_rule_index, '예외'] = '인프라정책'
            except (IndexError, KeyError):
                # deny_rule이 없는 경우 인프라 키워드로 처리
                infra_keywords = ['인프라', 'infra', 'Infrastructure']
                df.loc[
                    df['Rule Name'].str.contains('|'.join(infra_keywords), case=False, na=False),
                    '예외'
                ] = '인프라정책'

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
                    if pd.isna(row['REQUEST_END_DATE']):
                        return '미만료'
                    end_date = pd.to_datetime(row['REQUEST_END_DATE'])
                    return '미만료' if end_date > current_date else '만료'
                except:
                    return '만료'
            
            df['만료여부'] = df.apply(check_date, axis=1)
            
            # 불필요한 컬럼 제거
            if '날짜' in df.columns:
                df.drop(columns=['날짜'], inplace=True)
                
            # 컬럼명 변경
            df.rename(columns={'Request Type': '신청이력'}, inplace=True)

            return df
            
        except Exception as e:
            self.logger.error(f"팔로알토 정책 처리 중 오류 발생: {str(e)}")
            raise

    def _process_secui(self, df: pd.DataFrame) -> pd.DataFrame:
        """시큐아이 정책 처리"""
        try:
            current_date = datetime.now()
            three_months_ago = current_date - timedelta(days=90)

            df["예외"] = ''

            # 1. 예외 신청정책 처리
            df['REQUEST_ID'] = df['REQUEST_ID'].fillna('')
            except_list = ['1', '2', '3']  # 예외 신청번호 리스트
            for id in except_list:
                df.loc[df['REQUEST_ID'].str.startswith(id, na=False), '예외'] = '예외신청정책'
            
            # 2. 자동연장정책 처리
            df.loc[df['REQUEST_STATUS'] == '99', '예외'] = '자동연장정책'

            # 4. 인프라정책 처리
            try:
                deny_std_rule_index = df[df['Description'].str.contains('deny_rule') == True].index[0]
                df.loc[df.index < deny_std_rule_index, '예외'] = '인프라정책'
            except (IndexError, KeyError):
                # deny_rule이 없는 경우 인프라 키워드로 처리
                infra_keywords = ['인프라', 'infra', 'Infrastructure']
                df.loc[
                    df['Description'].str.contains('|'.join(infra_keywords), case=False, na=False),
                    '예외'
                ] = '인프라정책'

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
                    if pd.isna(row['REQUEST_END_DATE']):
                        return '미만료'
                    end_date = pd.to_datetime(row['REQUEST_END_DATE'])
                    return '미만료' if end_date > current_date else '만료'
                except:
                    return '만료'
            
            df['만료여부'] = df.apply(check_date, axis=1)
            
            # 컬럼명 변경
            df.rename(columns={'Request Type': '신청이력'}, inplace=True)

            # 불필요한 컬럼 제거
            try:
                df.drop(columns=['Request ID', 'Ruleset ID', 'MIS ID', 'Request User', 'Start Date', 'End Date'], inplace=True, errors='ignore')
            except:
                pass

            # 컬럼 순서 재조정
            try:
                cols = list(df.columns)
                cols.insert(cols.index('예외') + 1, cols.pop(cols.index('만료여부')))
                df = df[cols]
                cols.insert(cols.index('예외') + 1, cols.pop(cols.index('신청이력')))
                df = df[cols]
            except:
                pass

            return df
            
        except Exception as e:
            self.logger.error(f"시큐아이 정책 처리 중 오류 발생: {str(e)}")
            raise 