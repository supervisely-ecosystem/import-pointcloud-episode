import os
import supervisely_lib as sly

api: sly.Api = sly.Api.from_env()
my_app: sly.AppService = sly.AppService()

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = os.environ["context.teamId"]
WORKSPACE_ID = os.environ["context.workspaceId"]
INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")
assert INPUT_DIR or INPUT_FILE

storage_dir = my_app.data_dir
sly.fs.mkdir(storage_dir, True)