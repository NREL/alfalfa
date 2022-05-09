import glob
import os
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Run:
    dir: str
    id: str = uuid4()

    def join(self, *args):
        return os.path.join(self.dir, *args)

    def glob(self, search_str, recursive=True):
        return glob.glob(self.join(search_str), recursive=recursive)
