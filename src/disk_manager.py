import subprocess
import os
import re
import logging
import shutil
from pathlib import Path


class DiskManager(object):
    def __init__(self, folder, available_space_threshold_to_start_delete):
        self._folder = folder
        self._rest_space_threshold_to_start_delete = available_space_threshold_to_start_delete
        self._max_space_occupation_per_min = 100.0 * 1024.0 * 1024.0  # 100M

    def get_available_space(self):
        op = subprocess.check_output(['df',
                                      self._folder]).decode('utf-8').split('\n')
        params = op[1].split()
        available_space = int(params[3]) * 1024.0
        return available_space

    def get_next_time_interval_to_check(self, current_available_space):
        return (
                           current_available_space - self._rest_space_threshold_to_start_delete) / self._max_space_occupation_per_min * 60.0

    def check_and_delete_old_files(self):
        available_space = self.get_available_space()
        if available_space > self._rest_space_threshold_to_start_delete:
            return self.get_next_time_interval_to_check(available_space)
        else:
            logging.debug("Disk available space < {}M".format(available_space / (1024.0 * 1024.0)))

            folders = [f for f in Path(self._folder).glob('*') if re.search(r'^2\d{7}-\d{6}$', f.name)]
            folders = sorted(folders)
            if len(folders) == 0:
                raise Exception("Space less than {}M for reoording".format(available_space / (1024.0 * 1024.0)))

            for folder in folders[:-1]:
                shutil.rmtree(str(folder))
                logging.debug("Delete {} to free disk space".format(folder))
                current_available_space = self.get_available_space()
                if current_available_space > self._rest_space_threshold_to_start_delete:
                    return self.get_next_time_interval_to_check(current_available_space)

            # only one folder but has lots of files
            files = sorted([f for f in Path(folders[-1]).glob('*.mp4')])
            for f in files:
                os.remove(f)
                current_available_space = self.get_available_space()
                if current_available_space > self._rest_space_threshold_to_start_delete:
                    return self.get_next_time_interval_to_check(current_available_space)
