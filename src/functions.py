import os
import globals as g
import tarfile
import zipfile
from pathlib import Path

import download_progress
import supervisely_lib as sly


def download_input_files(api, task_id, input_dir, input_file):
    if input_dir:
        sizeb = api.file.get_directory_size(g.TEAM_ID, input_dir)
        cur_files_path = input_dir
        extract_dir = os.path.join(g.storage_dir, cur_files_path.lstrip("/").rstrip("/"))
        input_dir = extract_dir
        project_name = Path(cur_files_path).name

        progress_cb = download_progress.get_progress_cb(api, task_id, f"Downloading {g.INPUT_DIR.lstrip('/').rstrip('/')}", sizeb,
                                                        is_size=True)
        api.file.download_directory(g.TEAM_ID, cur_files_path, extract_dir, progress_cb)
    else:
        sizeb = api.file.get_info_by_path(g.TEAM_ID, input_file).sizeb
        cur_files_path = input_file
        archive_path = os.path.join(g.storage_dir, sly.fs.get_file_name_with_ext(cur_files_path))
        extract_dir = os.path.join(g.storage_dir, sly.fs.get_file_name(cur_files_path))
        input_dir = extract_dir
        project_name = sly.fs.get_file_name(input_file)

        progress_cb = download_progress.get_progress_cb(api, task_id, f"Downloading {g.INPUT_FILE.lstrip('/')}",
                                                        sizeb,
                                                        is_size=True)
        api.file.download(g.TEAM_ID, cur_files_path, archive_path, None, progress_cb)

        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                archive.extractall(extract_dir)
        elif zipfile.is_zipfile(archive_path):
            z_file = zipfile.ZipFile(archive_path)
            z_file.extractall(extract_dir)
        else:
            raise Exception("No such file".format(g.INPUT_FILE))
        sly.fs.silent_remove(archive_path)
    return input_dir, project_name
