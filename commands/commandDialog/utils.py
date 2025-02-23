import adsk.core
from ..commandDialog.dialog_config import dialogItems

app = adsk.core.Application.get()


def set_user_parameters(args: adsk.core.CommandEventArgs):

    design = app.activeProduct
    userParams = design.userParameters
    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs

    for paramInput in filter(lambda x: "paramName" in x, dialogItems):
        param = userParams.itemByName(paramInput["paramName"])
        if param:
            if paramInput["inputType"] in "value":
                param.expression = inputs.itemById(paramInput["inputName"]).expression
            elif paramInput["inputType"] == "bool":
                param.value = 1 if inputs.itemById(paramInput["inputName"]).value else 0
            elif paramInput["inputType"] == "integer":
                param.expression = str(inputs.itemById(paramInput["inputName"]).value)


def set_component_visibilit():
    app = adsk.core.Application.get()
    design = app.activeProduct
    rootComp = design.rootComponent

    gornja_ploca_presence = design.userParameters.itemByName("J1_gornja_ploca")
    ukrute_presence = design.userParameters.itemByName("J1_ukrute")
    fronta_presence = design.userParameters.itemByName("J1_fronta")

    # Get the target component (change index if needed)
    gornjaPlocaComp = None
    ukruteComp = None
    frontaComp = None
    for occurrence in rootComp.occurrences:
        if occurrence.component.name == "gornja_ploca":
            gornjaPlocaComp = occurrence
        elif occurrence.component.name == "ukrute":
            ukruteComp = occurrence
        elif occurrence.component.name == "fronta":
            frontaComp = occurrence
        if gornjaPlocaComp and ukruteComp:
            break

    if gornja_ploca_presence and gornjaPlocaComp:
        gornjaPlocaComp.isLightBulbOn = bool(gornja_ploca_presence.value)

    if fronta_presence:
        frontaComp.isLightBulbOn = bool(fronta_presence.value)

    app.log(
        f"Ukrute presence: {ukrute_presence and ukrute_presence.value}, ukruteComp: {ukruteComp and ukruteComp.name}"
    )
    if ukrute_presence and ukruteComp:
        ukruteComp.isLightBulbOn = bool(ukrute_presence.value)
