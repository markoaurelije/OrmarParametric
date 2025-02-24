from typing import Optional
import adsk.core
import adsk.core, adsk.fusion, adsk.cam, traceback
from ..commandDialog.dialog_config import DialogItem, dialogItems
from ..commandDialog.presets import presets
from ...lib import fusionAddInUtils as futil

app = adsk.core.Application.get()


def set_input_via_userparam(dialogItem: DialogItem, inputs: adsk.core.CommandInputs):
    design = app.activeProduct
    userParams = design.userParameters
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    param = (
        userParams.itemByName(dialogItem.get("paramName"))
        if dialogItem.get("paramName")
        else None
    )

    # find the input if it exists in inputs
    input = inputs.itemById(dialogItem["inputName"])
    if input:
        if not param:
            futil.log(
                f"User parameter {dialogItem.get('paramName')} not found",
                adsk.core.LogLevels.WarningLogLevel,
            )
            return
        if dialogItem.get("inputType") in ["value"]:
            input.value = param.value
        elif dialogItem.get("inputType") == "integer":
            input.value = int(param.value)
        elif dialogItem.get("inputType") == "bool":
            input.value = bool(param.value)
        elif dialogItem.get("inputType") == "group_with_checkbox":
            input.isEnabledCheckBoxChecked = bool(param.value)

        futil.log(
            f"Input {dialogItem['inputName']} updated.",
            adsk.core.LogLevels.WarningLogLevel,
        )
        return

    if dialogItem.get("parrent"):
        parent = inputs.itemById(dialogItem["parrent"])
        # if the parent is not found, log the error and continue
        if not parent:
            futil.log(
                f"Parent {dialogItem['parrent']} not found.",
                adsk.core.LogLevels.WarningLogLevel,
            )
        inputs = parent.children if parent else inputs

    if dialogItem["inputType"] == "value" and param:
        input = inputs.addValueInput(
            dialogItem["inputName"],
            dialogItem["inputDescription"],
            defaultLengthUnits,
            adsk.core.ValueInput.createByReal(param.value),
        )
    elif dialogItem["inputType"] == "bool" and param:
        input = inputs.addBoolValueInput(
            dialogItem["inputName"],
            dialogItem["inputDescription"],
            True,
            "",
            bool(param.value),
        )
    elif dialogItem["inputType"] == "integer" and param:
        input = inputs.addIntegerSpinnerCommandInput(
            dialogItem["inputName"],
            dialogItem["inputDescription"],
            1,
            100,
            1,
            int(param.value),
        )
    elif "group" in dialogItem["inputType"]:
        input = group = inputs.addGroupCommandInput(
            dialogItem["inputName"], dialogItem["inputDescription"]
        )
        group.isExpanded = True
        if "with_checkbox" in dialogItem["inputType"] and param:
            group.isEnabledCheckBoxDisplayed = True
            group.isEnabledCheckBoxChecked = bool(param.value)
    else:
        input = None
        futil.log(
            f"Dialog item {dialogItem} not created.",
            adsk.core.LogLevels.WarningLogLevel,
        )

    if input and dialogItem.get("tooltip"):
        input.tooltipDescription = dialogItem["tooltip"]


def create_dialog(args: adsk.core.CommandCreatedEventArgs):
    # Create a value input field and set the default using 1 unit of the default length unit.

    #####  CREATING A DIALOG  #####

    # get presets keys from presets key-value pairs
    presets_keys = presets.keys()
    # use addDropDownCommandInput to create a dropdown menu with presets
    dropdown = args.command.commandInputs.addDropDownCommandInput(
        "presets", "Presets", adsk.core.DropDownStyles.LabeledIconDropDownStyle
    )
    # add the presets to the dropdown menu
    for key in presets_keys:
        dropdown.listItems.add(key, False, "")

    inputs = args.command.commandInputs
    # default_value = adsk.core.ValueInput.createByString("60")
    for dialogItem in dialogItems:
        set_input_via_userparam(dialogItem, inputs)


def set_user_parameters_via_inputs(args: adsk.core.CommandEventArgs):

    design = app.activeProduct
    userParams = design.userParameters
    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs

    for paramInput in filter(lambda x: "paramName" in x, dialogItems):
        input_to_user_parameter(userParams, inputs, paramInput)


def input_to_user_parameter(userParams, inputs, paramInput: DialogItem):
    param = userParams.itemByName(paramInput["paramName"])
    if not param:
        futil.log(
            f"User parameter {paramInput['paramName']} not found",
            adsk.core.LogLevels.ErrorLogLevel,
        )
        return
    if paramInput["inputType"] in "value":
        param.expression = inputs.itemById(paramInput["inputName"]).expression
    elif paramInput["inputType"] == "bool":
        param.value = 1 if inputs.itemById(paramInput["inputName"]).value else 0
    elif paramInput["inputType"] == "group_with_checkbox":
        param.value = (
            1
            if inputs.itemById(paramInput["inputName"]).isEnabledCheckBoxChecked
            else 0
        )
    elif paramInput["inputType"] == "integer":
        param.expression = str(inputs.itemById(paramInput["inputName"]).value)


def set_component_visibility():
    app = adsk.core.Application.get()
    design = app.activeProduct
    rootComp = design.rootComponent

    gornja_ploca_presence = design.userParameters.itemByName("J1_gornja_ploca")
    ukrute_presence = design.userParameters.itemByName("J1_ukrute")
    fronta_presence = design.userParameters.itemByName("J1_fronta")
    lijevo_otvaranje = design.userParameters.itemByName("J1_fronta_ljevo_otvaranje")
    dvostrano_otvaranje = design.userParameters.itemByName("J1_fronta_ljeva_i_desna")

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

    # lijevi_pant = None
    # desni_pant = None
    # # find the Joint with name "vrata lijevo"
    # for joint in rootComp.joints:
    #     if joint.name == "vrata lijevo":
    #         lijevi_pant = joint
    #     elif joint.name == "vrata desno":
    #         desni_pant = joint
    #     if lijevi_pant and desni_pant:
    #         break
    # if lijevo_otvaranje:
    #     lijevi_pant.isSuppressed = not bool(lijevo_otvaranje.value)
    #     desni_pant.isSuppressed = bool(lijevo_otvaranje.value)

    app.log(
        f"Ukrute presence: {ukrute_presence and ukrute_presence.value}, ukruteComp: {ukruteComp and ukruteComp.name}"
    )
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
            input
            for input in dialogItems
            if input.get("paramName") == param["paramName"]
        ]
        if not input_param:
            futil.log(
                f"Input param {param['paramName']} not found",
                adsk.core.LogLevels.ErrorLogLevel,
            )
            continue
        input_param = input_param[0]

        set_user_parameter(input_param["paramName"], param["expression"])
        set_input_via_userparam(input_param, inputs)

    # design = app.activeProduct
    # userParams = design.userParameters
    # for param in preset:
    #     userParams.itemByName(param["paramName"]).expression = param["expression"]
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
