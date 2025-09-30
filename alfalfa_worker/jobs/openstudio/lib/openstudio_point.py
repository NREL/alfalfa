from dataclasses import dataclass

from alfalfa_worker.jobs.openstudio.lib.openstudio_component import (
    OpenStudioComponent
)
from alfalfa_worker.lib.enums import PointType
from alfalfa_worker.lib.job_exception import JobException
from alfalfa_worker.lib.models import Point, Run


@dataclass
class OpenStudioPoint:
    id: str
    name: str
    optional: bool = False
    units: str = None
    input: OpenStudioComponent = None
    output: OpenStudioComponent = None
    point: Point = None

    def __init__(self, id: str, name: str, optional: bool = False, units: str = None, input: dict = None, output: dict = None):
        self.id = id
        self.name = name
        self.optional = optional
        self.units = units
        self.input = OpenStudioComponent(**input) if input else None
        self.output = OpenStudioComponent(**output) if output else None

    def create_point(self):
        point_type = PointType.OUTPUT
        if self.input is not None:
            if self.output is not None:
                point_type = PointType.BIDIRECTIONAL
            else:
                point_type = PointType.INPUT

        self.point = Point(ref_id=self.id, point_type=point_type, name=self.name)
        if self.units is not None:
            self.point.units = self.units

    def attach_run(self, run: Run):
        if self.point is None:
            self.create_point()

        conflicting_points = Point.objects(ref_id=self.point.ref_id, run=run)
        needs_rename = len(conflicting_points) > 0
        if len(conflicting_points) == 1:
            needs_rename = not (conflicting_points[0] == self.point)

        if needs_rename:
            self.point.ref_id = self.point.ref_id + "_1"
            return self.attach_run(run)
        else:
            run.add_point(self.point)

    def pre_initialize(self, api, state):
        if self.input:
            self.input.pre_initialize(api, state)

        if self.output:
            self.output.pre_initialize(api, state)

    def initialize(self, api, state):
        try:
            if self.input:
                self.input.initialize(api, state)

            if self.output:
                self.output.initialize(api, state)
        except JobException as e:
            if self.optional:
                self.disable()
            else:
                raise e

    def disable(self):
        if self.point:
            if self.point.run:
                self.point.run = None

    def update_input(self, api, state):
        if self.input:
            self.input.write_value(api, state, self.point.value)

    def update_output(self, api, state) -> float:
        if self.output:
            value = self.output.read_value(api, state)
            if self.point:
                self.point.value = value
                return value
        return None
