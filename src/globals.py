import os
import supervisely as sly
from supervisely_lib.app.v1.app_service import AppService


from distutils.util import strtobool


api: sly.Api = sly.Api.from_env()
my_app = AppService()

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = os.environ["context.teamId"]
WORKSPACE_ID = os.environ["context.workspaceId"]
INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")

OUTPUT_PROJECT_NAME = os.environ.get("modal.state.project_name", "")
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))
assert INPUT_DIR or INPUT_FILE

storage_dir = my_app.data_dir
sly.fs.mkdir(storage_dir, True)
