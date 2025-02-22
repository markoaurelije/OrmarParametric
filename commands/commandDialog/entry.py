import adsk.core
import os

from ..commandDialog.utils import set_component_visibilit
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog"
CMD_NAME = "Ormari Parametric"
CMD_Description = "Kreiranje parametarskih ormara."

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidScriptsAddinsPanel"
COMMAND_BESIDE_ID = "ScriptsManagerCommand"

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

paramInputs = [
    {
        "paramName": "J1_sirina",
        "inputName": "ukupna_sirina",
        "inputType": "value",
        "inputDescription": "Ukupna Širina",
    },
    {
        "paramName": "J1_dubina",
        "inputName": "ukupna_dubina",
        "inputType": "value",
        "inputDescription": "Ukupna Dubina",
    },
    {
        "paramName": "J1_visina",
        "inputName": "ukupna_visina",
        "inputType": "value",
        "inputDescription": "Ukupna Visina",
    },
    {
        "paramName": "J1_ukrute",
        "inputName": "ukrute_enabled",
        "inputType": "bool",
        "inputDescription": "Ukrute",
    },
    {
        "paramName": "J1_gornja_ploca",
        "inputName": "gornja_ploca_enabled",
        "inputType": "bool",
        "inputDescription": "Gornja Ploča",
    },
    {
        "paramName": "J1_fronta",
        "inputName": "fronta_enabled",
        "inputType": "bool",
        "inputDescription": "Fronta",
    },
]


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Created Event")

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    # Create a simple text box input.
    # inputs.addTextBoxCommandInput("text_box", "Some Text", "Enter some text.", 1, False)

    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits

    # get the initial values (based on the userParamerters)
    design = app.activeProduct
    userParams = design.userParameters

    # default_value = adsk.core.ValueInput.createByString("60")
    for paramInput in paramInputs:
        param = userParams.itemByName(paramInput["paramName"])
        if param:
            if paramInput["inputType"] == "value":
                inputs.addValueInput(
                    paramInput["inputName"],
                    paramInput["inputDescription"],
                    defaultLengthUnits,
                    adsk.core.ValueInput.createByReal(param.value),
                )
            elif paramInput["inputType"] == "bool":
                inputs.addBoolValueInput(
                    paramInput["inputName"],
                    paramInput["inputDescription"],
                    True,
                    "",
                    bool(param.value),
                )

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.inputChanged, command_input_changed, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.executePreview, command_preview, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.validateInputs,
        command_validate_input,
        local_handlers=local_handlers,
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Execute Event")

    design = app.activeProduct
    userParams = design.userParameters
    #  ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs

    for paramInput in paramInputs:
        param = userParams.itemByName(paramInput["paramName"])
        if param:
            if paramInput["inputType"] == "value":
                param.expression = inputs.itemById(paramInput["inputName"]).expression
            elif paramInput["inputType"] == "bool":
                param.value = 1 if inputs.itemById(paramInput["inputName"]).value else 0

    set_component_visibilit()
    # ui.messageBox("Ormari su kreirani!")


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    inputs = args.command.commandInputs
    futil.log(f"{CMD_NAME} Command Preview Event")


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # if changed_input.id == "ukrute_enabled":
    #     # Get the value of the input
    #     value = changed_input.value
    #     # General logging for debug.
    #     futil.log(
    #         f"{CMD_NAME} Input Changed Event fired from a change to {changed_input.id} with value {value}"
    #     )
    #     # set the value of the user parameter
    #     design = app.activeProduct
    #     userParams = design.userParameters
    #     ukrute_enabled = userParams.itemByName("J1_ukrute")
    #     if ukrute_enabled:
    #         ukrute_enabled.value = 1 if value else 0
    #         futil.log(f"Set the value of the user parameter to {ukrute_enabled.value}")

    # General logging for debug.
    futil.log(
        f"{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}"
    )


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Validate Input Event")

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    for paramInput in filter(lambda x: x["inputType"] == "value", paramInputs):
        input = inputs.itemById(paramInput["inputName"])
        if input:
            if input.value == "":
                args.areInputsValid = False
                input.tooltip = "This value cannot be empty."
            elif input.value <= 0:
                args.areInputsValid = False
                input.tooltip = "This value must be greater than zero."
            else:
                args.areInputsValid = True


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
