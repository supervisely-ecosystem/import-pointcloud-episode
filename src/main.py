import os
import tarfile
from pathlib import Path

import supervisely_lib as sly
from supervisely_lib.api.module_api import ApiField
from supervisely_lib.pointcloud_annotation.pointcloud_episode_annotation import PointcloudEpisodeAnnotation
from supervisely_lib.project.pointcloud_episode_project import PointcloudEpisodeProject
from supervisely_lib.project.project_type import ProjectType
from supervisely_lib.video_annotation.key_id_map import KeyIdMap

my_app = sly.AppService()

TEAM_ID = os.environ["context.teamId"]
WORKSPACE_ID = os.environ["context.workspaceId"]
INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")
assert INPUT_DIR or INPUT_FILE


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
        ann_json = sly.io.json.load_json_file(dataset_fs.get_ann_path())
        episode_annotation = PointcloudEpisodeAnnotation.from_json(ann_json, project_fs.meta)

        dataset = api.dataset.create(project.id,
                                     dataset_fs.name,
                                     description=episode_annotation.description,
                                     change_name_if_conflict=True)
        app_logger.info("dataset {!r} [id={!r}] has been created".format(dataset.name, dataset.id))

        frame_to_pointcloud_ids = {}
        for item_name in dataset_fs:
            app_logger.info(f'Upload {item_name}')
            item_path, related_images_dir = dataset_fs.get_item_paths(item_name)
            related_items = dataset_fs.get_related_images(item_name)

            try:
                _, meta = related_items[0]
                timestamp = meta[ApiField.META]['timestamp']
                item_meta = {"timestamp": timestamp}
            except (KeyError, IndexError):
                item_meta = {}

            pointcloud = api.pointcloud_episode.upload_path(dataset.id, item_name, item_path, item_meta)  # upload pointcloud
            upload_related_items(api, related_items, pointcloud.id)  # upload related_images if exist

            frame_idx = dataset_fs.get_frame_idx(item_name)
            frame_to_pointcloud_ids[frame_idx] = pointcloud.id

        api.pointcloud_episode.annotation.append(dataset.id, episode_annotation, frame_to_pointcloud_ids, uploaded_objects)

    app_logger.info('PROJECT_UPLOADED', extra={'event_type': sly.EventType.PROJECT_CREATED, 'project_id': project.id})


@my_app.callback("import_pointcloud_episode")
@sly.timeit
def import_pointcloud_episode(api: sly.Api, task_id, context, state, app_logger):
    storage_dir = my_app.data_dir
    if INPUT_DIR:
        cur_files_path = INPUT_DIR
        extract_dir = os.path.join(storage_dir, str(Path(cur_files_path).parent).lstrip("/"))
        input_dir = os.path.join(extract_dir, Path(cur_files_path).name)
        archive_path = os.path.join(storage_dir, cur_files_path.strip("/") + ".tar")
        project_name = Path(cur_files_path).name
    else:
        cur_files_path = INPUT_FILE
        extract_dir = os.path.join(storage_dir, sly.fs.get_file_name(cur_files_path))
        archive_path = os.path.join(storage_dir, sly.fs.get_file_name_with_ext(cur_files_path))
        input_dir = extract_dir
        project_name = sly.fs.get_file_name(INPUT_FILE)

    sly.fs.silent_remove(archive_path)
    sly.fs.remove_dir(extract_dir)

    app_logger.info('Start downloading remote files...')
    api.file.download(TEAM_ID, cur_files_path, archive_path)  # TODO: make progress bar
    app_logger.info(f'{cur_files_path} downloaded to {archive_path}')
    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as archive:
            archive.extractall(extract_dir)
    else:
        raise Exception("No such file".format(INPUT_FILE))

    project = api.project.create(WORKSPACE_ID,
                                 project_name,
                                 type=ProjectType.POINT_CLOUD_EPISODES,
                                 change_name_if_conflict=True)

    process_episode_project(input_dir, project, api, app_logger)
    api.task.set_output_project(task_id, project.id, project.name)
    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "context.teamId": TEAM_ID,
        "context.workspaceId": WORKSPACE_ID,
        "modal.state.slyFolder": INPUT_DIR,
        "modal.state.slyFile": INPUT_FILE,
    })

    my_app.run(initial_events=[{"command": "import_pointcloud_episode"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
