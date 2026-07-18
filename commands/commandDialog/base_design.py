"""Programmatic reconstruction of the J1 base cabinet.

Builds the complete parametric cabinet (user parameters, panel components,
positioning, groove/split cuts, shelf pattern, Ultrabox sub-assembly) directly
in a design, so no J1 base document is needed.

Reverse-engineered from the original hand-modeled J1 design:
- every panel is an origin-anchored rectangle sketch + extrude, with sketch
  dimensions and extrude distance driven by user-parameter expressions
- positioning uses a joint origin in the root component whose offsetX/Y/Z
  carry the position expressions, plus a rigid joint to the part; this is
  equivalent to J1's face-to-face joints (parts reposition natively when
  parameters change) but deterministic to create through the API
- component and feature names match what utils.set_component_visibility and
  ultrabox.py expect ("ukrute" wrapper with "ukruta otraga" children,
  "split police"/"split ukrute" combine features, "Ultrabox" component)

Root coordinate frame (same as J1): X = width (from inner face of "bok
desno" toward "bok lijevo"), Y = depth (0 at the front face of the back
panel, + toward the cabinet front), Z = height (0 at the bottom face of
"donja_ploca"; the plinth hangs below into negative Z).

All expressions use {p} as placeholder for the parameter prefix ("J1_").
"""

import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# User parameters, exactly as in the original J1 design (order preserved).
# (name, expression, unit) -- unit "" means a unitless flag/count.
# ---------------------------------------------------------------------------
USER_PARAMS = [
    ("{p}dubina", "46.0 cm", "mm"),
    ("{p}debljina_ploce", "18 mm", "mm"),
    ("{p}visina", "90.0 cm", "mm"),
    ("{p}fronta_debljina", "18.0 mm", "mm"),
    ("{p}fronta_ofset", "2.0 mm", "mm"),
    ("{p}ledja_debljina", "6.0 mm", "mm"),
    ("{p}gornja_debljina", "( if({p}gornja_ploca; {p}gornja_ploca_debljina; 0.1 mm) )", "mm"),
    ("{p}fronta_lijevo_sirina", "if({p}fronta_desna; {p}sirina / 2; {p}sirina) - if({p}fronta_unutarnje_pokrivanje; if({p}fronta_desna; 0 mm; {p}bok_desno_debljina) + {p}bok_lijevo_debljina; 0 mm) - {p}fronta_ofset * if({p}fronta_desna; 1.5; 2)", "mm"),
    ("{p}donja_ploca_debljina", "18.0 mm", "mm"),
    ("{p}fronta_visina", "{p}visina - 2 * {p}fronta_ofset - if({p}fronta_pokriva_gornju_plocu and not({p}fronta_unutarnje_pokrivanje); 0 mm; {p}gornja_debljina) - if({p}fronta_pokriva_donju_plocu and not({p}fronta_unutarnje_pokrivanje); 0 mm; {p}donja_ploca_debljina) - if({p}cokla; {p}cokla_visina; 0 mm)", "mm"),
    ("{p}donja_ploca_dubina", "{p}dubina - {p}ledja_debljina - if({p}fronta_pokriva_donju_plocu and not({p}fronta_unutarnje_pokrivanje); {p}fronta_debljina; 0 mm) - {p}ledja_upust", "mm"),
    ("{p}bok_visina", "{p}visina - if({p}bokovi_preko_donje_ploce; 0 mm; {p}donja_ploca_debljina) - if({p}bokovi_preko_gornje_ploce; 0 mm; {p}gornja_ploca_debljina)", "mm"),
    ("{p}bok_desno_dubina", "{p}dubina - {p}ledja_debljina - if({p}fronta_unutarnje_pokrivanje; 0 mm; {p}fronta_debljina)", "mm"),
    ("{p}sirina", "100.00 cm", "mm"),
    ("{p}bok_desno_debljina", "18.0 mm", "cm"),
    ("{p}bok_lijevo_dubina", "{p}dubina - {p}ledja_debljina - if({p}fronta_unutarnje_pokrivanje; 0 cm; {p}fronta_debljina)", "cm"),
    ("{p}bok_lijevo_debljina", "18.0 mm", "cm"),
    ("{p}pregrada_ofset", "( {p}sirina - {p}bok_desno_debljina - {p}bok_lijevo_debljina ) / 2 + {p}debljina_ploce / 2", "cm"),
    ("{p}polica_dubina", "{p}dubina - {p}fronta_debljina - {p}ledja_debljina - {p}polica_upust - {p}ledja_upust", "cm"),
    ("{p}polica_sirina", "{p}sirina - {p}bok_desno_debljina - {p}bok_lijevo_debljina - {p}polica_suzenje", "cm"),
    ("{p}polica_debljina", "1.8 cm", "cm"),
    ("{p}broj_polica", "2", ""),
    ("{p}polica_ofset_visina", "( {p}visina - {p}gornja_debljina - {p}donja_ploca_debljina - if({p}cokla; {p}cokla_visina; 0 mm) - ( {p}broj_polica * {p}polica_debljina ) ) / ( {p}broj_polica + 1 )", "cm"),
    ("{p}gornja_ploca", "1", ""),
    ("{p}gornja_ploca_debljina", "18.0 mm", "mm"),
    ("{p}ukrute", "1", ""),
    ("{p}ledja_visina", "if({p}ukrute; {p}visina - {p}gornja_ploca * {p}gornja_debljina; {p}visina) - 2 * {p}ledja_ofset - if({p}cokla; {p}cokla_visina; 0 mm)", "cm"),
    ("{p}ukruta_sirina", "80.0 mm", "cm"),
    ("{p}ukruta_duljina", "{p}sirina - {p}bok_desno_debljina - {p}bok_lijevo_debljina", "cm"),
    ("{p}gornja_ploca_dubina", "{p}dubina + {p}gornja_napust - if({p}ukrute; 0 mm; {p}ledja_debljina) - if({p}fronta_pokriva_gornju_plocu and not({p}fronta_unutarnje_pokrivanje); {p}fronta_debljina; 0 mm) - {p}ledja_upust", "cm"),
    ("{p}gornja_sirina", "{p}sirina - if({p}bokovi_preko_gornje_ploce; {p}bok_desno_debljina + {p}bok_lijevo_debljina; 0 cm)", "cm"),
    ("{p}donja_sirina", "{p}sirina - if({p}bokovi_preko_donje_ploce; {p}bok_desno_debljina + {p}bok_lijevo_debljina; 0 cm)", "cm"),
    ("{p}gornja_napust", "5.0 mm", "mm"),
    ("{p}fronta", "0", ""),
    ("{p}fronta_pokriva_donju_plocu", "1", ""),
    ("{p}fronta_unutarnje_pokrivanje", "0", ""),
    ("{p}polica_upust", "20.0 mm", "cm"),
    ("{p}fronta_pokriva_gornju_plocu", "0", ""),
    ("{p}ledja_ofset", "1.0 mm", "mm"),
    ("{p}ledja_upust", "6 mm", "mm"),
    ("{p}ledja_sirina", "{p}sirina - 2 * {p}ledja_ofset - ( if({p}ledja_dubina_slota_u_bokovima > 0 mm; ( {p}bok_desno_debljina + {p}bok_lijevo_debljina - 2 * {p}ledja_dubina_slota_u_bokovima ); 0 mm) )", "mm"),
    ("{p}bokovi_preko_donje_ploce", "1", ""),
    ("{p}bokovi_preko_gornje_ploce", "0", ""),
    ("{p}ledja_dubina_slota_u_bokovima", "10 mm", "mm"),
    ("{p}polica_suzenje", "1.0 mm", "mm"),
    ("{p}fronta_lijeva", "0", ""),
    ("{p}fronta_desna", "0", ""),
    ("{p}fronta_desno_sirina", "if({p}fronta_lijeva; {p}sirina / 2; {p}sirina) - if({p}fronta_unutarnje_pokrivanje; if({p}fronta_lijeva; 0 mm; {p}bok_lijevo_debljina) + {p}bok_desno_debljina; 0 mm) - {p}fronta_ofset * if({p}fronta_lijeva; 1.5; 2)", "mm"),
    ("{p}cokla_visina", "50.0 mm", "mm"),
    ("{p}cokla", "1", ""),
    ("{p}pregrada_visina", "{p}bok_visina - if({p}cokla; {p}cokla_visina; 0 mm) - if({p}bokovi_preko_donje_ploce; {p}donja_ploca_debljina; 0 mm) - -if({p}bokovi_preko_gornje_ploce; {p}gornja_debljina; 0 mm)", "mm"),
    ("{p}pregrada", "0", ""),
    ("{p}police", "0", ""),
    ("{p}ultrabox_width", "{p}sirina - {p}bok_desno_debljina - {p}bok_lijevo_debljina - 31 mm", "mm"),
    ("{p}ultrabox_duljina", "400 mm", "mm"),
    ("{p}ultrabox_visina", "150 mm", "mm"),
    ("{p}ultrabox_podnica_debljina", "6 mm", "mm"),
    ("{p}ultrabox_fronta_visina", "160 mm", "mm"),
    ("{p}ultrabox_fronta_ofset_od_dna", "15 mm", "mm"),
]


# ---------------------------------------------------------------------------
# Shared expression fragments.
# ---------------------------------------------------------------------------
# height of the plinth, 0 when disabled
_CK = "if({p}cokla; {p}cokla_visina; 0 mm)"
# X of the inner face of "bok desno" (0 when the sides run past the bottom
# panel, otherwise the sides stand on top of it and shift right)
_XI = "if({p}bokovi_preko_donje_ploce; 0 mm; {p}bok_desno_debljina)"
# inner width between the side panels
_WIN = "({p}sirina - {p}bok_desno_debljina - {p}bok_lijevo_debljina)"
# Y of the cabinet front face (front edge of the side panels)
_FRONT = "({p}bok_desno_dubina - {p}ledja_debljina)"
# Z of the bottom edge of the side panels
_BOK_Z = "{p}donja_ploca_debljina - if({p}bokovi_preko_donje_ploce; {p}donja_ploca_debljina; 0 mm) - " + _CK
# Z of the bottom edge of a (closed) door
_DOOR_Z = "{p}fronta_ofset + if({p}fronta_pokriva_donju_plocu and not({p}fronta_unutarnje_pokrivanje); 0 mm; {p}donja_ploca_debljina)"

# Each panel: component name, sketch plane, box size along root X/Y/Z, and the
# position of the box's min corner in the parent frame.  plane "XY" extrudes
# +Z (size_z), "XZ" extrudes +Y (size_y), "YZ" extrudes +X (size_x).
PANELS = [
    {
        "name": "donja_ploca",
        "plane": "XY",
        "size": ("{p}donja_sirina", "{p}donja_ploca_dubina", "{p}donja_ploca_debljina"),
        # grounded reference part: stays at the parent origin
        "pos": None,
    },
    {
        "name": "bok desno",
        "plane": "YZ",
        "size": ("{p}bok_desno_debljina", "{p}bok_desno_dubina", "{p}bok_visina"),
        "pos": (_XI + " - {p}bok_desno_debljina", "-{p}ledja_debljina", _BOK_Z),
    },
    {
        "name": "bok_lijevo",
        "plane": "YZ",
        "size": ("{p}bok_lijevo_debljina", "{p}bok_lijevo_dubina", "{p}bok_visina"),
        "pos": (_XI + " + " + _WIN, "-{p}ledja_debljina", _BOK_Z),
    },
    {
        "name": "ledja",
        "plane": "XZ",
        "size": ("{p}ledja_sirina", "{p}ledja_debljina", "{p}ledja_visina"),
        "pos": (
            _XI + " + {p}ledja_ofset - if({p}ledja_dubina_slota_u_bokovima > 0 mm; {p}ledja_dubina_slota_u_bokovima; {p}bok_desno_debljina)",
            "-{p}ledja_debljina",
            "{p}ledja_ofset",
        ),
    },
    {
        "name": "gornja_ploca",
        "plane": "XY",
        "size": ("{p}gornja_sirina", "{p}gornja_ploca_dubina", "{p}gornja_debljina"),
        "pos": (
            _XI + " - if({p}bokovi_preko_gornje_ploce; 0 mm; {p}bok_desno_debljina)",
            "-if({p}ukrute; {p}ledja_debljina; 0 mm)",
            "{p}visina - " + _CK + " - {p}gornja_debljina",
        ),
    },
    {
        "name": "pregrada",
        "plane": "YZ",
        "size": (
            "{p}debljina_ploce",
            "{p}bok_desno_dubina - if({p}fronta_unutarnje_pokrivanje; {p}fronta_debljina; 0 mm) - {p}ledja_upust",
            "{p}pregrada_visina",
        ),
        "pos": (_XI + " + {p}pregrada_ofset - {p}debljina_ploce", "0 mm", "{p}donja_ploca_debljina"),
        "light_bulb": False,
    },
    {
        "name": "polica",
        "plane": "XY",
        "size": ("{p}polica_sirina", "{p}polica_dubina", "{p}polica_debljina"),
        "pos": (
            _XI + " + {p}polica_suzenje / 2",
            "0 mm",
            "{p}polica_ofset_visina + {p}donja_ploca_debljina - if({p}bokovi_preko_donje_ploce; {p}donja_ploca_debljina; 0 mm)",
        ),
        "light_bulb": False,
    },
    {
        "name": "cokla",
        "plane": "XZ",
        "size": (_WIN, "{p}debljina_ploce", "{p}cokla_visina"),
        "pos": (_XI, _FRONT + " - {p}debljina_ploce", _BOK_Z),
    },
    {
        "name": "fronta desno",
        "plane": "XZ",
        "size": ("{p}fronta_desno_sirina", "{p}fronta_debljina", "{p}fronta_visina"),
        "pos": (
            _XI + " - {p}bok_desno_debljina + {p}fronta_ofset + if({p}fronta_unutarnje_pokrivanje; {p}bok_desno_debljina; 0 mm)",
            _FRONT + " - if({p}fronta_unutarnje_pokrivanje; {p}fronta_debljina; 0 mm)",
            _DOOR_Z,
        ),
        "light_bulb": False,
    },
    {
        "name": "fronta lijevo",
        "plane": "XZ",
        "size": ("{p}fronta_lijevo_sirina", "{p}fronta_debljina", "{p}fronta_visina"),
        "pos": (
            _XI + " + " + _WIN + " + {p}bok_lijevo_debljina - {p}fronta_ofset - if({p}fronta_unutarnje_pokrivanje; {p}bok_lijevo_debljina; 0 mm) - {p}fronta_lijevo_sirina",
            _FRONT + " - if({p}fronta_unutarnje_pokrivanje; {p}fronta_debljina; 0 mm)",
            _DOOR_Z,
        ),
        "light_bulb": False,
    },
]

# the horizontal stiffener panel, occurring twice inside the "ukrute" wrapper
UKRUTA = {
    "name": "ukruta otraga",
    "plane": "XY",
    "size": ("{p}ukruta_duljina", "{p}ukruta_sirina", "if({p}ukrute; {p}debljina_ploce; 0.1 mm)"),
}
_UKRUTA_Z = "{p}visina - " + _CK + " - {p}gornja_debljina - if({p}ukrute; {p}debljina_ploce; 0.1 mm)"
UKRUTA_POSITIONS = [
    # back stiffener, against the back panel
    (_XI, "0 mm", _UKRUTA_Z),
    # front stiffener, behind the fronts
    (_XI, _FRONT + " - {p}ukruta_sirina - if({p}fronta_unutarnje_pokrivanje; {p}fronta_debljina; 0 mm)", _UKRUTA_Z),
]

# Ultrabox drawer sub-assembly: children positioned relative to the wrapper
# origin (= bottom-back-left corner of the drawer bottom panel).
ULTRABOX_PANELS = [
    {
        "name": "podnica",
        "plane": "XY",
        "size": ("{p}ultrabox_width", "{p}ultrabox_duljina", "{p}ultrabox_podnica_debljina"),
        "pos": None,  # grounded at the wrapper origin
    },
    {
        "name": "zadnja",
        "plane": "XZ",
        "size": ("{p}ultrabox_width", "{p}debljina_ploce", "{p}ultrabox_visina - {p}ultrabox_podnica_debljina"),
        "pos": ("0 mm", "0 mm", "{p}ultrabox_podnica_debljina"),
    },
    {
        "name": "fronta",
        "plane": "XZ",
        "size": ("{p}fronta_desno_sirina", "{p}fronta_debljina", "{p}ultrabox_fronta_visina"),
        "pos": (
            "-( (" + _WIN + " - {p}ultrabox_width) / 2 + {p}bok_desno_debljina - {p}fronta_ofset )",
            "{p}ultrabox_duljina",
            "-{p}ultrabox_fronta_ofset_od_dna",
        ),
    },
]
# wrapper position in the root frame (top drawer slot, same as original J1)
ULTRABOX_POS = (
    _XI + " + (" + _WIN + " - {p}ultrabox_width) / 2",
    _FRONT + " - {p}ultrabox_duljina",
    _DOOR_Z + " + {p}fronta_visina - {p}ultrabox_fronta_visina + {p}ultrabox_fronta_ofset_od_dna",
)


def _fmt(expr: str, prefix: str) -> str:
    return expr.replace("{p}", prefix)


def create_user_parameters(design: adsk.fusion.Design, prefix: str):
    """Create all user parameters. Two passes so that expressions may
    reference parameters that appear later in the list."""
    params = design.userParameters
    for name, _expr, unit in USER_PARAMS:
        name = _fmt(name, prefix)
        if not params.itemByName(name):
            initial = adsk.core.ValueInput.createByString("1" if unit == "" else "1 mm")
            params.add(name, initial, unit, "")
    for name, expr, _unit in USER_PARAMS:
        params.itemByName(_fmt(name, prefix)).expression = _fmt(expr, prefix)


def _build_panel(parent_comp: adsk.fusion.Component, spec: dict, prefix: str,
                 units) -> adsk.fusion.Occurrence:
    """Create a component with an origin-anchored box (sketch + extrude),
    all driven by parameter expressions."""
    occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = spec["name"]

    sx, sy, sz = (_fmt(e, prefix) for e in spec["size"])
    ev = lambda e: units.evaluateExpression(e, "cm")
    plane = spec["plane"]
    if plane == "XY":
        sketch_plane = comp.xYConstructionPlane
        u_expr, v_expr, ext_expr = sx, sy, sz
        u0, v0 = ev(sx), ev(sy)
    elif plane == "XZ":
        # sketch v axis maps to -Z, extrude goes +Y
        sketch_plane = comp.xZConstructionPlane
        u_expr, v_expr, ext_expr = sx, sz, sy
        u0, v0 = ev(sx), -ev(sz)
    else:  # YZ: sketch u axis maps to -Z, v to +Y, extrude goes +X
        sketch_plane = comp.yZConstructionPlane
        u_expr, v_expr, ext_expr = sz, sy, sx
        u0, v0 = -ev(sz), ev(sy)

    sketch = comp.sketches.add(sketch_plane)
    lines = sketch.sketchCurves.sketchLines
    rect = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(u0, v0, 0)
    )
    corner = rect.item(0).startSketchPoint
    sketch.geometricConstraints.addCoincident(corner, sketch.originPoint)
    dims = sketch.sketchDimensions
    d_u = dims.addDistanceDimension(
        rect.item(0).startSketchPoint, rect.item(0).endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(u0 / 2, v0 / 2, 0),
    )
    d_v = dims.addDistanceDimension(
        rect.item(1).startSketchPoint, rect.item(1).endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(u0 / 2, v0 / 2, 0),
    )
    d_u.parameter.expression = u_expr
    d_v.parameter.expression = v_expr

    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByString(ext_expr))
    extrudes.add(ext_input)
    return occ


def _position_occurrence(parent_comp: adsk.fusion.Component,
                         occ: adsk.fusion.Occurrence,
                         pos, prefix: str, name: str):
    """Pin an occurrence to an expression-driven point of the parent frame
    via a joint origin + rigid joint."""
    if pos is None:
        return  # grounded part, stays at the parent origin
    px, py, pz = (_fmt(e, prefix) for e in pos)
    V = adsk.core.ValueInput

    geo_parent = adsk.fusion.JointGeometry.createByPoint(parent_comp.originConstructionPoint)
    jo_input = parent_comp.jointOrigins.createInput(geo_parent)
    jo_input.offsetX = V.createByString(px)
    jo_input.offsetY = V.createByString(py)
    jo_input.offsetZ = V.createByString(pz)
    jo_parent = parent_comp.jointOrigins.add(jo_input)
    jo_parent.name = "pos " + name
    jo_parent.isLightBulbOn = False

    comp = occ.component
    geo_child = adsk.fusion.JointGeometry.createByPoint(
        comp.originConstructionPoint.createForAssemblyContext(occ)
    )
    jo_child = comp.jointOrigins.add(comp.jointOrigins.createInput(geo_child))
    jo_child.isLightBulbOn = False
    occ.isGroundToParent = False
    joint_input = parent_comp.joints.createInput(
        jo_child.createForAssemblyContext(occ), jo_parent
    )
    joint_input.setAsRigidJointMotion()
    joint = parent_comp.joints.add(joint_input)
    joint.name = name
    joint.isLightBulbOn = False


def create_cabinet(design: adsk.fusion.Design, prefix: str = "J1_",
                   parent_occurrence: adsk.fusion.Occurrence = None):
    """Build the complete cabinet into the component of `parent_occurrence`
    (or the design's root component when omitted).

    `prefix` must include the trailing underscore (e.g. "J1_"), matching how
    the rest of the add-in threads prefixes around.
    """
    root = parent_occurrence.component if parent_occurrence else design.rootComponent
    units = design.fusionUnitsManager
    create_user_parameters(design, prefix)

    occurrences = {}
    for spec in PANELS:
        occ = _build_panel(root, spec, prefix, units)
        _position_occurrence(root, occ, spec["pos"], prefix, spec["name"])
        occurrences[spec["name"]] = occ

    # --- stiffeners: "ukrute" wrapper with two "ukruta otraga" children ----
    ukrute_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    ukrute_comp = ukrute_occ.component
    ukrute_comp.name = "ukrute"
    first_child = _build_panel(ukrute_comp, UKRUTA, prefix, units)
    _position_occurrence(ukrute_comp, first_child, UKRUTA_POSITIONS[0], prefix, "ukruta")
    second_child = ukrute_comp.occurrences.addExistingComponent(
        first_child.component, adsk.core.Matrix3D.create()
    )
    _position_occurrence(ukrute_comp, second_child, UKRUTA_POSITIONS[1], prefix, "ukruta naprijed")
    occurrences["ukrute"] = ukrute_occ

    # --- cross-component cuts ---------------------------------------------
    # Like the shelf pattern below, these must be created in root context
    # with root-context body proxies: features built inside a nested
    # component fail to resolve the other occurrence's transform
    # ("Reference Failures" warnings, cut silently missing).
    def _root_occ(occ):
        return occ.createForAssemblyContext(parent_occurrence) if parent_occurrence else occ

    combines = design.rootComponent.features.combineFeatures

    # back-panel groove cut into both side panels
    ledja_body = _root_occ(occurrences["ledja"]).bRepBodies.item(0)
    for bok in ("bok desno", "bok_lijevo"):
        tools = adsk.core.ObjectCollection.create()
        tools.add(ledja_body)
        cut = combines.createInput(_root_occ(occurrences[bok]).bRepBodies.item(0), tools)
        cut.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        cut.isKeepToolBodies = True
        combines.add(cut)

    # divider splits (suppressed until `pregrada` is enabled)
    pregrada_body = _root_occ(occurrences["pregrada"]).bRepBodies.item(0)
    first_child_root = first_child.createForAssemblyContext(_root_occ(ukrute_occ))
    for target_occ, feature_name in (
        (_root_occ(occurrences["polica"]), "split police"),
        (first_child_root, "split ukrute"),
    ):
        tools = adsk.core.ObjectCollection.create()
        tools.add(pregrada_body)
        cut = combines.createInput(target_occ.bRepBodies.item(0), tools)
        cut.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        cut.isKeepToolBodies = True
        split = combines.add(cut)
        split.name = feature_name
        split.timelineObject.isSuppressed = True

    # --- shelf pattern driven by broj_polica ------------------------------
    # The pattern must be created in root context with the seed occurrence's
    # root-context proxy: a pattern created inside a nested component ignores
    # the seed's joint-driven position and copies from the component origin.
    real_root = design.rootComponent
    seed = occurrences["polica"]
    if parent_occurrence:
        seed = seed.createForAssemblyContext(parent_occurrence)
    pattern_input_entities = adsk.core.ObjectCollection.create()
    pattern_input_entities.add(seed)
    patterns = real_root.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(
        pattern_input_entities,
        real_root.zConstructionAxis,
        adsk.core.ValueInput.createByString(_fmt("{p}broj_polica", prefix)),
        adsk.core.ValueInput.createByString(
            _fmt("{p}polica_ofset_visina + {p}polica_debljina", prefix)
        ),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    pattern_input.quantityTwo = adsk.core.ValueInput.createByString("1")
    patterns.add(pattern_input)

    # --- Ultrabox drawer sub-assembly (hidden template) -------------------
    ultrabox_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    ultrabox_comp = ultrabox_occ.component
    ultrabox_comp.name = "Ultrabox"
    for spec in ULTRABOX_PANELS:
        child = _build_panel(ultrabox_comp, spec, prefix, units)
        _position_occurrence(ultrabox_comp, child, spec["pos"], prefix, spec["name"])
    _position_occurrence(root, ultrabox_occ, ULTRABOX_POS, prefix, "Ultrabox")
    ultrabox_occ.isLightBulbOn = False

    # --- initial visibility, matching the flag parameters -----------------
    for spec in PANELS:
        if not spec.get("light_bulb", True):
            occurrences[spec["name"]].isLightBulbOn = False
    # hide the shelf pattern copies as well
    for occ in root.occurrences:
        if occ.component.name.startswith("polica"):
            occ.isLightBulbOn = False

    return occurrences


def add_cabinet(design: adsk.fusion.Design, name: str) -> adsk.fusion.Occurrence:
    """Add a new cabinet named `name` (e.g. "O1") to the design's root: a
    wrapper component holding the full generated cabinet, with all its user
    parameters prefixed `<name>_`.  This replaces copying from the J1 base
    document.  Raises ValueError if the prefix is already taken."""
    if design.userParameters.itemByName(f"{name}_sirina"):
        raise ValueError(f"Parameters with prefix '{name}_' already exist in this design")
    wrapper_occ = design.rootComponent.occurrences.addNewComponent(
        adsk.core.Matrix3D.create()
    )
    wrapper_occ.component.name = name
    create_cabinet(design, prefix=name + "_", parent_occurrence=wrapper_occ)
    return wrapper_occ
