"""Offline test harness: a fake `globals` module and a small in-memory fake Supervisely API.

Nothing here talks to a Supervisely server. The app code is imported from ../src
(or from $APP_SRC, which lets the same tests run against an older checkout).

Run:  pip install -r dev_requirements.txt pytest && python -m pytest tests
"""

import os
import shutil
import sys
import types

import pytest

SRC = os.environ.get(
    "APP_SRC", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)
SRC = os.path.abspath(SRC)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import supervisely as sly  # noqa: E402
from supervisely.api.module_api import ApiField  # noqa: E402


def _make_fake_globals():
    """globals.py creates a real Api/AppService at import time; build a stand-in that
    keeps the app's real constants (everything after the env/bootstrap section)."""
    g = types.ModuleType("globals")
    with open(os.path.join(SRC, "globals.py")) as fh:
        text = fh.read()
    consts = text[text.index("RELATED_IMAGES_ANN_FIELDS") :]
    exec(consts, {"ApiField": ApiField}, g.__dict__)
    return g


sys.modules["globals"] = _make_fake_globals()


class FakeMyApp:
    def __init__(self):
        self.stopped = False

    def stop(self, *args, **kwargs):
        self.stopped = True


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeFileApi:
    """Team Files as a dict {"/abs/path/file": bytes}; directories are implicit."""

    def __init__(self, files):
        self.files = dict(files)
        self.removed = []

    @staticmethod
    def _dir_prefix(path):
        return path.rstrip("/") + "/"

    def listdir(self, team_id, path, recursive=False):
        prefix = self._dir_prefix(path)
        out = set()
        for p in self.files:
            if p.startswith(prefix):
                rest = p[len(prefix) :]
                out.add(prefix + rest.split("/")[0])
        return sorted(out)

    def get_directory_size(self, team_id, path):
        prefix = self._dir_prefix(path)
        return sum(len(v) for p, v in self.files.items() if p.startswith(prefix))

    def download_directory(self, team_id, remote_path, local_save_path, progress_cb=None):
        prefix = self._dir_prefix(remote_path)
        for p, data in self.files.items():
            if p.startswith(prefix):
                dst = os.path.join(local_save_path, p[len(prefix) :])
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as fh:
                    fh.write(data)

    def get_info_by_path(self, team_id, path):
        return Obj(sizeb=len(self.files[path]))

    def download(self, team_id, remote_path, local_save_path, cache=None, progress_cb=None):
        os.makedirs(os.path.dirname(local_save_path), exist_ok=True)
        with open(local_save_path, "wb") as fh:
            fh.write(self.files[remote_path])

    def is_on_agent(self, path):
        return False

    def remove(self, team_id, path):
        self.removed.append(path)
        prefix = self._dir_prefix(path)
        for p in list(self.files):
            if p == path or p.startswith(prefix):
                del self.files[p]


class FakeTaskApi:
    def __init__(self):
        self.errors = []
        self.output_projects = []

    def set_output_error(self, task_id, title, description=None, *a, **kw):
        self.errors.append(title)

    def set_output_project(self, task_id, project_id, project_name=None, *a, **kw):
        self.output_projects.append(project_id)


class FakeProjectApi:
    def __init__(self):
        self.created = {}
        self.removed = []

    def create(self, workspace_id, name, type=None, change_name_if_conflict=False, **kw):
        pid = 100 + len(self.created)
        self.created[pid] = Obj(id=pid, name=name)
        return self.created[pid]

    def remove(self, project_id):
        self.removed.append(project_id)

    def get_info_by_id(self, project_id):
        return self.created[project_id]


class FakeDatasetApi:
    def __init__(self):
        self.n = 0

    def create(self, project_id, name, change_name_if_conflict=False, **kw):
        self.n += 1
        return Obj(id=1000 + self.n, name=name)


class FakePointcloudEpisodeApi:
    def __init__(self):
        self.uploaded = []

    def upload_paths(self, dataset_id, names, paths, progress_cb=None, metas=None):
        self.uploaded.extend(names)
        return [Obj(id=i, name=n) for i, n in enumerate(names)]


class FakeApi:
    def __init__(self, files):
        self.file = FakeFileApi(files)
        self.task = FakeTaskApi()
        self.project = FakeProjectApi()
        self.dataset = FakeDatasetApi()
        self.pointcloud_episode = FakePointcloudEpisodeApi()


@pytest.fixture
def run_app(tmp_path, monkeypatch):
    """Returns run(files, folder=None, file=None, project_upload=None) -> FakeApi.

    `project_upload(input_dir)` replaces the SDK's upload_pointcloud_episode_project:
    return normally for success, raise to simulate a failed annotated upload.
    """
    import functions  # noqa: F401  (imported after the fake globals)
    import main

    g = sys.modules["globals"]

    def run(files, folder=None, file=None, project_upload=None):
        api = FakeApi(files)
        storage = tmp_path / "app_data"
        if storage.exists():
            shutil.rmtree(storage)
        storage.mkdir()
        monkeypatch.setattr(g, "api", api, raising=False)
        monkeypatch.setattr(g, "my_app", FakeMyApp(), raising=False)
        monkeypatch.setattr(g, "TASK_ID", 1, raising=False)
        monkeypatch.setattr(g, "TEAM_ID", 7, raising=False)
        monkeypatch.setattr(g, "WORKSPACE_ID", 9, raising=False)
        monkeypatch.setattr(g, "INPUT_DIR", folder, raising=False)
        monkeypatch.setattr(g, "INPUT_FILE", file, raising=False)
        monkeypatch.setattr(g, "OUTPUT_PROJECT_NAME", "", raising=False)
        monkeypatch.setattr(g, "REMOVE_SOURCE", True, raising=False)
        monkeypatch.setattr(g, "IS_ON_AGENT", False, raising=False)
        monkeypatch.setattr(g, "storage_dir", str(storage), raising=False)

        def fake_upload(input_dir, api_, workspace_id, project_name=None, log_progress=True):
            if project_upload is not None:
                project_upload(input_dir)
            return 555, project_name

        monkeypatch.setattr(main, "upload_pointcloud_episode_project", fake_upload)
        monkeypatch.setattr(main.w, "workflow_output", lambda *a, **kw: None)
        main.import_pointcloud_episode(api, 1)
        api.app_stopped = g.my_app.stopped
        return api

    return run
