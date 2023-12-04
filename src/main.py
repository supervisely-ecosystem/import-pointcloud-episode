import functions as f
import globals as g
import supervisely as sly
from supervisely.project.pointcloud_episode_project import (
    upload_pointcloud_episode_project,
)


@g.my_app.callback("import_pointcloud_episode")
@sly.timeit
def import_pointcloud_episode(api: sly.Api, task_id, context, state, app_logger):
    projects_cnt = 0
    project_dirs, only_pcd_dirs = f.download_input_files(api, task_id)

    if len(project_dirs) > 0:
        for input_dir in project_dirs:
            sly.logger.info(f"Working with '{input_dir}'")
            project_name = f.get_project_name_from_input_path(input_dir)

            project_name = (
                project_name if len(g.OUTPUT_PROJECT_NAME) == 0 else g.OUTPUT_PROJECT_NAME
            )
            sly.logger.info(f"Project name: '{project_name}'")

            f.validate_local_project(input_dir)

            try:
                project_id, project_name = upload_pointcloud_episode_project(
                    input_dir, api, g.WORKSPACE_ID, project_name=project_name, log_progress=True
                )
                api.task.set_output_project(task_id, project_id, project_name)
                sly.logger.info(
                    f"Project '{project_name}' was successfully uploaded. ID: {project_id}"
                )
                projects_cnt += 1
            except Exception as e:
                sly.logger.warn(f"Project '{project_name}' was not uploaded correctly. Error: {e}")
                only_pcd_dirs.append(input_dir)

    if len(only_pcd_dirs) > 0:
        sly.logger.warn("Not found pointcloud episodes projects in Supervisely format.")
        sly.logger.info(
            f"Trying to upload only pointclouds to the new project from the directories {only_pcd_dirs}."
        )
        f.upload_only_pcd(api, only_pcd_dirs)
        projects_cnt += 1

    if len(project_dirs) == 0 and len(only_pcd_dirs) == 0:
        msg = "Not found pointcloud episodes project in Supervisely format"
        description = "Please, read the app overview."
        sly.logger.error(msg)
        api.task.set_output_error(task_id, msg, description)
    elif projects_cnt == 0:
        msg = "No pointcloud episodes projects were uploaded."
        description = "Read the app overview and check the input data."
        sly.logger.error(msg)
        api.task.set_output_error(task_id, msg, description)
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
