import os
import shutil
import tarfile
import zipfile
from os.path import basename, dirname, normpath

import supervisely as sly
from supervisely.io.fs import get_file_ext

import download_progress
import globals as g


def get_project_name_from_input_path(input_path: str) -> str:
    """Returns project name from target sly folder name."""
    return os.path.basename(os.path.normpath(input_path))


def files_exists(files, path):
    listdir = [basename(normpath(x)) for x in g.api.file.listdir(g.TEAM_ID, path)]
    return all([file_name in listdir for file_name in files])


def check_input_path() -> None:
    if g.INPUT_DIR:
        listdir = g.api.file.listdir(g.TEAM_ID, g.INPUT_DIR)
        if len(listdir) == 0:
            raise Exception("Input directory is empty.")
        if len(listdir) == 1 and get_file_ext(listdir[0]) in [".zip", ".tar"]:
            sly.logger.info(
                "Folder mode is selected, but archive file is uploaded. Switching to file mode."
            )
            g.INPUT_DIR, g.INPUT_FILE = None, listdir[0]
        elif len(listdir) > 1 and any(get_file_ext(f) in [".zip", ".tar"] for f in listdir):
            raise ValueError("Multiple archives are not supported.")
        elif files_exists(["annotation.json", "frame_pointcloud_map.json"], g.INPUT_DIR):
            g.INPUT_DIR, g.INPUT_FILE = dirname(normpath(g.INPUT_DIR)), None

        elif all([get_file_ext(x) in [".json"] + sly.image.SUPPORTED_IMG_EXTS for x in listdir]):
            if basename(dirname(normpath(g.INPUT_DIR))) == "related_images":
                parent_dir = dirname(dirname(normpath(g.INPUT_DIR)))
                if files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                    parent_dir = dirname(normpath(parent_dir))
                if parent_dir != "/" and files_exists(["meta.json"], parent_dir):
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None
        elif (
            basename(normpath(g.INPUT_DIR)) == "pointcloud" and get_file_ext(listdir[0]) == ".pcd"
        ) or basename(normpath(g.INPUT_DIR)) == "related_images":
            parent_dir = dirname(normpath(g.INPUT_DIR))
            if files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                parent_dir = dirname(normpath(parent_dir))
            if parent_dir != "/" and files_exists(["meta.json"], parent_dir):
                g.INPUT_DIR, g.INPUT_FILE = parent_dir, None

    elif g.INPUT_FILE:
        available_archive_formats = list(zip(*shutil.get_archive_formats()))[0]
        file_ext = sly.fs.get_file_ext(g.INPUT_FILE)
        if file_ext.lstrip(".") not in available_archive_formats:
            sly.logger.info("File mode is selected, but uploaded file is not archive.")
            if basename(normpath(g.INPUT_FILE)) in ["meta.json", "key_id_map.json"]:
                g.INPUT_DIR, g.INPUT_FILE = dirname(g.INPUT_FILE), None
            elif basename(normpath(g.INPUT_FILE)) in [
                "annotation.json",
                "frame_pointcloud_map.json",
            ]:
                parent_dir = dirname(dirname(g.INPUT_FILE))
                if files_exists(["meta.json"], parent_dir):
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None
            elif sly.image.is_valid_ext(file_ext) or file_ext == ".json":
                parent_dir = dirname(dirname(dirname(normpath(g.INPUT_FILE))))
                if files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                    parent_dir = dirname(normpath(parent_dir))
                if parent_dir != "/" and files_exists(["meta.json"], parent_dir):
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None
            elif file_ext == ".pcd":
                parent_dir = dirname(dirname(normpath(g.INPUT_FILE)))
                if files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                    parent_dir = dirname(normpath(parent_dir))
                if parent_dir != "/" and files_exists(["meta.json"], parent_dir):
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None


def download_input_files(api: sly.Api, task_id):
    if not g.IS_ON_AGENT:
        check_input_path()

    if g.INPUT_DIR:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(g.INPUT_DIR)
        else:
            cur_files_path = g.INPUT_DIR

        if not cur_files_path.endswith("/"):
            cur_files_path += "/"
        sizeb = api.file.get_directory_size(g.TEAM_ID, g.INPUT_DIR)
        extract_dir = os.path.join(g.storage_dir, cur_files_path.strip("/"))
        progress_cb = download_progress.get_progress_cb(
            api, task_id, f"Downloading {g.INPUT_DIR.strip('/')}", sizeb, is_size=True
        )
        api.file.download_directory(g.TEAM_ID, g.INPUT_DIR, extract_dir, progress_cb)
    else:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(g.INPUT_FILE)
        else:
            cur_files_path = g.INPUT_FILE

        sizeb = api.file.get_info_by_path(g.TEAM_ID, g.INPUT_FILE).sizeb
        archive_path = os.path.join(g.storage_dir, sly.fs.get_file_name_with_ext(cur_files_path))
        extract_dir = os.path.join(g.storage_dir, sly.fs.get_file_name(cur_files_path))
        progress_cb = download_progress.get_progress_cb(
            api, task_id, f"Downloading {g.INPUT_FILE.lstrip('/')}", sizeb, is_size=True
        )
        api.file.download(g.TEAM_ID, g.INPUT_FILE, archive_path, None, progress_cb)

        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner) 
                    
                
                safe_extract(archive, extract_dir)
        elif zipfile.is_zipfile(archive_path):
            z_file = zipfile.ZipFile(archive_path)
            z_file.extractall(extract_dir)
        else:
            raise RuntimeError(
                f"File extension '{sly.fs.get_file_ext(archive_path)}' is not supported."
            )
        sly.fs.silent_remove(archive_path)
    sly.fs.remove_junk_from_dir(extract_dir)

    def search_projects(dir_path):
        files = os.listdir(dir_path)
        meta_exists = "meta.json" in files
        datasets = [f for f in files if sly.fs.dir_exists(os.path.join(dir_path, f))]
        datasets_exists = len(datasets) > 0
        return meta_exists and datasets_exists

    project_dirs = [project_dir for project_dir in sly.fs.dirs_filter(extract_dir, search_projects)]
    return project_dirs
