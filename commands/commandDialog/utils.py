from typing import Optional
import adsk.core, adsk.fusion, adsk.cam, traceback
from ..commandDialog.dialog_config import InputItem, input_items, InputType
from ..commandDialog.presets import presets
from ...lib import fusionAddInUtils as futil

app = adsk.core.Application.get()


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

    parent = inputs.itemById(prefix + input_item.parent) if input_item.parent else None
    if input_item.parent and not parent:
        futil.log(
            f"Parent {input_item.parent} not found.",
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
            1,
            100,
            1,
            int(param.value),
        )
    elif "group" in input_item.type.value:
        input = inputs.addGroupCommandInput(input_item_name, input_item.description)
        input.isExpanded = False
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
    input = inputs.itemById(f"{prefix}{input_item.name}")
    if input:
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

        futil.log(
            f"Input {input_item.name} updated.",
            adsk.core.LogLevels.WarningLogLevel,
        )
        return


def create_dialog(inputs: adsk.core.CommandInputs):
    # Create a value input field and set the default using 1 unit of the default length unit.

    #####  CREATING A DIALOG  #####
    # add bellow 2 inputs only if doc name is J1
    doc = app.activeDocument
    futil.log(f"Current document: {doc.name}")
    if doc.name.startswith("J1"):
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
            create_input(tab_input.children, input_item, prefix)
            set_input_via_userparam(input_item, tab_input.children, prefix)
    # set width of the dialog so all inputs are


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

    for input_item in input_items_without_groups[1:]:
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
    if input_item.type == InputType.VALUE:
        param.expression = adsk.core.ValueCommandInput.cast(
            inputs.itemById(user_param_name)
        ).expression
    elif input_item.type == InputType.BOOL:
        param.value = 1 if inputs.itemById(user_param_name).value else 0
    elif input_item.type == InputType.GROUP_WITH_CHECKBOX:
        param.value = (
            1 if inputs.itemById(user_param_name).isEnabledCheckBoxChecked else 0
        )
    elif input_item.type == InputType.INTEGER:
        param.expression = str(inputs.itemById(user_param_name).value)


def set_component_visibility(prefix):
    design = adsk.fusion.Design.cast(app.activeProduct)

    futil.log(f"Setting visibility for prefix: {prefix}")

    gornja_ploca_presence = design.userParameters.itemByName(prefix + "gornja_ploca")
    ukrute_presence = design.userParameters.itemByName(prefix + "ukrute")
    fronta_presence = design.userParameters.itemByName(prefix + "fronta")
    lijevo_otvaranje = design.userParameters.itemByName(
        prefix + "fronta_lijeva"
    )
    desno_otvaranje = design.userParameters.itemByName(
        prefix + "fronta_desna"
    )
    cokla_presence = design.userParameters.itemByName(prefix + "cokla")
    pregrada_presence = design.userParameters.itemByName(prefix + "pregrada")

    # Get the target component (change index if needed)
    gornjaPlocaComp = None
    ukruteComp = None
    lijevaFrontaComp = None
    desnaFrontaComp = None
    coklaComp = None
    pregradaComp = None
    policaComp = None
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
            policaComp = occurrence

        if all(
            comp is not None for comp in components_to_find
        ):
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

    if cokla_presence and coklaComp:
        coklaComp.isLightBulbOn = bool(cokla_presence.value)
    
    if pregradaComp and pregrada_presence:
        pregradaComp.isLightBulbOn = bool(pregrada_presence.value)

    # now suppress features based on user parameters
    for feature in ukruteComp.childOccurrences[0].component.features:
        futil.log(f"Checking feature: {feature.name}")
        if feature.name.startswith("split ukrute"):
            futil.log(f"Setting feature {feature.name} suppressed: {not pregradaComp.isLightBulbOn}")
            feature.isSuppressed = not pregradaComp.isLightBulbOn
            break
    for feature in policaComp.component.features:
        futil.log(f"Checking feature: {feature.name}")
        if feature.name.startswith("split police"):
            futil.log(f"Setting feature {feature.name} suppressed: {not pregradaComp.isLightBulbOn}")
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


def add_parametric_component(name: str, create_new_design: bool = False):
    base_data_file = get_design_by_name("J1", "Default Project", "Ormari - parametric")
    if not base_data_file:
        app.userInterface.messageBox("Base design not found", "Erorr")
        return
    futil.log(f"Base design found: {base_data_file.name}")

    # open new design and insert the base design
    if create_new_design:
        target_doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        futil.log(f"Activating")
        target_doc.activate()
    else:
        # get curently active design
        doc = app.activeDocument
        futil.log(f"Current document: {doc.name}")
        if not doc.name.startswith("J1"):
            target_doc = doc
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
    rename_user_parameters(name)
    futil.log(f"New component inserted: {occurrence.component.name}")


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
