"""
File Archiver

A tool for organizing and archiving files based on type, date, and other criteria.
Supports deduplication, metadata extraction, and customizable organization rules.
"""

import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import logging
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Data class for storing file information"""
    path: Path
    size: int
    created_time: datetime
    modified_time: datetime
    file_type: str
    hash: str = ""

@dataclass
class ArchiveStats:
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    duplicates: int = 0
    total_size: int = 0
    by_type: Dict[str, int] = None

class FileArchiver:
    """Main class for file archiving operations"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the file archiver with configuration
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.source_dirs = [Path(p).expanduser() for p in self.config['source_directories']]
        self.target_dir = Path(self.config['target_directory']).expanduser()
        self.file_types = self.config['file_types']
        
        # Set up logging based on config
        self._setup_logging(
            level=self.config['logging']['level'],
            log_file=self.config['logging']['file']
        )
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Validate required fields
            required_fields = [
                'source_directories',
                'target_directory',
                'organization',
                'file_types',
                'logging',
                'backup',
                'processing'
            ]
            
            # Validate required sub-fields
            if 'organization' in config:
                required_org_fields = ['by_date', 'remove_duplicates']
                for field in required_org_fields:
                    if field not in config['organization']:
                        raise KeyError(f"Missing required field in organization: {field}")
            
            if 'backup' in config:
                required_backup_fields = ['enabled', 'keep_original', 'verify_copy']
                for field in required_backup_fields:
                    if field not in config['backup']:
                        raise KeyError(f"Missing required field in backup: {field}")
            
            if 'logging' in config:
                required_logging_fields = ['level', 'file']
                for field in required_logging_fields:
                    if field not in config['logging']:
                        raise KeyError(f"Missing required field in logging: {field}")
            
            for field in required_fields:
                if field not in config:
                    raise KeyError(f"Missing required field in config: {field}")
                    
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {config_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _setup_logging(self, level: str = "INFO", log_file: str = "file_archiver.log"):
        """Configure logging settings from config"""
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get_file_info(self, file_path: Path) -> FileInfo:
        """Get detailed information about a file"""
        stats = file_path.stat()
        return FileInfo(
            path=file_path,
            size=stats.st_size,
            created_time=datetime.fromtimestamp(stats.st_ctime),
            modified_time=datetime.fromtimestamp(stats.st_mtime),
            file_type=self._get_file_type(file_path.suffix.lower())
        )
    
    def _get_file_type(self, extension: str) -> str:
        """Determine file type based on extension"""
        for file_type, extensions in self.file_types.items():
            if extension in extensions:
                return file_type
        return 'others'
    
    def scan_files(self) -> List[FileInfo]:
        """Scan source directories for files"""
        files = []
        
        for source_dir in self.source_dirs:
            logger.info(f"Scanning directory: {source_dir}")
            try:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        files.append(self.get_file_info(file_path))
                
            except Exception as e:
                logger.error(f"Error scanning directory {source_dir}: {str(e)}")
                continue
        
        logger.info(f"Found {len(files)} files in total")
        return files
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def organize_files(self):
        """Organize files according to configuration"""
        files = self.scan_files()
        total = len(files)
        processed = 0
        processed_hashes = {}  # Dictionary to store hash values and their corresponding first file path
        
        # Initialize statistics
        stats = ArchiveStats(
            total_files=total,
            by_type={}
        )
        
        logger.info(f"Starting to process {total} files...")
        
        for file_info in files:
            try:
                # Update file type statistics
                stats.by_type[file_info.file_type] = stats.by_type.get(file_info.file_type, 0) + 1
                stats.total_size += file_info.size
                
                # Check for duplicates if enabled
                if self.config['organization']['remove_duplicates']:
                    file_hash = self.get_file_hash(file_info.path)
                    if file_hash in processed_hashes:
                        original_file = processed_hashes[file_hash]
                        logger.info(f"Found duplicate file: {file_info.path} is identical to {original_file}")
                        stats.duplicates += 1
                        continue
                    processed_hashes[file_hash] = str(file_info.path)
                
                # Determine target path based on configuration
                if self.config['organization']['by_date']:
                    date_path = f"{file_info.created_time.year}/{file_info.created_time.month:02d}"
                    target_path = self.target_dir / file_info.file_type / date_path
                else:
                    target_path = self.target_dir / file_info.file_type
                
                # Create directory and handle file
                target_path.mkdir(parents=True, exist_ok=True)
                
                # Generate unique filename
                target_filename = self._generate_unique_filename(target_path, file_info.path.name)
                target_file = target_path / target_filename
                
                if self.config['backup']['enabled']:
                    if self._safe_copy(file_info.path, target_file):
                        logger.info(f"Copied {file_info.path} to {target_file}")
                        stats.processed_files += 1
                        
                        if not self.config['backup']['keep_original']:
                            file_info.path.unlink()
                            logger.info(f"Removed original file: {file_info.path}")
                    else:
                        stats.failed_files += 1
                
                processed += 1
                if processed % 10 == 0:  # Show progress every 10 files
                    logger.info(f"Progress: {processed}/{total} ({processed/total*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error processing {file_info.path}: {str(e)}")
                stats.failed_files += 1
        
        # Generate and display report
        report = self.generate_report(stats)
        logger.info("\n" + report)
    
    def _generate_unique_filename(self, target_path: Path, original_name: str) -> str:
        """Generate a unique filename to avoid conflicts"""
        name = Path(original_name).stem
        suffix = Path(original_name).suffix
        counter = 1
        new_name = original_name
        
        while (target_path / new_name).exists():
            new_name = f"{name}_{counter}{suffix}"
            counter += 1
        
        return new_name
    
    def verify_file_integrity(self, source_path: Path, target_path: Path) -> bool:
        """Verify file integrity using MD5 hash"""
        source_hash = self.get_file_hash(source_path)
        target_hash = self.get_file_hash(target_path)
        return source_hash == target_hash
    
    def _safe_copy(self, source: Path, target: Path) -> bool:
        """Safe file copy with verification and error recovery"""
        try:
            # Create temporary file
            temp_target = target.with_suffix(target.suffix + '.tmp')
            shutil.copy2(source, temp_target)
            
            # Verify integrity
            if self.verify_file_integrity(source, temp_target):
                temp_target.rename(target)
                return True
            else:
                temp_target.unlink()
                logger.error(f"File integrity verification failed: {source}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to copy file {source}: {str(e)}")
            if temp_target.exists():
                temp_target.unlink()
            return False
    
    def generate_report(self, stats: ArchiveStats):
        """Generate archiving report"""
        report = [
            "Archiving Report",
            f"Total files: {stats.total_files}",
            f"Successfully processed: {stats.processed_files}",
            f"Failed: {stats.failed_files}",
            f"Duplicates: {stats.duplicates}",
            f"Total size: {stats.total_size / (1024*1024):.2f} MB",
            "\nBy file type:",
        ]
        
        for file_type, count in stats.by_type.items():
            report.append(f"- {file_type}: {count}")
        
        return "\n".join(report)
    
    def _validate_config(self, config: dict) -> None:
        """Validate configuration validity"""
        # Validate path existence
        for source_dir in config['source_directories']:
            path = Path(source_dir).expanduser()
            if not path.exists():
                raise ValueError(f"Source directory does not exist: {source_dir}")
        
        # Validate target directory permissions
        target_path = Path(config['target_directory']).expanduser()
        if target_path.exists() and not os.access(target_path, os.W_OK):
            raise ValueError(f"No write permission for target directory: {target_path}")

def main():
    """Main function"""
    try:
        archiver = FileArchiver()
        archiver.organize_files()
        logger.info("File organization completed successfully")
    except Exception as e:
        logger.error(f"File organization failed: {str(e)}")
        return 1
    return 0

if __name__ == '__main__':
    exit(main()) 