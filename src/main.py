import globals as g
import functions as f
import supervisely as sly
from supervisely.project.pointcloud_episode_project import upload_pointcloud_episode_project


@g.my_app.callback("import_pointcloud_episode")
@sly.timeit
def import_pointcloud_episode(api: sly.Api, task_id, context, state, app_logger):
    input_dir, project_name = f.download_input_files(api, task_id, g.INPUT_DIR, g.INPUT_FILE)
    
    project_name = project_name if len(g.OUTPUT_PROJECT_NAME) == 0 else g.OUTPUT_PROJECT_NAME

    project_id, project_name = upload_pointcloud_episode_project(input_dir, api, g.WORKSPACE_ID, project_name=project_name, log_progress=True)
    api.task.set_output_project(task_id, project_id, project_name)
    
    if g.REMOVE_SOURCE:
        api.file.remove(team_id=g.TEAM_ID, path=g.INPUT_DIR)
        source_dir_name = g.INPUT_DIR.lstrip("/").rstrip("/")
        sly.logger.info(
            msg=f"Source directory: '{source_dir_name}' was successfully removed."
        )
    
    g.my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "context.teamId": g.TEAM_ID,
        "context.workspaceId": g.WORKSPACE_ID,
        "modal.state.slyFolder": g.INPUT_DIR,
        "modal.state.slyFile": g.INPUT_FILE,
    })

    g.my_app.run(initial_events=[{"command": "import_pointcloud_episode"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
