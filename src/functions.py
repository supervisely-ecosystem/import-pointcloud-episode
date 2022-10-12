import os
import globals as g
import tarfile
import zipfile
from pathlib import Path

import download_progress
import supervisely as sly


def get_project_name_from_input_path(input_path: str) -> str:
    """Returns project name from target sly folder name."""
    full_path_dir = os.path.dirname(input_path)
    return os.path.basename(full_path_dir)


def download_input_files(api, task_id, input_dir, input_file):
    if input_dir:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(input_dir)
        else:
            cur_files_path = input_dir

        sizeb = api.file.get_directory_size(g.TEAM_ID, input_dir)
        extract_dir = os.path.join(g.storage_dir, cur_files_path.strip("/"))
        project_name = Path(cur_files_path).name
        progress_cb = download_progress.get_progress_cb(api, task_id, f"Downloading {g.INPUT_DIR.strip('/')}", sizeb,
                                                        is_size=True)
        api.file.download_directory(g.TEAM_ID, input_dir, extract_dir, progress_cb)
    else:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(input_file)
        else:
            cur_files_path = input_file

        sizeb = api.file.get_info_by_path(g.TEAM_ID, input_file).sizeb
        archive_path = os.path.join(g.storage_dir, sly.fs.get_file_name_with_ext(cur_files_path))
        extract_dir = os.path.join(g.storage_dir, sly.fs.get_file_name(cur_files_path))
        project_name = sly.fs.get_file_name(input_file)
        progress_cb = download_progress.get_progress_cb(api, task_id, f"Downloading {g.INPUT_FILE.lstrip('/')}",
                                                        sizeb,
                                                        is_size=True)
        api.file.download(g.TEAM_ID, input_file, archive_path, None, progress_cb)

        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                archive.extractall(extract_dir)
        elif zipfile.is_zipfile(archive_path):
            z_file = zipfile.ZipFile(archive_path)
            z_file.extractall(extract_dir)
        else:
            raise NotImplementedError("File extension is not supported.")
        sly.fs.silent_remove(archive_path)
    return extract_dir, project_name
