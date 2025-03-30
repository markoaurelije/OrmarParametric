import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    get_prefixes,
    set_component_visibility,
    set_user_parameters_via_inputs,
)


class CommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        futil.log("CommandExecutePreviewHandler created")

    def __del__(self):
        futil.log("CommandExecutePreviewHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        futil.log(f"Command Execute Preview Event")

        prefixis = get_prefixes()
        for prefix in prefixis:
            set_user_parameters_via_inputs(args.command.commandInputs, prefix)
            set_component_visibility(prefix)

        futil.log(f"Command Execute Preview Event finished")
