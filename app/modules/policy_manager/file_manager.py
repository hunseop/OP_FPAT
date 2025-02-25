import logging
from pathlib import Path
from typing import Union, List, Optional
import pandas as pd
import shutil
from datetime import datetime

class FileManager:
    """파일 관리 클래스"""
    
    def __init__(self, output_dir: str = None):
        """
        Args:
            output_dir: 결과 파일을 저장할 디렉토리 경로
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / 'output'
        self.ensure_directory(self.output_dir)
        
        # 중간 결과물 저장 디렉토리
        self.intermediate_dir = self.output_dir / 'intermediate'
        self.ensure_directory(self.intermediate_dir)
        
        # 보고서 저장 디렉토리
        self.reports_dir = self.output_dir / 'reports'
        self.ensure_directory(self.reports_dir)
        
        # 백업 디렉토리
        self.backup_dir = self.output_dir / 'backup'
        self.ensure_directory(self.backup_dir)
        
        # 파일 저장 이력
        self.saved_files = {
            'intermediate': [],
            'reports': [],
            'backup': []
        }
    
    def ensure_directory(self, directory_path: Union[str, Path]) -> Path:
        """디렉토리가 존재하는지 확인하고, 없으면 생성
        
        Args:
            directory_path: 확인할 디렉토리 경로
            
        Returns:
            생성된 디렉토리 경로
        """
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def save_dataframe(self, df: pd.DataFrame, filename_prefix: str, 
                       directory: str = 'intermediate', include_timestamp: bool = True) -> str:
        """데이터프레임을 엑셀 파일로 저장
        
        Args:
            df: 저장할 데이터프레임
            filename_prefix: 파일명 접두사
            directory: 저장할 디렉토리 ('intermediate', 'reports', 'backup')
            include_timestamp: 파일명에 타임스탬프 포함 여부
            
        Returns:
            저장된 파일 경로
        """
        if directory not in ['intermediate', 'reports', 'backup']:
            raise ValueError(f"지원되지 않는 디렉토리: {directory}")
        
        # 저장 디렉토리 선택
        if directory == 'intermediate':
            save_dir = self.intermediate_dir
        elif directory == 'reports':
            save_dir = self.reports_dir
        else:
            save_dir = self.backup_dir
        
        # 파일명 생성
        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_prefix}_{timestamp}.xlsx"
        else:
            filename = f"{filename_prefix}.xlsx"
        
        # 파일 저장
        file_path = save_dir / filename
        df.to_excel(file_path, index=False)
        
        # 저장 이력 업데이트
        self.saved_files[directory].append(str(file_path))
        
        self.logger.info(f"파일 저장 완료: {file_path}")
        return str(file_path)
    
    def load_dataframe(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """엑셀 파일에서 데이터프레임 로드
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            로드된 데이터프레임
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            df = pd.read_excel(path)
            self.logger.info(f"파일 로드 완료: {file_path}")
            return df
        except Exception as e:
            self.logger.error(f"파일 로드 중 오류 발생: {str(e)}")
            raise
    
    def backup_file(self, file_path: Union[str, Path], backup_prefix: str = None) -> str:
        """파일 백업
        
        Args:
            file_path: 백업할 파일 경로
            backup_prefix: 백업 파일명 접두사 (기본값: 원본 파일명)
            
        Returns:
            백업된 파일 경로
        """
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"백업할 파일을 찾을 수 없습니다: {file_path}")
        
        # 백업 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_prefix = backup_prefix or source_path.stem
        backup_filename = f"{backup_prefix}_backup_{timestamp}{source_path.suffix}"
        
        # 백업 파일 저장
        backup_path = self.backup_dir / backup_filename
        shutil.copy2(source_path, backup_path)
        
        # 백업 이력 업데이트
        self.saved_files['backup'].append(str(backup_path))
        
        self.logger.info(f"파일 백업 완료: {source_path} -> {backup_path}")
        return str(backup_path)
    
    def get_latest_file(self, directory: str = 'intermediate', prefix: str = None) -> Optional[str]:
        """최신 파일 경로 반환
        
        Args:
            directory: 검색할 디렉토리 ('intermediate', 'reports', 'backup')
            prefix: 파일명 접두사 필터
            
        Returns:
            최신 파일 경로 또는 None
        """
        if directory not in ['intermediate', 'reports', 'backup']:
            raise ValueError(f"지원되지 않는 디렉토리: {directory}")
        
        # 디렉토리 선택
        if directory == 'intermediate':
            search_dir = self.intermediate_dir
        elif directory == 'reports':
            search_dir = self.reports_dir
        else:
            search_dir = self.backup_dir
        
        # 파일 검색
        files = list(search_dir.glob(f"{prefix or ''}*.xlsx"))
        if not files:
            return None
        
        # 최신 파일 반환
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        return str(latest_file)
    
    def list_files(self, directory: str = 'intermediate', prefix: str = None) -> List[str]:
        """디렉토리 내 파일 목록 반환
        
        Args:
            directory: 검색할 디렉토리 ('intermediate', 'reports', 'backup')
            prefix: 파일명 접두사 필터
            
        Returns:
            파일 경로 목록
        """
        if directory not in ['intermediate', 'reports', 'backup']:
            raise ValueError(f"지원되지 않는 디렉토리: {directory}")
        
        # 디렉토리 선택
        if directory == 'intermediate':
            search_dir = self.intermediate_dir
        elif directory == 'reports':
            search_dir = self.reports_dir
        else:
            search_dir = self.backup_dir
        
        # 파일 검색
        files = list(search_dir.glob(f"{prefix or ''}*.xlsx"))
        return [str(file) for file in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)]
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """파일 삭제
        
        Args:
            file_path: 삭제할 파일 경로
            
        Returns:
            삭제 성공 여부
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.warning(f"삭제할 파일이 존재하지 않습니다: {file_path}")
            return False
        
        try:
            path.unlink()
            
            # 저장 이력에서 제거
            for directory in self.saved_files:
                if str(file_path) in self.saved_files[directory]:
                    self.saved_files[directory].remove(str(file_path))
            
            self.logger.info(f"파일 삭제 완료: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"파일 삭제 중 오류 발생: {str(e)}")
            return False
    
    def clean_directory(self, directory: str = 'intermediate', keep_latest: int = 5) -> int:
        """디렉토리 정리 (오래된 파일 삭제)
        
        Args:
            directory: 정리할 디렉토리 ('intermediate', 'reports', 'backup')
            keep_latest: 유지할 최신 파일 수
            
        Returns:
            삭제된 파일 수
        """
        if directory not in ['intermediate', 'reports', 'backup']:
            raise ValueError(f"지원되지 않는 디렉토리: {directory}")
        
        # 디렉토리 선택
        if directory == 'intermediate':
            search_dir = self.intermediate_dir
        elif directory == 'reports':
            search_dir = self.reports_dir
        else:
            search_dir = self.backup_dir
        
        # 파일 목록 가져오기
        files = list(search_dir.glob("*.xlsx"))
        files.sort(key=lambda x: x.stat().st_mtime)
        
        # 오래된 파일 삭제
        files_to_delete = files[:-keep_latest] if len(files) > keep_latest else []
        deleted_count = 0
        
        for file in files_to_delete:
            if self.delete_file(file):
                deleted_count += 1
        
        self.logger.info(f"{directory} 디렉토리 정리 완료: {deleted_count}개 파일 삭제")
        return deleted_count 