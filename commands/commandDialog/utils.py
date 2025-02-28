from typing import Optional
import adsk.core
import adsk.core, adsk.fusion, adsk.cam, traceback
from ..commandDialog.dialog_config import InputItem, input_items, InputType
from ..commandDialog.presets import presets
from ...lib import fusionAddInUtils as futil

app = adsk.core.Application.get()


def create_input(inputs: adsk.core.CommandInputs, input_item: InputItem):
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    design = app.activeProduct
    userParams = design.userParameters
    param = (
        userParams.itemByName(input_item.user_param) if input_item.user_param else None
    )

    parent = inputs.itemById(input_item.parent) if input_item.parent else None
    if input_item.parent and not parent:
        futil.log(
            f"Parent {input_item.parent} not found.",
            adsk.core.LogLevels.WarningLogLevel,
        )
    inputs = parent.children if parent else inputs

    futil.log(f"Creating input {input_item.name}")
    if input_item.type == InputType.VALUE and param:
        input = inputs.addValueInput(
            input_item.name,
            input_item.description,
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(param.value),
        )
    elif input_item.type == InputType.BOOL and param:
        input = inputs.addBoolValueInput(
            input_item.name,
            input_item.description,
            True,
            "",
            bool(param.value),
        )
    elif input_item.type == InputType.INTEGER and param:
        input = inputs.addIntegerSpinnerCommandInput(
            input_item.name,
            input_item.description,
            1,
            100,
            1,
            int(param.value),
        )
    elif "group" in input_item.type.name:
        input = group = inputs.addGroupCommandInput(
            input_item.name, input_item.description
        )
        group.isExpanded = True
        if "with_checkbox" in input_item.type.name and param:
            group.isEnabledCheckBoxDisplayed = True
            group.isEnabledCheckBoxChecked = bool(param.value)
    else:
        input = None
        futil.log(
            f"Dialog item {input_item.name} not created.",
            adsk.core.LogLevels.WarningLogLevel,
        )

    if input and input_item.tooltip:
        input.tooltipDescription = input_item.tooltip


def set_input_via_userparam(input_item: InputItem, inputs: adsk.core.CommandInputs):
    if input_item is None:
        return

    design = app.activeProduct
    userParams = design.userParameters
    param = (
        userParams.itemByName(input_item.user_param) if input_item.user_param else None
    )
    if param is None:
        futil.log(
            f"User parameter {input_item.user_param} not found",
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

    # get presets keys from presets key-value pairs
    presets_keys = presets.keys()
    # use addDropDownCommandInput to create a dropdown menu with presets
    dropdown = inputs.addDropDownCommandInput(
        "presets", "Presets", adsk.core.DropDownStyles.LabeledIconDropDownStyle
    )
    # add the presets to the dropdown menu
    for key in presets_keys:
        dropdown.listItems.add(key, False, "")

    for input_item in input_items:
        create_input(inputs, input_item)
        set_input_via_userparam(input_item, inputs)


def set_user_parameters_via_inputs(inputs: adsk.core.CommandInputs):
    design = app.activeProduct
    userParams = design.userParameters

    for input_with_user_param in filter(lambda x: x.user_param, input_items):
        input_to_user_parameter(userParams, inputs, input_with_user_param)


def input_to_user_parameter(
    userParams, inputs: adsk.core.CommandInputs, input_item: InputItem
):
    param = userParams.itemByName(input_item.user_param)
    if not param:
        futil.log(
            f"User parameter {input_item.user_param} not found",
            adsk.core.LogLevels.ErrorLogLevel,
        )
        return
    if input_item.type == InputType.VALUE:
        param.expression = inputs.itemById(input_item.name).expression
    elif input_item.type == InputType.BOOL:
        param.value = 1 if inputs.itemById(input_item.name).value else 0
    elif input_item.type == InputType.GROUP_WITH_CHECKBOX:
        param.value = (
            1 if inputs.itemById(input_item.name).isEnabledCheckBoxChecked else 0
        )
    elif input_item.type == InputType.INTEGER:
        param.expression = str(inputs.itemById(input_item.name).value)


def set_component_visibility():
    app = adsk.core.Application.get()
    design = app.activeProduct
    rootComp = design.rootComponent

    gornja_ploca_presence = design.userParameters.itemByName("J1_gornja_ploca")
    ukrute_presence = design.userParameters.itemByName("J1_ukrute")
    fronta_presence = design.userParameters.itemByName("J1_fronta")
    lijevo_otvaranje = design.userParameters.itemByName("J1_fronta_lijevo_otvaranje")
    dvostrano_otvaranje = design.userParameters.itemByName("J1_fronta_lijeva_i_desna")

    # Get the target component (change index if needed)
    gornjaPlocaComp = None
    ukruteComp = None
    lijeva_fronta = None
    desna_fronta = None
    for occurrence in rootComp.occurrences:
        # futil.log(f"Occurrence: {occurrence.name}")
        if occurrence.component.name == "gornja_ploca":
            gornjaPlocaComp = occurrence
        elif occurrence.component.name == "ukrute":
            ukruteComp = occurrence
        elif occurrence.name == "fronta:1":
            lijeva_fronta = occurrence
        elif occurrence.name == "fronta:2":
            desna_fronta = occurrence

        if gornjaPlocaComp and ukruteComp and lijeva_fronta and desna_fronta:
            break

    if gornja_ploca_presence and gornjaPlocaComp:
        gornjaPlocaComp.isLightBulbOn = bool(gornja_ploca_presence.value)

    if fronta_presence:
        lijeva_fronta.isLightBulbOn = bool(
            lijevo_otvaranje.value or dvostrano_otvaranje.value
        )
        desna_fronta.isLightBulbOn = bool(
            not lijevo_otvaranje.value or dvostrano_otvaranje.value
        )
    else:
        lijeva_fronta.isLightBulbOn = False
        desna_fronta.isLightBulbOn = False

    if ukrute_presence and ukruteComp:
        ukruteComp.isLightBulbOn = bool(ukrute_presence.value)


def get_design_by_name(
    design_name: str,
    project_name: Optional[str] = None,
    folder_name: Optional[str] = None,
) -> Optional[adsk.fusion.Design]:
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


def load_preset(preset_name: str, inputs: adsk.core.CommandInputs):
    preset = presets.get(preset_name)
    if not preset:
        futil.log("Preset not found", adsk.core.LogLevels.ErrorLogLevel)
        return

    # set the input values to the preset values
    for param in preset:
        input_param = [
            input for input in input_items if input.user_param == param["paramName"]
        ]
        if not input_param:
            futil.log(
                f"Input param {param['paramName']} not found",
                adsk.core.LogLevels.ErrorLogLevel,
            )
            continue
        input_param = input_param[0]

        set_user_parameter(input_param.user_param, param["expression"])
        set_input_via_userparam(input_param, inputs)

    set_component_visibility()


def add_preset_comonent(preset_name: str):
    base_design = get_design_by_name("J1", "Ormari - parametric")
    if not base_design:
        futil.log("Base design not found", adsk.core.LogLevels.ErrorLogLevel)
        return

    # open new design and insert the bae design
    new_design = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    new_design.activate()

    design = adsk.fusion.Design.cast(app.activeProduct)
    design.rootComponent.occurrences.addByInsert(
        base_design, adsk.core.Matrix3D.create(), False
    )


def set_user_parameter(param_name: str, value: str):
    design = app.activeProduct
    userParams = design.userParameters
    param = userParams.itemByName(param_name)
    if param:
        param.expression = value
    else:
        futil.log(
            f"Parameter {param_name} not found", adsk.core.LogLevels.ErrorLogLevel
        )
