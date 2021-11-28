import subprocess
import re
import logging
import shutil
from pathlib import Path


class DiskManager(object):
    def __init__(self, folder, occupation_threshold_to_delete):
        self._folder = folder
        self._occupation_threshold_to_delete = occupation_threshold_to_delete

    def get_disk_usage(self):
        op = subprocess.check_output(['df',
                                      self._folder]).decode('utf-8').split('\n')
        params = op[1].split()
        usage = int(params[4].strip('%')) / 100.0  # Percent used
        return usage

    def check_and_delete_old_files(self):
        usage = self.get_disk_usage()
        if usage > self._occupation_threshold_to_delete:
            logging.debug("Disk usage > {}".format(usage))
            folders = [f for f in Path(self._folder).glob('*') if re.search(r'^2\d{7}-\d{6}$', f.name)]
            folders = sorted(folders)
            for folder in folders:
                shutil.rmtree(str(folder))
                logging.debug("Delete {} to free disk space".format(folder))
                if self.get_disk_usage() < self._occupation_threshold_to_delete:
                    break
