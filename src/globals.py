import os
from pathlib import Path
import supervisely as sly
from supervisely.app.v1.app_service import AppService


from distutils.util import strtobool

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
sly.logger.info(f"App root directory: {app_root_directory}")

# debug
# from dotenv import load_dotenv
# load_dotenv(os.path.join(app_root_directory, "debug.env"))
# load_dotenv(os.path.join(app_root_directory, "secret_debug.env"))

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

if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)

storage_dir = my_app.data_dir
sly.fs.mkdir(storage_dir, True)
