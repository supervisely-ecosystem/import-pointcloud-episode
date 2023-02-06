import globals as g

# import functions as f
import supervisely as sly
import os, shutil
from supervisely.io.fs import silent_remove, get_file_name
from supervisely.project.pointcloud_episode_project import upload_pointcloud_episode_project
from os.path import join


class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):

        project_dir = context.path

        if context.is_directory is False:
            project_folder = join(g.STORAGE_DIR, get_file_name(project_dir))
            shutil.unpack_archive(project_dir, project_folder)
            silent_remove(project_dir)
            project_dir = project_folder

        project_name = (
            os.path.basename(project_dir)
            if len(g.OUTPUT_PROJECT_NAME) == 0
            else g.OUTPUT_PROJECT_NAME
        )

        # input_dir, project_name = f.download_input_files(api, task_id, g.INPUT_DIR, g.INPUT_FILE)

        # project_name = project_name if len(g.OUTPUT_PROJECT_NAME) == 0 else g.OUTPUT_PROJECT_NAME

        project_id, project_name = upload_pointcloud_episode_project(
            project_name, g.api, context.workspace_id, project_name=project_name, log_progress=True
        )
        # api.task.set_output_project(task_id, project_id, project_name)

        if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
            if g.INPUT_DIR is not None:
                path_to_remove = g.INPUT_DIR
            else:
                path_to_remove = g.INPUT_FILE
            g.api.file.remove(team_id=context.team_id, path=path_to_remove)
            source_dir_name = path_to_remove.strip("/")
            sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")


app = MyImport()
app.run()
