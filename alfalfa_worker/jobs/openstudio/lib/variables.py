import json
from os import PathLike
from pathlib import Path
from typing import List

from alfalfa_worker.lib.enums import PointType
from alfalfa_worker.lib.models import Point, Run


class Variables:
    def __init__(self, run: Run) -> None:
        self.run = run
        self.points = self._load_json('**/points.json')

    def _load_json(self, glob: str) -> List:
        result = {}
        files = self.run.glob(glob)
        for file in files:
            with open(str(file), 'r') as fp:
                result.update(json.load(fp))

        return result

    def load_reports(self):
        self.points = self._load_json('**/*_report_points.json')

    def write_files(self, dir_name: PathLike):
        dir = Path(dir_name)
        points_file = dir / 'points.json'

        with points_file.open('w') as fp:
            json.dump(self.points, fp)

    def generate_points(self):
        for id, point in self.points.items():
            point = Point(ref_id=id, point_type=PointType.OUTPUT, name=point["display_name"])
            if "input" in point and "output" in point:
                point.point_type = PointType.BIDIRECTIONAL
            elif "input" in point:
                point.point_type = PointType.INPUT
            self.run.add_point(point)

        self.run.save()
