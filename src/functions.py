import os
import tarfile
import zipfile
from collections import defaultdict
from os.path import basename, dirname, normpath

import download_progress
import globals as g
import supervisely as sly
from supervisely.api.module_api import ApiField
from supervisely.io.fs import get_file_ext


def get_project_name_from_input_path(input_path: str) -> str:
    """Returns project name from target sly folder name."""
    return os.path.basename(os.path.normpath(input_path))


def files_exists(files, path):
    listdir = [basename(normpath(x)) for x in g.api.file.listdir(g.TEAM_ID, path)]
    return all([file_name in listdir for file_name in files])


def search_projects(dir_path):
    files = os.listdir(dir_path)
    meta_exists = "meta.json" in files
    datasets = [f for f in files if sly.fs.dir_exists(os.path.join(dir_path, f))]
    datasets_exists = len(datasets) > 0
    return meta_exists and datasets_exists


def search_pcd_dir(dir_path):
    listdir = os.listdir(dir_path)
    is_pcd_dir = any(sly.pointcloud.has_valid_ext(f) for f in listdir)
    return is_pcd_dir


def is_archive_path(path):
    return get_file_ext(path) in [".zip", ".tar"] or path.endswith(".tar.gz")


def get_project_dirs(input_dir):
    project_dirs = [project_dir for project_dir in sly.fs.dirs_filter(input_dir, search_projects)]

    only_pcd_dirs = []
    if len(project_dirs) == 0:
        only_pcd_dirs = [pcd_dir for pcd_dir in sly.fs.dirs_filter(input_dir, search_pcd_dir)]
    return project_dirs, only_pcd_dirs


def check_input_path() -> None:
    if g.INPUT_DIR:
        listdir = g.api.file.listdir(g.TEAM_ID, g.INPUT_DIR)
        if len(listdir) == 0:
            raise Exception("Input directory is empty.")
        if len(listdir) == 1 and is_archive_path(listdir[0]):
            sly.logger.info(
                "Folder mode is selected, but archive file is uploaded. Switching to file mode."
            )
            g.INPUT_DIR, g.INPUT_FILE = None, listdir[0]
        elif len(listdir) > 1 and any(is_archive_path(f) for f in listdir):
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
        file_ext = sly.fs.get_file_ext(g.INPUT_FILE)
        if not is_archive_path(g.INPUT_FILE):
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
            elif sly.image.has_valid_ext(g.INPUT_FILE) or file_ext == ".json":
                parent_dir = dirname(g.INPUT_FILE)
                if parent_dir != "/":
                    parent_dir = dirname(parent_dir)
                if basename(normpath(parent_dir)) == "related_images":
                    parent_dir = dirname(parent_dir)
                if files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                    parent_dir = dirname(parent_dir)
                if files_exists(["meta.json"], parent_dir):
                    parent_dir = dirname(parent_dir)
                if parent_dir != "/":
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None
            elif sly.pointcloud.has_valid_ext(g.INPUT_FILE):
                parent_dir = dirname(normpath(g.INPUT_FILE))
                possible_ds_dir = dirname(parent_dir)
                if files_exists(["annotation.json", "frame_pointcloud_map.json"], possible_ds_dir):
                    parent_dir = possible_ds_dir
                possible_proj_dir = dirname(parent_dir)
                if files_exists(["meta.json"], possible_proj_dir):
                    parent_dir = possible_proj_dir
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

        if is_archive_path(archive_path):
            if tarfile.is_tarfile(archive_path):
                with tarfile.open(archive_path) as archive:
                    archive.extractall(extract_dir)
            elif zipfile.is_zipfile(archive_path):
                z_file = zipfile.ZipFile(archive_path)
                z_file.extractall(extract_dir)
            else:
                raise Exception(f"Failed to extract archive '{archive_path}'.")
            # else:
            #     raise Exception(
            #         f"Incorrect input file format. Upload archive or directory with pointcloud episodes in Supervisely format."
            #     )
            sly.fs.silent_remove(archive_path)
    sly.fs.remove_junk_from_dir(g.storage_dir)

    project_dirs, only_pcd_dirs = get_project_dirs(g.storage_dir)
    return project_dirs, only_pcd_dirs


def validate_local_project(input_dir):
    """
    Validate local project before uploading to Supervisely.
    # * Validate related images with corresponding JSON annotation files *
    """
    project_locally = sly.PointcloudEpisodeProject.read_single(input_dir)
    for dataset_locally in project_locally.datasets:
        bad_related_images = defaultdict(lambda: defaultdict(list))
        for name in dataset_locally:
            path = dataset_locally.get_related_images_path(name)
            if sly.fs.dir_exists(path):
                files = sly.fs.list_files(path, sly.image.SUPPORTED_IMG_EXTS)
                for file in files:
                    file_name = sly.fs.get_file_name_with_ext(file)
                    img_meta_path = os.path.join(
                        path, sly.fs.get_file_name_with_ext(file) + ".json"
                    )
                    if not sly.fs.file_exists(img_meta_path):
                        bad_related_images[g.RELATED_IMAGES_ANN_NOT_FOUND][name].append(file_name)
                        sly.fs.silent_remove(file)
                        continue
                    img_meta = sly.json.load_json_file(img_meta_path)
                    need_required_field = False
                    for field in g.RELATED_IMAGES_ANN_FIELDS:
                        if field not in img_meta.keys():
                            bad_related_images[g.RELATED_IMAGES_ANN_WRONG_FIELDS(field)][
                                name
                            ].append(file)
                            need_required_field = True
                    if need_required_field:
                        sly.fs.silent_remove(file)
                        continue
                    if img_meta[ApiField.NAME] != sly.fs.get_file_name_with_ext(file):
                        bad_related_images[g.RELATED_IMAGES_ANN_WRONG_NAME][name].append(file_name)
                        sly.fs.silent_remove(file)
                        continue
                    if not isinstance(img_meta[ApiField.META], dict):
                        bad_related_images[g.RELATED_IMAGES_ANN_META_TYPE][name].append(file_name)
                        sly.fs.silent_remove(file)
                        continue
                    if g.RELATED_IMAGES_SENSOR_DATA not in img_meta[ApiField.META].keys():
                        bad_related_images[g.SENSOR_DATA_NOT_FOUND][name].append(file_name)
                        sly.fs.silent_remove(file)
                        continue
                    if not isinstance(img_meta[ApiField.META][g.RELATED_IMAGES_SENSOR_DATA], dict):
                        bad_related_images[g.SENSOR_DATA_TYPE][name].append(file_name)
                        sly.fs.silent_remove(file)
                        continue
                    bad_sensor_data_field = False
                    for field, valid_length in g.RELATED_IMAGES_SENSOR_DATA_FIELDS.items():
                        if (
                            field
                            not in img_meta[ApiField.META][g.RELATED_IMAGES_SENSOR_DATA].keys()
                        ):
                            bad_related_images[g.SENSOR_DATA_FIELD(field)][name].append(file_name)
                            bad_sensor_data_field = True
                        elif not isinstance(
                            img_meta[ApiField.META][g.RELATED_IMAGES_SENSOR_DATA][field], list
                        ):
                            bad_related_images[g.SENSOR_DATA_FIELDS_TYPE(field)][name].append(
                                file_name
                            )
                            bad_sensor_data_field = True
                        elif (
                            len(img_meta[ApiField.META][g.RELATED_IMAGES_SENSOR_DATA][field])
                            != valid_length
                        ):
                            bad_related_images[
                                g.SENSOR_DATA_WRONG_LENGTH({"field": field, "length": valid_length})
                            ][name].append(file_name)
                            bad_sensor_data_field = True
                    if bad_sensor_data_field:
                        sly.fs.silent_remove(file)
                        continue
        if len(bad_related_images) > 0:
            sly.logger.warn(
                f"Related images validation errors for dataset '{dataset_locally.name}':"
            )
            for error, items in bad_related_images.items():
                sly.logger.warn(f"    - {error} for items: {list(items.values())}")
            sly.logger.warn("All related images with errors will be skipped.")


def upload_only_pcd(api: sly.Api, input_dirs):
    project = api.project.create(
        g.WORKSPACE_ID,
        "Pointclouds",
        sly.ProjectType.POINT_CLOUD_EPISODES,
        change_name_if_conflict=True,
    )
    pcd_cnt = 0
    for input_dir in input_dirs:
        if not sly.fs.dir_exists(input_dir):
            continue
        pcd_paths = sly.fs.list_files(
            input_dir,
            valid_extensions=sly.pointcloud.ALLOWED_POINTCLOUD_EXTENSIONS,
            ignore_valid_extensions_case=True,
        )
        # sort by names:
        pcd_paths = sorted(pcd_paths)
        if len(pcd_paths) == 0:
            continue
        dataset_name = os.path.basename(os.path.normpath(input_dir))
        dataset = api.dataset.create(project.id, dataset_name, change_name_if_conflict=True)
        pcd_names = [
            os.path.basename(path) for path in pcd_paths if sly.pointcloud.has_valid_ext(path)
        ]
        if len(pcd_names) != len(pcd_paths):
            sly.logger.warn("Not all files have valid pointcloud extensions.")
            continue
        metas = [{"frame": i} for i in range(len(pcd_paths))]
        progress_cb = sly.Progress(
            f"Uploading pointclouds...", total_cnt=len(pcd_paths)
        ).iters_done_report
        pcd_infos = api.pointcloud_episode.upload_paths(
            dataset.id, pcd_names, pcd_paths, progress_cb, metas
        )
        pcd_cnt += len(pcd_infos)
        sly.fs.remove_dir(input_dir)
    if pcd_cnt > 1:
        sly.logger.info(f"{pcd_cnt} pointclouds were uploaded to project '{project.name}'.")
    elif pcd_cnt == 1:
        sly.logger.info(f"{pcd_cnt} pointcloud was uploaded to project '{project.name}'.")
    else:
        api.project.remove(project.id)
        return None
    project = api.project.get_info_by_id(project.id)
    return project
