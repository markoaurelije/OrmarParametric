from collections import defaultdict
import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    collect_delete_requests,
    materialize_pending_cabinets,
    materialize_pending_deletions,
    refresh_colors_in_use,
    update_cabinets,
)
from ..preview_state import session_state
from ...commandDialog.ultrabox import perform_add_ultrabox


class CommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    ultrabox_add_fired: dict[str, int] = defaultdict(int)
    # cabinet name -> template ("predložak") name, or None for the base cabinet
    pending_cabinets: dict = {}
    pending_deletions: set = set()

    def __init__(self):
        super().__init__()
        futil.log("CommandExecutePreviewHandler created")
        CommandExecutePreviewHandler.ultrabox_add_fired = defaultdict(int)
        CommandExecutePreviewHandler.pending_cabinets = {}
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

        deleting_prefixes = set(CommandExecutePreviewHandler.pending_deletions)
        materialize_pending_cabinets(CommandExecutePreviewHandler.pending_cabinets)
        # Preview cannot delete user parameters (Fusion API restriction) —
        # only remove the occurrence for visual feedback.  Full cleanup
        # (params + occurrence) happens on execute.
        materialize_pending_deletions(
            CommandExecutePreviewHandler.pending_deletions, delete_params=False
        )
        CommandExecutePreviewHandler.pending_deletions.update(deleting_prefixes)
        session_state.discard(deleting_prefixes)

        prefixes = session_state.preview_prefixes()
        prefixes.update(
            f"{name}_" for name in CommandExecutePreviewHandler.pending_cabinets
        )
        prefixes.update(CommandExecutePreviewHandler.ultrabox_add_fired)
        prefixes.difference_update(deleting_prefixes)

        succeeded = update_cabinets(args.command.commandInputs, prefixes)
        session_state.mark_preview_succeeded(succeeded)

        for prefix in sorted(succeeded):
            for idx in range(
                CommandExecutePreviewHandler.ultrabox_add_fired.get(prefix, 0)
            ):
                perform_add_ultrabox(prefix, idx + 1)

        if succeeded:
            refresh_colors_in_use(args.command.commandInputs)

        futil.log(f"Command Execute Preview Event finished")
