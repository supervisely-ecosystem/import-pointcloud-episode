import os
from collections import defaultdict

import globals as g
import functions as f
import supervisely as sly
from supervisely.project.pointcloud_episode_project import upload_pointcloud_episode_project
from supervisely.api.module_api import ApiField


@g.my_app.callback("import_pointcloud_episode")
@sly.timeit
def import_pointcloud_episode(api: sly.Api, task_id, context, state, app_logger):
    input_dirs = f.download_input_files(api, task_id, g.INPUT_DIR, g.INPUT_FILE)
    for input_dir in input_dirs:
        sly.logger.info(f"Working with '{input_dir}'")
        project_name = f.get_project_name_from_input_path(input_dir)

        project_name = project_name if len(g.OUTPUT_PROJECT_NAME) == 0 else g.OUTPUT_PROJECT_NAME
        sly.logger.info(f"Project name: '{project_name}'")

        # * Validate related images with corresponding JSON annotation files *
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
                            bad_related_images[g.RELATED_IMAGES_ANN_NOT_FOUND][name].append(
                                file_name
                            )
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
                            bad_related_images[g.RELATED_IMAGES_ANN_WRONG_NAME][name].append(
                                file_name
                            )
                            sly.fs.silent_remove(file)
                            continue
                        if not isinstance(img_meta[ApiField.META], dict):
                            bad_related_images[g.RELATED_IMAGES_ANN_META_TYPE][name].append(
                                file_name
                            )
                            sly.fs.silent_remove(file)
                            continue
                        if g.RELATED_IMAGES_SENSOR_DATA not in img_meta[ApiField.META].keys():
                            bad_related_images[g.SENSOR_DATA_NOT_FOUND][name].append(file_name)
                            sly.fs.silent_remove(file)
                            continue
                        if not isinstance(
                            img_meta[ApiField.META][g.RELATED_IMAGES_SENSOR_DATA], dict
                        ):
                            bad_related_images[g.SENSOR_DATA_TYPE][name].append(file_name)
                            sly.fs.silent_remove(file)
                            continue
                        bad_sensor_data_field = False
                        for field, valid_length in g.RELATED_IMAGES_SENSOR_DATA_FIELDS.items():
                            if (
                                field
                                not in img_meta[ApiField.META][g.RELATED_IMAGES_SENSOR_DATA].keys()
                            ):
                                bad_related_images[g.SENSOR_DATA_FIELD(field)][name].append(
                                    file_name
                                )
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
                                    g.SENSOR_DATA_WRONG_LENGTH(
                                        {"field": field, "length": valid_length}
                                    )
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

        project_id, project_name = upload_pointcloud_episode_project(
            input_dir, api, g.WORKSPACE_ID, project_name=project_name, log_progress=True
        )
        api.task.set_output_project(task_id, project_id, project_name)
        sly.logger.info(f"Project '{project_name}' was successfully uploaded. ID: {project_id}")

    if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
        if g.INPUT_DIR is not None:
            path_to_remove = g.INPUT_DIR
        else:
            path_to_remove = g.INPUT_FILE
        api.file.remove(team_id=g.TEAM_ID, path=path_to_remove)
        source_dir_name = path_to_remove.strip("/")
        sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")

    g.my_app.stop()


def main():
    sly.logger.info(
        "Script arguments",
        extra={
            "context.teamId": g.TEAM_ID,
            "context.workspaceId": g.WORKSPACE_ID,
            "modal.state.slyFolder": g.INPUT_DIR,
            "modal.state.slyFile": g.INPUT_FILE,
        },
    )

    g.my_app.run(initial_events=[{"command": "import_pointcloud_episode"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
