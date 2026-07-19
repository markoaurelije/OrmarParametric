import os
import json
from typing import Optional
import adsk.core, adsk.fusion, adsk.cam, traceback
from ..commandDialog.dialog_config import InputItem, input_items, InputType
from ..commandDialog import presets as presets_store
from ..commandDialog import base_design
from ...lib import fusionAddInUtils as futil

app = adsk.core.Application.get()

# Template ("predložak") UI labels: the neutral first item of each cabinet
# tab's template dropdown, and the "no template" choice for a new cabinet.
PRESET_PLACEHOLDER = "(odaberi predložak)"
NO_PRESET_ITEM = "Osnovni ormar"


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


def _create_project_tab(inputs: adsk.core.CommandInputs):
    """Build the leading, design-scope "Projekt" tab.

    Everything here applies to the *whole design*, not to a single cabinet:
    adding a cabinet, the design-wide finish palette + click pickers (they act
    on any clicked board across all cabinets), and the cut-list export.  Keeping
    them in their own tab is what separates project-level actions from the
    per-cabinet parameter tabs that follow, so the two scopes never mix.
    """
    res_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    # An icon on this tab sets it apart from the plain-text cabinet tabs.
    project_tab = inputs.addTabCommandInput("projekt_tab", "Projekt", res_dir)
    tab = project_tab.children

    # -- Ormari: add a new cabinet ------------------------------------------
    ormari = tab.addGroupCommandInput("projekt_ormari", "Ormari")
    ormari.isExpanded = True

    # Template to build the new cabinet from: "Osnovni ormar" is the plain
    # code-generated cabinet, any other choice applies that template's full
    # parameter set right after generation.
    preset_dd = ormari.children.addDropDownCommandInput(
        "new_cabinet_preset",
        "Predložak",
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    preset_dd.listItems.add(NO_PRESET_ITEM, True, "")
    for preset_name in presets_store.get_presets():
        preset_dd.listItems.add(preset_name, False, "")
    preset_dd.tooltip = (
        "Predložak za novi ormar: 'Osnovni ormar' stvara ormar sa zadanim "
        "parametrima, a predložak odmah postavlja sve parametre (npr. "
        "kuhinjski donji element)."
    )

    add_btn = ormari.children.addBoolValueInput(
        "addCabinetButton", "Dodaj ormar", False, "", True
    )
    add_btn.tooltip = (
        "Dodaj novi ormar u dizajn prema odabranom predlošku. Ime se traži pri "
        "kliku (predloži se sljedeće slobodno ime)."
    )

    # -- Bojanje i kantiranje: design-wide finish palette + pickers ---------
    finish = tab.addGroupCommandInput("projekt_finish", "Bojanje i kantiranje")
    finish.isExpanded = True

    # Read-only status line: which decors are currently used in the design.
    # Refreshed on every preview and after every finish click.
    colors_box = finish.children.addTextBoxCommandInput(
        "finish_colors_in_use", "Boje u projektu", _colors_in_use_text(), 1, True
    )
    colors_box.tooltip = (
        "Boje trenutno korištene na pločama i rubovima u cijelom dizajnu."
    )

    # Active decor: the colour the paint-bucket applies.  Populated from the
    # decor palette (decors.json).
    decor_dd = finish.children.addDropDownCommandInput(
        "finish_active_decor", "Boja", adsk.core.DropDownStyles.TextListDropDownStyle
    )
    for name in _DECOR_ORDER:
        decor_dd.listItems.add(name, name == _DEFAULT_FRONT, "")
    if decor_dd.listItems.count and decor_dd.selectedItem is None:
        decor_dd.listItems.item(0).isSelected = True
    decor_dd.tooltip = (
        "Boja koja se nanosi kad klikneš ploču. Uredi paletu u decors.json."
    )

    # Click-to-colour: pick a board in the viewport to paint it the active decor
    # (pick 'Bijela' to send it back to interior white).  It is a momentary
    # picker -- the click sets the board's per-cabinet decor and the selection is
    # cleared immediately; the model itself shows each board's colour.
    paint_sel = finish.children.addSelectionInput(
        "finish_paint_select", "Oboji ploču", "Klikni ploču za bojanje"
    )
    paint_sel.addSelectionFilter("SolidFaces")
    paint_sel.setSelectionLimits(0, 0)
    paint_sel.tooltip = (
        "Klikni ploču u modelu da je obojiš u odabranu boju ('Boja' gore). "
        "Odaberi 'Bijela' pa klikni da je vratiš u bijelo. Fronte i gornja ploča "
        "su obojane po defaultu."
    )

    # Click-to-band: pick a narrow edge face to band it in the active decor
    # (click again with the same decor to make it raw).
    band_sel = finish.children.addSelectionInput(
        "finish_band_select", "Kantiraj rub", "Klikni rub (usku plohu) za kantiranje"
    )
    band_sel.addSelectionFilter("SolidFaces")
    band_sel.setSelectionLimits(0, 0)
    band_sel.tooltip = (
        "Klikni usku plohu (rub) ploče da je kantiraš u odabranoj boji ('Boja' "
        "gore) -- neovisno o boji ploče. Klikni ponovno istom bojom da rub "
        "postane nekantiran (prugast)."
    )

    # Project-wide colour swap from one click: reads the clicked board's current
    # decor as the source and repaints every board/edge in that colour to the
    # active decor.
    swap_sel = finish.children.addSelectionInput(
        "finish_swap_select",
        "Zamijeni boju u projektu",
        "Klikni ploču da sve iste boje postanu odabrana boja",
    )
    swap_sel.addSelectionFilter("SolidFaces")
    swap_sel.setSelectionLimits(0, 0)
    swap_sel.tooltip = (
        "Klikni ploču: SVE ploče i rubovi u projektu koji su iste boje kao ta "
        "ploča postanu odabrana boja ('Boja' gore). Promjena jednim klikom."
    )

    # -- Izvoz: cut-list export ---------------------------------------------
    izvoz = tab.addGroupCommandInput("projekt_izvoz", "Izvoz")
    izvoz.isExpanded = True
    export_btn = izvoz.children.addBoolValueInput(
        "exportCutListButton", "Izvezi krojnu listu u Excel", False, "", True
    )
    export_btn.tooltip = (
        "Spremi krojnu listu svih ormara u kopiju narudžbenice (.xlsm) na "
        "Desktop. Predložak narudzba-excel.xlsm se ne mijenja."
    )


def create_dialog(inputs: adsk.core.CommandInputs):
    #####  CREATING A DIALOG  #####
    # cabinets are generated from code (base_design.py), so any design can
    # add one - no J1 base document needed anymore
    doc = app.activeDocument
    futil.log(f"Current document: {doc.name}")

    # Leading tab: whole-design actions (add cabinet / finish palette / export).
    _create_project_tab(inputs)

    # Then one tab per cabinet, holding only that cabinet's parameters.
    prefixis = get_prefixes()
    for prefix in prefixis:
        futil.log(f"Adding tab: {prefix}")
        tab_input = inputs.addTabCommandInput(prefix, prefix)
        dropdown = tab_input.children.addDropDownCommandInput(
            f"{prefix}presets",
            "Predložak",
            adsk.core.DropDownStyles.LabeledIconDropDownStyle,
        )
        dropdown.listItems.add(PRESET_PLACEHOLDER, True, "")
        for preset_name in presets_store.get_presets():
            dropdown.listItems.add(preset_name, False, "")
        dropdown.tooltip = (
            "Primijeni predložak na ovaj ormar (postavlja sve njegove parametre)."
        )

        save_btn = tab_input.children.addBoolValueInput(
            f"{prefix}save_preset", "Spremi kao predložak", False, "", False
        )
        save_btn.tooltip = (
            "Spremi trenutne parametre ovog ormara kao imenovani predložak "
            "(postojeće ime = uredi/prepiši predložak, novo ime = dodaj novi)."
        )

        # delete-cabinet button (per tab)
        tab_input.children.addBoolValueInput(
            f"{prefix}delete_cabinet",
            "Obriši ormar",
            False,
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "resources", "remove"
            ),
            False,
        )

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


def reseat_free_wrappers(prefix: str):
    """Self-healing pass, run every preview/execute cycle per cabinet.

    Cabinets are meant to live in a multi-cabinet design where the *cabinet
    root occurrences* get connected to each other with user-created joints
    (at most one cabinet grounded as the design's anchor) - so this must
    never touch a cabinet's own root occurrence, its grounding, or its
    position. Forcing every free cabinet root to ``isGrounded`` would fight
    that workflow directly (a cabinet the user is about to joint to another
    one needs to stay free/unconstrained until that joint exists).

    What *does* need self-healing is internal to a single cabinet, and comes
    in two flavours, both harmless regardless of how the cabinet root itself
    is constrained (grounded, jointed to another cabinet, or fully free):

    1. Any child occurrence with **no joint of its own is a free rigid body**
       Fusion lets the user click-drag anywhere in the viewport - a shelf
       pattern only joints its *seed* occurrence (the first shelf); the
       ``broj_polica``-driven copies get no joint at all, so without this
       fix every shelf but the first can be dragged out of the cabinet. Any
       such un-jointed occurrence is grounded *to its own parent* (the
       cabinet component), which stops it being draggable without
       interfering with whatever still legitimately drives its position
       (verified live: a grounded pattern copy keeps updating correctly
       across ``broj_polica`` changes). Grounding *is* skipped for anything
       referenced by one of the cabinet's own joints - forcing that as well
       conflicts with the joint and freezes the part at the wrong position
       (confirmed live: grounding the already-jointed seed shelf broke it).
    2. The joint-less ``ukrute``/``nogice`` wrapper occurrences additionally
       have *nothing at all* driving their transform (unlike pattern copies,
       which the pattern feature keeps recomputing), so besides grounding
       they can also end up stranded at a stale position if the cabinet
       moves. Reset those two specifically to the cabinet's exact frame
       (full matrix, not just translation, so a cabinet joined to another at
       an angle is handled correctly too).
    """
    design = adsk.fusion.Design.cast(app.activeProduct)
    cabinet_name = prefix.rstrip("_")
    occ = next(
        (o for o in design.rootComponent.occurrences
         if o.component.name == cabinet_name),
        None,
    )
    if occ is None:
        return
    try:
        jointed_names = set()
        for j in occ.component.joints:
            if j.occurrenceOne is not None:
                jointed_names.add(j.occurrenceOne.name)
            if j.occurrenceTwo is not None:
                jointed_names.add(j.occurrenceTwo.name)

        cab_transform = occ.transform2
        for child in occ.childOccurrences:
            if child.name in jointed_names:
                continue  # already fully constrained by a real joint

            base = base_design.base_component_name(child.component.name, prefix)
            if base in ("ukrute", "nogice") and not child.transform2.isEqualTo(cab_transform):
                # proxy from root: world frame; the wrapper's correct frame
                # is exactly the cabinet's own (local identity within it)
                child.transform2 = cab_transform.copy()
                futil.log(f"Re-seated stranded wrapper '{child.component.name}'")

            if not child.isGroundToParent:
                child.isGroundToParent = True
                futil.log(f"Grounded free occurrence '{child.component.name}' to its cabinet")
    except Exception as e:
        futil.log(
            f"reseat_free_wrappers({prefix}) failed: {e}",
            adsk.core.LogLevels.WarningLogLevel,
        )


def next_free_cabinet_name(base: str = "O") -> str:
    """Suggest the next unused cabinet name (``O1``, ``O2`` ...).

    Checks both the discovered prefixes and the raw parameter list so the
    suggestion never collides with a cabinet already in the design (a collision
    would trip request_add_cabinet's "already exist" guard)."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    existing_prefixes = set(get_prefixes())  # e.g. {"J1_", "O1_"}
    n = 1
    while True:
        candidate = f"{base}{n}"
        if (
            f"{candidate}_" not in existing_prefixes
            and design.userParameters.itemByName(f"{candidate}_sirina") is None
        ):
            return candidate
        n += 1


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
    nogice_presence = design.userParameters.itemByName(prefix + "nogice")
    pregrada_presence = design.userParameters.itemByName(prefix + "pregrada")
    police_presence = design.userParameters.itemByName(prefix + "police")

    # Get the target component (change index if needed)
    gornjaPlocaComp = None
    ukruteComp = None
    lijevaFrontaComp = None
    desnaFrontaComp = None
    coklaComp = None
    nogiceComp = None
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
        # strip the cabinet prefix (and any ' (N)' suffix), then normalise
        # underscores to spaces so both the scoped new names ('O2_gornja ploca')
        # and legacy underscore names ('gornja_ploca') match the same way.
        base = base_design.base_component_name(
            occurrence.component.name, prefix
        ).replace("_", " ")
        if base.startswith("gornja ploca"):
            gornjaPlocaComp = occurrence
        elif base.startswith("ukrute"):
            ukruteComp = occurrence
        elif base.startswith("fronta lijevo"):
            lijevaFrontaComp = occurrence
        elif base.startswith("fronta desno"):
            desnaFrontaComp = occurrence
        elif base.startswith("cokla"):
            coklaComp = occurrence
        elif base.startswith("nogice"):
            nogiceComp = occurrence
        elif base.startswith("pregrada"):
            pregradaComp = occurrence
        elif base.startswith("polica"):
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

    if nogice_presence and nogiceComp:
        nogiceComp.isLightBulbOn = bool(nogice_presence.value)

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


# ---------------------------------------------------------------------------
# Board finish (colour) + edge-banding (kantiranje) visualisation.
#
# Each board is painted so the model reads like the real cabinet:
#   * broad faces  -> finish COLOUR if the board is "coloured" (visible outside),
#                     otherwise WHITE (interior board).
#   * banded edges -> finish COLOUR (the edge-band tape).
#   * raw edges    -> a STRIPED texture, so "no banding here" is unmistakable and
#                     never confused with a white board face.
#
# Each board carries a *decor* (a named colour from the palette in decors.json).
# Which boards are coloured by default and which edges are banded comes from
# base_design (defaults + board_rules.json), re-evaluated against the cabinet's
# live flag parameters every preview.  Per-cabinet user overrides -- the decor a
# board was painted with, and per-edge banding -- are stored as occurrence
# attributes and win over the defaults.  apply_finish mirrors
# set_component_visibility: it runs after the parameters are pushed, on every
# preview and on execute.  A board's faces AND its banded edges are painted its
# decor colour; raw edges get the striped 'no banding' texture.
# ---------------------------------------------------------------------------
_STRIPE_APPEARANCE_NAME = "Ormar - bez kanta"   # striped 'no banding' edge
_STRIPE_FALLBACK_RGB = (120, 120, 120)  # if the striped texture can't be built
_STRIPE_PNG = os.path.join(
    os.path.dirname(__file__), "resources", "textures", "no_banding.png"
)
_STRIPE_SIZE_MM = 6.0  # physical stripe tile size, small enough to read on edges

# --- decor palette (decors.json) -------------------------------------------
_DECORS = {}          # name -> {"rgb": (r,g,b), "code": str}
_DECOR_ORDER = []     # decor names in palette order (for the dropdown)
_DEFAULT_FRONT = "Boja"     # decor for coloured boards, overridden by the file
_DEFAULT_INTERIOR = "Bijelo"  # decor for interior/white boards
_DECOR_FALLBACK_RGB = (200, 200, 200)


def _load_decors():
    """Load the decor palette from decors.json; keep a small built-in fallback."""
    global _DEFAULT_FRONT, _DEFAULT_INTERIOR
    _DECORS.clear()
    _DECOR_ORDER.clear()
    path = os.path.join(os.path.dirname(__file__), "decors.json")
    data = None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = None
    if not data:
        data = {
            "default_front": "Hrast",
            "default_interior": "Bijela",
            "decors": [
                {"name": "Bijela", "rgb": [244, 244, 240], "code": ""},
                {"name": "Hrast", "rgb": [196, 160, 106], "code": ""},
            ],
        }
    for entry in data.get("decors", []):
        name = entry.get("name")
        if not name:
            continue
        rgb = tuple(entry.get("rgb", _DECOR_FALLBACK_RGB))[:3]
        _DECORS[name] = {"rgb": rgb, "code": entry.get("code", "")}
        _DECOR_ORDER.append(name)
    _DEFAULT_FRONT = data.get("default_front") or (_DECOR_ORDER[-1] if _DECOR_ORDER else "Hrast")
    _DEFAULT_INTERIOR = data.get("default_interior") or (_DECOR_ORDER[0] if _DECOR_ORDER else "Bijela")


_load_decors()


def decor_rgb(name):
    """Preview RGB for a decor name (fallback grey for unknown names)."""
    entry = _DECORS.get(name)
    return entry["rgb"] if entry else _DECOR_FALLBACK_RGB

# per-cabinet user overrides live in attributes under these groups:
_FINISH_ATTR_GROUP = "OrmarFinish"    # which boards are coloured (per spec name)
_BANDING_ATTR_GROUP = "OrmarBanding"  # which edges are banded ("<spec>:<orient>")

_FACE_TOL = 0.1  # cm; a face this close to the bbox extreme is an outer face

# world axis + sign -> edge orientation. +X points from "bok desno" toward
# "bok lijevo", +Y toward the cabinet front, +Z up (see base_design frame).
_ORIENTATION_AXIS = {
    (0, 1): "left", (0, -1): "right",
    (1, 1): "front", (1, -1): "back",
    (2, 1): "top", (2, -1): "bottom",
}
_ALL_ORIENTATIONS = ("front", "back", "left", "right", "top", "bottom")


def _appearance_library():
    """The library that holds appearances; its exact name varies by Fusion
    version/locale ("Fusion Appearance Library", "Fusion 360 Appearance ...")."""
    libs = app.materialLibraries
    for i in range(libs.count):
        lib = libs.item(i)
        if "Appearance" in lib.name and lib.appearances.count:
            return lib
    for i in range(libs.count):
        if libs.item(i).appearances.count:
            return libs.item(i)
    return None


def _get_or_create_solid_appearance(design, name, rgb):
    """A named solid-colour appearance, created once by copying a plain library
    appearance and recolouring it."""
    appr = design.appearances.itemByName(name)
    if appr:
        return appr
    lib = _appearance_library()
    if lib is None:
        return None
    base = None
    for candidate in ("ABS (White)", "Plastic - Matte (White)",
                      "Powder Coat (Gloss - White)", "Paint - Enamel Glossy (White)"):
        base = lib.appearances.itemByName(candidate)
        if base:
            break
    if base is None:
        base = lib.appearances.item(0)
    if base is None:
        return None
    appr = design.appearances.addByCopy(base, name)
    for i in range(appr.appearanceProperties.count):
        prop = appr.appearanceProperties.item(i)
        if isinstance(prop, adsk.core.ColorProperty):
            prop.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
            break
    return appr


def _get_or_create_stripe_appearance(design, name):
    """A named appearance carrying the diagonal-stripe 'no banding' texture.
    Built by copying a library appearance that already has an image texture on
    its Colour ("Fabric (Grey)") and swapping in resources/textures/no_banding.png;
    falls back to a solid grey if that isn't possible."""
    appr = design.appearances.itemByName(name)
    if appr:
        return appr
    lib = _appearance_library()
    base = lib.appearances.itemByName("Fabric (Grey)") if lib else None
    if base is None or not os.path.exists(_STRIPE_PNG):
        return _get_or_create_solid_appearance(design, name, _STRIPE_FALLBACK_RGB)
    appr = design.appearances.addByCopy(base, name)
    try:
        cp = appr.appearanceProperties.itemByName("Color")
        if cp and cp.hasConnectedTexture:
            tex = cp.connectedTexture
            tex.changeTextureImage(_STRIPE_PNG)
            for prop_name in ("Sample Size", "Size Y"):
                pp = tex.properties.itemByName(prop_name)
                if pp:
                    pp.value = _STRIPE_SIZE_MM
    except Exception as e:
        futil.log(f"apply_finish: stripe texture setup failed: {e}")
    return appr


def _bbox_frame(body):
    """(lo, hi, center, thickness_axis) for a board body in its current context."""
    bb = body.boundingBox
    lo = (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z)
    hi = (bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)
    center = tuple((hi[i] + lo[i]) / 2.0 for i in range(3))
    thickness_axis = min(range(3), key=lambda i: hi[i] - lo[i])
    return lo, hi, center, thickness_axis


def _classify_face(frame, face):
    """Classify a planar face of a board box as ('big', None) for a broad face,
    ('edge', orientation) for one of the four narrow outer edges, or
    (None, None) for a recessed/interior face (groove/slot).  Same geometry used
    by _paint_board and by the edge-banding picker so they always agree."""
    lo, hi, center, thickness_axis = frame
    c = face.centroid
    cc = (c.x, c.y, c.z)
    d = tuple(cc[i] - center[i] for i in range(3))
    axis = max(range(3), key=lambda i: abs(d[i]))
    sign = 1 if d[axis] > 0 else -1
    extreme = hi[axis] if sign > 0 else lo[axis]
    if abs(cc[axis] - extreme) > _FACE_TOL:
        return (None, None)  # recessed
    if axis == thickness_axis:
        return ("big", None)
    return ("edge", _ORIENTATION_AXIS[(axis, sign)])


def _paint_board(body, appr_face, band_appr_by_orient, appr_stripe):
    """Paint one board body: big faces get the board's decor appearance; each
    narrow edge gets its band-colour appearance (from band_appr_by_orient) if
    banded, else the striped texture.  Robust to grooves/splits -- only faces on
    the bounding box's outer plane count; recessed interior faces are left alone."""
    frame = _bbox_frame(body)

    for face in body.faces:
        try:
            if not isinstance(face.geometry, adsk.core.Plane):
                continue
            kind, orient = _classify_face(frame, face)
            if kind is None:
                continue  # recessed face (groove/slot interior)
            if kind == "big":
                target = appr_face
            else:
                target = band_appr_by_orient.get(orient, appr_stripe)
            if target is None:
                continue
            cur = face.appearance
            if cur is None or cur.name != target.name:
                face.appearance = target
        except Exception as e:
            futil.log(f"apply_finish: skipping a face: {e}")


def _cabinet_flags(design, prefix):
    """This cabinet's parameter values, keyed by base name (prefix stripped)."""
    flags = {}
    for i in range(design.userParameters.count):
        p = design.userParameters.item(i)
        if p.name.startswith(prefix):
            flags[p.name[len(prefix):]] = p.value
    return flags


def get_decor_override(holder, spec_name):
    """The user's persisted per-cabinet decor override for a board (a decor name),
    or None if unset.  Legacy "1"/"0" values map to the default front/interior."""
    attr = holder.attributes.itemByName(_FINISH_ATTR_GROUP, spec_name)
    if attr is None:
        return None
    if attr.value == "1":
        return _DEFAULT_FRONT
    if attr.value == "0":
        return _DEFAULT_INTERIOR
    return attr.value


def set_decor_override(holder, spec_name, decor_name):
    holder.attributes.add(_FINISH_ATTR_GROUP, spec_name, decor_name)


def set_banding_override(holder, spec_name, orient, value):
    """Persist one edge's banding override: a decor name = banded in that colour,
    "" = raw (not banded)."""
    holder.attributes.add(_BANDING_ATTR_GROUP, f"{spec_name}:{orient}", value)


# In-memory overrides for the *current dialog session*.  Clicks in the dialog
# land here rather than writing attributes directly: model changes made from the
# inputChanged handler are rolled back on the next preview cycle, but a plain
# Python dict survives, and apply_finish (run every preview / execute) reads it.
# persist_finish_overrides() flushes both to attributes on OK.
_session_decor_overrides = {}    # (prefix, spec) -> decor name
_session_banding_overrides = {}  # (prefix, spec, orient) -> decor name ("" = raw)


def clear_session_finish_overrides():
    """Reset session overrides -- call when the dialog (re)opens so a cancelled
    session doesn't leak into the next one; persisted attributes remain."""
    _session_decor_overrides.clear()
    _session_banding_overrides.clear()


def effective_decor(design, prefix, spec, holder, flags):
    """The decor name a board is painted with, honouring (in priority order) a
    live session override, a persisted attribute override, then the rule default
    (the default-front decor for a coloured board, default-interior otherwise)."""
    key = (prefix, spec)
    if key in _session_decor_overrides:
        return _session_decor_overrides[key]
    override = get_decor_override(holder, spec)
    if override is not None:
        return override
    default_colored = base_design.resolved_colored(spec, flags, None)
    return _DEFAULT_FRONT if default_colored else _DEFAULT_INTERIOR


def _raw_banding_override(prefix, spec, orient, holder):
    """The stored banding override string for one edge, or None if unset.
    A decor name means banded in that colour, "" means raw."""
    key = (prefix, spec, orient)
    if key in _session_banding_overrides:
        return _session_banding_overrides[key]
    attr = holder.attributes.itemByName(_BANDING_ATTR_GROUP, f"{spec}:{orient}")
    return attr.value if attr else None


def effective_banding(design, prefix, spec, holder, flags):
    """Map of banded edge orientation -> decor name (the band colour) for a board.
    Rule-banded edges default to the board's own decor; per-edge overrides (a
    decor name to band in that colour, "" to make it raw) apply on top.  Raw
    edges are omitted from the map."""
    board_decor = effective_decor(design, prefix, spec, holder, flags)
    banded = {o: board_decor
              for o in base_design.resolved_banding(base_design.BANDING_BY_NAME[spec], flags)}
    for orient in _ALL_ORIENTATIONS:
        ov = _raw_banding_override(prefix, spec, orient, holder)
        if ov is None:
            continue
        if ov in ("", "0"):          # explicit raw ("0" = legacy off)
            banded.pop(orient, None)
        elif ov == "1":               # legacy on -> banded in board decor
            banded[orient] = board_decor
        else:                          # banded in the named decor
            banded[orient] = ov
    return banded


def persist_finish_overrides():
    """Write this session's colour + banding overrides to occurrence attributes
    so they survive save/reload.  Called on execute (OK)."""
    design = adsk.fusion.Design.cast(app.activeProduct)

    def _holder(prefix):
        wrapper = next(
            (o for o in design.rootComponent.occurrences
             if o.component.name == prefix.rstrip("_")),
            None,
        )
        return wrapper if wrapper is not None else design.rootComponent

    for (prefix, spec), decor in _session_decor_overrides.items():
        set_decor_override(_holder(prefix), spec, decor)
    for (prefix, spec, orient), value in _session_banding_overrides.items():
        set_banding_override(_holder(prefix), spec, orient, value)


def apply_finish(prefix):
    """Paint one cabinet's boards (faces + edges) to reflect finish colour and
    edge banding.  Run after the parameters are pushed, every preview + execute."""
    design = adsk.fusion.Design.cast(app.activeProduct)

    appr_stripe = _get_or_create_stripe_appearance(design, _STRIPE_APPEARANCE_NAME)

    # one appearance per decor, created on demand and cached for this run
    decor_appr_cache = {}

    def _decor_appearance(decor_name):
        if decor_name not in decor_appr_cache:
            decor_appr_cache[decor_name] = _get_or_create_solid_appearance(
                design, "Ormar - " + decor_name, decor_rgb(decor_name)
            )
        return decor_appr_cache[decor_name]

    flags = _cabinet_flags(design, prefix)
    wrapper = next(
        (occ for occ in design.rootComponent.occurrences
         if occ.component.name == prefix.rstrip("_")),
        None,
    )
    # per-cabinet overrides live on the wrapper occurrence (root comp for legacy)
    attr_holder = wrapper if wrapper is not None else design.rootComponent

    face_appr_cache = {}   # spec -> board's face appearance
    band_appr_cache = {}   # spec -> {orient: band appearance}

    # Walk from the root-level occurrence via childOccurrences: a nested
    # component's `allOccurrences` gives proxies missing the root->wrapper step,
    # and BRepFace.appearance then raises InternalValidationError.
    def _paint_tree(occ):
        spec = base_design.spec_name_for_component(occ.component.name, prefix)
        if spec is not None:
            if spec not in face_appr_cache:
                face_appr_cache[spec] = _decor_appearance(
                    effective_decor(design, prefix, spec, attr_holder, flags)
                )
                band_map = effective_banding(design, prefix, spec, attr_holder, flags)
                band_appr_cache[spec] = {
                    orient: _decor_appearance(decor)
                    for orient, decor in band_map.items()
                }
            appr_face = face_appr_cache[spec]
            if appr_face is not None:
                for body in occ.bRepBodies:
                    _paint_board(body, appr_face, band_appr_cache[spec], appr_stripe)
        for child in occ.childOccurrences:
            _paint_tree(child)

    if wrapper is not None:
        _paint_tree(wrapper)
    else:
        for occ in design.rootComponent.occurrences:
            _paint_tree(occ)


def _entity_to_occurrence(entity):
    """Resolve a picked face/body/occurrence to its owning leaf occurrence."""
    try:
        if isinstance(entity, adsk.fusion.BRepFace):
            return entity.body.assemblyContext
        if isinstance(entity, adsk.fusion.BRepBody):
            return entity.assemblyContext
        if isinstance(entity, adsk.fusion.Occurrence):
            return entity
    except Exception:
        pass
    return None


def _resolve_board_context(occ):
    """From a picked leaf occurrence -> (spec, prefix, holder, flags), or None
    if it is not a recognised board."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    # fullPathName is "<wrapper>:1+<child>:1..." -> first token is the cabinet
    wrapper_name = occ.fullPathName.split("+")[0].split(":")[0]
    prefix = wrapper_name + "_"
    # resolve the spec with the cabinet prefix so scoped names ('O2_polica') map
    spec = base_design.spec_name_for_component(occ.component.name, prefix)
    if spec is None:
        return None
    wrapper = next(
        (o for o in design.rootComponent.occurrences
         if o.component.name == wrapper_name),
        None,
    )
    holder = wrapper if wrapper is not None else design.rootComponent
    return spec, prefix, holder, _cabinet_flags(design, prefix)


def set_board_decor(entity, decor_name):
    """Paint a clicked board with `decor_name` for its cabinet.  Records the
    choice in the in-memory session store (NOT a direct attribute write -- that
    would be rolled back after the inputChanged handler); apply_finish paints
    from it every preview and persist_finish_overrides() commits it on OK.
    Returns (prefix, spec_name, decor_name) or None if not a recognised board."""
    occ = _entity_to_occurrence(entity)
    if occ is None:
        return None
    ctx = _resolve_board_context(occ)
    if ctx is None:
        return None
    spec, prefix, holder, flags = ctx
    _session_decor_overrides[(prefix, spec)] = decor_name
    return (prefix, spec, decor_name)


def set_edge_band(entity, decor_name):
    """Band a clicked narrow edge in `decor_name` (the active decor).  Clicking an
    edge already banded in that same decor turns it raw (toggle off).  Records the
    choice in the session store (same reason as set_board_decor).  Returns
    (prefix, spec_name, orientation, new_decor_or_"") or None if the pick is not a
    bandable edge face (a broad face or an interior/groove face)."""
    if not isinstance(entity, adsk.fusion.BRepFace):
        return None
    body = entity.body
    occ = body.assemblyContext
    if occ is None:
        return None
    ctx = _resolve_board_context(occ)
    if ctx is None:
        return None
    spec, prefix, holder, flags = ctx
    kind, orient = _classify_face(_bbox_frame(body), entity)
    if kind != "edge" or orient is None:
        return None  # a broad face or a recessed face -- not a bandable edge
    design = adsk.fusion.Design.cast(app.activeProduct)
    current = effective_banding(design, prefix, spec, holder, flags).get(orient)
    new_value = "" if current == decor_name else decor_name  # "" = raw
    _session_banding_overrides[(prefix, spec, orient)] = new_value
    return (prefix, spec, orient, new_value)


def _iter_cabinet_boards(design):
    """Yield (prefix, spec, wrapper, flags) for every board across all cabinets,
    de-duplicated per (prefix, spec).  Mirrors apply_finish's tree walk: each
    root-level wrapper occurrence that owns our `<name>_sirina` parameter is a
    cabinet, and its whole occurrence subtree is scanned for board components."""
    for wrapper in design.rootComponent.occurrences:
        prefix = wrapper.component.name + "_"
        if design.userParameters.itemByName(prefix + "sirina") is None:
            continue  # not one of our cabinets
        flags = _cabinet_flags(design, prefix)
        seen = set()
        stack = [wrapper]
        while stack:
            occ = stack.pop()
            spec = base_design.spec_name_for_component(occ.component.name, prefix)
            if spec is not None and spec not in seen:
                seen.add(spec)
                yield prefix, spec, wrapper, flags
            for child in occ.childOccurrences:
                stack.append(child)


def _remap_decor_everywhere(design, source_decor, target_decor):
    """Repaint every board and edge-band whose *current* colour is `source_decor`
    to `target_decor`, across all cabinets, via the session-override store (so it
    previews live and persists on OK).  Returns the set of affected prefixes.

    Rule-banded edges that merely follow their board's colour are left untouched
    when that board is itself being remapped -- they keep tracking the board
    automatically -- so only genuinely source-coloured faces/edges are pinned."""
    affected = set()
    for prefix, spec, holder, flags in _iter_cabinet_boards(design):
        # snapshot both before mutating, so banding defaults still reflect the
        # pre-swap board decor
        cur_decor = effective_decor(design, prefix, spec, holder, flags)
        cur_bands = effective_banding(design, prefix, spec, holder, flags)

        if cur_decor == source_decor:
            _session_decor_overrides[(prefix, spec)] = target_decor
            affected.add(prefix)

        for orient, band_decor in cur_bands.items():
            if band_decor != source_decor:
                continue
            # a rule-default band matching a board that's also being remapped
            # will follow the board on its own; don't pin it.
            if (
                cur_decor == source_decor
                and _raw_banding_override(prefix, spec, orient, holder) is None
            ):
                continue
            _session_banding_overrides[(prefix, spec, orient)] = target_decor
            affected.add(prefix)
    return affected


def swap_project_decor(entity, target_decor):
    """Project-wide colour swap from a single click.  Reads the clicked board's
    current decor as the *source*, then remaps every board and edge-band in that
    colour -- across all cabinets -- to `target_decor`.  Returns
    (source_decor, target_decor, affected_prefixes) or None if the pick is not a
    recognised board.  A no-op (source == target) returns an empty prefix set."""
    occ = _entity_to_occurrence(entity)
    if occ is None:
        return None
    ctx = _resolve_board_context(occ)
    if ctx is None:
        return None
    spec, prefix, holder, flags = ctx
    design = adsk.fusion.Design.cast(app.activeProduct)
    source_decor = effective_decor(design, prefix, spec, holder, flags)
    if source_decor == target_decor:
        return (source_decor, target_decor, set())
    affected = _remap_decor_everywhere(design, source_decor, target_decor)
    return (source_decor, target_decor, affected)


def decors_in_use():
    """The distinct decors currently painted on any board face or edge-band in
    the design, in palette order (unknown names sorted last)."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    used = set()
    for prefix, spec, holder, flags in _iter_cabinet_boards(design):
        used.add(effective_decor(design, prefix, spec, holder, flags))
        used.update(effective_banding(design, prefix, spec, holder, flags).values())
    ordered = [d for d in _DECOR_ORDER if d in used]
    ordered += sorted(d for d in used if d not in _DECOR_ORDER)
    return ordered


def _colors_in_use_text():
    names = decors_in_use()
    return ", ".join(names) if names else "(nema)"


def refresh_colors_in_use(inputs: adsk.core.CommandInputs):
    """Update the read-only "Boje u projektu" status line to the current set of
    in-use decors.  Safe to call every preview / after every finish click."""
    box = inputs.itemById("finish_colors_in_use") if inputs else None
    if box is None:
        return
    try:
        text = _colors_in_use_text()
        if box.formattedText != text:
            box.formattedText = text
    except Exception as e:
        futil.log(f"refresh_colors_in_use failed: {e}")


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


def _preset_expression(expression: str, prefix: str) -> str:
    """Resolve a template expression's "{prefix}" placeholder (see presets.py)
    against the target cabinet's prefix."""
    return expression.replace("{prefix}", prefix)


def load_preset(preset_name: str, inputs: adsk.core.CommandInputs, prefix: str = "J1_"):
    preset = presets_store.get_presets().get(preset_name)
    if not preset:
        futil.log(
            f"Template '{preset_name}' not found", adsk.core.LogLevels.ErrorLogLevel
        )
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

        set_user_parameter(
            f"{prefix}{input_param.name}",
            _preset_expression(param["expression"], prefix),
        )
        set_input_via_userparam(input_param, inputs, prefix)

    set_component_visibility(prefix)


def apply_preset_params(cabinet_name: str, preset_name: str):
    """Set a freshly generated cabinet's user parameters from a template.

    Used by the add-cabinet flow, where the new cabinet has no dialog tab yet,
    so parameters are written directly (visibility/finish are applied by the
    normal per-prefix pass that runs right after materialization)."""
    preset = presets_store.get_presets().get(preset_name)
    if not preset:
        futil.log(
            f"Template '{preset_name}' not found", adsk.core.LogLevels.ErrorLogLevel
        )
        return
    prefix = f"{cabinet_name}_"
    for param in preset:
        set_user_parameter(
            prefix + param["paramName"],
            _preset_expression(param["expression"], prefix),
        )


def save_cabinet_as_preset(prefix: str, preset_name: str):
    """Save a cabinet's current parameter values as a named template.

    Reads every dialog-managed user parameter of the cabinet and writes the
    full set into presets.json (existing name = overwrite/edit, new name =
    add).  The cabinet's own prefix inside an expression is stored as the
    "{prefix}" placeholder so cross-parameter references stay portable."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    params = []
    for item in input_items:
        if item.input_has_no_param:
            continue
        user_param = design.userParameters.itemByName(prefix + item.name)
        if user_param is None:
            continue
        params.append(
            {
                "paramName": item.name,
                "expression": user_param.expression.replace(prefix, "{prefix}"),
            }
        )
    presets_store.save_preset(preset_name, params)
    futil.log(f"Saved template '{preset_name}' ({len(params)} params) from {prefix}")


def refresh_preset_dropdowns(inputs: adsk.core.CommandInputs):
    """Add newly saved template names to the open dialog's template dropdowns
    (the project tab's new-cabinet one and each cabinet tab's) so a template
    saved mid-session is immediately selectable."""
    names = list(presets_store.get_presets().keys())
    dropdown_ids = ["new_cabinet_preset"] + [f"{p}presets" for p in get_prefixes()]
    for dropdown_id in dropdown_ids:
        dropdown = adsk.core.DropDownCommandInput.cast(
            _find_command_input(inputs, dropdown_id)
        )
        if not dropdown:
            continue
        existing = {
            dropdown.listItems.item(i).name for i in range(dropdown.listItems.count)
        }
        for name in names:
            if name not in existing:
                dropdown.listItems.add(name, False, "")


def request_add_cabinet(new_component_name: str, preset_name: Optional[str] = None):
    """Handle a "Dodaj ormar" click, optionally applying a template.

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
        if preset_name:
            # no dialog is attached to the brand-new document, so apply the
            # template and the resulting visibility/finish directly
            apply_preset_params(new_component_name, preset_name)
            set_component_visibility(f"{new_component_name}_")
            apply_finish(f"{new_component_name}_")
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

    CommandExecutePreviewHandler.pending_cabinets[new_component_name] = preset_name
    CommandExecuteHandler.pending_cabinets[new_component_name] = preset_name
    futil.log(
        f"Queued cabinet '{new_component_name}' (template: {preset_name}) "
        "to materialize on next preview/execute"
    )


_materializing = False


def materialize_pending_cabinets(pending_cabinets: dict):
    """pending_cabinets maps cabinet name -> template name (or None)."""
    global _materializing
    if not pending_cabinets or _materializing:
        # guards against reentrant preview/execute cycles Fusion may pump
        # while add_cabinet's own API calls are still running
        return
    _materializing = True
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        for name, preset_name in pending_cabinets.items():
            if design.userParameters.itemByName(f"{name}_sirina"):
                continue  # already persisted this cycle (e.g. on execute, no rollback happened)
            try:
                base_design.add_cabinet(design, name)
                if preset_name:
                    apply_preset_params(name, preset_name)
                futil.log(
                    f"Materialized pending cabinet '{name}' (template: {preset_name})"
                )
            except ValueError as e:
                futil.log(
                    f"Failed to materialize cabinet '{name}': {e}",
                    adsk.core.LogLevels.ErrorLogLevel,
                )
    finally:
        _materializing = False


def request_delete_cabinet(prefix: str):
    """Handle an "Obriši ormar" click.

    Queues the prefix for deletion on the next preview/execute cycle,
    following the same deferred-materialization pattern as add_cabinet
    and add_ultrabox to survive Fusion's preview rollback behaviour.
    """
    from .event_handlers.command_execute_handler import CommandExecuteHandler
    from .event_handlers.command_execute_preview_handler import (
        CommandExecutePreviewHandler,
    )

    CommandExecutePreviewHandler.pending_deletions.add(prefix)
    CommandExecuteHandler.pending_deletions.add(prefix)
    futil.log(f"Queued cabinet '{prefix}' for deletion on next preview/execute")


def perform_delete_cabinet(prefix: str, delete_params: bool = True):
    """Delete a cabinet and all its user parameters from the design.

    The wrapper occurrence is deleted *before* the parameters. This order
    is essential: every cabinet parameter drives sketch dimensions /
    extrude distances inside the occurrence, and Fusion refuses to delete
    a parameter that is still referenced by a feature (isDeletable is
    False while the geometry exists). Only once the occurrence — and with
    it all its parameter-driven features — is gone do the parameters
    become deletable. Deleting params first (with the occurrence still
    present) silently leaves them all behind, which is how orphaned
    parameter sets with no occurrence get created.

    Set `delete_params=False` during preview — Fusion blocks parameter
    deletion in preview mode, so we only remove the occurrence for visual
    feedback and defer the full cleanup to the execute cycle.
    """
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    cabinet_name = prefix.rstrip("_")

    deleted_count = 0

    # 1) Delete the wrapper occurrence first, so its parameter-driven
    #    features release the user parameters (see docstring). Deleting
    #    the occurrence also cleans up the root-level combine/pattern
    #    features that operate on the cabinet's bodies.
    occ = next(
        (o for o in root.occurrences if o.component.name == cabinet_name),
        None,
    )
    if occ is not None:
        futil.log(f"Deleting cabinet occurrence '{cabinet_name}'")
        try:
            occ.deleteMe()
        except Exception as e:
            futil.log(
                f"Failed to delete occurrence '{cabinet_name}': {e}",
                adsk.core.LogLevels.ErrorLogLevel,
            )
    else:
        futil.log(
            f"Cabinet occurrence '{cabinet_name}' not found for deletion",
            adsk.core.LogLevels.WarningLogLevel,
        )

    # 2) Delete all user parameters matching the prefix.
    #    Fusion silently refuses deleteMe() on a parameter that is still
    #    referenced by another parameter's expression, so we retry in
    #    passes: each pass deletes the current leaf parameters, freeing
    #    the ones that referenced them for the next pass. Fusion also
    #    blocks ALL parameter deletion during preview — so this only runs
    #    on execute (delete_params=True).
    if delete_params:
        remaining = set()
        for i in range(design.userParameters.count):
            p = design.userParameters.item(i)
            if p.name.startswith(prefix):
                remaining.add(p.name)

        while remaining:
            deleted_any = False
            for name in list(remaining):
                param = design.userParameters.itemByName(name)
                if param is None:
                    remaining.discard(name)
                    deleted_any = True
                    continue
                try:
                    futil.log(f"Deleting user parameter '{name}'")
                    param.deleteMe()
                except Exception as e:
                    futil.log(
                        f"deleteMe raised for '{name}': {e}",
                        adsk.core.LogLevels.WarningLogLevel,
                    )
                # Fusion may silently refuse — verify it's actually gone.
                if design.userParameters.itemByName(name) is None:
                    remaining.discard(name)
                    deleted_count += 1
                    deleted_any = True
            if not deleted_any:
                futil.log(
                    f"Could not delete {len(remaining)} parameters: {remaining}",
                    adsk.core.LogLevels.WarningLogLevel,
                )
                break

    futil.log(
        f"Deleted cabinet '{cabinet_name}' "
        f"({deleted_count} parameters)"
    )


_deleting = False


def materialize_pending_deletions(pending_deletion_prefixes: set,
                                  delete_params: bool = True):
    global _deleting
    if not pending_deletion_prefixes or _deleting:
        return
    _deleting = True
    try:
        for prefix in list(pending_deletion_prefixes):
            try:
                perform_delete_cabinet(prefix, delete_params=delete_params)
                futil.log(f"Materialized deletion of cabinet '{prefix}'")
            except Exception as e:
                futil.log(
                    f"Failed to delete cabinet '{prefix}': {e}",
                    adsk.core.LogLevels.ErrorLogLevel,
                )
            finally:
                pending_deletion_prefixes.discard(prefix)
    finally:
        _deleting = False


def collect_delete_requests(inputs: adsk.core.CommandInputs):
    """Walk the entire command-inputs tree and, for any pressed
    delete-cabinet button, call request_delete_cabinet (which queues the
    prefix in *both* the preview and execute pending-deletion sets).

    This is a safety net for the case where inputChanged does not fire
    for a BoolValueCommandInput inside a TabCommandInput (a known quirk
    in some Fusion versions).  The button value is reset so it does not
    re-fire on subsequent cycles.
    """

    def _walk(container):
        for i in range(container.count):
            inp = container.item(i)
            if inp.id.endswith("_delete_cabinet") and inp.value:
                prefix = inp.id[: -len("delete_cabinet")]
                futil.log(f"Collecting delete request for '{prefix}' from input scan")
                request_delete_cabinet(prefix)
                inp.value = False  # reset
            if hasattr(inp, "children"):
                _walk(inp.children)

    _walk(inputs)


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
