import adsk.core


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
