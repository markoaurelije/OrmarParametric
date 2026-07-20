import traceback
import adsk
import adsk.core

from ...commandDialog.ultrabox import add_ultrabox, remove_ultrabox
from ...commandDialog import excel_export
from ...commandDialog import iverpan_export
from ....lib import fusionAddInUtils as futil

from ..utils import (
    request_add_cabinet,
    request_delete_cabinet,
    load_preset,
    save_cabinet_as_preset,
    refresh_preset_dropdowns,
    next_free_cabinet_name,
    set_board_decor,
    set_edge_band,
    swap_project_decor,
    refresh_colors_in_use,
    apply_finish,
    NO_PRESET_ITEM,
    PRESET_PLACEHOLDER,
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

            if changed_input.id in (
                "finish_paint_select",
                "finish_band_select",
                "finish_swap_select",
            ):
                # momentary pickers: paint the clicked board the active decor /
                # toggle the clicked edge's banding / swap that colour across the
                # whole project, then clear so the next click works again.
                # Re-fires with selectionCount == 0, which this ignores.
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
                            continue
                        if changed_input.id == "finish_band_select":
                            result = set_edge_band(entity, active_decor)
                            if result:
                                touched.add(result[0])
                        elif changed_input.id == "finish_swap_select":
                            # (source, target, affected_prefixes)
                            result = swap_project_decor(entity, active_decor)
                            if result:
                                touched.update(result[2])
                        else:  # finish_paint_select
                            result = set_board_decor(entity, active_decor)
                            if result:
                                touched.add(result[0])
                        if result:
                            futil.log(f"Finish change: {result}")
                    sel_input.clearSelection()
                    # repaint the affected cabinet(s) now for immediate feedback
                    # (the executePreview pass repaints too, but may not fire on
                    # a selection-only change).
                    for prefix in touched:
                        apply_finish(prefix)
                    if touched:
                        refresh_colors_in_use(self.inputs)
                return

            if changed_input.id.endswith("_presets"):
                prefix = changed_input.id[: -len("presets")]
                selected = changed_input.selectedItem
                if selected and selected.name != PRESET_PLACEHOLDER:
                    load_preset(selected.name, self.inputs, prefix)
                return
            elif changed_input.id.endswith("_save_preset"):
                # Save this cabinet's current parameters as a named template.
                prefix = changed_input.id[: -len("save_preset")]
                app = adsk.core.Application.get()
                ui = app.userInterface
                # Default to the tab's currently selected template so plain
                # Enter edits (overwrites) it; otherwise suggest the cabinet's
                # own name as a starting point.
                dropdown = adsk.core.DropDownCommandInput.cast(
                    self.inputs.itemById(f"{prefix}presets")
                )
                default_name = (
                    dropdown.selectedItem.name
                    if dropdown
                    and dropdown.selectedItem
                    and dropdown.selectedItem.name != PRESET_PLACEHOLDER
                    else prefix.rstrip("_")
                )
                name, cancelled = ui.inputBox(
                    "Ime predloška (postojeće ime = prepiši):",
                    "Spremi predložak",
                    default_name,
                )
                if cancelled or not name.strip():
                    return
                save_cabinet_as_preset(prefix, name.strip())
                refresh_preset_dropdowns(self.inputs)
                ui.messageBox(f"Predložak '{name.strip()}' spremljen.")
                return
            elif changed_input.id == "addCabinetButton":
                # Ask for the name in a plain modal prompt (no inline field, so
                # no Fusion parameter-name autocomplete) pre-filled with the next
                # free name.  The cabinet is generated from code into the active
                # design (from the template chosen in the "Predložak" dropdown),
                # so no target-design lookup is needed.
                app = adsk.core.Application.get()
                ui = app.userInterface
                preset_dd = adsk.core.DropDownCommandInput.cast(
                    self.inputs.itemById("new_cabinet_preset")
                )
                preset_name = (
                    preset_dd.selectedItem.name
                    if preset_dd and preset_dd.selectedItem
                    else None
                )
                if preset_name == NO_PRESET_ITEM:
                    preset_name = None
                name, cancelled = ui.inputBox(
                    "Ime novog ormara:", "Dodaj ormar", next_free_cabinet_name()
                )
                if cancelled or not name.strip():
                    return
                request_add_cabinet(name.strip(), preset_name)
                return
            elif changed_input.id == "exportCutListButton":
                app = adsk.core.Application.get()
                ui = app.userInterface
                try:
                    output_paths = excel_export.export_cut_list()
                except Exception:
                    ui.messageBox(
                        "Izvoz krojne liste nije uspio:\n{}".format(
                            traceback.format_exc()
                        )
                    )
                else:
                    if output_paths is None:
                        ui.messageBox("Nema ormara za izvoz u ovom dizajnu.")
                    else:
                        paths_text = "\n".join(output_paths)
                        ui.messageBox(f"Krojna lista spremljena:\n{paths_text}")
                return
            elif changed_input.id == "exportIverpanButton":
                app = adsk.core.Application.get()
                ui = app.userInterface
                try:
                    output_path = iverpan_export.export_cut_list()
                except Exception:
                    ui.messageBox(
                        "Izvoz krojne liste za Iverpan nije uspio:\n{}".format(
                            traceback.format_exc()
                        )
                    )
                else:
                    if output_path is None:
                        ui.messageBox("Nema ormara za izvoz u ovom dizajnu.")
                    else:
                        ui.messageBox(
                            "Krojna lista za Iverpan spremljena:\n{}\n\n"
                            "Šifre materijala i rubnih traka su naši nazivi "
                            "dekora -- zamijeni ih pravim Iverpan šiframa "
                            "prije slanja narudžbe.".format(output_path)
                        )
                return
            elif changed_input.id == "chooseExportFolderButton":
                app = adsk.core.Application.get()
                ui = app.userInterface
                folder_dialog = ui.createFolderDialog()
                folder_dialog.title = "Odaberi mapu za izvoz krojne liste"
                current = excel_export.get_export_folder()
                if current:
                    folder_dialog.initialDirectory = current
                if folder_dialog.showDialog() == adsk.core.DialogResults.DialogOK:
                    excel_export.set_export_folder(folder_dialog.folder)
                    label = adsk.core.TextBoxCommandInput.cast(
                        self.inputs.itemById("exportFolderLabel")
                    )
                    if label:
                        label.text = folder_dialog.folder
                return
            elif changed_input.id.endswith("_fronta"):
                # When the Fronta group checkbox is turned ON, ensure some
                # opening style is enabled so the user actually sees a door
                # appear -- but only if none of the four is already on.
                prefix = changed_input.id[: -len("fronta")]
                fronta_input = adsk.core.GroupCommandInput.cast(changed_input)
                if fronta_input and fronta_input.isEnabledCheckBoxChecked:
                    boxes = {
                        name: adsk.core.BoolValueCommandInput.cast(
                            self.inputs.itemById(prefix + "fronta_" + name)
                        )
                        for name in ("lijeva", "desna", "gore", "dolje")
                    }
                    if not any(b is not None and b.value for b in boxes.values()):
                        if boxes["desna"] is not None:
                            boxes["desna"].value = True
                            futil.log(
                                f"Fronta ON: auto-enabled {prefix}fronta_desna"
                            )
            elif changed_input.id.endswith(
                ("fronta_lijeva", "fronta_desna", "fronta_gore", "fronta_dolje")
            ):
                # Exactly one opening style at a time.  The side-hinged pair
                # (lijeva/desna, which may both be on for a two-door cabinet)
                # and the flaps are mutually exclusive; and a flap is always a
                # single full-width panel, so gore and dolje exclude each other
                # too.  Only act when a box is switched ON -- the clearing
                # writes below re-enter this handler with value False and stop.
                box = adsk.core.BoolValueCommandInput.cast(changed_input)
                if box is not None and box.value:
                    for suffix, clear in (
                        ("fronta_gore", ("fronta_dolje", "fronta_lijeva", "fronta_desna")),
                        ("fronta_dolje", ("fronta_gore", "fronta_lijeva", "fronta_desna")),
                        ("fronta_lijeva", ("fronta_gore", "fronta_dolje")),
                        ("fronta_desna", ("fronta_gore", "fronta_dolje")),
                    ):
                        if not changed_input.id.endswith(suffix):
                            continue
                        prefix = changed_input.id[: -len(suffix)]
                        for name in clear:
                            other = adsk.core.BoolValueCommandInput.cast(
                                self.inputs.itemById(prefix + name)
                            )
                            if other is not None and other.value:
                                other.value = False
                                futil.log(
                                    f"Otvaranje '{suffix}' ON: cleared {prefix}{name}"
                                )
                        break
                return
            elif changed_input.id.endswith("_nogice"):
                # Legs and plinth are mutually exclusive: turning legs ON
                # switches the plinth (cokla) OFF for this cabinet.
                prefix = changed_input.id[: -len("nogice")]
                grp = adsk.core.GroupCommandInput.cast(changed_input)
                if grp and grp.isEnabledCheckBoxChecked:
                    cokla = adsk.core.GroupCommandInput.cast(
                        self.inputs.itemById(prefix + "cokla")
                    )
                    if cokla and cokla.isEnabledCheckBoxChecked:
                        cokla.isEnabledCheckBoxChecked = False
                        futil.log(f"Nogice ON: auto-disabled {prefix}cokla")
            elif changed_input.id.endswith("_cokla"):
                # ...and symmetrically, turning the plinth ON switches legs OFF.
                prefix = changed_input.id[: -len("cokla")]
                grp = adsk.core.GroupCommandInput.cast(changed_input)
                if grp and grp.isEnabledCheckBoxChecked:
                    nogice = adsk.core.GroupCommandInput.cast(
                        self.inputs.itemById(prefix + "nogice")
                    )
                    if nogice and nogice.isEnabledCheckBoxChecked:
                        nogice.isEnabledCheckBoxChecked = False
                        futil.log(f"Cokla ON: auto-disabled {prefix}nogice")
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
