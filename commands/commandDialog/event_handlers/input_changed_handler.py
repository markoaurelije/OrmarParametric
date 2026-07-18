import traceback
import adsk
import adsk.core

from ...commandDialog.ultrabox import add_ultrabox, remove_ultrabox
from ....lib import fusionAddInUtils as futil

from ..utils import request_add_cabinet, request_delete_cabinet, load_preset
from ..dialog_config import InputType, input_items


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(
        self,
        #  inputsManager: InputsManager,
        inputs: adsk.core.CommandInputs,
    ):
        super().__init__()
        # self.inputsManager = inputsManager
        self.inputs = inputs
        futil.log("InputChangedHandler created")

    def __del__(self):
        futil.log("InputChangedHandler deleted")

    def notify(self, args: adsk.core.InputChangedEventArgs):
        try:
            # Process the changed input through the dependency manager
            # self.inputsManager.processChangedInput(self.inputs, args.input)
            changed_input = args.input
            futil.log(f"Input changed: {changed_input.id}")

            if changed_input.id.endswith("_presets"):
                prefix = changed_input.id[: -len("presets")]
                selected_preset = changed_input.selectedItem.name
                load_preset(selected_preset, self.inputs, prefix)
                return
            elif changed_input.id == "addPresetButton":
                # get the input valur of 'newComponentName' input
                new_name = next(
                    (input for input in self.inputs if input.id == "newComponentName"),
                    None,
                )
                # the cabinet is generated from code into the active design,
                # so no target-design lookup is needed anymore
                request_add_cabinet(new_name.text if new_name else "Ox")
                return
            elif changed_input.id.endswith("_fronta"):
                # When the Fronta group checkbox is turned ON, ensure at least
                # one door direction (left or right) is also enabled so the
                # user actually sees a door appear.
                prefix = changed_input.id[: -len("fronta")]
                fronta_input = adsk.core.GroupCommandInput.cast(changed_input)
                if fronta_input and fronta_input.isEnabledCheckBoxChecked:
                    lijevo = adsk.core.BoolValueCommandInput.cast(
                        self.inputs.itemById(prefix + "fronta_lijeva")
                    )
                    desno = adsk.core.BoolValueCommandInput.cast(
                        self.inputs.itemById(prefix + "fronta_desna")
                    )
                    if (
                        lijevo is not None
                        and desno is not None
                        and not lijevo.value
                        and not desno.value
                    ):
                        desno.value = True
                        futil.log(
                            f"Fronta ON: auto-enabled {prefix}fronta_desna"
                        )
            elif changed_input.id.endswith("_delete_cabinet"):
                prefix = changed_input.id[: -len("delete_cabinet")]
                futil.log(f"Deleting cabinet with prefix: {prefix}")
                request_delete_cabinet(prefix)
            elif changed_input.id.endswith("add_ultrabox"):
                prefix = changed_input.id.split("add_ultrabox")[0]
                futil.log(f"Adding ultrabox with prefix: {prefix}")
                add_ultrabox(prefix)
            elif changed_input.id.endswith("remove_ultrabox"):
                remove_ultrabox()

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
