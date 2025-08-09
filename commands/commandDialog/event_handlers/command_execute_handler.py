from collections import defaultdict
import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    get_prefixes,
    set_component_visibility,
    set_user_parameters_via_inputs,
)
from ...commandDialog.ultrabox import perform_add_ultrabox


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    ultrabox_add_fired: dict[str, int] = defaultdict(int)

    def __init__(self):
        super().__init__()
        futil.log("CommandExecuteHandler created")
        CommandExecuteHandler.ultrabox_add_fired = defaultdict(int)

    def __del__(self):
        futil.log("CommandExecuteHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        futil.log(f"Command Execute Event")

        prefixis = get_prefixes()

        for prefix in prefixis:
            set_user_parameters_via_inputs(args.command.commandInputs, prefix)
            set_component_visibility(prefix)

            for idx in range(CommandExecuteHandler.ultrabox_add_fired.get(prefix, 0)):
                perform_add_ultrabox(prefix, idx + 1)
