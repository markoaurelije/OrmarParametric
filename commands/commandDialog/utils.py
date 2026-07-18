import os
from typing import Optional
import adsk.core, adsk.fusion, adsk.cam, traceback
from ..commandDialog.dialog_config import InputItem, input_items, InputType
from ..commandDialog.presets import presets
from ..commandDialog import base_design
from ...lib import fusionAddInUtils as futil

app = adsk.core.Application.get()


def _find_command_input(input_container, input_id):
    if input_container is None:
        return None

    if getattr(input_container, "id", None) == input_id:
        return input_container

    if hasattr(input_container, "itemById"):
        try:
            found = input_container.itemById(input_id)
            if found:
                return found
        except Exception:
            pass

    children = None
    if hasattr(input_container, "children"):
        children = input_container.children
    elif isinstance(input_container, (list, tuple)):
        children = input_container
    elif hasattr(input_container, "count") and hasattr(input_container, "item"):
        # CommandInputs collection — has count/item but no .children
        children = [input_container.item(i) for i in range(input_container.count)]

    if children is None:
        return None

    for child in children:
        found = _find_command_input(child, input_id)
        if found:
            return found

    return None


def create_input(
    inputs: adsk.core.CommandInputs, input_item: InputItem, prefix: str = "J1_"
):
    input_item_name = prefix + input_item.name
    design = adsk.fusion.Design.cast(app.activeProduct)

    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    user_param_name = prefix + input_item.name if input_item.name else None
    param = (
        design.userParameters.itemByName(user_param_name) if user_param_name else None
    )

    parent: Optional[adsk.core.GroupCommandInput] = (
        inputs.itemById(prefix + input_item.parent) if input_item.parent else None
    )
    if input_item.parent and not parent:
        futil.log(
            f"Parent {input_item.parent} not found. Availalable parents: {[i.id for i in inputs]}. Searching in parents children...",
            adsk.core.LogLevels.WarningLogLevel,
        )
    inputs = parent.children if parent else inputs

    if input_item.type == InputType.VALUE and param:
        input = inputs.addValueInput(
            input_item_name,
            input_item.description,
            defaultLengthUnits,
            adsk.core.ValueInput.createByString(param.expression),
        )
    elif input_item.type == InputType.BOOL and param:
        input = inputs.addBoolValueInput(
            input_item_name,
            input_item.description,
            True,
            "",
            bool(param.value),
        )
    elif input_item.type == InputType.INTEGER and param:
        input = inputs.addIntegerSpinnerCommandInput(
            input_item_name,
            input_item.description,
            input_item.min_value or 1,
            input_item.max_value or 100,
            1,
            int(param.value),
        )
    elif input_item.type == InputType.DROPDOWN and param:
        input = inputs.addDropDownCommandInput(
            input_item_name,
            input_item.description,
            adsk.core.DropDownStyles.LabeledIconDropDownStyle,
        )
        for value in input_item.values or []:
            input.listItems.add(value, value == param.expression, "")
    elif (
        input_item.type == InputType.GROUP
        or input_item.type == InputType.GROUP_WITH_CHECKBOX
    ):
        input = inputs.addGroupCommandInput(input_item_name, input_item.description)
        input.isExpanded = bool(input_item.expanded)
        if input_item.type == InputType.GROUP_WITH_CHECKBOX and param:
            input.isEnabledCheckBoxDisplayed = True
            input.isEnabledCheckBoxChecked = bool(param.value)
    elif input_item.type == InputType.TABLE:
        input = inputs.addTableCommandInput(
            input_item_name, input_item.description, 3, "1:1:1"
        )
        input.minimumVisibleRows = 3
        input.maximumVisibleRows = 6
        input.columnSpacing = 1
        input.rowSpacing = 1
        input.tablePresentationStyle = (
            adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
        )
        input.hasGrid = False
    elif input_item.type == InputType.BUTTON:
        table: adsk.core.TableCommandInput = (
            inputs.itemById(prefix + input_item.table) if input_item.table else None
        )
        if table and table.classType() == adsk.core.TableCommandInput.classType():
            input = inputs.addBoolValueInput(
                input_item_name,
                input_item.description,
                False,
                input_item.icon or "",
                False,
            )
            # input.isEnabled = False
            table.addToolbarCommandInput(input)
        else:
            input = None

        # # table rows
        # stringInput = inputs.addStringValueInput("string1", "", "Sample Text")
        # stringInput.isReadOnly = True
        # table.addCommandInput(stringInput, 0, 0, 0, 0)
    else:
        input = None
        futil.log(
            f"Dialog item {prefix + input_item.name} not created.",
            adsk.core.LogLevels.WarningLogLevel,
        )

    if input and input_item.tooltip:
        input.tooltipDescription = input_item.tooltip


def set_input_via_userparam(
    input_item: InputItem, inputs: adsk.core.CommandInputs, prefix: str = "J1_"
):
    if input_item is None:
        return

    design = adsk.fusion.Design.cast(app.activeProduct)
    user_param_name = prefix + input_item.name if input_item.name else None
    param = (
        design.userParameters.itemByName(user_param_name) if user_param_name else None
    )
    if param is None:
        futil.log(
            f"User parameter {user_param_name} not found.",
            adsk.core.LogLevels.WarningLogLevel,
        )
        return

    futil.log(f"Setting input {input_item.name} to {param.expression}")

    # find the input if it exists in inputs
    input = _find_command_input(inputs, f"{prefix}{input_item.name}")
    if not input:
        futil.log(
            f"Input {prefix}{input_item.name} not found in inputs.",
            adsk.core.LogLevels.WarningLogLevel,
        )
        futil.log(f"Available inputs: {[i.id for i in inputs]}")
        return

    futil.log(f"Updating input {input_item.name}")
    if input_item.type == InputType.VALUE:
        input = adsk.core.ValueCommandInput.cast(input)
        input.expression = param.expression
    elif input_item.type == InputType.INTEGER:
        input.value = int(param.value)
    elif input_item.type == InputType.BOOL:
        input.value = bool(param.value)
    elif input_item.type == InputType.GROUP_WITH_CHECKBOX:
        input.isEnabledCheckBoxChecked = bool(param.value)
    elif input_item.type == InputType.DROPDOWN:
        input = adsk.core.DropDownCommandInput.cast(input)
        # find the item in the dropdown that matches the param value
        for item in input.listItems:
            if item.name == param.expression:
                input.selectedItem = item
                break

    futil.log(
        f"Input {input_item.name} updated.",
        adsk.core.LogLevels.WarningLogLevel,
    )


def create_dialog(inputs: adsk.core.CommandInputs):
    # Create a value input field and set the default using 1 unit of the default length unit.

    #####  CREATING A DIALOG  #####
    # cabinets are generated from code (base_design.py), so any design can
    # add one - no J1 base document needed anymore
    doc = app.activeDocument
    futil.log(f"Current document: {doc.name}")
    inputs.addBoolValueInput("addPresetButton", "Dodaj ormar", False, "", True)
    inputs.addTextBoxCommandInput(
        "newComponentName", "Ime novog ormara", "O1", 1, False
    )

    prefixis = get_prefixes()
    for prefix in prefixis:
        futil.log(f"Adding tab: {prefix}")
        tab_input = inputs.addTabCommandInput(prefix, prefix)
        dropdown = tab_input.children.addDropDownCommandInput(
            f"{prefix}presets",
            "Presets",
            adsk.core.DropDownStyles.LabeledIconDropDownStyle,
        )
        for key in presets.keys():
            dropdown.listItems.add(key, False, "")

        for input_item in input_items:
            create_input(tab_input.children, input_item, prefix)
            if input_item.input_has_no_param is False:
                set_input_via_userparam(input_item, tab_input.children, prefix)


def get_prefixes():
    input_items_with_params = [
        item for item in input_items if item.input_has_no_param is False
    ]
    design = adsk.fusion.Design.cast(app.activeProduct)
    userParams = [param.name for param in design.userParameters]
    param_base_name = input_items_with_params[0].name
    prefixis = {
        param.split(param_base_name)[0]
        for param in userParams
        if param.endswith(param_base_name)
    }

    for input_item in input_items_with_params[1:]:
        if input_item.name is None:
            continue
        param_base_name = input_item.name
        matching_user_params = {
            param.split(param_base_name)[0]
            for param in userParams
            if param.endswith(param_base_name)
        }
        prefixis.intersection_update(matching_user_params)
        if not prefixis:
            break

    prefixis = sorted(prefixis)
    futil.log(f"found prefixes: {prefixis}")
    return prefixis


def set_user_parameters_via_inputs(inputs: adsk.core.CommandInputs, prefix: str):
    design = adsk.fusion.Design.cast(app.activeProduct)
    for input_with_user_param in filter(
        lambda x: x.input_has_no_param != True, input_items
    ):
        input_to_user_parameter(
            design.userParameters, inputs, input_with_user_param, prefix
        )


def input_to_user_parameter(
    userParams: adsk.fusion.UserParameters,
    inputs: adsk.core.CommandInputs,
    input_item: InputItem,
    prefix: str,
):
    user_param_name = prefix + input_item.name
    param = userParams.itemByName(user_param_name)
    if not param:
        futil.log(
            f"User parameter {user_param_name} not found",
            adsk.core.LogLevels.ErrorLogLevel,
        )
        return

    # futil.log(f"Setting user parameter {user_param_name}")
    input = _find_command_input(inputs, user_param_name)
    if input is None:
        futil.log(
            f"Input {user_param_name} not found in inputs.",
            adsk.core.LogLevels.WarningLogLevel,
        )
        return

    if input_item.type == InputType.VALUE:
        param.expression = adsk.core.ValueCommandInput.cast(input).expression
    elif input_item.type == InputType.BOOL:
        param.value = 1 if input.value else 0
    elif input_item.type == InputType.GROUP_WITH_CHECKBOX:
        param.value = 1 if input.isEnabledCheckBoxChecked else 0
    elif input_item.type == InputType.INTEGER:
        param.expression = str(input.value)
    elif input_item.type == InputType.DROPDOWN:
        selected_item = adsk.core.DropDownCommandInput.cast(input).selectedItem
        if selected_item:
            param.expression = selected_item.name
        else:
            futil.log(
                f"Selected item for {user_param_name} is None",
                adsk.core.LogLevels.WarningLogLevel,
            )


def set_component_visibility(prefix):
    design = adsk.fusion.Design.cast(app.activeProduct)

    futil.log(f"Setting visibility for prefix: {prefix}")

    gornja_ploca_presence = design.userParameters.itemByName(prefix + "gornja_ploca")
    ukrute_presence = design.userParameters.itemByName(prefix + "ukrute")
    fronta_presence = design.userParameters.itemByName(prefix + "fronta")
    lijevo_otvaranje = design.userParameters.itemByName(prefix + "fronta_lijeva")
    desno_otvaranje = design.userParameters.itemByName(prefix + "fronta_desna")
    cokla_presence = design.userParameters.itemByName(prefix + "cokla")
    pregrada_presence = design.userParameters.itemByName(prefix + "pregrada")
    police_presence = design.userParameters.itemByName(prefix + "police")

    # Get the target component (change index if needed)
    gornjaPlocaComp = None
    ukruteComp = None
    lijevaFrontaComp = None
    desnaFrontaComp = None
    coklaComp = None
    pregradaComp = None
    policaComp = []
    components_to_find = [
        gornjaPlocaComp,
        ukruteComp,
        lijevaFrontaComp,
        desnaFrontaComp,
        coklaComp,
        pregradaComp,
        policaComp,
    ]

    rootComp = next(
        (
            comp.component
            for comp in design.rootComponent.occurrences
            if comp.component.name == prefix.rstrip("_")
        ),
        None,
    )
    if rootComp is None:
        futil.log(
            f"Component {prefix.rstrip("_")} not found. Using root comp. Availible components: {[comp.component.name for comp in design.rootComponent.occurrences]}"
        )
        rootComp = design.rootComponent

    for occurrence in rootComp.occurrences:
        if occurrence.component.name.startswith("gornja_ploca"):
            gornjaPlocaComp = occurrence
        elif occurrence.component.name.startswith("ukrute"):
            ukruteComp = occurrence
        elif occurrence.component.name.startswith("fronta lijevo"):
            lijevaFrontaComp = occurrence
        elif occurrence.component.name.startswith("fronta desno"):
            desnaFrontaComp = occurrence
        elif occurrence.component.name.startswith("cokla"):
            coklaComp = occurrence
        elif occurrence.component.name.startswith("pregrada"):
            pregradaComp = occurrence
        elif occurrence.component.name.startswith("polica"):
            policaComp.append(occurrence)

        if all(comp is not None for comp in components_to_find):
            break

    if gornja_ploca_presence and gornjaPlocaComp:
        gornjaPlocaComp.isLightBulbOn = bool(gornja_ploca_presence.value)

    if lijevaFrontaComp:
        lijevaFrontaComp.isLightBulbOn = bool(
            fronta_presence.value and lijevo_otvaranje.value
        )
    if desnaFrontaComp:
        desnaFrontaComp.isLightBulbOn = bool(
            fronta_presence.value and desno_otvaranje.value
        )

    if ukrute_presence and ukruteComp:
        ukruteComp.isLightBulbOn = bool(ukrute_presence.value)

    if policaComp and police_presence:
        for polica in policaComp:
            polica.isLightBulbOn = bool(police_presence.value)

    if cokla_presence and coklaComp:
        coklaComp.isLightBulbOn = bool(cokla_presence.value)

    if pregradaComp and pregrada_presence:
        pregradaComp.isLightBulbOn = bool(pregrada_presence.value)

    # now suppress features based on user parameters
    if ukruteComp and pregradaComp:
        for feature in ukruteComp.childOccurrences[0].component.features:
            futil.log(f"Checking feature: {feature.name}")
            if feature.name.startswith("split ukrute"):
                futil.log(
                    f"Setting feature {feature.name} suppressed: {not pregradaComp.isLightBulbOn}"
                )
                feature.isSuppressed = not pregradaComp.isLightBulbOn
                break

    if pregradaComp:
        for polica in policaComp:
            for feature in polica.component.features:
                futil.log(f"Checking feature: {feature.name}")
                if feature.name.startswith("split police"):
                    futil.log(
                        f"Setting feature {feature.name} suppressed: {not pregradaComp.isLightBulbOn}"
                    )
                    feature.isSuppressed = not pregradaComp.isLightBulbOn
                    break


def get_design_by_name(
    design_name: str,
    project_name: Optional[str] = None,
    folder_name: Optional[str] = None,
) -> Optional[adsk.core.DataFile]:
    try:
        app = adsk.core.Application.get()
        if not app:
            return None
        data_mgr = app.data
        projects = data_mgr.dataProjects

        for project in projects:
            folders = project.rootFolder.dataFolders
            futil.log(f"Project: {project.name}")
            if project_name and project.name != project_name:
                continue

            for folder in [project.rootFolder, *folders]:
                futil.log(f"Folder: {folder.name}")
                if folder_name and folder.name != folder_name:
                    continue
                items = folder.dataFiles

                for item in items:
                    futil.log(f"Item: {item.name}")
                    if item.name == design_name:
                        return item  # Returns the DataFile object

        return None  # Design not found

    except Exception as e:
        futil.log(f"Error: {e}", adsk.core.LogLevels.ErrorLogLevel)
        return None


def load_preset(preset_name: str, inputs: adsk.core.CommandInputs, prefix: str = "J1_"):
    preset = presets.get(preset_name)
    if not preset:
        futil.log("Preset not found", adsk.core.LogLevels.ErrorLogLevel)
        return

    # set the input values to the preset values
    for param in preset:
        input_param = [
            input
            for input in input_items
            if f"{prefix}{input.name}" == f"{prefix}{param['paramName']}"
        ]
        if not input_param:
            futil.log(
                f"Input param {prefix}{param['paramName']} not found",
                adsk.core.LogLevels.ErrorLogLevel,
            )
            continue
        input_param = input_param[0]

        set_user_parameter(f"{prefix}{input_param.name}", param["expression"])
        set_input_via_userparam(input_param, inputs, prefix)

    set_component_visibility(prefix)


def request_add_cabinet(new_component_name: str):
    """Handle a "Dodaj ormar" click.

    J1 is kept pristine: it has no special role anymore (nothing is copied
    from it), but a cabinet generated at the origin would land exactly on
    top of J1's own geometry, silently cluttering the master file, so that
    case still routes into a brand-new document, immediately and directly
    (matching the original J1-copy implementation's behavior).

    For any other (normal project) document, the cabinet is added directly
    into that same document - but not immediately. While our command is
    active on a document, Fusion silently rolls back any structural model
    changes (new components/bodies) made from the inputChanged handler on
    the very next preview cycle; only parameter edits survive, because
    set_user_parameters_via_inputs re-applies them every cycle. So instead
    the request is queued, and materialize_pending_cabinets() rebuilds it
    from scratch on every preview/execute cycle (same pattern already used
    for "add ultrabox" via ultrabox_add_fired) - idempotent-by-construction,
    giving live preview and surviving through to the final commit on OK.
    """
    doc = app.activeDocument
    if doc.name.startswith("J1"):
        target_doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        futil.log(f"Activating")
        target_doc.activate()

        design = adsk.fusion.Design.cast(app.activeProduct)
        futil.log(f"Generating cabinet '{new_component_name}' in {app.activeDocument.name}")
        try:
            occurrence = base_design.add_cabinet(design, new_component_name)
        except ValueError as e:
            app.userInterface.messageBox(str(e), "Error")
            return
        futil.log(f"New cabinet generated: {occurrence.component.name}")
        return

    design = adsk.fusion.Design.cast(app.activeProduct)
    if design.userParameters.itemByName(f"{new_component_name}_sirina"):
        app.userInterface.messageBox(
            f"Parameters with prefix '{new_component_name}_' already exist in this design",
            "Error",
        )
        return

    from .event_handlers.command_execute_handler import CommandExecuteHandler
    from .event_handlers.command_execute_preview_handler import (
        CommandExecutePreviewHandler,
    )

    CommandExecutePreviewHandler.pending_cabinets.add(new_component_name)
    CommandExecuteHandler.pending_cabinets.add(new_component_name)
    futil.log(f"Queued cabinet '{new_component_name}' to materialize on next preview/execute")


_materializing = False


def materialize_pending_cabinets(pending_cabinet_names: set):
    global _materializing
    if not pending_cabinet_names or _materializing:
        # guards against reentrant preview/execute cycles Fusion may pump
        # while add_cabinet's own API calls are still running
        return
    _materializing = True
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        for name in pending_cabinet_names:
            if design.userParameters.itemByName(f"{name}_sirina"):
                continue  # already persisted this cycle (e.g. on execute, no rollback happened)
            try:
                base_design.add_cabinet(design, name)
                futil.log(f"Materialized pending cabinet '{name}'")
            except ValueError as e:
                futil.log(
                    f"Failed to materialize cabinet '{name}': {e}",
                    adsk.core.LogLevels.ErrorLogLevel,
                )
    finally:
        _materializing = False


def rename_user_parameters(name: str):
    design = adsk.fusion.Design.cast(app.activeProduct)
    # rename all user parameters that start with J1_* with the <name>_
    futil.log(f"Renaming user parameters to {name}_*")
    for user_param in design.userParameters:
        if user_param.name.startswith("J1_"):
            user_param.name = name + "_" + user_param.name[3:]


def set_user_parameter(param_name: str, value: str):
    design = adsk.fusion.Design.cast(app.activeProduct)
    param = design.userParameters.itemByName(param_name)
    futil.log(f"Setting user parameter {param_name} to {value}")
    if param:
        param.expression = value
    else:
        futil.log(
            f"Parameter {param_name} not found", adsk.core.LogLevels.ErrorLogLevel
        )
