"""Cabinet templates ("predlošci").

A template is a named, complete set of parameter values applied to a cabinet
either at creation time (the "Predložak" dropdown next to "Dodaj ormar") or
afterwards via the per-cabinet-tab "Predložak" dropdown.

Templates live in presets.json next to this module (hand-editable, same
pattern as decors.json / board_rules.json).  The built-in lists below are only
the fallback used when that file is missing or unreadable.  "Spremi kao
predložak" in the dialog writes a cabinet's current parameters back into
presets.json under a chosen name — an existing name overwrites (edits) that
template, a new name adds one.

Inside an expression the source cabinet's prefix is stored as the literal
placeholder "{prefix}" so cross-parameter references stay portable; utils
replaces it with the target cabinet's prefix when the template is applied.
"""

import json
import os

_PRESETS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "presets.json"
)

kuhinja_viseci_element = [
    {
        "paramName": "sirina",
        "expression": "60.00 cm",
    },
    {
        "paramName": "dubina",
        "expression": "30.0 cm",
    },
    {
        "paramName": "visina",
        "expression": "50.0 cm",
    },
    {
        "paramName": "donja_ploca_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "bokovi_preko_donje_ploce",
        "expression": "1",
    },
    {
        "paramName": "bokovi_preko_gornje_ploce",
        "expression": "1",
    },
    {
        "paramName": "bok_lijevo_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "bok_desno_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "gornja_ploca",
        "expression": "1",
    },
    {
        "paramName": "gornja_ploca_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "gornja_napust",
        "expression": "0.0 mm",
    },
    {
        "paramName": "ukrute",
        "expression": "0",
    },
    {
        "paramName": "ukruta_sirina",
        "expression": "80.0 mm",
    },
    {
        "paramName": "ledja_debljina",
        "expression": "3.0 mm",
    },
    {
        "paramName": "ledja_ofset",
        "expression": "1.0 mm",
    },
    {"paramName": "ledja_upust", "expression": "18 mm"},
    {
        "paramName": "ledja_dubina_slota_u_bokovima",
        "expression": "10.0 mm",
    },
    {
        "paramName": "fronta",
        "expression": "1",
    },
    {
        "paramName": "fronta_pokriva_donju_plocu",
        "expression": "1",
    },
    {
        "paramName": "fronta_unutarnje_pokrivanje",
        "expression": "0",
    },
    {
        "paramName": "fronta_ofset",
        "expression": "2.0 mm",
    },
    {
        "paramName": "fronta_debljina",
        "expression": "19.0 mm",
    },
    {
        "paramName": "fronta_pokriva_gornju_plocu",
        "expression": "1",
    },
    {
        "paramName": "police",
        "expression": "1",
    },
    {
        "paramName": "polica_upust",
        "expression": "20.0 mm",
    },
    {
        "paramName": "polica_suzenje",
        "expression": "1.0 mm",
    },
    {
        "paramName": "broj_polica",
        "expression": "2",
    },
    {
        "paramName": "cokla",
        "expression": "0",
    },
    {"paramName": "cokla_visina", "expression": "60.0 mm"},
]
kuhinja_donji_element = [
    {
        "paramName": "sirina",
        "expression": "60.00 cm",
    },
    {
        "paramName": "dubina",
        "expression": "60.0 cm",
    },
    {
        "paramName": "visina",
        "expression": "78.0 cm",
    },
    {
        "paramName": "donja_ploca_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "bokovi_preko_donje_ploce",
        "expression": "0",
    },
    {
        "paramName": "bokovi_preko_gornje_ploce",
        "expression": "1",
    },
    {
        "paramName": "bok_lijevo_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "bok_desno_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "gornja_ploca",
        "expression": "0",
    },
    # {
    #     "paramName": "gornja_ploca_debljina",
    #     "expression": "18.0 mm",
    # },
    # {
    #     "paramName": "gornja_napust",
    #     "expression": "0.0 mm",
    # },
    {
        "paramName": "ukrute",
        "expression": "1",
    },
    {
        "paramName": "ukruta_sirina",
        "expression": "80.0 mm",
    },
    {
        "paramName": "ledja_debljina",
        "expression": "3.0 mm",
    },
    {
        "paramName": "ledja_ofset",
        "expression": "1.0 mm",
    },
    {"paramName": "ledja_upust", "expression": "0 mm"},
    {
        "paramName": "ledja_dubina_slota_u_bokovima",
        "expression": "0 mm",
    },
    {
        "paramName": "fronta",
        "expression": "1",
    },
    {
        "paramName": "fronta_pokriva_donju_plocu",
        "expression": "1",
    },
    {
        "paramName": "fronta_unutarnje_pokrivanje",
        "expression": "0",
    },
    {
        "paramName": "fronta_ofset",
        "expression": "2.0 mm",
    },
    {
        "paramName": "fronta_debljina",
        "expression": "19.0 mm",
    },
    # {
    #     "paramName": "fronta_pokriva_gornju_plocu",
    #     "expression": "1",
    # },
    {
        "paramName": "police",
        "expression": "1",
    },
    {
        "paramName": "polica_upust",
        "expression": "20.0 mm",
    },
    {
        "paramName": "polica_suzenje",
        "expression": "1.0 mm",
    },
    {
        "paramName": "broj_polica",
        "expression": "2",
    },
    {
        "paramName": "cokla",
        "expression": "0",
    },
    {"paramName": "cokla_visina", "expression": "60.0 mm"},
]

komoda = [
    {
        "paramName": "sirina",
        "expression": "100.00 cm",
    },
    {
        "paramName": "dubina",
        "expression": "45.0 cm",
    },
    {
        "paramName": "visina",
        "expression": "90.0 cm",
    },
    {
        "paramName": "donja_ploca_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "bokovi_preko_donje_ploce",
        "expression": "1",
    },
    {
        "paramName": "bokovi_preko_gornje_ploce",
        "expression": "0",
    },
    {
        "paramName": "bok_lijevo_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "bok_desno_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "gornja_ploca",
        "expression": "1",
    },
    # {
    #     "paramName": "gornja_ploca_debljina",
    #     "expression": "18.0 mm",
    # },
    {
        "paramName": "gornja_napust",
        "expression": "5.0 mm",
    },
    {
        "paramName": "ukrute",
        "expression": "1",
    },
    {
        "paramName": "ukruta_sirina",
        "expression": "80.0 mm",
    },
    {
        "paramName": "ledja_debljina",
        "expression": "3.0 mm",
    },
    {
        "paramName": "ledja_ofset",
        "expression": "1.0 mm",
    },
    {"paramName": "ledja_upust", "expression": "3 mm"},
    {
        "paramName": "ledja_dubina_slota_u_bokovima",
        "expression": "10 mm",
    },
    {
        "paramName": "fronta",
        "expression": "1",
    },
    {
        "paramName": "fronta_pokriva_donju_plocu",
        "expression": "1",
    },
    {
        "paramName": "fronta_unutarnje_pokrivanje",
        "expression": "0",
    },
    {
        "paramName": "fronta_ofset",
        "expression": "2.0 mm",
    },
    {
        "paramName": "fronta_debljina",
        "expression": "18.0 mm",
    },
    {
        "paramName": "fronta_pokriva_gornju_plocu",
        "expression": "0",
    },
    {
        "paramName": "police",
        "expression": "1",
    },
    {
        "paramName": "polica_upust",
        "expression": "20.0 mm",
    },
    {
        "paramName": "polica_suzenje",
        "expression": "1.0 mm",
    },
    {
        "paramName": "broj_polica",
        "expression": "2",
    },
    {
        "paramName": "cokla",
        "expression": "1",
    },
    {"paramName": "cokla_visina", "expression": "60.0 mm"},
]
_BUILTIN_PRESETS = {
    "Kuhinja - viseći element": kuhinja_viseci_element,
    "Kuhinja - donji element": kuhinja_donji_element,
    "Komoda": komoda,
}


def get_presets() -> dict:
    """All templates by display name: presets.json if readable, else built-ins."""
    try:
        with open(_PRESETS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            return data
    except Exception:
        pass
    return dict(_BUILTIN_PRESETS)


def save_preset(name: str, params: list) -> None:
    """Add or overwrite one template in presets.json.

    The file is (re)written with the full current template set, so the first
    save seeds it from the built-ins and later hand-edits are preserved."""
    all_presets = get_presets()
    all_presets[name] = params
    with open(_PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_presets, f, ensure_ascii=False, indent=2)
        f.write("\n")
