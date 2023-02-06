import supervisely as sly
import os, shutil
from supervisely.io.fs import silent_remove, get_file_name
from supervisely.project.pointcloud_episode_project import upload_pointcloud_episode_project
from os.path import join
from distutils.util import strtobool
from dotenv import load_dotenv

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()

INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")

OUTPUT_PROJECT_NAME = os.environ.get("modal.state.project_name", "")
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))
assert INPUT_DIR or INPUT_FILE

if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)

STORAGE_DIR: str = sly.app.get_data_dir()
sly.fs.mkdir(STORAGE_DIR, True)


class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):

        project_dir = context.path

        if context.is_directory is False:
            project_folder = join(STORAGE_DIR, get_file_name(project_dir))
            shutil.unpack_archive(project_dir, project_folder)
            silent_remove(project_dir)
            project_dir = project_folder

        project_name = (
            os.path.basename(project_dir) if len(OUTPUT_PROJECT_NAME) == 0 else OUTPUT_PROJECT_NAME
        )

        project_id, project_name = upload_pointcloud_episode_project(
            project_dir, api, context.workspace_id, project_name=project_name, log_progress=True
        )

        if REMOVE_SOURCE and not IS_ON_AGENT:
            if INPUT_DIR is not None:
                path_to_remove = INPUT_DIR
            else:
                path_to_remove = INPUT_FILE
            api.file.remove(team_id=context.team_id, path=path_to_remove)
            source_dir_name = path_to_remove.strip("/")
            sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")


app = MyImport()
app.run()
