import traceback
import adsk
import adsk.core

from ...commandDialog.ultrabox import add_ultrabox, remove_ultrabox
from ....lib import fusionAddInUtils as futil

from ..utils import add_parametric_component, load_preset
from ..dialog_config import InputType, input_items


persistant_target_design_name = None


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
        global persistant_target_design_name
        try:
            # Process the changed input through the dependency manager
            # self.inputsManager.processChangedInput(self.inputs, args.input)
            changed_input = args.input
            futil.log(f"Input changed: {changed_input.id}")

            if changed_input.id == "presets":
                selected_preset = changed_input.selectedItem.name
                load_preset(selected_preset, self.inputs)
                return
            elif changed_input.id == "addPresetButton":
                # get the input valur of 'newComponentName' input
                new_name = next(
                    (input for input in self.inputs if input.id == "newComponentName"),
                    None,
                )

                # ask the user to input a name for target design, open a dialog
                app = adsk.core.Application.get()
                ui = app.userInterface
                target_design_name, canceled = ui.inputBox(
                    "Enter a name for the target design:",
                    "Test Design Name",
                    persistant_target_design_name or "Test Design",
                )
                if canceled:
                    futil.log("User canceled the input box")
                    return

                add_parametric_component(
                    new_name.text if new_name else "Ox",
                    target_design_name=target_design_name,
                )
                persistant_target_design_name = target_design_name
                return
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
