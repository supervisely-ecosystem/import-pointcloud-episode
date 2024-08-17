
# This module contains the functions that are used to configure the input and output of the workflow for the current app.

import supervisely as sly

def workflow_input(api):
    raise NotImplementedError

def workflow_output(api: sly.Api, project_id: int):
    api.app.workflow.add_output_project(project_id)
    sly.logger.debug(f"Workflow: Output project - {project_id}")