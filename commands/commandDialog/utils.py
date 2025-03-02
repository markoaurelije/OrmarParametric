from typing import Optional
import adsk.core
import adsk.core, adsk.fusion, adsk.cam, traceback
from ..commandDialog.dialog_config import InputItem, input_items, InputType
from ..commandDialog.presets import presets
from ...lib import fusionAddInUtils as futil

app = adsk.core.Application.get()


def create_input(
    inputs: adsk.core.CommandInputs, input_item: InputItem, prefix: str = "J1_"
):
    input_item_name = prefix + input_item.name
    futil.log(f"Creating input {input_item_name}")
    design = adsk.fusion.Design.cast(app.activeProduct)

    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    user_param_name = prefix + input_item.name if input_item.name else None
    param = (
        design.userParameters.itemByName(user_param_name) if user_param_name else None
    )

    futil.log(f"Parent: {input_item.parent}")

    parent = inputs.itemById(prefix + input_item.parent) if input_item.parent else None
    if input_item.parent and not parent:
        futil.log(
            f"Parent {input_item.parent} not found.",
            adsk.core.LogLevels.WarningLogLevel,
        )
    inputs = parent.children if parent else inputs

    if input_item.type == InputType.VALUE and param:
        futil.log(f"Creating input {input_item_name}, step2")
        input = inputs.addValueInput(
            input_item_name,
            input_item.description,
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(param.value),
        )
        futil.log(f"Creating input {input_item_name}, step3")
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
            1,
            100,
            1,
            int(param.value),
        )
    elif "group" in input_item.type.value:
        input = inputs.addGroupCommandInput(input_item_name, input_item.description)
        input.isExpanded = True
        if "with_checkbox" in input_item.type.value and param:
            input.isEnabledCheckBoxDisplayed = True
            input.isEnabledCheckBoxChecked = bool(param.value)
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

    futil.log(f"Setting input {input_item.name}")

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

    # find the input if it exists in inputs
    input = inputs.itemById(input_item.name)
    if input:
        futil.log(f"Updating input {input_item.name}")
        if input_item.type == InputType.VALUE:
            input.value = param.value
        elif input_item.type == InputType.INTEGER:
            input.value = int(param.value)
        elif input_item.type == InputType.BOOL:
            input.value = bool(param.value)
        elif input_item.type == InputType.GROUP_WITH_CHECKBOX:
            input.isEnabledCheckBoxChecked = bool(param.value)

        futil.log(
            f"Input {input_item.name} updated.",
            adsk.core.LogLevels.WarningLogLevel,
        )
        return


def create_dialog(inputs: adsk.core.CommandInputs):
    # Create a value input field and set the default using 1 unit of the default length unit.

    #####  CREATING A DIALOG  #####
    inputs.addBoolValueInput("addPresetButton", "Dodaj ormar", False, "", True)
    inputs.addTextBoxCommandInput(
        "newComponentName", "Ime novog ormara", "O1", 1, False
    )

    prefixis = get_prefixes()
    for prefix in prefixis:
        futil.log(f"Adding tab: {prefix}")
        tab_input = inputs.addTabCommandInput(prefix, prefix)
        dropdown = tab_input.children.addDropDownCommandInput(
            "presets", "Presets", adsk.core.DropDownStyles.LabeledIconDropDownStyle
        )
        for key in presets.keys():
            dropdown.listItems.add(key, False, "")

        for input_item in input_items:
            # futil.log(f"Adding input: {input_item.name}")
            create_input(tab_input.children, input_item, prefix)
            set_input_via_userparam(input_item, tab_input.children, prefix)


def get_prefixes():
    input_items_without_groups = [
        item for item in input_items if item.type != InputType.GROUP
    ]
    design = adsk.fusion.Design.cast(app.activeProduct)
    userParams = [param.name for param in design.userParameters]
    param_base_name = input_items_without_groups[0].name
    prefixis = {
        param.split(param_base_name)[0]
        for param in userParams
        if param.endswith(param_base_name)
    }
    futil.log(f"initial prefixes: {prefixis}")

    for input_item in input_items_without_groups[1:]:
        if input_item.name is None:
            continue
        param_base_name = input_item.name
        matching_user_params = {
            param.split(param_base_name)[0]
            for param in userParams
            if param.endswith(param_base_name)
        }
        # futil.log(f"matching prefixes: {matching_user_params} for {input_item.name}")
        prefixis.intersection_update(matching_user_params)
        if not prefixis:
            break

    prefixis = sorted(prefixis)
    futil.log(f"resulting prefixes: {prefixis}")
    return prefixis

    # dropdown = inputs.addDropDownCommandInput(
    #         "presets", "Presets", adsk.core.DropDownStyles.LabeledIconDropDownStyle
    #     )
    # for key in presets.keys():
    #     dropdown.listItems.add(key, False, "")

    # for input_item in input_items:
    #     create_input(inputs, input_item)
    #     set_input_via_userparam(input_item, inputs)


def set_user_parameters_via_inputs(inputs: adsk.core.CommandInputs, prefix: str):
    design = adsk.fusion.Design.cast(app.activeProduct)
    for input_with_user_param in filter(
        lambda x: x.type != InputType.GROUP, input_items
    ):
        input_to_user_parameter(
            design.userParameters, inputs, input_with_user_param, prefix
        )


def input_to_user_parameter(
    userParams,
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
    if input_item.type == InputType.VALUE:
        param.expression = inputs.itemById(user_param_name).expression
    elif input_item.type == InputType.BOOL:
        param.value = 1 if inputs.itemById(user_param_name).value else 0
    elif input_item.type == InputType.GROUP_WITH_CHECKBOX:
        param.value = (
            1 if inputs.itemById(user_param_name).isEnabledCheckBoxChecked else 0
        )
    elif input_item.type == InputType.INTEGER:
        param.expression = str(inputs.itemById(user_param_name).value)


def set_component_visibility():
    design = adsk.fusion.Design.cast(app.activeProduct)

    for prefix in get_prefixes():
        futil.log(f"Setting visibility for prefix: {prefix}")

        gornja_ploca_presence = design.userParameters.itemByName(
            prefix + "gornja_ploca"
        )
        ukrute_presence = design.userParameters.itemByName(prefix + "ukrute")
        fronta_presence = design.userParameters.itemByName(prefix + "fronta")
        lijevo_otvaranje = design.userParameters.itemByName(
            prefix + "fronta_lijevo_otvaranje"
        )
        dvostrano_otvaranje = design.userParameters.itemByName(
            prefix + "fronta_lijeva_i_desna"
        )

        futil.log(f"Finished getting user parameters")
        # Get the target component (change index if needed)
        gornjaPlocaComp = None
        ukruteComp = None
        lijevaFrontaComp = None
        desnaFrontaComp = None

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
                f"Component {prefix.rstrip("_")} not found. Availible components: {[comp.component.name for comp in design.rootComponent.occurrences]}"
            )
            rootComp = design.rootComponent

        futil.log(f"Root component: {rootComp.name}")
        # futil.log(
        #     f"Root component occurrences: {[comp.component.name for comp in rootComp.occurrences]}"
        # )
        for occurrence in rootComp.occurrences:
            # futil.log(f"Occurrence: {occurrence.name}")
            if occurrence.component.name == "gornja_ploca":
                gornjaPlocaComp = occurrence
            elif occurrence.component.name == "ukrute":
                ukruteComp = occurrence
            elif occurrence.component.name == "fronta lijevo":
                lijevaFrontaComp = occurrence
            elif occurrence.component.name == "fronta desno":
                desnaFrontaComp = occurrence

            if gornjaPlocaComp and ukruteComp and lijevaFrontaComp and desnaFrontaComp:
                break

        if gornja_ploca_presence and gornjaPlocaComp:
            gornjaPlocaComp.isLightBulbOn = bool(gornja_ploca_presence.value)

        if lijevaFrontaComp:
            lijevaFrontaComp.isLightBulbOn = bool(
                fronta_presence and lijevo_otvaranje.value or dvostrano_otvaranje.value
            )
        if desnaFrontaComp:
            desnaFrontaComp.isLightBulbOn = bool(
                fronta_presence
                and not lijevo_otvaranje.value
                or dvostrano_otvaranje.value
            )

        if ukrute_presence and ukruteComp:
            ukruteComp.isLightBulbOn = bool(ukrute_presence.value)


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
            if f"{prefix}{input.name}" == param["paramName"]
        ]
        if not input_param:
            futil.log(
                f"Input param {param['paramName']} not found",
                adsk.core.LogLevels.ErrorLogLevel,
            )
            continue
        input_param = input_param[0]

        set_user_parameter(input_param.name, param["expression"])
        set_input_via_userparam(input_param, inputs)

    set_component_visibility()


def add_parametric_component(name: str, create_new_design: bool = False):
    base_data_file = get_design_by_name("J1", "Ormari - parametric")
    if not base_data_file:
        app.userInterface.messageBox("Base design not found", "Erorr")
        return
    futil.log(f"Base design found: {base_data_file.name}")

    # open new design and insert the base design
    if create_new_design:
        target_doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    else:
        # target data_file
        target_data_file = get_design_by_name("test", "Ormari - parametric")
        if not target_data_file:
            app.userInterface.messageBox("Target design not found", "Erorr")
            return
        # open and activate a data file
        futil.log(f"Opening target document: {target_data_file.name}")
        target_doc = app.documents.open(target_data_file)

    futil.log(f"Activating")
    target_doc.activate()
    futil.log(f"Target document activated: {target_doc.name}")

    design = adsk.fusion.Design.cast(app.activeProduct)
    # make sure "design" is not a base design, compare by name
    if design.rootComponent.name == "J1":
        app.userInterface.messageBox(
            "Current design is the base design. Open new desing, and try again.",
            "Erorr",
        )
        return

    futil.log(f"Current design: {design.rootComponent.name}")
    occurrence = design.rootComponent.occurrences.addByInsert(
        base_data_file, adsk.core.Matrix3D.create(), False
    )
    occurrence.component.name = name
    # rename all user parameters that start with J1_* with the <name>_
    for user_param in design.userParameters:
        if user_param.name.startswith("J1_"):
            user_param.name = name + "_" + user_param.name[3:]
    futil.log(f"New component inserted: {occurrence.component.name}")


def set_user_parameter(param_name: str, value: str):
    design = adsk.fusion.Design.cast(app.activeProduct)
    param = design.userParameters.itemByName(param_name)
    if param:
        param.expression = value
    else:
        futil.log(
            f"Parameter {param_name} not found", adsk.core.LogLevels.ErrorLogLevel
        )
