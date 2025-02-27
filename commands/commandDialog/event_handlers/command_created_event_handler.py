import adsk, adsk.core, adsk.cam
from ..utils import create_dialog
from .input_changed_handler import InputChangedHandler

# from .command_destroy_handler import CommandDestroyHandler
from .command_execute_handler import CommandExecuteHandler
from .command_execute_preview_handler import CommandExecutePreviewHandler
from ..inputs_manager import InputsManager
from ....lib import fusionAddInUtils as futil

local_handlers = []


class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        futil.log("CommandDestroyHandler created")

    def __del__(self):
        futil.log("CommandDestroyHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        global local_handlers

        eventArgs = adsk.core.CommandEventArgs.cast(args)
        futil.log(f"Command Destroy Event")
        local_handlers = []


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        futil.log("CommandCreatedEventHandler init")
        super().__init__()

    def __del__(self):
        futil.log("CommandCreatedEventHandler del")
        super().__del__()

    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            global local_handlers
            local_handlers = []
            cmd = args.command
            inputs = cmd.commandInputs

            create_dialog(inputs)

            # inputs_manager = InputsManager(inputs)

            # Connect to the input changed event
            onInputChanged = InputChangedHandler(None, inputs)
            local_handlers.append(onInputChanged)
            cmd.inputChanged.add(onInputChanged)

            onExecute = CommandExecuteHandler()
            local_handlers.append(onExecute)
            cmd.execute.add(onExecute)

            onExecutePreview = CommandExecutePreviewHandler()
            local_handlers.append(onExecutePreview)
            cmd.executePreview.add(onExecutePreview)
            # cmd.validateInputs.add(command_validate_input)

            onDestroy = CommandDestroyHandler()
            local_handlers.append(onDestroy)
            cmd.destroy.add(onDestroy)
        except Exception as e:
            futil.log(f"Error: {e}", adsk.core.LogLevels.ErrorLogLevel)
