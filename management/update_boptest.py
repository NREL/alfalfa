import distutils.cmd
import distutils.log
import os
import requests


class UpdateBoptest(distutils.cmd.Command):
    """Custom comand for updating the GeoJSON schemas on which this project depends."""

    description = "Download and overwrite latest BOPTEST files from source"

    user_options = [("baseurl=", "u", "base URL from which to download the schemas")]

    def initialize_options(self):
        self.files_to_download = {
            'data/categories.json': 'alfalfa_worker/lib/data/categories.json'
        }

        # For now the branch is 'master' but will need to be moved to develop after it is merged.
        self.baseurl = "https://raw.githubusercontent.com/ibpsa/project1-boptest/master"  # noqa

    def finalize_options(self):
        if self.baseurl is None:
            print("Downloading the files from the default url: %s" % self.baseurl)

    def run(self):
        for left, right in self.files_to_download.items():
            url = "%s/%s" % (self.baseurl, left)
            response = requests.get(url)
            self.announce("Downloading file: %s" % str(url), level=distutils.log.INFO)
            self.announce("Saving file to: %s" % str(right), level=distutils.log.INFO)
            if os.path.exists(right):
                os.remove(right)
            with open(right, "wb") as outf:
                outf.write(response.content)
