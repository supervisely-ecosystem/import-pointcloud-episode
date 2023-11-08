import os

from distutils.util import strtobool
from dotenv import load_dotenv
from pathlib import Path

import supervisely as sly
from supervisely.api.module_api import ApiField
from supervisely.app.v1.app_service import AppService


app_root_directory = str(Path(__file__).parent.absolute().parents[0])
sly.logger.info(f"App root directory: {app_root_directory}")


if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()
my_app = AppService()

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = os.environ["context.teamId"]
WORKSPACE_ID = os.environ["context.workspaceId"]
INPUT_DIR = os.environ.get("modal.state.slyFolder")
INPUT_FILE = os.environ.get("modal.state.slyFile")

OUTPUT_PROJECT_NAME = os.environ.get("modal.state.project_name", "")
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))

if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)

storage_dir = my_app.data_dir
sly.fs.mkdir(storage_dir, True)

# related images annotation files required fields
RELATED_IMAGES_ANN_FIELDS = [ApiField.NAME, ApiField.META]
RELATED_IMAGES_SENSOR_DATA = "sensorsData"
RELATED_IMAGES_SENSOR_DATA_FIELDS = {"extrinsicMatrix": 12, "intrinsicMatrix": 9}

# COMMON ERROR MESSAGES
RELATED_IMAGES_ANN_NOT_FOUND = "Related image JSON annotation file not found"
RELATED_IMAGES_ANN_WRONG_FIELDS = (
    lambda x: f"Related image annotation JSON must contain '{x}' field"
)
RELATED_IMAGES_ANN_META_TYPE = (
    "Related image annotation JSON 'meta' field value must be a dictionary"
)

RELATED_IMAGES_ANN_WRONG_NAME = (
    "Related image annotation JSON wrong format - 'name' field value contains wrong image path"
)
SENSOR_DATA_NOT_FOUND = "Sensor data not found in related image annotation 'meta' field"
SENSOR_DATA_TYPE = "'SensorData' field value must be a dictionary"
SENSOR_DATA_FIELD = lambda field: f"Sensor data field '{field}' not found in 'sensorsData' field"
SENSOR_DATA_FIELDS_TYPE = lambda field: f"Sensor data '{field}' field value must be a list"
SENSOR_DATA_WRONG_LENGTH = (
    lambda x: f"Sensor data '{x['field']}' must contain {x['length']} numbers"
)
