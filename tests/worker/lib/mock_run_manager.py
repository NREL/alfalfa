import shutil
from pathlib import Path
from typing import Dict, List

from alfalfa_worker.lib.logger_mixins import LoggerMixinBase
from alfalfa_worker.lib.point import Point
from alfalfa_worker.lib.run import Run
from alfalfa_worker.lib.run_manager import RunManager


class MockRunManager(RunManager, LoggerMixinBase):
    runs: Dict[str, Run] = {}

    def __init__(self, run_dir: Path, s3_dir: Path):
        self.run_dir = run_dir
        self.s3_dir = s3_dir
        self.tmp_dir = run_dir / 'tmp'
        LoggerMixinBase.__init__(self, "MockRunManager")

    def s3_download(self, key: str, file_path: str):
        src = self.s3_dir / key
        shutil.copy(src, file_path)

    def s3_upload(self, file_path: str, key: str):
        dest = self.s3_dir / key
        shutil.copy(file_path, dest)

    def register_run(self, run: Run):
        self.runs[run.id] = run

    def update_db(self, run: Run):
        pass

    def get_run(self, run_id: str) -> Run:
        return self.runs[run_id]

    def add_points_to_run(self, run: Run, points: List[Point]):
        self.runs[run.id].points = points
