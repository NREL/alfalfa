

import json
import os
from subprocess import call

from alfalfa_worker.lib.job import Job, JobExceptionInvalidModel
from alfalfa_worker.lib.logger_mixins import AddSiteLoggerMixin
from alfalfa_worker.lib.point import Point, PointType
from alfalfa_worker.lib.tagutils import make_ids_unique, replace_site_id
from alfalfa_worker.lib.utils import rel_symlink


class CreateRun(AddSiteLoggerMixin, Job):

    def __init__(self, upload_id, model_name):
        super().__init__()
        self.run = self.create_run(upload_id, model_name)
        # self.logger.info("starting job")

    def exec(self):
        osws = self.run.glob("**/*.osw")
        if osws:
            # there is only support for one osw at this time
            submitted_osw_path = osws[0]
            submitted_workflow_path = os.path.dirname(submitted_osw_path)
        else:
            raise JobExceptionInvalidModel("No .osw file found")

        # locate the "default" workflow
        default_workflow_path: str = '/alfalfa/alfalfa_worker/worker_openstudio/lib/workflow/workflow.osw'

        # Merge the default workflow measures into the user submitted workflow
        call(['openstudio', '/alfalfa/alfalfa_worker/worker_openstudio/lib/merge_osws.rb', default_workflow_path, submitted_osw_path])

        # run workflow
        call(['openstudio', 'run', '-m', '-w', submitted_osw_path])

        points_json_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_haystack.json')
        mapping_json_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_mapping.json')
        self.insert_os_tags(points_json_path, mapping_json_path)

        # create a "simulation" directory that has everything required for simulation
        simulation_dir = self.join('simulation/')
        os.mkdir(simulation_dir)

        idf_src_path = os.path.join(submitted_workflow_path, 'run/in.idf')
        idf_dest_path = os.path.join(simulation_dir, 'sim.idf')
        rel_symlink(idf_src_path, idf_dest_path)

        haystack_src_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_mapping.json')
        haystack_dest_path = os.path.join(simulation_dir, 'haystack_report_mapping.json')
        rel_symlink(haystack_src_path, haystack_dest_path)

        haystack_src_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_haystack.json')
        haystack_dest_path = os.path.join(simulation_dir, 'haystack_report_haystack.json')
        rel_symlink(haystack_src_path, haystack_dest_path)

        variables_src_path = os.path.join(submitted_workflow_path, 'reports/export_bcvtb_report_variables.cfg')
        variables_dest_path = os.path.join(simulation_dir, 'variables.cfg')
        rel_symlink(variables_src_path, variables_dest_path)

        # variables.cfg also needs to be located next to the idf to satisfy EnergyPlus conventions
        idf_src_dir = os.path.dirname(idf_src_path)
        variables_ep_path = os.path.join(idf_src_dir, 'variables.cfg')
        rel_symlink(variables_src_path, variables_ep_path)

        # hack. need to find a more general approach to preserve osw resources that might be needed at simulation time
        for file in self.run.glob(submitted_workflow_path + '/python/*'):
            idfdir = os.path.dirname(idf_src_path)
            filename = os.path.basename(file)
            dst = os.path.join(idfdir, filename)
            rel_symlink(file, dst)

        # find weather file (if) defined by osw and copy into simulation directory
        with open(submitted_osw_path, 'r') as osw:
            data = osw.read()
        submitted_osw = json.loads(data)

        epw_name = submitted_osw['weather_file']
        if epw_name:
            epw_src_path = self.run.glob(os.path.join(submitted_workflow_path, '**', epw_name))[0]
            epw_dst_path = os.path.join(simulation_dir, 'sim.epw')
            rel_symlink(epw_src_path, epw_dst_path)

        self.logger.info("checking in run")
        self.checkin_run(self.run)

        # Should the default behavior be to stop the job after running the `exec` function?
        # or to start spinning the message handler
        self.logger.info("trying to stop")
        self.stop()

    def insert_os_tags(self, points_json_path, mapping_json_path):
        """
        Make unique ids and replace site_id.  Upload to mongo and filestore.
        :return:
        """
        # load mapping and points json files generated by previous workflow
        with open(points_json_path, 'r') as f:
            data = f.read()
        points_json = json.loads(data)

        with open(mapping_json_path, 'r') as f:
            data = f.read()
        mapping_json = json.loads(data)

        # fixup tags
        # This is important to avoid duplicates in the case when a client submits the same model
        # more than one time
        points_json, mapping_json = make_ids_unique(points_json, mapping_json)
        points_json = replace_site_id(self.run.id, points_json)
        points = []
        for json_point in points_json:
            point = Point(json_point['dis'], PointType.BIDIRECTIONAL, json_point, json_point['id'].replace('r:', ''))
            points.append(point)
            self.logger.info(point)

        # save "fixed up" json
        with open(points_json_path, 'w') as fp:
            json.dump(points_json, fp)

        with open(mapping_json_path, 'w') as fp:
            json.dump(mapping_json, fp)

        # add points to database
        self.add_points(self.run, points)
