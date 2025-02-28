from dataclasses import dataclass, field
from enum import Enum
from typing import List, NotRequired, Optional, TypedDict


@dataclass
class Dependency:
    name: str
    value: str
    triggerring_value: str


class InputType(Enum):
    VALUE = "value"
    BOOL = "bool"
    INTEGER = "integer"
    GROUP = "group"
    GROUP_WITH_CHECKBOX = "group_with_checkbox"
    PRESETS = "presets"


@dataclass
class InputItem:
    name: str
    type: InputType
    description: str
    user_param: Optional[str] = None
    parent: Optional[str] = None
    tooltip: Optional[str] = None
    dependencies: Optional[List[Dependency]] = field(default_factory=list)


input_items: list[InputItem] = [
    InputItem(
        name="ukupna_sirina",
        type=InputType.VALUE,
        description="Ukupna Širina",
        user_param="J1_sirina",
    ),
    InputItem(
        name="ukupna_dubina",
        type=InputType.VALUE,
        description="Ukupna Dubina",
        user_param="J1_dubina",
    ),
    InputItem(
        name="ukupna_visina",
        type=InputType.VALUE,
        description="Ukupna Visina",
        user_param="J1_visina",
    ),
    InputItem(
        name="donja_ploca_debljina",
        type=InputType.VALUE,
        description="Debljina donje ploče",
        user_param="J1_donja_ploca_debljina",
    ),
    InputItem(
        name="grupa_bokovi",
        type=InputType.GROUP,
        description="Bokovi",
    ),
    InputItem(
        name="bokovi_na_donju_plocu",
        type=InputType.BOOL,
        description="Bokovi na donju ploču",
        user_param="J1_bokovi_na_donju_plocu",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="bokovi_do_gornje_ploce",
        type=InputType.BOOL,
        description="Bokovi do gornje ploče",
        user_param="J1_bokovi_do_gornje_ploce",
        parent="grupa_bokovi",
        dependencies=[
            Dependency(
                name="J1_ukrute",
                value="0",
                triggerring_value=False,
            )
        ],
    ),
    InputItem(
        name="bok_lijevo_debljina",
        type=InputType.VALUE,
        description="Debljina boka lijevo",
        user_param="J1_bok_lijevo_debljina",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="bok_desno_debljina",
        type=InputType.VALUE,
        description="Debljina boka desno",
        user_param="J1_bok_desno_debljina",
        parent="grupa_bokovi",
    ),
    InputItem(
        name="grupa_gornja_ploca",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Gornja Ploča",
        user_param="J1_gornja_ploca",
    ),
    InputItem(
        name="gornja_ploca_debljina",
        type=InputType.VALUE,
        description="Debljina gornje ploče",
        user_param="J1_gornja_ploca_debljina",
        parent="grupa_gornja_ploca",
    ),
    InputItem(
        name="gornja_ploca_napust",
        type=InputType.VALUE,
        description="Napust gornje ploče",
        user_param="J1_gornja_napust",
        parent="grupa_gornja_ploca",
    ),
    InputItem(
        name="grupa_ukrute",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Ukrute",
        user_param="J1_ukrute",
    ),
    InputItem(
        name="ukruta_sirina",
        type=InputType.VALUE,
        description="Širina ukrute",
        user_param="J1_ukruta_širina",
        parent="grupa_ukrute",
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
        user_param="J1_leđa_debljina",
        parent="grupa_ledja",
    ),
    InputItem(
        name="ledja_ofset",
        type=InputType.VALUE,
        description="Ofset leđa",
        user_param="J1_leđa_ofset",
        parent="grupa_ledja",
    ),
    InputItem(
        name="ledja_upust",
        type=InputType.VALUE,
        description="Upust leđa",
        user_param="J1_leđa_upust",
        parent="grupa_ledja",
    ),
    InputItem(
        name="ledja_dubina_slota_u_bokovima",
        type=InputType.VALUE,
        description="Dubina slota u bokovima",
        user_param="J1_leđa_dubina_slota_u_bokovima",
        parent="grupa_ledja",
    ),
    InputItem(
        name="grupa_fronta",
        type=InputType.GROUP_WITH_CHECKBOX,
        description="Fronta",
        user_param="J1_fronta",
    ),
    InputItem(
        name="fronta_pokriva_donju_plocu",
        type=InputType.BOOL,
        description="Fronta pokriva donju ploču",
        user_param="J1_fronta_pokriva_donju_plocu",
        parent="grupa_fronta",
    ),
    InputItem(
        name="fronta_pokriva_gornju_plocu",
        type=InputType.BOOL,
        description="Fronta pokriva gornju ploču",
        user_param="J1_fronta_pokriva_gornju_plocu",
        parent="grupa_fronta",
    ),
    InputItem(
        name="fronta_unutarnje_pokrivanje",
        type=InputType.BOOL,
        description="Unutarnje pokrivanje",
        user_param="J1_fronta_unutarnje_pokrivanje",
        parent="grupa_fronta",
    ),
    InputItem(
        name="fronta_ofset",
        type=InputType.VALUE,
        description="Ofset fronte",
        user_param="J1_fronta_ofset",
        parent="grupa_fronta",
    ),
    InputItem(
        name="fronta_debljina",
        type=InputType.VALUE,
        description="Debljina fronte",
        user_param="J1_fronta_debljina",
        parent="grupa_fronta",
    ),
    InputItem(
        name="fronta_lijevo_otvaranje",
        type=InputType.BOOL,
        description="Lijevo otvaranje",
        user_param="J1_fronta_lijevo_otvaranje",
        parent="grupa_fronta",
    ),
    InputItem(
        name="fronta_lijeva_i_desna",
        type=InputType.BOOL,
        description="Dvostrano otvaranje",
        user_param="J1_fronta_lijeva_i_desna",
        parent="grupa_fronta",
    ),
    InputItem(
        name="grupa_police",
        type=InputType.GROUP,
        description="Police",
    ),
    InputItem(
        name="polica_upust",
        type=InputType.VALUE,
        description="Upust police",
        user_param="J1_polica_upust",
        parent="grupa_police",
    ),
    InputItem(
        name="polica_suzenje",
        type=InputType.VALUE,
        description="Suženje police",
        user_param="J1_polica_suzenje",
        parent="grupa_police",
    ),
    InputItem(
        name="broj_polica",
        type=InputType.INTEGER,
        description="Broj polica",
        user_param="J1_broj_polica",
        parent="grupa_police",
    ),
]
