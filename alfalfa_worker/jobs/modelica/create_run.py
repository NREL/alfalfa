from pathlib import Path

from alfalfa_worker.lib.enums import RunStatus, SimType
from alfalfa_worker.lib.job import Job


class CreateRun(Job):

    def __init__(self, model_id, run_id=None):
        self.create_run_from_model(model_id, SimType.MODELICA, run_id=run_id)

        model_name = self.run.model.model_name

        # Define FMU specific attributes
        self.upload_fmu: Path = self.dir / model_name
        self.fmu_path = self.dir / 'model.fmu'
        self.model_name = model_name

        # Needs to be set after files are uploaded / parsed.
        self.site_ref = None

    def exec(self):
        self.set_run_status(RunStatus.PREPROCESSING)
        """
        Workflow for fmu.  External call to python2 must be made since currently we are using an
        old version of the Modelica Buildings Library and JModelica.
        :return:
        """
        self.logger.info("add_fmu for {}".format(self.run.ref_id))

        self.upload_fmu.rename(self.fmu_path)

    def validate(self) -> None:
        assert (self.dir / 'model.fmu').exists(), "model file not created"

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.READY)
