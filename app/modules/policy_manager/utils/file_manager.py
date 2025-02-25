import logging
from datetime import datetime
from pathlib import Path
import shutil
import re

class FileManager:
    """파일 관리를 담당하는 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def update_version(self, file_path: str, final_version: bool = False) -> str:
        """파일 버전 업데이트
        
        Args:
            file_path: 파일 경로
            final_version: 최종 버전 여부
            
        Returns:
            업데이트된 파일 경로
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return file_path
            
            # 파일명과 확장자 분리
            stem = path.stem
            suffix = path.suffix
            
            # 버전 패턴 확인
            version_pattern = r'_v(\d+)$'
            match = re.search(version_pattern, stem)
            
            if match:
                # 기존 버전 번호 증가
                current_version = int(match.group(1))
                new_version = current_version + 1
                new_stem = re.sub(version_pattern, f'_v{new_version}', stem)
            else:
                # 새로운 버전 추가
                new_stem = f"{stem}_v1"
            
            # 최종 버전인 경우 '_final' 추가
            if final_version:
                new_stem = f"{new_stem}_final"
            
            new_path = path.with_name(f"{new_stem}{suffix}")
            
            return str(new_path)
            
        except Exception as e:
            self.logger.error(f"파일 버전 업데이트 중 오류 발생: {str(e)}")
            raise

    def backup_file(self, file_path: str) -> str:
        """파일 백업
        
        Args:
            file_path: 백업할 파일 경로
            
        Returns:
            백업 파일 경로
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return None
            
            # 백업 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = path.with_name(f"{path.stem}_backup_{timestamp}{path.suffix}")
            
            # 파일 복사
            shutil.copy2(path, backup_path)
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"파일 백업 중 오류 발생: {str(e)}")
            raise

    def cleanup_temp_files(self, directory: str, pattern: str = '*_v[0-9]*.*', days: int = 7) -> None:
        """임시 파일 정리
        
        Args:
            directory: 정리할 디렉토리 경로
            pattern: 파일 패턴
            days: 보관 기간(일)
        """
        try:
            path = Path(directory)
            
            if not path.exists():
                return
            
            current_time = datetime.now()
            
            # 패턴에 맞는 파일 검색
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    # 파일 수정 시간 확인
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    # 지정된 기간보다 오래된 파일 삭제
                    if (current_time - mtime).days > days:
                        file_path.unlink()
            
        except Exception as e:
            self.logger.error(f"임시 파일 정리 중 오류 발생: {str(e)}")
            raise

    def ensure_directory(self, directory: str) -> None:
        """디렉토리 존재 확인 및 생성
        
        Args:
            directory: 생성할 디렉토리 경로
        """
        try:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"디렉토리 생성 중 오류 발생: {str(e)}")
            raise 