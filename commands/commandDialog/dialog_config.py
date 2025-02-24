from typing import NotRequired, TypedDict


class DialogItem(TypedDict):
    paramName: NotRequired[str]
    inputName: str
    inputType: str
    inputDescription: str
    parrent: NotRequired[str]
    tooltip: NotRequired[str]


dialogItems: list[DialogItem] = [
    # global
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
        "paramName": "J1_donja_ploca_debljina",
        "inputName": "donja_ploca_debljina",
        "inputType": "value",
        "inputDescription": "Debljina donje ploče",
    },
    # group bokovi
    {
        "inputName": "grupa_bokovi",
        "inputType": "group",
        "inputDescription": "Bokovi",
    },
    {
        "paramName": "J1_bokovi_na_donju_plocu",
        "inputName": "bokovi_na_donju_plocu",
        "inputType": "bool",
        "inputDescription": "Bokovi na donju ploču",
        "parrent": "grupa_bokovi",
    },
    {
        "paramName": "J1_bokovi_do_gornje_ploce",
        "inputName": "bokovi_do_gornje_ploce",
        "inputType": "bool",
        "inputDescription": "Bokovi do gornje ploče",
        "parrent": "grupa_bokovi",
    },
    {
        "paramName": "J1_bok_lijevo_debljina",
        "inputName": "bok_lijevo_debljina",
        "inputType": "value",
        "inputDescription": "Debljina boka lijevo",
        "parrent": "grupa_bokovi",
    },
    {
        "paramName": "J1_bok_desno_debljina",
        "inputName": "bok_desno_debljina",
        "inputType": "value",
        "inputDescription": "Debljina boka desno",
        "parrent": "grupa_bokovi",
    },
    # grupa gornja ploca
    {
        "paramName": "J1_gornja_ploca",
        "inputName": "grupa_gornja_ploca",
        "inputType": "group_with_checkbox",
        "inputDescription": "Gornja Ploča",
    },
    {
        "paramName": "J1_gornja_ploca_debljina",
        "inputName": "gornja_ploca_debljina",
        "inputType": "value",
        "inputDescription": "Debljina gornje ploče",
        "parrent": "grupa_gornja_ploca",
    },
    {
        "paramName": "J1_gornja_napust",
        "inputName": "gornja_ploca_napust",
        "inputType": "value",
        "inputDescription": "Napust gornje ploče",
        "parrent": "grupa_gornja_ploca",
    },
    # grupa ukrute
    {
        "paramName": "J1_ukrute",
        "inputName": "grupa_ukrute",
        "inputType": "group_with_checkbox",
        "inputDescription": "Ukrute",
    },
    {
        "paramName": "J1_ukruta_širina",
        "inputName": "ukruta_sirina",
        "inputType": "value",
        "inputDescription": "Širina ukrute",
        "parrent": "grupa_ukrute",
    },
    # group ledja
    {
        "inputName": "grupa_ledja",
        "inputType": "group",
        "inputDescription": "Ledja",
    },
    {
        "paramName": "J1_leđa_debljina",
        "inputName": "ledja_debljina",
        "inputType": "value",
        "inputDescription": "Debljina leđa",
        "parrent": "grupa_ledja",
    },
    {
        "paramName": "J1_leđa_ofset",
        "inputName": "ledja_ofset",
        "inputType": "value",
        "inputDescription": "Ofset leđa",
        "parrent": "grupa_ledja",
    },
    {
        "paramName": "J1_leđa_upust",
        "inputName": "ledja_upust",
        "inputType": "value",
        "inputDescription": "Upust leđa",
        "parrent": "grupa_ledja",
        "tooltip": "Za kuhinjske visece elemente upust je 15mm od kraja ledja, upisati 15+J1_leđa_debljina",
    },
    {
        "paramName": "J1_leđa_dubina_slota_u_bokovima",
        "inputName": "ledja_dubina_slota_u_bokovima",
        "inputType": "value",
        "inputDescription": "Dubina slota u bokovima",
        "parrent": "grupa_ledja",
    },
    # grupa fronta
    {
        "paramName": "J1_fronta",
        "inputName": "grupa_fronta",
        "inputType": "group_with_checkbox",
        "inputDescription": "Fronta",
    },
    {
        "paramName": "J1_fronta_pokriva_donju_plocu",
        "inputName": "fronta_pokriva_donju_plocu",
        "inputType": "bool",
        "inputDescription": "Fronta pokriva donju ploču",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronta_pokriva_gornju_plocu",
        "inputName": "fronta_pokriva_gornju_plocu",
        "inputType": "bool",
        "inputDescription": "Fronta pokriva gornju ploču",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronta_unutarnje_pokrivanje",
        "inputName": "fronta_unutarnje_pokrivanje",
        "inputType": "bool",
        "inputDescription": "Unutarnje pokrivanje",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronte_ofset",
        "inputName": "fronta_ofset",
        "inputType": "value",
        "inputDescription": "Ofset fronte",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_debljina_fronte",
        "inputName": "fronta_debljina",
        "inputType": "value",
        "inputDescription": "Debljina fronte",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronta_ljevo_otvaranje",
        "inputName": "fronta_ljevo_otvaranje",
        "inputType": "bool",
        "inputDescription": "Ljevo otvaranje",
        "parrent": "grupa_fronta",
    },
    # grupa police
    {
        "inputName": "grupa_police",
        "inputType": "group",
        "inputDescription": "Police",
    },
    {
        "paramName": "J1_polica_upust",
        "inputName": "polica_upust",
        "inputType": "value",
        "inputDescription": "Upust police",
        "parrent": "grupa_police",
    },
    {
        "paramName": "J1_polica_suzenje",
        "inputName": "polica_suzenje",
        "inputType": "value",
        "inputDescription": "Suženje police",
        "parrent": "grupa_police",
    },
    {
        "paramName": "J1_broj_polica",
        "inputName": "broj_polica",
        "inputType": "integer",
        "inputDescription": "Broj polica",
        "parrent": "grupa_police",
    },
]
