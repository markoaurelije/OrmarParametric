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

Edge banding (kantiranje)
-------------------------
Every panel carries a ``banding`` dict describing which of its narrow (thickness)
edges must be edge-banded so the finished cabinet looks clean -- only edges that
stay *visible* are banded; edges hidden against the wall, floor, another board,
a door or the plinth are left raw.  Keys are the world-frame orientation of the
edge's outward normal (see the coordinate frame above):

    "front" (+Y)   "back" (-Y)
    "left"  (+X)   "right" (-X)     # +X points from "bok desno" toward "bok lijevo"
    "top"   (+Z)   "bottom" (-Z)

A value of ``True`` means always banded; a string is a Python condition on the
cabinet's flag parameters (referenced by their base name, e.g.
``"bokovi_preko_donje_ploce == 0"``) evaluated live each preview so banding
follows the construction.  Absent orientations are never banded.  These rules
now live in board_rules.json (loaded below) with the tables here as fallback
defaults; ``utils.apply_finish`` colours faces + edges from them, and
``board_banding_counts`` reduces banding to the (long, short) counts the cut
list needs.
"""

import math
import re

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
    ("{p}fronta_visina", "{p}visina - 2 * {p}fronta_ofset - if({p}fronta_pokriva_gornju_plocu and not({p}fronta_unutarnje_pokrivanje); 0 mm; {p}gornja_debljina) - if({p}fronta_pokriva_donju_plocu and not({p}fronta_unutarnje_pokrivanje); 0 mm; {p}donja_ploca_debljina) - ( if({p}cokla; {p}cokla_visina; 0 mm) + if({p}nogice; {p}nogice_visina; 0 mm) )", "mm"),
    ("{p}donja_ploca_dubina", "{p}dubina - {p}ledja_debljina - if({p}fronta_pokriva_donju_plocu and not({p}fronta_unutarnje_pokrivanje); {p}fronta_debljina; 0 mm) - {p}ledja_upust", "mm"),
    ("{p}bok_visina", "{p}visina - if({p}bokovi_preko_donje_ploce; 0 mm; {p}donja_ploca_debljina) - if({p}bokovi_preko_gornje_ploce; 0 mm; {p}gornja_ploca_debljina) - if({p}nogice; {p}nogice_visina; 0 mm)", "mm"),
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
    ("{p}polica_ofset_visina", "( {p}visina - {p}gornja_debljina - {p}donja_ploca_debljina - ( if({p}cokla; {p}cokla_visina; 0 mm) + if({p}nogice; {p}nogice_visina; 0 mm) ) - ( {p}broj_polica * {p}polica_debljina ) ) / ( {p}broj_polica + 1 )", "cm"),
    ("{p}gornja_ploca", "1", ""),
    ("{p}gornja_ploca_debljina", "18.0 mm", "mm"),
    ("{p}ukrute", "1", ""),
    ("{p}ledja_visina", "if({p}ukrute; {p}visina - {p}gornja_ploca * {p}gornja_debljina; {p}visina) - 2 * {p}ledja_ofset - ( if({p}cokla; {p}cokla_visina; 0 mm) + if({p}nogice; {p}nogice_visina; 0 mm) )", "cm"),
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
    # cabinet legs (nogice): mutually exclusive with the plinth (cokla).  Four
    # cylindrical feet lift the carcass off the floor by nogice_visina, filling
    # the same vertical zone the plinth would; default off (cokla is on).
    ("{p}nogice", "0", ""),
    ("{p}nogice_visina", "100.0 mm", "mm"),
    ("{p}nogice_promjer", "40.0 mm", "mm"),
    ("{p}nogice_odmak", "35.0 mm", "mm"),
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
# height of the plinth, 0 when disabled.  This is the *side-skirt* height: only
# a plinth extends the side panels down to the floor, so _BOK_Z uses this alone.
_CK = "if({p}cokla; {p}cokla_visina; 0 mm)"
# overall height the carcass is lifted off the floor: the plinth OR the legs
# (mutually exclusive), whichever is enabled.  The legs occupy the same vertical
# zone the plinth would, so the top of the cabinet rises by this either way;
# unlike a plinth, legs do NOT extend the sides down (see _CK / bok_visina).
_LIFT = "( if({p}cokla; {p}cokla_visina; 0 mm) + if({p}nogice; {p}nogice_visina; 0 mm) )"
# X of the inner face of "bok desno" (0 when the sides run past the bottom
# panel, otherwise the sides stand on top of it and shift right)
_XI = "if({p}bokovi_preko_donje_ploce; 0 mm; {p}bok_desno_debljina)"
# inner width between the side panels
_WIN = "({p}sirina - {p}bok_desno_debljina - {p}bok_lijevo_debljina)"
# Y of the cabinet front face (front edge of the side panels).  Uses
# ledja_upust, not ledja_debljina: the side panels' back edge sits at
# -ledja_upust (see "bok desno"/"bok lijevo" below), so their front edge --
# and everything referencing _FRONT (cokla, the doors) -- must track upust
# too, or it drifts out of flush with donja_ploca/gornja_ploca (whose own
# depth already shrinks by upust) whenever upust != ledja_debljina.
_FRONT = "({p}bok_desno_dubina - {p}ledja_upust)"
# Z of the bottom edge of the side panels
_BOK_Z = "{p}donja_ploca_debljina - if({p}bokovi_preko_donje_ploce; {p}donja_ploca_debljina; 0 mm) - " + _CK
# Z of the bottom edge of a (closed) door
_DOOR_Z = "{p}fronta_ofset + if({p}fronta_pokriva_donju_plocu and not({p}fronta_unutarnje_pokrivanje); 0 mm; {p}donja_ploca_debljina)"

# How far a door may swing on its revolute joint (0 deg = closed).  The door is
# limited to the outward direction only (0..MAX for a +open door, -MAX..0 for a
# -open one, given by the panel's "open_dir"), so it can't rotate into the box.
_DOOR_OPEN_MAX_DEG = 110.0

# Each panel: component name, sketch plane, box size along root X/Y/Z, and the
# position of the box's min corner in the parent frame.  plane "XY" extrudes
# +Z (size_z), "XZ" extrudes +Y (size_y), "YZ" extrudes +X (size_x).
PANELS = [
    {
        "name": "donja ploca",
        "plane": "XY",
        "size": ("{p}donja_sirina", "{p}donja_ploca_dubina", "{p}donja_ploca_debljina"),
        # grounded reference part: stays at the parent origin
        "pos": None,
        # front edge shows behind the door; side edges only when the bottom
        # runs full width (sides sit on top of it), otherwise the sides cover
        # them; back edge faces the wall.
        "banding": {
            "front": True,
            "left": "bokovi_preko_donje_ploce == 0",
            "right": "bokovi_preko_donje_ploce == 0",
        },
    },
    {
        "name": "bok desno",
        "plane": "YZ",
        "size": ("{p}bok_desno_debljina", "{p}bok_desno_dubina", "{p}bok_visina"),
        "pos": (_XI + " - {p}bok_desno_debljina", "-{p}ledja_upust", _BOK_Z),
        # front vertical edge always shows; top edge only when the side is the
        # topmost surface; bottom edge only on wall units (no plinth); back
        # edge faces the wall.
        "banding": {
            "front": True,
            "top": "bokovi_preko_gornje_ploce == 1",
            "bottom": "bokovi_preko_donje_ploce == 1 and cokla == 0",
        },
    },
    {
        "name": "bok lijevo",
        "plane": "YZ",
        "size": ("{p}bok_lijevo_debljina", "{p}bok_lijevo_dubina", "{p}bok_visina"),
        "pos": (_XI + " + " + _WIN, "-{p}ledja_upust", _BOK_Z),
        # same rule as "bok desno"
        "banding": {
            "front": True,
            "top": "bokovi_preko_gornje_ploce == 1",
            "bottom": "bokovi_preko_donje_ploce == 1 and cokla == 0",
        },
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
        # thin panel sunk in a groove, fully hidden
        "banding": {},
    },
    {
        "name": "gornja ploca",
        "plane": "XY",
        "size": ("{p}gornja_sirina", "{p}gornja_ploca_dubina", "{p}gornja_debljina"),
        "pos": (
            _XI + " - if({p}bokovi_preko_gornje_ploce; 0 mm; {p}bok_desno_debljina)",
            "-if({p}ukrute; {p}ledja_debljina; 0 mm)",
            "{p}visina - " + _LIFT + " - {p}gornja_debljina",
        ),
        # front edge always shows; side edges only when the top runs full
        # width (sides do not run past it); back edge faces the wall.  Front
        # overhang (napust) does not add banded edges (still one front edge).
        "banding": {
            "front": True,
            "left": "bokovi_preko_gornje_ploce == 0",
            "right": "bokovi_preko_gornje_ploce == 0",
        },
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
        # only the front vertical edge shows
        "banding": {"front": True},
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
        # only the front edge shows; sides butt the boks, back to the ledja
        "banding": {"front": True},
    },
    {
        "name": "cokla",
        "plane": "XZ",
        "size": (_WIN, "{p}debljina_ploce", "{p}cokla_visina"),
        "pos": (_XI, _FRONT + " - {p}debljina_ploce", _BOK_Z),
        # front face shows but no narrow edge is exposed (top under the
        # cabinet, bottom on the floor, sides recessed between the boks)
        "banding": {},
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
        # a door: exposed on all four sides.  The door lies in the XZ plane
        # (its big faces point +/-Y), so its four narrow edges are the
        # left/right verticals and the top/bottom horizontals.
        "banding": {"left": True, "right": True, "top": True, "bottom": True},
        # Swings on a revolute joint about the vertical (Z) axis at its outer
        # (cabinet-side) edge.  This panel sits on the cabinet's left half
        # (its origin corner is the outer edge), so the hinge is at offset 0.
        # It opens in the +angle direction, limited to 0..110 deg.
        "hinge_offset": "0 mm",
        "open_dir": +1,
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
        # a door: exposed on all four narrow edges (see "fronta desno")
        "banding": {"left": True, "right": True, "top": True, "bottom": True},
        # Swings on a revolute joint about the vertical (Z) axis at its outer
        # (cabinet-side) edge.  This panel sits on the cabinet's right half
        # (its outer edge is origin + width), so the hinge is at that offset.
        # It opens in the -angle direction, limited to -110..0 deg.
        "hinge_offset": "{p}fronta_lijevo_sirina",
        "open_dir": -1,
    },
]

# the horizontal stiffener panel, occurring twice inside the "ukrute" wrapper
UKRUTA = {
    "name": "ukruta otraga",
    "plane": "XY",
    "size": ("{p}ukruta_duljina", "{p}ukruta_sirina", "if({p}ukrute; {p}debljina_ploce; 0.1 mm)"),
    # hidden under the top/counter
    "banding": {},
}
_UKRUTA_Z = "{p}visina - " + _LIFT + " - {p}gornja_debljina - if({p}ukrute; {p}debljina_ploce; 0.1 mm)"
UKRUTA_POSITIONS = [
    # back stiffener, against the back panel
    (_XI, "0 mm", _UKRUTA_Z),
    # front stiffener, behind the fronts
    (_XI, _FRONT + " - {p}ukruta_sirina - if({p}fronta_unutarnje_pokrivanje; {p}fronta_debljina; 0 mm)", _UKRUTA_Z),
]

# Cabinet legs (nogice): four cylindrical feet, one under each corner of the
# bottom panel (donja_ploca spans X:[0, donja_sirina], Y:[0, donja_ploca_dubina]
# in the cabinet frame), inset from every edge by nogice_odmak.  Each leg's
# component origin is its axis centre at the top (Z = 0, the underside of the
# bottom board); the leg extrudes downward by nogice_visina into the base zone.
_LEG_X_RIGHT = "{p}nogice_odmak"
_LEG_X_LEFT = "{p}donja_sirina - {p}nogice_odmak"
_LEG_Y_BACK = "{p}nogice_odmak"
_LEG_Y_FRONT = "{p}donja_ploca_dubina - {p}nogice_odmak"
LEG_POSITIONS = [
    (_LEG_X_RIGHT, _LEG_Y_BACK, "0 mm"),
    (_LEG_X_RIGHT, _LEG_Y_FRONT, "0 mm"),
    (_LEG_X_LEFT, _LEG_Y_BACK, "0 mm"),
    (_LEG_X_LEFT, _LEG_Y_FRONT, "0 mm"),
]

# Ultrabox drawer sub-assembly: children positioned relative to the wrapper
# origin (= bottom-back-left corner of the drawer bottom panel).
ULTRABOX_PANELS = [
    {
        "name": "podnica",
        "plane": "XY",
        "size": ("{p}ultrabox_width", "{p}ultrabox_duljina", "{p}ultrabox_podnica_debljina"),
        "pos": None,  # grounded at the wrapper origin
        # internal drawer bottom, not visible
        "banding": {},
    },
    {
        "name": "zadnja",
        "plane": "XZ",
        "size": ("{p}ultrabox_width", "{p}debljina_ploce", "{p}ultrabox_visina - {p}ultrabox_podnica_debljina"),
        "pos": ("0 mm", "0 mm", "{p}ultrabox_podnica_debljina"),
        # internal drawer back, not visible
        "banding": {},
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
        # the drawer front is a visible door: banded on all four narrow edges
        # (XZ plane, so left/right verticals and top/bottom horizontals)
        "banding": {"left": True, "right": True, "top": True, "bottom": True},
    },
]
# wrapper position in the root frame (top drawer slot, same as original J1)
ULTRABOX_POS = (
    _XI + " + (" + _WIN + " - {p}ultrabox_width) / 2",
    _FRONT + " - {p}ultrabox_duljina",
    _DOOR_Z + " + {p}fronta_visina - {p}ultrabox_fronta_visina + {p}ultrabox_fronta_ofset_od_dna",
)


# ---------------------------------------------------------------------------
# Finish (colour) and edge-banding lookup and reduction, shared by
# utils.apply_finish (which colours faces + edges) and the future cut-list
# export (which needs per-board banded-edge counts).  Pure data logic -- no
# adsk calls -- so it stays unit-testable and reusable.
#
# These are the built-in *defaults*.  board_rules.json (loaded below) overrides
# them board-by-board and is the file a user is meant to edit; see
# board_rules.README.md.
# ---------------------------------------------------------------------------
_ALL_SPECS = PANELS + [UKRUTA] + ULTRABOX_PANELS
BANDING_BY_NAME = {s["name"]: s.get("banding", {}) for s in _ALL_SPECS}
PLANE_BY_NAME = {s["name"]: s["plane"] for s in _ALL_SPECS}

# Default face-finish per board: True = decorative colour, False = white
# (interior).  Only visible-outside boards are coloured by default -- the doors
# and the top panel; the user colours anything else per cabinet in the dialog.
COLORED_DEFAULTS = {name: False for name in BANDING_BY_NAME}
for _n in ("fronta desno", "fronta lijevo", "fronta", "gornja ploca"):
    COLORED_DEFAULTS[_n] = True
COLORED_BY_NAME = dict(COLORED_DEFAULTS)


def _load_board_rules_json():
    """Override BANDING_BY_NAME / COLORED_BY_NAME from board_rules.json if it is
    present and valid; otherwise keep the built-in defaults."""
    import os, json
    path = os.path.join(os.path.dirname(__file__), "board_rules.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return
    boards = data.get("boards", data)  # allow a flat map too
    if not isinstance(boards, dict):
        return
    for name, rules in boards.items():
        if name.startswith("_") or not isinstance(rules, dict):
            continue
        if "banding" in rules:
            BANDING_BY_NAME[name] = rules["banding"]
        if "colored" in rules:
            COLORED_BY_NAME[name] = rules["colored"]


_load_board_rules_json()

# For a board in a given sketch plane, the dim index (0=X, 1=Y, 2=Z) that gives
# the *length* of the edge whose outward face normal has each orientation.  The
# board's thickness axis is excluded (those are the two big faces, never banded).
_EDGE_DIM = {
    "XY": {"front": 0, "back": 0, "left": 1, "right": 1},
    "XZ": {"left": 2, "right": 2, "top": 0, "bottom": 0},
    "YZ": {"front": 2, "back": 2, "top": 1, "bottom": 1},
}
# the two in-plane dim indices (the non-thickness axes) per sketch plane
_INPLANE = {"XY": (0, 1), "XZ": (0, 2), "YZ": (1, 2)}


def _eval_banding_condition(cond, flags: dict) -> bool:
    """A banding value is either True (always) or a Python expression string on
    the cabinet's flag parameters (base names -> numeric values)."""
    if cond is True:
        return True
    if isinstance(cond, str):
        try:
            return bool(eval(cond, {"__builtins__": {}}, flags))
        except Exception:
            return False
    return bool(cond)


def resolved_banding(banding: dict, flags: dict) -> set:
    """The set of edge orientations actually banded for the given flag values."""
    return {o for o, cond in (banding or {}).items()
            if _eval_banding_condition(cond, flags)}


def resolved_colored(name: str, flags: dict, override=None) -> bool:
    """Whether a board's faces get the finish colour.  A per-cabinet `override`
    (True/False from a user click, or None for 'use the default') wins; else the
    board_rules.json / built-in default is evaluated against the flags."""
    if override is not None:
        return bool(override)
    return _eval_banding_condition(COLORED_BY_NAME.get(name, False), flags)


_DEDUP_SUFFIX_RE = re.compile(r"\s*\(\d+\)$")


def scoped_name(prefix: str, base: str) -> str:
    """The cabinet-scoped, globally-unique component name for a part.

    Component names are unique per *design* in Fusion, so a second cabinet that
    reused the same base names ('polica', ...) used to collide and get an
    auto-appended ' (N)' suffix.  Prefixing every component with the cabinet's
    parameter prefix ('O2_polica') keeps them unique deterministically and
    mirrors the user-parameter naming.  `prefix` includes the trailing '_'."""
    return prefix + base


def base_component_name(comp_name: str, prefix: str = "") -> str:
    """Recover a component's base name from its Fusion component name: strip the
    cabinet `prefix` if the name carries it (new scoped naming) and Fusion's
    ' (N)' uniqueness suffix if present (legacy collided names).  Leaves
    rectangular-pattern trailing digits ('polica3') for callers that want them."""
    name = comp_name
    if prefix and name.startswith(prefix):
        name = name[len(prefix):]
    return _DEDUP_SUFFIX_RE.sub("", name)


# Board spec names use spaces ("bok lijevo", "gornja ploca").  Older designs
# were built with underscore variants ("bok_lijevo", "gornja_ploca"), so the
# resolver matches underscore/space-insensitively -- existing cabinets keep
# resolving to the current spec name without any migration.  Built from the
# canonical spec names only (not the board_rules.json overlay) so a stray JSON
# key can't shadow a real spec.
def _norm_name(name: str) -> str:
    return name.replace("_", " ")


_NORM_TO_SPEC = {_norm_name(s["name"]): s["name"] for s in _ALL_SPECS}


def spec_name_for_component(comp_name: str, prefix: str = ""):
    """Map a Fusion component name to its board spec name, or None if it is not a
    banded board.  `prefix` (the cabinet's, e.g. 'O2_') is stripped first so
    scoped names resolve; it is optional and the resolver stays backward
    compatible with legacy unprefixed / ' (N)'-suffixed and underscore-vs-space
    names either way.  Rectangular-pattern copies ('polica3') are also handled."""
    if comp_name in BANDING_BY_NAME:
        return comp_name
    name = base_component_name(comp_name, prefix)
    # try the name as-is and with pattern-copy trailing digits stripped; each
    # first exact, then underscore/space-insensitive.
    for cand in (name, name.rstrip("0123456789").rstrip()):
        if cand in BANDING_BY_NAME:
            return cand
        hit = _NORM_TO_SPEC.get(_norm_name(cand))
        if hit:
            return hit
    return None


def _reduce_banding_counts(plane: str, banded, dims):
    """Reduce a *set of banded orientations* to ``(long_count, short_count)``,
    each in {0, 1, 2}: how many of the board's two long edges and two short edges
    are banded.  ``dims`` is the board's (dx, dy, dz) size in any single
    consistent unit; long/short is decided from the actual geometry so it stays
    correct on deep or tall boards."""
    # A board has exactly two edge pairs; each banded edge belongs to the pair
    # running along one in-plane axis (its length = that axis's dim).  Count per
    # pair first, then label the longer-edge pair "long" -- so the count in each
    # pair can never exceed 2 even when the board is square.
    per_axis = {}  # in-plane dim index -> banded count in that pair
    for orientation in banded:
        idx = _EDGE_DIM[plane].get(orientation)
        if idx is None:
            continue
        per_axis[idx] = per_axis.get(idx, 0) + 1
    a, b = _INPLANE[plane]
    long_idx, short_idx = (a, b) if dims[a] >= dims[b] else (b, a)
    return (per_axis.get(long_idx, 0), per_axis.get(short_idx, 0))


def banding_counts_for_orientations(comp_name: str, orientations, dims):
    """Like ``board_banding_counts`` but from an explicit set of banded edge
    orientations (e.g. the live/overridden banding the model is painted with),
    rather than re-deriving it from the rule defaults.  This is what the cut list
    should use so its counts always match what ``utils.apply_finish`` paints."""
    name = spec_name_for_component(comp_name)
    if name is None:
        return (0, 0)
    return _reduce_banding_counts(PLANE_BY_NAME[name], set(orientations), dims)


def banding_decors_for_orientations(comp_name: str, banded: dict, dims):
    """Like ``banding_counts_for_orientations`` but keeps *which* decor bands
    each edge instead of collapsing to a count: returns
    ``(long_decors, short_decors)``, each a list of 0-2 decor names (one per
    banded edge in that pair) -- so a board banded in two different colours on
    its two long edges is represented, not just counted.  ``banded`` is an
    orientation -> decor name map (e.g. from ``utils.effective_banding``)."""
    name = spec_name_for_component(comp_name)
    if name is None:
        return ([], [])
    plane = PLANE_BY_NAME[name]
    per_axis = {}
    for orientation, decor in banded.items():
        idx = _EDGE_DIM[plane].get(orientation)
        if idx is None:
            continue
        per_axis.setdefault(idx, []).append(decor)
    a, b = _INPLANE[plane]
    long_idx, short_idx = (a, b) if dims[a] >= dims[b] else (b, a)
    return (per_axis.get(long_idx, []), per_axis.get(short_idx, []))


def board_banding_counts(comp_name: str, flags: dict, dims):
    """Reduce a board's rule-default banding to the ``(long_count, short_count)``
    the cut list needs.  ``dims`` is the board's evaluated (dx, dy, dz) size in
    any single consistent unit."""
    name = spec_name_for_component(comp_name)
    if name is None:
        return (0, 0)
    banded = resolved_banding(BANDING_BY_NAME[name], flags)
    return _reduce_banding_counts(PLANE_BY_NAME[name], banded, dims)


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
    comp.name = scoped_name(prefix, spec["name"])

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


def _build_leg(parent_comp: adsk.fusion.Component, prefix: str,
               units) -> adsk.fusion.Occurrence:
    """Create a 'noga' cylinder component: a leg of diameter nogice_promjer
    extruded downward (-Z) by nogice_visina from the component origin.  The
    origin sits at the top-face axis centre, so positioning the occurrence's
    origin drops the leg straight down from that point (see LEG_POSITIONS)."""
    occ = parent_comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = scoped_name(prefix, "noga")

    diam_expr = _fmt("{p}nogice_promjer", prefix)
    r0 = units.evaluateExpression(diam_expr, "cm") / 2

    sketch = comp.sketches.add(comp.xYConstructionPlane)
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), r0
    )
    sketch.geometricConstraints.addCoincident(
        circle.centerSketchPoint, sketch.originPoint
    )
    dim = sketch.sketchDimensions.addDiameterDimension(
        circle, adsk.core.Point3D.create(r0, 0, 0)
    )
    dim.parameter.expression = diam_expr

    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(
        False, adsk.core.ValueInput.createByString(_fmt("-{p}nogice_visina", prefix))
    )
    extrudes.add(ext_input)
    return occ


def _position_occurrence(parent_comp: adsk.fusion.Component,
                         occ: adsk.fusion.Occurrence,
                         pos, prefix: str, name: str,
                         hinge_offset: str = None, open_dir: int = None):
    """Pin an occurrence to an expression-driven point of the parent frame
    via a joint origin + joint.

    Normally a rigid joint (part follows the parent frame exactly).  When
    `hinge_offset` is given (an X-distance expression from the part's origin
    corner to its hinge edge), a **revolute** joint about the vertical (Z)
    axis is built instead so a door can swing -- matching the original J1
    design.  Both joint origins are shifted by the same hinge offset, so the
    door's closed position is unchanged but the pivot lands on the hinge edge.

    `open_dir` (+1 / -1) is the outward-opening sign of a hinged door; when
    given, the revolute joint is limited to 0..110 deg in that direction so
    the door swings open but never rotates into the cabinet.
    """
    if pos is None:
        return  # grounded part, stays at the parent origin
    px, py, pz = (_fmt(e, prefix) for e in pos)
    V = adsk.core.ValueInput

    hinge = _fmt(hinge_offset, prefix) if hinge_offset is not None else None
    parent_x = px if hinge is None else "(" + px + ") + (" + hinge + ")"

    geo_parent = adsk.fusion.JointGeometry.createByPoint(parent_comp.originConstructionPoint)
    jo_input = parent_comp.jointOrigins.createInput(geo_parent)
    jo_input.offsetX = V.createByString(parent_x)
    jo_input.offsetY = V.createByString(py)
    jo_input.offsetZ = V.createByString(pz)
    jo_parent = parent_comp.jointOrigins.add(jo_input)
    jo_parent.name = "pos " + name
    jo_parent.isLightBulbOn = False

    comp = occ.component
    geo_child = adsk.fusion.JointGeometry.createByPoint(
        comp.originConstructionPoint.createForAssemblyContext(occ)
    )
    child_input = comp.jointOrigins.createInput(geo_child)
    if hinge is not None:
        child_input.offsetX = V.createByString(hinge)
    jo_child = comp.jointOrigins.add(child_input)
    jo_child.isLightBulbOn = False
    occ.isGroundToParent = False
    joint_input = parent_comp.joints.createInput(
        jo_child.createForAssemblyContext(occ), jo_parent
    )
    if hinge is None:
        joint_input.setAsRigidJointMotion()
    else:
        joint_input.setAsRevoluteJointMotion(
            adsk.fusion.JointDirections.ZAxisJointDirection
        )
    joint = parent_comp.joints.add(joint_input)
    joint.name = name
    joint.isLightBulbOn = False

    if hinge is not None and open_dir:
        max_rad = math.radians(_DOOR_OPEN_MAX_DEG)
        limits = joint.jointMotion.rotationLimits
        limits.isMinimumValueEnabled = True
        limits.isMaximumValueEnabled = True
        limits.minimumValue = 0.0 if open_dir > 0 else -max_rad
        limits.maximumValue = max_rad if open_dir > 0 else 0.0


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
        _position_occurrence(root, occ, spec["pos"], prefix, spec["name"],
                             spec.get("hinge_offset"), spec.get("open_dir"))
        occurrences[spec["name"]] = occ

    # --- stiffeners: "ukrute" wrapper with two "ukruta otraga" children ----
    ukrute_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    # The wrapper has no joint of its own, so it must be grounded to the
    # parent: a free occurrence does not follow the jointed cluster when the
    # cabinet is moved or its joints recompute, leaving the stiffeners
    # stranded at the cabinet's old position.
    ukrute_occ.isGroundToParent = True
    ukrute_comp = ukrute_occ.component
    ukrute_comp.name = scoped_name(prefix, "ukrute")
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
    for bok in ("bok desno", "bok lijevo"):
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

    # Pattern copies get no joint of their own (only the seed shelf does), so
    # without grounding they'd be free rigid bodies the user could drag
    # anywhere in the viewport. utils.reseat_free_wrappers re-grounds any new
    # copy every preview/execute cycle as broj_polica changes, but ground the
    # one(s) created here too so a freshly built cabinet is clean immediately.
    polica_comp_name = occurrences["polica"].component.name
    for occ_candidate in root.occurrences:
        if (occ_candidate.component.name == polica_comp_name
                and occ_candidate.name != occurrences["polica"].name):
            occ_candidate.isGroundToParent = True

    # --- Ultrabox drawer sub-assembly (hidden template) -------------------
    ultrabox_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    ultrabox_comp = ultrabox_occ.component
    ultrabox_comp.name = scoped_name(prefix, "Ultrabox")
    for spec in ULTRABOX_PANELS:
        child = _build_panel(ultrabox_comp, spec, prefix, units)
        _position_occurrence(ultrabox_comp, child, spec["pos"], prefix, spec["name"])
    _position_occurrence(root, ultrabox_occ, ULTRABOX_POS, prefix, "Ultrabox")
    ultrabox_occ.isLightBulbOn = False

    # --- legs (nogice): "nogice" wrapper with four "noga" corner cylinders --
    # Each leg is its OWN component (not one component instanced four times):
    # a shared component's joint origins appear as a separate proxy in every
    # instance, and the native isLightBulbOn=False set in _position_occurrence
    # only hides the native copy -- the other instances' proxies stay visible.
    # Giving each leg its own component keeps every joint origin native (hidden),
    # just like the panels.  Off by default (the plinth is on).
    nogice_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    # ground the joint-less wrapper, same reason as the ukrute wrapper above
    nogice_occ.isGroundToParent = True
    nogice_comp = nogice_occ.component
    nogice_comp.name = scoped_name(prefix, "nogice")
    for i, pos in enumerate(LEG_POSITIONS):
        leg_occ = _build_leg(nogice_comp, prefix, units)
        _position_occurrence(nogice_comp, leg_occ, pos, prefix, f"noga {i + 1}")
    occurrences["nogice"] = nogice_occ
    nogice_occ.isLightBulbOn = False

    # --- initial visibility, matching the flag parameters -----------------
    for spec in PANELS:
        if not spec.get("light_bulb", True):
            occurrences[spec["name"]].isLightBulbOn = False
    # hide the shelf pattern copies as well
    for occ in root.occurrences:
        if base_component_name(occ.component.name, prefix).startswith("polica"):
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
