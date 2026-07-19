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
    # 1) copy this cabinet's hidden Ultrabox template.  Components are now scoped
    #    to the cabinet ('<prefix>Ultrabox') and the template lives inside the
    #    cabinet's wrapper occurrence, so search that wrapper's subtree.
    cabinet = prefix.rstrip("_")
    wrapper = next(
        (o for o in rootComp.occurrences if o.component.name == cabinet), None
    )
    search_scope = wrapper.component.occurrences if wrapper else rootComp.occurrences
    template_name = prefix + "Ultrabox"
    ultrabox_base = next(
        (
            occurrence
            for occurrence in search_scope
            if occurrence.component.name == template_name
        ),
        None,
    )

    if not ultrabox_base:
        futil.log(f"Ultrabox base component '{template_name}' not found")
        return

    new_occurrence = search_scope.addNewComponentCopy(
        ultrabox_base.component, adsk.core.Matrix3D.create()
    )

    # 2) change the name of the component to "<prefix>Ultrabox <number>"
    new_occurrence.component.name = f"{prefix}Ultrabox {index}"
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
