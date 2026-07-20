from dataclasses import dataclass, field
from enum import Enum
import os
from typing import List, NotRequired, Optional, TypedDict


@dataclass
class Dependency:
    name: str
    value: str
    triggerring_value: str
    # conditions: list["Dependency"]


class InputType(Enum):
    VALUE = "value"
    BOOL = "bool"
    INTEGER = "integer"
    GROUP = "group"
    GROUP_WITH_CHECKBOX = "group_with_checkbox"
    DROPDOWN = "dropdown"
    TABLE = "table"
    # TABLE_TOOLBAR = "table_toolbar"
    BUTTON = "button"


@dataclass
class InputItem:
    name: str
    type: InputType
    description: str
    parent: Optional[str] = None
    tooltip: Optional[str] = None
    values: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[float] = None
    input_has_no_param: bool = False
    expanded: Optional[bool] = None
    icon: Optional[str] = None
    table: Optional[str] = None  # For Table children inputs
    table_column: Optional[int] = None


input_items: list[InputItem] = [
    InputItem(
        name="osnovne_dimenzije",
        type=InputType.GROUP,
        description="Osnovne Dimenzije",
        input_has_no_param=True,
        expanded=True,  # the group edited on almost every interaction -> open it
    ),
    InputItem(
        name="sirina",
        type=InputType.VALUE,
        description="Ukupna Širina",
        parent="osnovne_dimenzije",
    ),
    InputItem(
        name="dubina",
        type=InputType.VALUE,
        description="Ukupna Dubina",
        parent="osnovne_dimenzije",
    ),
    InputItem(
        name="visina",
        type=InputType.VALUE,
        description="Ukupna Visina",
        parent="osnovne_dimenzije",
    ),
    InputItem(
        name="donja_ploca_debljina",
        type=InputType.VALUE,
        description="Debljina donje ploče",
        parent="osnovne_dimenzije",
    ),
    InputItem(
        name="grupa_bokovi",
        type=InputType.GROUP,
        description="Bokovi",
        input_has_no_param=True,
    ),
    InputItem(
        name="bokovi_preko_donje_ploce",
        type=InputType.BOOL,
        description="Bokovi preko donje ploče",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="bokovi_preko_gornje_ploce",
        type=InputType.BOOL,
        description="Bokovi preko gornje ploče",
        parent="grupa_bokovi",
        # ],
    ),
    InputItem(
        name="pregrada",
        type=InputType.BOOL,
        description="Pregrada",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="bok_lijevo_debljina",
        type=InputType.VALUE,
        description="Debljina boka lijevo",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="bok_desno_debljina",
        type=InputType.VALUE,
        description="Debljina boka desno",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="gornja_ploca",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Gornja Ploča",
    ),
    InputItem(
        name="gornja_ploca_debljina",
        type=InputType.VALUE,
        description="Debljina gornje ploče",
        parent="gornja_ploca",
    ),
    InputItem(
        name="gornja_napust",
        type=InputType.VALUE,
        description="Napust gornje ploče",
        parent="gornja_ploca",
    ),
    InputItem(
        name="ukrute",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Ukrute",
    ),
    InputItem(
        name="ukruta_sirina",
        type=InputType.VALUE,
        description="Širina ukrute",
        parent="ukrute",
    ),
    InputItem(
        name="grupa_ledja",
        type=InputType.GROUP,
        description="Ledja",
        input_has_no_param=True,
    ),
    InputItem(
        name="ledja_debljina",
        type=InputType.VALUE,
        description="Debljina leđa",
        parent="grupa_ledja",
    ),
    InputItem(
        name="ledja_ofset",
        type=InputType.VALUE,
        description="Ofset leđa",
        parent="grupa_ledja",
    ),
    InputItem(
        name="ledja_upust",
        type=InputType.VALUE,
        description="Upust leđa",
        parent="grupa_ledja",
    ),
    InputItem(
        name="ledja_dubina_slota_u_bokovima",
        type=InputType.VALUE,
        description="Dubina slota u bokovima",
        parent="grupa_ledja",
    ),
    InputItem(
        name="fronta",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Fronta",
    ),
    InputItem(
        name="fronta_pokriva_donju_plocu",
        type=InputType.BOOL,
        description="Fronta pokriva donju ploču",
        parent="fronta",
    ),
    InputItem(
        name="fronta_pokriva_gornju_plocu",
        type=InputType.BOOL,
        description="Fronta pokriva gornju ploču",
        parent="fronta",
    ),
    InputItem(
        name="fronta_unutarnje_pokrivanje",
        type=InputType.BOOL,
        description="Unutarnje pokrivanje",
        parent="fronta",
    ),
    InputItem(
        name="fronta_ofset",
        type=InputType.VALUE,
        description="Ofset fronte",
        parent="fronta",
    ),
    InputItem(
        name="fronta_debljina",
        type=InputType.VALUE,
        description="Debljina fronte",
        parent="fronta",
    ),
    InputItem(
        name="fronta_lijeva",
        type=InputType.BOOL,
        description="Lijevo otvaranje",
        parent="fronta",
    ),
    InputItem(
        name="fronta_desna",
        type=InputType.BOOL,
        description="Desno otvaranje",
        parent="fronta",
    ),
    InputItem(
        name="fronta_gore",
        type=InputType.BOOL,
        description="Otvaranje prema gore (podizna)",
        parent="fronta",
    ),
    InputItem(
        name="fronta_dolje",
        type=InputType.BOOL,
        description="Otvaranje prema dolje (preklopna)",
        parent="fronta",
    ),
    InputItem(
        name="police",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Police",
    ),
    InputItem(
        name="polica_upust",
        type=InputType.VALUE,
        description="Upust police",
        parent="police",
    ),
    InputItem(
        name="polica_suzenje",
        type=InputType.VALUE,
        description="Suženje police",
        parent="police",
    ),
    InputItem(
        name="broj_polica",
        type=InputType.INTEGER,
        description="Broj polica",
        parent="police",
    ),
    InputItem(name="cokla", type=InputType.GROUP_WITH_CHECKBOX, description="Cokla"),
    InputItem(
        name="cokla_visina",
        type=InputType.VALUE,
        description="Visina cokle",
        parent="cokla",
    ),
    # Legs (nogice): mutually exclusive with the plinth (cokla) -- turning one
    # on switches the other off (handled in input_changed_handler).
    InputItem(
        name="nogice",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Nogice",
        tooltip="Četiri nogice u kutovima donje ploče (isključuje coklu)",
    ),
    InputItem(
        name="nogice_visina",
        type=InputType.VALUE,
        description="Visina nogica",
        parent="nogice",
    ),
    InputItem(
        name="nogice_promjer",
        type=InputType.VALUE,
        description="Promjer nogica",
        parent="nogice",
    ),
    InputItem(
        name="nogice_odmak",
        type=InputType.VALUE,
        description="Odmak nogica od ruba",
        parent="nogice",
    ),
    # InputItem(
    #     name="ultrabox",
    #     type=InputType.GROUP,
    #     description="Ultrabox Ladica",
    #     input_has_no_param=True,
    #     expanded=True,
    # ),
    InputItem(
        name="ultrabox_table",
        type=InputType.TABLE,
        description="Konfiguracija ultrabox ladice",
        input_has_no_param=True,
        # parent="ultrabox",
    ),
    InputItem(
        name="add_ultrabox",
        type=InputType.BUTTON,
        description="Dodaj ultrabox ladicu",
        icon=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources", "plus"
        ),
        input_has_no_param=True,
        table="ultrabox_table",
    ),
    InputItem(
        name="remove_ultrabox",
        type=InputType.BUTTON,
        description="Izbaci ultrabox ladicu",
        icon=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources", "remove"
        ),
        input_has_no_param=True,
        table="ultrabox_table",
    ),
    # InputItem(
    #     name="ultrabox_duljina",
    #     type=InputType.DROPDOWN,
    #     description="Duljina ultrabox ladice",
    #     values=["270 mm", "350 mm", "400 mm", "450 mm", "500 mm"],
    #     table="ultrabox_table",
    #     table_column=1,
    # ),
    # InputItem(
    #     name="ultrabox_visina",
    #     type=InputType.DROPDOWN,
    #     description="Visina ultrabox ladice",
    #     values=["86 mm", "118 mm", "150 mm"],
    #     table="ultrabox_table",
    #     table_column=2,
    # ),
    # InputItem(
    #     name="ultrabox_fronta_visina",
    #     type=InputType.VALUE,
    #     description="Visina fronte ultrabox ladice",
    #     table="ultrabox_table",
    #     table_column=3,
    # ),
    # InputItem(
    #     name="ultrabox_podnica_debljina",
    #     type=InputType.VALUE,
    #     description="Debljina podnice ultrabox ladice",
    #     parent="ultrabox",
    # ),
    # InputItem(
    #     name="ultrabox_fronta_ofset_od_dna",
    #     type=InputType.VALUE,
    #     description="Ofset fronte ultrabox ladice od dna",
    #     parent="ultrabox",
    # ),
]
