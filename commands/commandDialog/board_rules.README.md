# board_rules.json — finish & edge-banding rules

This file is the single, editable source of truth for two things per board:

- **`colored`** — does the board's **broad faces** get the decorative finish colour?
  `true` = colour, `false` = white (interior). You can also write a **condition
  string** (see below) for boards that should be coloured only in some
  constructions. This is only the *default* — in the dialog a user can click any
  board to colour it or turn it white per cabinet; that per-cabinet choice
  overrides this default.
- **`banding`** — which **narrow (thickness) edges** get edge-banded. Listed
  edges are banded (shown in the finish colour); every other edge stays raw
  (shown with a striped "no-banding" texture). Only visible edges should be
  banded.

## Edge orientations

Keys in `banding` are the edge's outward direction in the cabinet's world frame:

| key | direction | key | direction |
|---|---|---|---|
| `front` | toward the room (+Y) | `back` | toward the wall (−Y) |
| `left` | toward "bok lijevo" (+X) | `right` | toward "bok desno" (−X) |
| `top` | up (+Z) | `bottom` | down (−Z) |

A board only has four narrow edges — the two along its thickness are its big
faces and are never banded, so only the four valid orientations for that board
do anything (extra keys are harmless).

## Values: `true`, `false`, or a condition

- `true` — always coloured / banded.
- `false` (or the key omitted, for banding) — never.
- A **string** — a Python condition on the cabinet's flag parameters, referenced
  by their base name (no prefix). It is re-evaluated live every preview, so the
  result follows the construction. Examples already in use:
  - `"bokovi_preko_donje_ploce == 0"` — the bottom panel's side edges are only
    exposed (and so banded) when the bottom runs full width.
  - `"bokovi_preko_donje_ploce == 1 and cokla == 0"` — a side panel's bottom
    edge is banded only on wall units (side runs to the floor, no plinth hiding
    it).

Available flags include: `bokovi_preko_donje_ploce`, `bokovi_preko_gornje_ploce`,
`cokla`, `fronta`, `gornja_ploca`, `ukrute`, `pregrada`, `police`,
`fronta_unutarnje_pokrivanje`, and any other `<prefix>`-stripped user parameter.

## Board names

The keys under `boards` are the Fusion component names built by `base_design.py`
(`donja_ploca`, `bok desno`, `bok_lijevo`, `ledja`, `gornja_ploca`, `pregrada`,
`polica`, `cokla`, `fronta desno`, `fronta lijevo`, `ukruta otraga`, and the
Ultrabox parts `podnica` / `zadnja` / `fronta`). Shelf pattern copies (`polica2`,
`polica3`, …) resolve back to `polica` automatically.

## Fallback

If this file is missing or unparseable, the built-in defaults in `base_design.py`
(`BANDING_BY_NAME`, `COLORED_DEFAULTS`) are used instead. Values here override
those defaults board-by-board.
