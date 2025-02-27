import adsk.core
from .utils import load_preset
from ...lib import fusionAddInUtils as futil


class InputsManager:
    def __init__(self):
        pass

    def processChangedInput(
        inputs: adsk.core.CommandInputs, changed_input: adsk.core.CommandInput
    ):
        futil.log(f"processChangedInput: {changed_input.id}")
        if changed_input.id == "presets":
            selected_preset = changed_input.selectedItem.name
            load_preset(selected_preset, inputs)
