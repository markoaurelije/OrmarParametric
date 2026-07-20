from collections import defaultdict
import adsk, adsk.core
from ....lib import fusionAddInUtils as futil
from ..utils import (
    collect_delete_requests,
    reseat_free_wrappers,
    materialize_enabled_parts,
    get_prefixes,
    materialize_pending_cabinets,
    materialize_pending_deletions,
    apply_finish,
    persist_finish_overrides,
    set_component_visibility,
    set_user_parameters_via_inputs,
)
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

        materialize_pending_cabinets(CommandExecuteHandler.pending_cabinets)
        materialize_pending_deletions(CommandExecuteHandler.pending_deletions)

        prefixis = get_prefixes()

        for prefix in prefixis:
            reseat_free_wrappers(prefix)
            set_user_parameters_via_inputs(args.command.commandInputs, prefix)
            materialize_enabled_parts(prefix)
            set_component_visibility(prefix)
            apply_finish(prefix)

            for idx in range(CommandExecuteHandler.ultrabox_add_fired.get(prefix, 0)):
                perform_add_ultrabox(prefix, idx + 1)

        # commit the session's colour + banding clicks to attributes (persistence)
        persist_finish_overrides()
