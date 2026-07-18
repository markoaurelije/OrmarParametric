import traceback
import adsk
import adsk.core

from ...commandDialog.ultrabox import add_ultrabox, remove_ultrabox
from ...commandDialog import excel_export
from ....lib import fusionAddInUtils as futil

from ..utils import (
    request_add_cabinet,
    request_delete_cabinet,
    load_preset,
    set_board_decor,
    set_edge_band,
    apply_finish,
)
from ..dialog_config import InputType, input_items


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(
        self,
        #  inputsManager: InputsManager,
        inputs: adsk.core.CommandInputs,
    ):
        super().__init__()
        # self.inputsManager = inputsManager
        self.inputs = inputs
        futil.log("InputChangedHandler created")

    def __del__(self):
        futil.log("InputChangedHandler deleted")

    def notify(self, args: adsk.core.InputChangedEventArgs):
        try:
            # Process the changed input through the dependency manager
            # self.inputsManager.processChangedInput(self.inputs, args.input)
            changed_input = args.input
            futil.log(f"Input changed: {changed_input.id}")

            if changed_input.id in ("finish_paint_select", "finish_band_select"):
                # momentary pickers: paint the clicked board the active decor /
                # toggle the clicked edge's banding, then clear so the next click
                # works again.  Re-fires with selectionCount == 0, which this
                # ignores.
                is_band = changed_input.id == "finish_band_select"
                decor_dd = self.inputs.itemById("finish_active_decor")
                active_decor = (
                    decor_dd.selectedItem.name
                    if decor_dd and decor_dd.selectedItem
                    else None
                )
                sel_input = adsk.core.SelectionCommandInput.cast(changed_input)
                if sel_input and sel_input.selectionCount > 0:
                    touched = set()
                    for i in range(sel_input.selectionCount):
                        entity = sel_input.selection(i).entity
                        if not active_decor:
                            result = None
                        elif is_band:
                            result = set_edge_band(entity, active_decor)
                        else:
                            result = set_board_decor(entity, active_decor)
                        if result:
                            touched.add(result[0])
                            futil.log(f"Finish change: {result}")
                    sel_input.clearSelection()
                    # repaint the affected cabinet(s) now for immediate feedback
                    # (the executePreview pass repaints too, but may not fire on
                    # a selection-only change).
                    for prefix in touched:
                        apply_finish(prefix)
                return

            if changed_input.id.endswith("_presets"):
                prefix = changed_input.id[: -len("presets")]
                selected_preset = changed_input.selectedItem.name
                load_preset(selected_preset, self.inputs, prefix)
                return
            elif changed_input.id == "addPresetButton":
                # get the input valur of 'newComponentName' input
                new_name = next(
                    (input for input in self.inputs if input.id == "newComponentName"),
                    None,
                )
                # the cabinet is generated from code into the active design,
                # so no target-design lookup is needed anymore
                request_add_cabinet(new_name.text if new_name else "Ox")
                return
            elif changed_input.id == "exportCutListButton":
                app = adsk.core.Application.get()
                ui = app.userInterface
                try:
                    output_path = excel_export.export_cut_list()
                except Exception:
                    ui.messageBox(
                        "Izvoz krojne liste nije uspio:\n{}".format(
                            traceback.format_exc()
                        )
                    )
                else:
                    if output_path:
                        ui.messageBox(f"Krojna lista spremljena:\n{output_path}")
                    else:
                        ui.messageBox(
                            "Nema ormara za izvoz u ovom dizajnu."
                        )
                return
            elif changed_input.id.endswith("_fronta"):
                # When the Fronta group checkbox is turned ON, ensure at least
                # one door direction (left or right) is also enabled so the
                # user actually sees a door appear.
                prefix = changed_input.id[: -len("fronta")]
                fronta_input = adsk.core.GroupCommandInput.cast(changed_input)
                if fronta_input and fronta_input.isEnabledCheckBoxChecked:
                    lijevo = adsk.core.BoolValueCommandInput.cast(
                        self.inputs.itemById(prefix + "fronta_lijeva")
                    )
                    desno = adsk.core.BoolValueCommandInput.cast(
                        self.inputs.itemById(prefix + "fronta_desna")
                    )
                    if (
                        lijevo is not None
                        and desno is not None
                        and not lijevo.value
                        and not desno.value
                    ):
                        desno.value = True
                        futil.log(
                            f"Fronta ON: auto-enabled {prefix}fronta_desna"
                        )
            elif changed_input.id.endswith("_delete_cabinet"):
                prefix = changed_input.id[: -len("delete_cabinet")]
                futil.log(f"Deleting cabinet with prefix: {prefix}")
                request_delete_cabinet(prefix)
            elif changed_input.id.endswith("add_ultrabox"):
                prefix = changed_input.id.split("add_ultrabox")[0]
                futil.log(f"Adding ultrabox with prefix: {prefix}")
                add_ultrabox(prefix)
            elif changed_input.id.endswith("remove_ultrabox"):
                remove_ultrabox()

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
