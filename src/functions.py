import os
import globals as g
import tarfile
import zipfile
from pathlib import Path

import download_progress
import supervisely_lib as sly
from supervisely_lib.api.module_api import ApiField
from supervisely_lib.pointcloud_annotation.pointcloud_episode_annotation import PointcloudEpisodeAnnotation
from supervisely_lib.project.pointcloud_episode_project import PointcloudEpisodeProject
from supervisely_lib.video_annotation.key_id_map import KeyIdMap


def upload_related_items(api, related_items, pointcloud_id):
    if len(related_items) != 0:
        img_infos = []
        for img_path, meta_json in related_items:
            img = api.pointcloud_episode.upload_related_image(img_path)[0]
            img_infos.append({ApiField.ENTITY_ID: pointcloud_id,
                               ApiField.NAME: meta_json[ApiField.NAME],
                               ApiField.HASH: img,
                               ApiField.META: meta_json[ApiField.META]})

        api.pointcloud_episode.add_related_images(img_infos)


def process_episode_project(input_dir, project, api, app_logger):
    project_fs = PointcloudEpisodeProject.read_single(input_dir)

    api.project.update_meta(project.id, project_fs.meta.to_json())
    app_logger.info("Project {!r} [id={!r}] has been created".format(project.name, project.id))

    uploaded_objects = KeyIdMap()
    for dataset_fs in project_fs:
        ann_json = sly.json.load_json_file(dataset_fs.get_ann_path())
        episode_annotation = PointcloudEpisodeAnnotation.from_json(ann_json, project_fs.meta)

        dataset = api.dataset.create(project.id,
                                     dataset_fs.name,
                                     description=episode_annotation.description,
                                     change_name_if_conflict=True)
        app_logger.info("dataset {!r} [id={!r}] has been created".format(dataset.name, dataset.id))

        frame_to_pointcloud_ids = {}
        progress = sly.Progress(f"Importing {dataset_fs.name}", len(dataset_fs))
        for item_name in dataset_fs:
            item_path, related_images_dir = dataset_fs.get_item_paths(item_name)
            related_items = dataset_fs.get_related_images(item_name)

            item_meta = {}
            try:
                _, meta = related_items[0]
                timestamp = meta[ApiField.META]['timestamp']
                item_meta["timestamp"] = timestamp
            except (KeyError, IndexError):
                pass

            frame_idx = dataset_fs.get_frame_idx(item_name)
            item_meta["frame"] = frame_idx

            pointcloud = api.pointcloud_episode.upload_path(dataset.id, item_name, item_path, item_meta)  # upload pointcloud
            upload_related_items(api, related_items, pointcloud.id)  # upload related_images if exist
            frame_to_pointcloud_ids[frame_idx] = pointcloud.id
            app_logger.info(f'{item_name} has been uploaded')
            progress.iter_done_report()

        api.pointcloud_episode.annotation.append(dataset.id, episode_annotation, frame_to_pointcloud_ids, uploaded_objects)

    app_logger.info('PROJECT_UPLOADED', extra={'event_type': sly.EventType.PROJECT_CREATED, 'project_id': project.id})


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
