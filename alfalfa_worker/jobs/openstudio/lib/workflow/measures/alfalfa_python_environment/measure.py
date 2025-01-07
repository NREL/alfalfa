"""insert your copyright here.

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/
"""

import os
from pathlib import Path

import openstudio


class AlfalfaPythonEnvironment(openstudio.measure.EnergyPlusMeasure):
    """An EnergyPlusMeasure."""

    def name(self):
        """Returns the human readable name.

        Measure name should be the title case of the class name.
        The measure name is the first contact a user has with the measure;
        it is also shared throughout the measure workflow, visible in the OpenStudio Application,
        PAT, Server Management Consoles, and in output reports.
        As such, measure names should clearly describe the measure's function,
        while remaining general in nature
        """
        return "AlfalfaPythonEnvironment"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Add alfalfa python environment to IDF"

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Add python script path to IDF"

    def arguments(self, workspace: openstudio.Workspace):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        return args

    def run(
        self,
        workspace: openstudio.Workspace,
        runner: openstudio.measure.OSRunner,
        user_arguments: openstudio.measure.OSArgumentMap,
    ):
        """Defines what happens when the measure is run."""
        super().run(workspace, runner, user_arguments)  # Do **NOT** remove this line

        if not (runner.validateUserArguments(self.arguments(workspace), user_arguments)):
            return False

        run_dir = os.getenv("RUN_DIR")
        if run_dir:
            venv_dir = Path(run_dir) / '.venv'
            if venv_dir.exists():
                python_paths = openstudio.IdfObject(openstudio.IddObjectType("PythonPlugin:SearchPaths"))
                python_paths.setString(0, "Alfalfa Virtual Environment Path")
                python_paths.setString(1, 'No')
                python_paths.setString(2, 'No')
                python_paths.setString(3, 'No')
                python_paths.setString(4, str(venv_dir / 'lib' / 'python3.12' / 'site-packages'))

                workspace.addObject(python_paths)

        return True


# register the measure to be used by the application
AlfalfaPythonEnvironment().registerWithApplication()
