import globals as g
import functions as f
import supervisely_lib as sly
from supervisely_lib.project.project_type import ProjectType


@g.my_app.callback("import_pointcloud_episode")
@sly.timeit
def import_pointcloud_episode(api: sly.Api, task_id, context, state, app_logger):
    input_dir, project_name = f.download_input_files(api, task_id, g.INPUT_DIR, g.INPUT_FILE)
    project = api.project.create(g.WORKSPACE_ID,
                                 project_name,
                                 type=ProjectType.POINT_CLOUD_EPISODES,
                                 change_name_if_conflict=True)

    f.process_episode_project(input_dir, project, api, app_logger)
    api.task.set_output_project(task_id, project.id, project.name)
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
