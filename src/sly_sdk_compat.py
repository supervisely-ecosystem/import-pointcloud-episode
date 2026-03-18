import supervisely as sly


_PATCHED = False


class _StrWithRemoveSuffix(str):
    def removesuffix(self, suffix):
        if suffix == "":
            return str(self)
        if self.endswith(suffix):
            return self[: -len(suffix)]
        return str(self)


def _wrap_str_with_removesuffix(value: str):
    if isinstance(value, str) and not hasattr(value, "removesuffix"):
        return _StrWithRemoveSuffix(value)
    return value


def _patch_project_read_single(ProjectCls) -> None:
    read_single = getattr(ProjectCls, "read_single", None)
    if read_single is None:
        return

    if getattr(read_single, "__name__", "") == "_read_single_compat":
        return

    try:
        original_func = read_single.__func__
    except AttributeError:
        original_func = read_single

    def _read_single_compat(cls, directory):
        project = original_func(cls, directory)
        try:
            for dataset in project.datasets:
                try:
                    if hasattr(dataset, "_name"):
                        dataset._name = _wrap_str_with_removesuffix(dataset._name)
                    else:
                        # Fallback for unexpected SDK changes
                        dataset_name = getattr(dataset, "name", None)
                        wrapped = _wrap_str_with_removesuffix(dataset_name)
                        if wrapped is not dataset_name:
                            setattr(dataset, "_name", wrapped)
                except Exception:
                    continue
        except Exception:
            pass
        return project

    ProjectCls.read_single = classmethod(_read_single_compat)


def patch_supervisely_sdk_for_py38() -> None:
    """Work around Supervisely SDK usage of `str.removesuffix()` on Python 3.8.

    Supervisely SDK v6.73.511 contains a few `.removesuffix()` calls on plain strings.
    Since this method exists only in Python >= 3.9, the calls raise AttributeError
    in older runtimes (e.g. docker images based on Python 3.8).

    This patch wraps dataset names returned by `read_single()` into a `str` subclass
    that provides a compatible `.removesuffix()` implementation.
    """

    global _PATCHED
    if _PATCHED:
        return

    if hasattr(str, "removesuffix"):
        _PATCHED = True
        return

    try:
        from supervisely.project.pointcloud_episode_project import (
            PointcloudEpisodeProject,
        )
        from supervisely.project.pointcloud_project import PointcloudProject

        _patch_project_read_single(PointcloudEpisodeProject)
        _patch_project_read_single(PointcloudProject)
        sly.logger.info(
            "Applied Python 3.8 compatibility patch for Supervisely SDK (.removesuffix)."
        )
    except Exception as e:
        sly.logger.warning(
            "Failed to apply Python 3.8 compatibility patch for Supervisely SDK: %s", e
        )

    _PATCHED = True
