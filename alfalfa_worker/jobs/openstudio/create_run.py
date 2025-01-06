import json
import os
from pathlib import Path

from alfalfa_worker.jobs.openstudio import lib_dir
from alfalfa_worker.lib.enums import RunStatus, SimType
from alfalfa_worker.lib.job import Job, JobExceptionInvalidModel
from alfalfa_worker.lib.utils import rel_symlink


class CreateRun(Job):

    def __init__(self, model_id, run_id=None):
        self.create_run_from_model(model_id, SimType.OPENSTUDIO, run_id=run_id)

    def exec(self):
        self.set_run_status(RunStatus.PREPROCESSING)
        osws = self.run.glob("**/*.osw")
        if osws:
            # there is only support for one osw at this time
            submitted_osw_path = osws[0]
            submitted_workflow_path = Path(os.path.dirname(submitted_osw_path))
        else:
            raise JobExceptionInvalidModel("No .osw file found")

        # create a "simulation" directory that has everything required for simulation
        simulation_dir = self.dir / 'simulation'
        simulation_dir.mkdir()

        # If there are requirements.txt files in the model create a python virtual environment and install packaged there
        requirements = self.run.glob("**/requirements.txt")
        if len(requirements) > 0:
            self.log_subprocess(["python3.12", "-m", "venv", "--system-site-packages", "--symlinks", str(self.dir / '.venv')])
            for requirements_file in requirements:
                self.log_subprocess([str(self.dir / '.venv' / 'bin' / 'pip'), "install", "-r", str(requirements_file)])

        # locate the "default" workflow
        default_workflow_path: str = lib_dir / 'workflow/workflow.osw'

        # Merge the default workflow measures into the user submitted workflow
        self.log_subprocess(['openstudio', str(lib_dir / 'merge_osws.rb'), str(default_workflow_path), str(submitted_osw_path)])

        # run workflow
        self.log_subprocess(['openstudio', '--verbose', 'run', '--show-stdout', '-m', '-w', str(submitted_osw_path)])

        self.logger.info('Loading Building Metadata')
        metadata_json_path = submitted_workflow_path / 'reports' / 'alfalfa_metadata_report_metadata.json'
        if metadata_json_path.exists():
            self.load_metadata(metadata_json_path)
        else:
            self.logger.info('Could not find Alfalfa Metadata Report')

        self.logger.info("Setting up symlinks")
        idf_src_path = submitted_workflow_path / 'run' / 'in.idf'
        idf_dest_path = simulation_dir / 'sim.idf'
        rel_symlink(idf_src_path, idf_dest_path)

        # hack. need to find a more general approach to preserve osw resources that might be needed at simulation time
        for file in self.run.glob(submitted_workflow_path / 'python' / '*'):
            idfdir = idf_src_path.parents[0]
            filename = os.path.basename(file)
            dst = idfdir / filename
            rel_symlink(file, dst)

        # find weather file (if) defined by osw and copy into simulation directory
        with open(submitted_osw_path, 'r') as osw:
            data = osw.read()
        submitted_osw = json.loads(data)

        epw_name = submitted_osw['weather_file']
        if epw_name:
            epw_src_path = self.run.glob(submitted_workflow_path / '**' / epw_name)[0]
            epw_dst_path = simulation_dir / 'sim.epw'
            rel_symlink(epw_src_path, epw_dst_path)

    def validate(self) -> None:
        assert (self.dir / 'simulation' / 'sim.idf').exists(), "Idf was not created"
        assert (self.dir / 'simulation' / 'sim.epw').exists(), "Weather file was not created"

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.READY)

    def load_metadata(self, metadata_json: Path):
        with open(metadata_json) as fp:
            metadata_dict = json.load(fp)
            if 'building_name' in metadata_dict:
                self.run.name = metadata_dict['building_name']
                self.run.save()
