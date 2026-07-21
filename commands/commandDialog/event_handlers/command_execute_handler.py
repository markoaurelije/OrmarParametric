from collections import defaultdict
import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    collect_delete_requests,
    materialize_pending_cabinets,
    materialize_pending_deletions,
    persist_finish_overrides,
    update_cabinets,
)
from ..preview_state import session_state
from ...commandDialog.ultrabox import perform_add_ultrabox


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    ultrabox_add_fired: dict[str, int] = defaultdict(int)
    # cabinet name -> template ("predložak") name, or None for the base cabinet
    pending_cabinets: dict = {}
    pending_deletions: set = set()

    def __init__(self):
        super().__init__()
        futil.log("CommandExecuteHandler created")
        CommandExecuteHandler.ultrabox_add_fired = defaultdict(int)
        CommandExecuteHandler.pending_cabinets = {}
        CommandExecuteHandler.pending_deletions = set()

    def __del__(self):
        futil.log("CommandExecuteHandler deleted")

    def notify(self, args: adsk.core.CommandEventArgs):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        futil.log(f"Command Execute Event")

        # Belt-and-suspenders: scan inputs for pressed delete buttons
        # in case inputChanged didn't fire for a button inside a tab.
        # This calls request_delete_cabinet which populates *both*
        # pending_deletions sets.
        collect_delete_requests(args.command.commandInputs)

        deleting_prefixes = set(CommandExecuteHandler.pending_deletions)
        materialize_pending_cabinets(CommandExecuteHandler.pending_cabinets)
        materialize_pending_deletions(CommandExecuteHandler.pending_deletions)
        session_state.discard(deleting_prefixes)

        prefixes = session_state.execute_prefixes()
        prefixes.update(
            f"{name}_" for name in CommandExecuteHandler.pending_cabinets
        )
        prefixes.update(CommandExecuteHandler.ultrabox_add_fired)
        prefixes.difference_update(deleting_prefixes)

        succeeded = update_cabinets(args.command.commandInputs, prefixes)
        failed = prefixes - succeeded
        if failed:
            CommandExecuteHandler.pending_deletions.update(deleting_prefixes)
            eventArgs.executeFailed = True
            eventArgs.executeFailedMessage = (
                "Ažuriranje ormara nije uspjelo: "
                + ", ".join(prefix.rstrip("_") for prefix in sorted(failed))
            )
            return

        for prefix in sorted(succeeded):
            for idx in range(CommandExecuteHandler.ultrabox_add_fired.get(prefix, 0)):
                perform_add_ultrabox(prefix, idx + 1)

        # commit the session's colour + banding clicks to attributes (persistence)
        persist_finish_overrides()
