from collections import defaultdict
import adsk.core, adsk.fusion
from ...lib import fusionAddInUtils as futil


def add_ultrabox(prefix: str):
    """
    Function to add a new ultrabox configuration to the dialog.
    This function will be called when the 'add_ultrabox' button is clicked.
    """
    # global ultrabox_add_fired_preview
    # global ultrabox_add_fired_execute
    # ultrabox_add_fired_preview[prefix] = True
    from .event_handlers.command_execute_handler import CommandExecuteHandler
    from .event_handlers.command_execute_preview_handler import (
        CommandExecutePreviewHandler,
    )

    CommandExecutePreviewHandler.ultrabox_add_fired[prefix] += 1
    CommandExecuteHandler.ultrabox_add_fired[prefix] += 1
    futil.log(
        f"CommandExecutePreviewHandler.ultrabox_add_fired: {CommandExecutePreviewHandler.ultrabox_add_fired}"
    )
    return


def perform_add_ultrabox(prefix: str, index: int):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = design.rootComponent

    futil.log("Adding a new ultrabox configuration")
    # 1) copy the base component named "Ultrabox" - it should exist in the active design
    # find the component named "Ultrabox" in the active design
    ultrabox_base = next(
        (
            occurrence
            for occurrence in rootComp.occurrences
            if occurrence.component.name == "Ultrabox"
        ),
        None,
    )

    if not ultrabox_base:
        futil.log("Ultrabox base component not found")
        return

    new_occurrence = rootComp.occurrences.addNewComponentCopy(
        ultrabox_base.component, adsk.core.Matrix3D.create()
    )

    # 2) change the name of the component to "Ultrabox <number>"
    new_occurrence.component.name = f"Ultrabox {index}"
    new_occurrence.isLightBulbOn = True

    # 3) set the parameters for the component based on the inputs in the dialog

    # 4) add the component to the dialog inputs (the table)


def remove_ultrabox():
    """
    Function to remove an ultrabox configuration from the dialog.
    This function will be called when the 'remove_ultrabox' button is clicked.
    """
    # Logic to remove an ultrabox configuration
    futil.log("Removing an ultrabox configuration")

    ...
