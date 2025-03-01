import traceback
import adsk
import adsk.core
import adsk.fusion
import time
from ....lib import fusionAddInUtils as futil

# from ..inputs_manager import InputsManager
from ..utils import load_preset, set_input_via_userparam, set_user_parameter
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

            if changed_input.id == "presets":
                selected_preset = changed_input.selectedItem.name
                load_preset(selected_preset, self.inputs)

            # track time execution of this part of code, start timer here
            start_time = time.time()
            # find this input in InputItems list, and check if it has dependencies
            for input_item in input_items:
                if input_item.name == changed_input.id:
                    for dependency in input_item.dependencies:
                        if input_item.type == InputType.GROUP_WITH_CHECKBOX:
                            value = changed_input.isEnabledCheckBoxChecked
                        elif input_item.type == InputType.BOOL:
                            value = changed_input.value
                        if dependency.triggerring_value == value:
                            # find the input that needs changing
                            d_input = next(
                                (
                                    input
                                    for input in input_items
                                    if input.name == dependency.name
                                ),
                                None,
                            )
                            if d_input:
                                futil.log(
                                    f"Changing dependency input: {dependency.name} to {dependency.value}"
                                )
                                set_user_parameter(d_input.user_param, dependency.value)
                                set_input_via_userparam(d_input, self.inputs)
                    break
            # track time execution of this part of code, end timer here
            end_time = time.time()
            execution_time = end_time - start_time
            futil.log(f"Execution time: {execution_time} seconds")

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
