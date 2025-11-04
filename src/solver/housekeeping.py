"""
Data safety and housekeeping utilities.
Manages temporary directories, disk space, and cleanup.
"""

import atexit
import signal
import shutil
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any


class TmpDirManager:
    """Manages per-run temporary directories with automatic cleanup."""
    
    def __init__(self, run_id: str, base_dir: Path = None):
        """
        Initialize temporary directory manager.
        
        Args:
            run_id: Unique identifier for the run
            base_dir: Base directory for temporary files (default: ./tmp)
        """
        self.run_id = run_id
        self.base_dir = base_dir or Path("tmp")
        self.tmp_dir = self.base_dir / f"run_{run_id}"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals and cleanup."""
        self.cleanup()
        exit(0)
    
    def cleanup(self):
        """Remove temporary directory and contents."""
        if self.tmp_dir.exists():
            try:
                shutil.rmtree(self.tmp_dir)
            except Exception as e:
                print(f"Warning: Failed to cleanup {self.tmp_dir}: {e}")
    
    def get_path(self, filename: str) -> Path:
        """Get path to a file in the temporary directory."""
        return self.tmp_dir / filename
    
    def write_file(self, filename: str, content: str):
        """Write content to a file in the temporary directory."""
        path = self.get_path(filename)
        path.write_text(content, encoding='utf-8')
    
    def read_file(self, filename: str) -> str:
        """Read content from a file in the temporary directory."""
        path = self.get_path(filename)
        return path.read_text(encoding='utf-8')


class DiskWatermark:
    """Monitor disk space and enforce watermarks."""
    
    def __init__(self, min_free_mb: float = 100.0, degraded_mb: float = 500.0):
        """
        Initialize disk watermark monitor.
        
        Args:
            min_free_mb: Minimum free space in MB (below this, operations pause)
            degraded_mb: Degraded mode threshold in MB
        """
        self.min_free_mb = min_free_mb
        self.degraded_mb = degraded_mb
        self.degraded_mode = False
    
    def check_space(self, path: Path = Path.cwd()) -> Dict[str, Any]:
        """
        Check available disk space.
        
        Returns:
            Dictionary with space info and status
        """
        stat = shutil.disk_usage(path)
        free_mb = stat.free / (1024 * 1024)
        
        status = {
            'free_mb': free_mb,
            'total_mb': stat.total / (1024 * 1024),
            'used_mb': stat.used / (1024 * 1024),
            'can_write': free_mb >= self.min_free_mb,
            'degraded': free_mb < self.degraded_mb
        }
        
        if status['degraded'] and not self.degraded_mode:
            self.degraded_mode = True
            print(f"WARNING: Entering degraded mode - low disk space ({free_mb:.2f} MB free)")
        elif not status['degraded'] and self.degraded_mode:
            self.degraded_mode = False
            print(f"INFO: Exiting degraded mode - sufficient disk space ({free_mb:.2f} MB free)")
        
        return status
    
    def ensure_space(self, path: Path = Path.cwd()) -> bool:
        """
        Ensure sufficient disk space is available.
        
        Returns:
            True if sufficient space, False otherwise
        """
        status = self.check_space(path)
        return status['can_write']


def export_topk(results: List[Dict[str, Any]], output_path: Path):
    """
    Export top-K results to JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by profit descending
    sorted_results = sorted(results, key=lambda x: x.get('profit', 0), reverse=True)
    
    output = {
        'timestamp': time.time(),
        'count': len(sorted_results),
        'results': sorted_results
    }
    
    output_path.write_text(json.dumps(output, indent=2), encoding='utf-8')


def export_run_summary(run_data: Dict[str, Any], output_path: Path):
    """
    Export run summary to JSON file.
    
    Args:
        run_data: Run metadata and results
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        'timestamp': time.time(),
        'run_id': run_data.get('run_id'),
        'strategy': run_data.get('strategy'),
        'K': run_data.get('K'),
        'duration': run_data.get('duration'),
        'terminal_states_count': run_data.get('terminal_states_count'),
        'timed_out': run_data.get('timed_out', False),
        'best_profit': run_data.get('best_profit'),
        'best_path': run_data.get('best_path'),
        'constraints': run_data.get('constraints', {})
    }
    
    output_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')


def export_metrics(metrics: List[Dict[str, Any]], output_path: Path):
    """
    Export metrics to JSONL file (one JSON object per line).
    
    Args:
        metrics: List of metric dictionaries
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open('w', encoding='utf-8') as f:
        for metric in metrics:
            f.write(json.dumps(metric) + '\n')


def clean_tmp_dirs(base_dir: Path = Path("tmp"), keep_recent: int = 0):
    """
    Clean up temporary directories.
    
    Args:
        base_dir: Base directory containing tmp dirs
        keep_recent: Number of recent directories to keep (0 = remove all)
    
    Returns:
        Number of directories removed
    """
    if not base_dir.exists():
        return 0
    
    # Get all run directories
    run_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('run_')],
                     key=lambda d: d.stat().st_mtime, reverse=True)
    
    # Keep recent ones
    to_remove = run_dirs[keep_recent:] if keep_recent > 0 else run_dirs
    
    removed = 0
    for dir_path in to_remove:
        try:
            shutil.rmtree(dir_path)
            removed += 1
        except Exception as e:
            print(f"Warning: Failed to remove {dir_path}: {e}")
    
    return removed


def clean_runs_dir(runs_dir: Path = Path("runs"), older_than_days: Optional[int] = None):
    """
    Clean up old run files and checkpoints.
    
    Args:
        runs_dir: Directory containing run files
        older_than_days: Remove files older than this many days (None = keep all)
    
    Returns:
        Number of files removed
    """
    if not runs_dir.exists():
        return 0
    
    cutoff_time = time.time() - (older_than_days * 86400) if older_than_days else 0
    
    removed = 0
    for file_path in runs_dir.iterdir():
        if file_path.is_file():
            if older_than_days is None or file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as e:
                    print(f"Warning: Failed to remove {file_path}: {e}")
    
    return removed


def get_dir_size(dir_path: Path) -> float:
    """
    Calculate total size of a directory in MB.
    
    Args:
        dir_path: Directory to measure
    
    Returns:
        Size in MB
    """
    if not dir_path.exists():
        return 0.0
    
    total = 0
    for entry in dir_path.rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    
    return total / (1024 * 1024)
