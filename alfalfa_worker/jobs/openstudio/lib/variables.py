import json
from pathlib import Path

from alfalfa_worker.lib.enums import PointType
from alfalfa_worker.lib.models import Point, Run


class Variables:
    def __init__(self, run: Run) -> None:
        self.run = run
        self.points = {}
        self.points_path = run.dir / 'simulation' / 'points.json'
        if self.points_path.exists():
            with open(self.points_path, 'r') as fp:
                self.points = json.load(fp)

    def generate_points(self, alfalfa_json: Path) -> None:
        with open(alfalfa_json, 'r') as fp:
            points = json.load(fp)
            point_id_count = {}
            for point in points:
                id = point["id"]

                # Make IDs unique
                if id in point_id_count.keys():
                    point_id_count[id] = point_id_count[id] + 1
                    id = f"{id}_{point_id_count[id]}"

                # Set point type
                point_type = PointType.OUTPUT
                if "input" in point and "output" in point:
                    point_type = PointType.BIDIRECTIONAL
                elif "input" in point:
                    point_type = PointType.INPUT

                # Create point and add to Run
                run_point = Point(ref_id=id, point_type=point_type, name=point["name"])
                self.run.add_point(run_point)

                # Set value for "Constant" type points
                if "output" in point and point["output"]["type"] == "Constant":
                    run_point.value = point["output"]["parameters"]["value"]

                if "units" in point:
                    run_point.units = point["units"]

                self.points[id] = point
                if point["name"] == "Whole Building Electricity":
                    self.points[id]["output"]["multiplier"] = 1 / 60
                del self.points[id]["id"]

            self.run.save()

        with open(self.points_path, 'w') as fp:
            json.dump(self.points, fp)
