from typing import NotRequired, TypedDict


class DialogItem(TypedDict):
    paramName: NotRequired[str]
    inputName: str
    inputType: str
    inputDescription: str
    parrent: NotRequired[str]


dialogItems: list[DialogItem] = [
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
        "paramName": "J1_ukrute",
        "inputName": "ukrute_enabled",
        "inputType": "bool",
        "inputDescription": "Ukrute",
    },
    {
        "paramName": "J1_donja_ploca_debljina",
        "inputName": "donja_ploca_debljina",
        "inputType": "value",
        "inputDescription": "Debljina donje ploče",
    },
    {
        "inputName": "grupa_gornja_ploca",
        "inputType": "group",
        "inputDescription": "Gornja Ploča",
    },
    {
        "paramName": "J1_gornja_ploca",
        "inputName": "gornja_ploca_enabled",
        "inputType": "bool",
        "inputDescription": "Gornja Ploča",
        "parrent": "grupa_gornja_ploca",
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
    # grupa fronta
    {
        "inputName": "grupa_fronta",
        "inputType": "group",
        "inputDescription": "Fronta",
    },
    {
        "paramName": "J1_fronta",
        "inputName": "fronta_enabled",
        "inputType": "bool",
        "inputDescription": "Fronta",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronta_pokriva_donju_plocu",
        "inputName": "fronta_pokriva_donju_plocu",
        "inputType": "bool",
        "inputDescription": "Fronta pokriva donju ploču",
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
        "paramName": "J1_fronta_ofset",
        "inputName": "fronta_ofset",
        "inputType": "value",
        "inputDescription": "Ofset fronte",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronta_debljina",
        "inputName": "fronta_debljina",
        "inputType": "value",
        "inputDescription": "Debljina fronte",
        "parrent": "grupa_fronta",
    },
    {
        "paramName": "J1_fronta_pokriva_gornju_plocu",
        "inputName": "fronta_pokriva_gornju_plocu",
        "inputType": "bool",
        "inputDescription": "Fronta pokriva gornju ploču",
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
        "paramName": "J1_broj_polica",
        "inputName": "broj_polica",
        "inputType": "integer",
        "inputDescription": "Broj polica",
        "parrent": "grupa_police",
    },
]
