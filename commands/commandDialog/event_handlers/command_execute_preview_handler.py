from collections import defaultdict
import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    collect_delete_requests,
    get_prefixes,
    materialize_pending_cabinets,
    materialize_pending_deletions,
    set_component_visibility,
    set_user_parameters_via_inputs,
)
from ...commandDialog.ultrabox import perform_add_ultrabox


class CommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    ultrabox_add_fired: dict[str, int] = defaultdict(int)
    pending_cabinets: set = set()
    pending_deletions: set = set()

    def __init__(self):
        super().__init__()
        futil.log("CommandExecutePreviewHandler created")
        CommandExecutePreviewHandler.ultrabox_add_fired = defaultdict(int)
        CommandExecutePreviewHandler.pending_cabinets = set()
        CommandExecutePreviewHandler.pending_deletions = set()

    def __del__(self):
        futil.log("CommandExecutePreviewHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        futil.log(f"Command Execute Preview Event")

        # Belt-and-suspenders: scan inputs for pressed delete buttons
        # in case inputChanged didn't fire for a button inside a tab.
        # This calls request_delete_cabinet which populates *both*
        # pending_deletions sets.
        collect_delete_requests(args.command.commandInputs)

        materialize_pending_cabinets(CommandExecutePreviewHandler.pending_cabinets)
        # Preview cannot delete user parameters (Fusion API restriction) —
        # only remove the occurrence for visual feedback.  Full cleanup
        # (params + occurrence) happens on execute.
        materialize_pending_deletions(
            CommandExecutePreviewHandler.pending_deletions, delete_params=False
        )

        prefixis = get_prefixes()

        for prefix in prefixis:
            set_user_parameters_via_inputs(args.command.commandInputs, prefix)
            set_component_visibility(prefix)

            for idx in range(
                CommandExecutePreviewHandler.ultrabox_add_fired.get(prefix, 0)
            ):
                perform_add_ultrabox(prefix, idx + 1)

        futil.log(f"Command Execute Preview Event finished")
