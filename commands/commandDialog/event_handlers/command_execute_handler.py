import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    get_prefixes,
    set_component_visibility,
    set_user_parameters_via_inputs,
)


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        futil.log("CommandExecuteHandler created")

    def __del__(self):
        futil.log("CommandExecuteHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        futil.log(f"Command Execute Event")

        #  ******************************** Your code here ********************************
        prefixis = get_prefixes()
        for prefix in prefixis:
            set_user_parameters_via_inputs(args.command.commandInputs, prefix)
            set_component_visibility(prefix)
