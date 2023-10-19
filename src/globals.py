import os
import shutil

from distutils.util import strtobool
from dotenv import load_dotenv
from os.path import basename, dirname, normpath
from pathlib import Path

import supervisely as sly
from supervisely.io.fs import get_file_ext
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


def _files_exists(files, path):
    listdir = [basename(normpath(x)) for x in api.file.listdir(TEAM_ID, path)]
    return all([file_name in listdir for file_name in files])


if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
    if IS_ON_AGENT:
        _, INPUT_DIR = api.file.parse_agent_id_and_path(INPUT_DIR)
    listdir = api.file.listdir(TEAM_ID, INPUT_DIR)
    if len(listdir) == 0:
        raise Exception("Input directory is empty.")
    if len(listdir) == 1 and get_file_ext(listdir[0]) in [".zip", ".tar"]:
        sly.logger.info(
            "Folder mode is selected, but archive file is uploaded. Switching to file mode."
        )
        INPUT_DIR, INPUT_FILE = None, listdir[0]
    elif len(listdir) > 1 and any(get_file_ext(f) in [".zip", ".tar"] for f in listdir):
        raise ValueError("Multiple archives are not supported.")
    elif _files_exists(["annotation.json", "frame_pointcloud_map.json"], INPUT_DIR):
        INPUT_DIR, INPUT_FILE = dirname(normpath(INPUT_DIR)), None

    elif all([get_file_ext(x) in [".json"] + sly.image.SUPPORTED_IMG_EXTS for x in listdir]):
        if basename(dirname(normpath(INPUT_DIR))) == "related_images":
            parent_dir = dirname(dirname(normpath(INPUT_DIR)))
            if _files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                parent_dir = dirname(normpath(parent_dir))
            if parent_dir != "/" and _files_exists(["meta.json"], parent_dir):
                INPUT_DIR, INPUT_FILE = parent_dir, None
    elif (
        basename(normpath(INPUT_DIR)) == "pointcloud" and get_file_ext(listdir[0]) == ".pcd"
    ) or basename(normpath(INPUT_DIR)) == "related_images":
        parent_dir = dirname(normpath(INPUT_DIR))
        if _files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
            parent_dir = dirname(normpath(parent_dir))
        if parent_dir != "/" and _files_exists(["meta.json"], parent_dir):
            INPUT_DIR, INPUT_FILE = parent_dir, None

else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)
    if IS_ON_AGENT:
        _, INPUT_PATH = api.file.parse_agent_id_and_path(INPUT_FILE)
    available_archive_formats = list(zip(*shutil.get_archive_formats()))[0]
    file_ext = sly.fs.get_file_ext(INPUT_FILE)
    if file_ext.lstrip(".") not in available_archive_formats:
        sly.logger.info("File mode is selected, but uploaded file is not archive.")
        if basename(normpath(INPUT_FILE)) in ["meta.json", "key_id_map.json"]:
            INPUT_DIR, INPUT_FILE = dirname(INPUT_FILE), None
        elif basename(normpath(INPUT_FILE)) in ["annotation.json", "frame_pointcloud_map.json"]:
            parent_dir = dirname(dirname(INPUT_FILE))
            if _files_exists(["meta.json"], parent_dir):
                INPUT_DIR, INPUT_FILE = parent_dir, None
        elif sly.image.is_valid_ext(file_ext) or file_ext == ".json":
            parent_dir = dirname(dirname(dirname(normpath(INPUT_FILE))))
            if _files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                parent_dir = dirname(normpath(parent_dir))
            if parent_dir != "/" and _files_exists(["meta.json"], parent_dir):
                INPUT_DIR, INPUT_FILE = parent_dir, None
        elif file_ext == ".pcd":
            parent_dir = dirname(dirname(normpath(INPUT_FILE)))
            if _files_exists(["annotation.json", "frame_pointcloud_map.json"], parent_dir):
                parent_dir = dirname(normpath(parent_dir))
            if parent_dir != "/" and _files_exists(["meta.json"], parent_dir):
                INPUT_DIR, INPUT_FILE = parent_dir, None


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
