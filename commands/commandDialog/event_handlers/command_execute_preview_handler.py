from collections import defaultdict
import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    get_prefixes,
    materialize_pending_cabinets,
    set_component_visibility,
    set_user_parameters_via_inputs,
)
from ...commandDialog.ultrabox import perform_add_ultrabox


class CommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    ultrabox_add_fired: dict[str, int] = defaultdict(int)
    pending_cabinets: set = set()

    def __init__(self):
        super().__init__()
        futil.log("CommandExecutePreviewHandler created")
        CommandExecutePreviewHandler.ultrabox_add_fired = defaultdict(int)
        CommandExecutePreviewHandler.pending_cabinets = set()

    def __del__(self):
        futil.log("CommandExecutePreviewHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        futil.log(f"Command Execute Preview Event")

        materialize_pending_cabinets(CommandExecutePreviewHandler.pending_cabinets)

        prefixis = get_prefixes()

        for prefix in prefixis:
            set_user_parameters_via_inputs(args.command.commandInputs, prefix)
            set_component_visibility(prefix)

            for idx in range(
                CommandExecutePreviewHandler.ultrabox_add_fired.get(prefix, 0)
            ):
                perform_add_ultrabox(prefix, idx + 1)

        futil.log(f"Command Execute Preview Event finished")
