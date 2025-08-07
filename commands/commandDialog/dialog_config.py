from dataclasses import dataclass, field
from enum import Enum
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


@dataclass
class InputItem:
    name: str
    type: InputType
    description: str
    parent: Optional[str] = None
    tooltip: Optional[str] = None
    values: Optional[List[str]] = None
    dependencies: Optional[List[Dependency]] = field(default_factory=list)


input_items: list[InputItem] = [
    InputItem(
        name="osnovne_dimenzije",
        type=InputType.GROUP,
        description="Osnovne Dimenzije",
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
        # dependencies=[
        #     Dependency(
        #         name="grupa_ukrute",
        #         value="0",
        #         triggerring_value=True,
        #     )
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
        # dependencies=[
        #     Dependency(
        #         name="bokovi_preko_gornje_ploce",
        #         value="1",
        #         triggerring_value=False,
        #     )
        # ],
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
    InputItem(
        name="ultrabox",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Ultrabox Ladica",
    ),
    InputItem(
        name="ultrabox_duljina",
        type=InputType.DROPDOWN,
        description="Duljina ultrabox ladice",
        values=["270 mm", "350 mm", "400 mm", "450 mm", "500 mm"],
        parent="ultrabox",
    ),
    InputItem(
        name="ultrabox_visina",
        type=InputType.DROPDOWN,
        description="Visina ultrabox ladice",
        values=["86 mm", "118 mm", "150 mm"],
        parent="ultrabox",
    ),
    InputItem(
        name="ultrabox_fronta_visina",
        type=InputType.VALUE,
        description="Visina fronte ultrabox ladice",
        parent="ultrabox",
    ),
    InputItem(
        name="ultrabox_podnica_debljina",
        type=InputType.VALUE,
        description="Debljina podnice ultrabox ladice",
        parent="ultrabox",
    ),
    InputItem(
        name="ultrabox_fronta_ofset_od_dna",
        type=InputType.VALUE,
        description="Ofset fronte ultrabox ladice od dna",
        parent="ultrabox",
    ),
]
