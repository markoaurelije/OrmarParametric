import traceback
import adsk
import adsk.core
import adsk.fusion
from ....lib import fusionAddInUtils as futil
from ..inputs_manager import InputsManager
from ..utils import load_preset


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self, inputsManager: InputsManager, inputs):
        super().__init__()
        self.inputsManager = inputsManager
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

            if changed_input.id == "presets":
                selected_preset = changed_input.selectedItem.name
                load_preset(selected_preset, self.inputs)

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
