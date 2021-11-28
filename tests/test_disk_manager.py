import unittest
import time, pathlib, os, glob
import shutil
import pytest

from .context import src
from src.disk_manager import DiskManager


def generate_big_random_bin_file(filename, size):
    """
    generate big binary file with the specified size in bytes
    :param filename: the filename
    :param size: the size in bytes
    :return:void
    """
    with open('%s' % filename, 'wb') as fout:
        fout.write(os.urandom(size))


# To execute the test, run 'create_loop_fs.sh' and uncomment the skip
# In the end run 'clean_loop_fs.sh'
@pytest.mark.skip(reason="can not mount loop fs on CI")
class TestDiskManager(unittest.TestCase):
    def setUp(self):
        self._recording_folder = "tests/loopfs"
        self._occupation_threshold_to_delete = 0.7
        self._disk_manager = DiskManager(self._recording_folder, self._occupation_threshold_to_delete)

    def tearDown(self):
        for f in self._get_subfolders():
            shutil.rmtree(str(f))

    def _get_subfolders(self):
        return [f for f in pathlib.Path(self._recording_folder).glob('*')]

    def _occupy_disk_with_files_with_non_datetime_filenames(self):
        subfolders = []
        names = ["abc", "home", "root", "data", "123"]
        for i, name in enumerate(names):
            subfolder = pathlib.Path(self._recording_folder).joinpath(name)
            subfolder.mkdir(parents=True, exist_ok=True)
            subfolders.append(subfolder)
            generate_big_random_bin_file(str(subfolder.joinpath("{}.txt".format(i))), 1024)
        return subfolders

    def _occupy_disk_with_M_files_of_N_MB(self, M, N):
        subfolders = []
        for i in range(M):
            subfolder = pathlib.Path(self._recording_folder).joinpath(
                time.strftime("%Y%m%d-%H%M%S"))
            subfolder.mkdir(parents=True, exist_ok=True)
            subfolders.append(subfolder)
            generate_big_random_bin_file(str(subfolder.joinpath("{}.mp4".format(i))), N * 1024 * 1024)
            time.sleep(1)
        return subfolders

    def test_no_delete_old_files_when_space_enough(self):
        sub_folders = self._occupy_disk_with_M_files_of_N_MB(3, 1)
        usage_percentage_old = self._disk_manager.get_disk_usage()
        self.assertLess(usage_percentage_old, self._occupation_threshold_to_delete)

        self._disk_manager.check_and_delete_old_files()
        usage_percentage_new = self._disk_manager.get_disk_usage()
        self.assertEqual(usage_percentage_new, usage_percentage_old)

        sub_folders_new = self._get_subfolders()
        self.assertListEqual(sorted(sub_folders), sorted(sub_folders_new))

    def test_delete_old_files_when_space_full(self):
        user_sub_folders = self._occupy_disk_with_files_with_non_datetime_filenames()

        sub_folders = self._occupy_disk_with_M_files_of_N_MB(6, 1)
        usage_percentage = self._disk_manager.get_disk_usage()
        self.assertGreater(usage_percentage, self._occupation_threshold_to_delete)
        self._disk_manager.check_and_delete_old_files()
        usage_percentage = self._disk_manager.get_disk_usage()
        self.assertLess(usage_percentage, self._occupation_threshold_to_delete)

        sub_folders_new = self._get_subfolders()
        self.assertListEqual(sorted(sorted(sub_folders)[1:] + user_sub_folders), sorted(sub_folders_new))
