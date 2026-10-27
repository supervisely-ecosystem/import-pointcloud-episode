"""The source in Team Files must be removed only after a complete import, and only the
path the user selected. Each test reproduces one data-loss scenario from the 2026-10
ecosystem security audit (section 2.2), plus the normal success case."""

import json

PCD = b"# .PCD v0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH 0\nHEIGHT 1\nPOINTS 0\nDATA ascii\n"


def episode_project(root, datasets=("ds0",), related_image_without_json=False):
    """A minimal valid pointcloud episode project in Supervisely format under `root`."""
    files = {
        f"{root}/meta.json": json.dumps(
            {"classes": [], "tags": [], "projectType": "point_cloud_episodes"}
        ).encode(),
    }
    for ds in datasets:
        files[f"{root}/{ds}/annotation.json"] = json.dumps(
            {"description": "", "key": "0" * 32, "tags": [], "objects": [], "frames": [], "framesCount": 1}
        ).encode()
        files[f"{root}/{ds}/frame_pointcloud_map.json"] = json.dumps({"0": "0.pcd"}).encode()
        files[f"{root}/{ds}/pointcloud/0.pcd"] = PCD
        if related_image_without_json:
            files[f"{root}/{ds}/related_images/0_pcd/cam0.png"] = b"\x89PNG"
    return files


# --- normal case: unchanged behaviour ---------------------------------------------


def test_success_removes_selected_folder(run_app):
    files = episode_project("/data/proj")
    files["/data/keep_me.txt"] = b"unrelated"
    api = run_app(files, folder="/data/proj/")
    assert api.task.errors == []
    assert api.task.output_projects == [555]
    assert api.file.removed == ["/data/proj/"]
    assert set(api.file.files) == {"/data/keep_me.txt"}
    assert api.app_stopped


def test_success_drag_and_drop_removes_only_app_upload_folder(run_app):
    up = "/import/import-pointcloud-episode/42/"
    files = episode_project(up + "proj")
    files["/import/import-pointcloud-episode/41/other_user_upload/a.pcd"] = PCD
    api = run_app(files, folder=up)
    assert api.task.errors == []
    assert api.file.removed == [up]
    assert set(api.file.files) == {"/import/import-pointcloud-episode/41/other_user_upload/a.pcd"}


def test_success_pcd_only_folder_removes_selected_folder(run_app):
    files = {"/data/scans/a.pcd": PCD, "/data/scans/b.pcd": PCD}
    api = run_app(files, folder="/data/scans/")
    assert api.task.errors == []
    assert sorted(api.pointcloud_episode.uploaded) == ["a.pcd", "b.pcd"]
    assert api.file.removed == ["/data/scans/"]


# --- loss scenario 1: nothing found -> error, but the source was still removed ----


def test_nothing_found_keeps_source(run_app):
    files = {"/data/notes/readme.txt": b"not a pointcloud"}
    api = run_app(files, folder="/data/notes/")
    assert api.task.errors, "the app must report an error"
    assert api.file.removed == []
    assert "/data/notes/readme.txt" in api.file.files
    assert api.app_stopped


# --- loss scenario 2: failed / partial import -> source removed anyway --------------


def test_failed_annotated_upload_keeps_source(run_app):
    """The only project fails to upload with annotations; the pcd-only fallback cannot
    import it either. Old code set an error and then deleted the annotations' only copy."""
    files = episode_project("/data/proj")

    def boom(input_dir):
        raise RuntimeError("server rejected annotation")

    api = run_app(files, folder="/data/proj/", project_upload=boom)
    assert api.task.errors
    assert api.file.removed == []
    assert "/data/proj/ds0/annotation.json" in api.file.files


def test_partial_failure_one_of_two_projects_keeps_source(run_app):
    """Two projects in the selected folder; one uploads, the other fails. Old code counted
    the run as a success (projects_cnt > 0) and deleted both, losing the second one."""
    files = {}
    files.update(episode_project("/data/batch/good"))
    files.update(episode_project("/data/batch/bad"))

    def fail_bad(input_dir):
        if input_dir.rstrip("/").endswith("bad"):
            raise RuntimeError("upload failed")

    api = run_app(files, folder="/data/batch/", project_upload=fail_bad)
    assert api.file.removed == []
    assert "/data/batch/bad/ds0/annotation.json" in api.file.files


def test_skipped_invalid_related_images_keep_source(run_app):
    """validate_local_project drops related images without their JSON; they are not
    imported, so the source must not be removed."""
    files = episode_project("/data/proj", related_image_without_json=True)
    api = run_app(files, folder="/data/proj/")
    assert api.task.errors == []
    assert api.file.removed == []
    assert "/data/proj/ds0/related_images/0_pcd/cam0.png" in api.file.files


def test_pcd_only_nested_dir_skipped_keeps_source(run_app):
    """pcd-only mode: uploading /scans removes its local copy including scans/sub, so
    scans/sub/b.pcd is never uploaded. Old code reported success and deleted b.pcd."""
    files = {"/data/scans/a.pcd": PCD, "/data/scans/sub/b.pcd": PCD}
    api = run_app(files, folder="/data/scans/")
    assert api.pointcloud_episode.uploaded == ["a.pcd"]
    assert api.file.removed == []
    assert "/data/scans/sub/b.pcd" in api.file.files


# --- loss scenario 3: re-pointed parent folder is removed ----------------------------


def test_selected_dataset_folder_does_not_remove_parent(run_app):
    """Selecting a dataset folder re-points INPUT_DIR to the project folder; old code
    removed the whole parent, including files the user never selected."""
    files = episode_project("/data/proj", datasets=("ds0", "ds1"))
    files["/data/proj/my_notes.txt"] = b"never selected, never imported"
    api = run_app(files, folder="/data/proj/ds0/")
    assert api.task.errors == []
    assert api.file.removed == ["/data/proj/ds0/"]
    assert "/data/proj/my_notes.txt" in api.file.files
    assert "/data/proj/ds1/annotation.json" in api.file.files


def test_selected_top_level_dataset_never_removes_team_files_root(run_app):
    """A top-level dataset folder re-points INPUT_DIR to "/"; old code removed "/"."""
    files = {
        "/ds0/annotation.json": b"{}",
        "/ds0/frame_pointcloud_map.json": json.dumps({"0": "0.pcd"}).encode(),
        "/ds0/pointcloud/0.pcd": PCD,
        "/other_team_data/important.bin": b"x",
    }
    api = run_app(files, folder="/ds0/")
    assert "/" not in api.file.removed
    assert "/other_team_data/important.bin" in api.file.files
    assert all(p.startswith("/ds0") for p in api.file.removed)


def test_selected_json_file_does_not_remove_grandparent(run_app):
    """Selecting a .json/image file re-points INPUT_DIR two levels up
    (/data/exports/x/y.json -> /data/exports); only the selected file may be removed."""
    files = {
        "/data/exports/x/y.json": b"{}",
        "/data/exports/scan/0.pcd": PCD,
        "/data/exports/unrelated.csv": b"a,b",
    }
    api = run_app(files, file="/data/exports/x/y.json")
    assert "/data/exports" not in [p.rstrip("/") for p in api.file.removed]
    assert "/data/exports/unrelated.csv" in api.file.files
    assert "/data/exports/scan/0.pcd" in api.file.files
    assert api.file.removed == ["/data/exports/x/y.json"]
