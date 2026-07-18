# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An Autodesk Fusion 360 Add-In, written in Python against the `adsk` API (`adsk.core`, `adsk.fusion`, `adsk.cam`). It generates parametric wardrobe/cabinet furniture ("Ormari Parametric" — Croatian for "Parametric Wardrobes") by driving Fusion's user parameters, component visibility, and feature suppression from a custom command dialog.

There is no standalone runtime: `adsk` only exists inside Fusion 360's embedded Python interpreter. There is no `requirements.txt`, `pyproject.toml`, build step, linter config, or test suite in this repo — none of the usual Python tooling commands apply here.

## Running / debugging

- The add-in is loaded by pointing Fusion 360's Scripts and Add-Ins panel at this folder (identified by `OrmarParametric.manifest`, `id: 7f99ac39-252e-42db-93bd-e3903a22363e`).
- Once running inside Fusion, attach VS Code with the "Python: Attach" config in [.vscode/launch.json](.vscode/launch.json) (debugpy on `localhost:9000`) to set breakpoints and inspect state live.
- `config.DEBUG` (in [config.py](config.py)) controls whether log messages are mirrored to Fusion's Text Command window; errors always go there and to the Fusion log file regardless.
- There is no automated way to exercise this code outside a running Fusion session with the target document(s) open — changes should be verified manually in Fusion.

## Lifecycle & structure

- [OrmarParametric.py](OrmarParametric.py) is the add-in entry point Fusion calls: `run(context)` / `stop(context)`. It puts `lib/` on `sys.path` and delegates to `commands.start()` / `commands.stop()`.
- [commands/\_\_init\_\_.py](commands/__init__.py) is the registry: each subfolder under `commands/` is a self-contained command exposing `start()`/`stop()` in its `entry.py`, and must be added to the `commands` list here to be active. Currently only `commandDialog` is registered; `paletteShow`/`paletteSend` are Autodesk's stock sample-add-in templates (palette + postMessage bridge) kept around as reference/scaffolding but not wired in.
- [lib/fusionAddInUtils/](lib/fusionAddInUtils/) is Autodesk's standard add-in utility template: `general_utils.py` (`log`, `handle_error`) and `event_utils.py` (`add_handler`/`clear_handlers`, which wraps a callback in a generated `adsk` event-handler subclass and keeps a reference alive so it isn't GC'd). Treat this as boilerplate, not project-specific logic.
- [lib/openpyxl/](lib/openpyxl) and [lib/et_xmlfile/](lib/et_xmlfile) are vendored third-party packages (added because Fusion's Python has no package manager access). `openpyxl` is not yet called from any project code — it's staged for future Excel export work related to `narudzba-excel.xlsm` (an order-form template at the repo root), not currently wired up.

## The `commandDialog` command (the actual product)

This is where all domain logic lives, under [commands/commandDialog/](commands/commandDialog/):

- **[dialog_config.py](commands/commandDialog/dialog_config.py)** is the single source of truth for the UI: a declarative list of `InputItem` (name, `InputType`, parent group, tooltip, min/max, table binding, etc.). Adding or changing a dialog field means editing this list — `utils.py` renders it generically, there's no per-field UI code to hand-write. Each `InputItem` (unless `input_has_no_param=True`, i.e. it's a pure layout group) maps 1:1 to a Fusion **user parameter** of the same name.
- **[utils.py](commands/commandDialog/utils.py)** does the heavy lifting:
  - `create_dialog`/`create_input` walk `input_items` and build the actual Fusion `CommandInputs` tree (groups, value/bool/integer/dropdown inputs, the ultrabox table and its toolbar buttons), seeding each from the matching user parameter's current expression/value.
  - `set_user_parameters_via_inputs` / `input_to_user_parameter` push edited dialog values back into Fusion user parameters on execute/preview.
  - `set_component_visibility` reads user parameters after they're set and toggles occurrence light bulbs (show/hide) and suppresses specific features (e.g. `"split ukrute"`, `"split police"`) based on flags like `pregrada` (divider) — this is how boolean toggles in the dialog become visible geometry changes.
  - **Prefix system**: multiple cabinets can coexist as parameter sets in one design, distinguished by a name prefix (e.g. `J1_sirina`, `O1_sirina`). `get_prefixes()` discovers all prefixes present by intersecting which prefixes exist for every non-group parameter name. Nearly every function threads a `prefix` argument through for this reason — the dialog renders one tab per prefix.
  - `add_parametric_component`/`rename_user_parameters` implement "add a new cabinet": copy the base design's root component into the target design and rename its `J1_*` parameters to `<newname>_*`.
- **[presets.py](commands/commandDialog/presets.py)** holds named parameter presets (`kuhinja_viseci_element`, `kuhinja_donji_element`, `komoda`) — full sets of `{paramName, expression}` applied together via `load_preset` in utils.py.
- **[ultrabox.py](commands/commandDialog/ultrabox.py)** is a work-in-progress feature for inserting drawer sub-assemblies ("Ultrabox") dynamically per cabinet, driven by add/remove toolbar buttons on the ultrabox table. The actual per-instance parameterization (step 3/4 in `perform_add_ultrabox`) is not yet implemented — only base copy-and-rename.
- **[event_handlers/](commands/commandDialog/event_handlers/)** wires Fusion's command lifecycle: `command_created_event_handler.py` builds the dialog and registers the other handlers; `input_changed_handler.py` reacts to preset selection, the "add cabinet" button, and the ultrabox add/remove buttons; `command_execute_handler.py` / `command_execute_preview_handler.py` both run the same param-sync → visibility → ultrabox-materialization sequence (preview does it live as the user edits, execute commits on OK) — keep these two handlers behaviorally in sync when changing this flow.

## Code-generated base cabinet

Cabinets are generated entirely from code by **[base_design.py](commands/commandDialog/base_design.py)** — the old workflow of copying a hand-modeled `J1` base document from the cloud is gone (`get_design_by_name`/`rename_user_parameters` in utils.py are leftovers of it). `add_cabinet(design, name)` creates a wrapper component named `name` at root and builds the full parametric cabinet inside it with `<name>_*` user parameters: every panel is an origin-anchored rectangle sketch + extrude driven by parameter expressions, positioned by a rigid joint to an expression-driven joint origin (equivalent to the original J1's face-to-face joints — geometry natively follows parameter edits). The declarative tables at the top of the module (`USER_PARAMS`, `PANELS`, `UKRUTA_POSITIONS`, `ULTRABOX_PANELS`) were reverse-engineered from the original J1 design and are the single source of truth for cabinet geometry.

Two Fusion API gotchas are baked into `create_cabinet` and must be preserved: (1) new occurrences default to `isGroundToParent=True`, which silently breaks joints until unset; (2) rectangular patterns and cross-component combine features created *inside* a nested component ignore/fail on other occurrences' joint-driven transforms — they must be created on `design.rootComponent.features` using root-context proxies (`createForAssemblyContext`). Component/feature names are load-bearing: `utils.set_component_visibility` matches occurrences by name prefix (`"polica"`, `"ukrute"` wrapper with children, features `"split police"`/`"split ukrute"`) and finds each cabinet as a root occurrence whose component name equals the parameter prefix minus the underscore; `ultrabox.py` needs a component named `"Ultrabox"`.

A third gotcha governs `utils.add_parametric_component` specifically: while our command dialog is active on a document, Fusion silently rolls back any *structural* model changes (new occurrences/bodies) made from the `inputChanged` handler on the very next preview cycle — only parameter edits survive, because `set_user_parameters_via_inputs` re-applies them every cycle, whereas a one-shot component creation is never re-applied and gets discarded. A cabinet built by `add_cabinet` directly into the document the dialog is open on will flash into existence and vanish before the user can see it. `add_parametric_component` works around this by always calling `app.documents.add(...)` and building the cabinet into that brand-new, command-free document instead — never into the currently active one. This is also why the pre-code-gen implementation always opened a separate "target design" rather than inserting into the active document; don't remove that behavior when touching this function.

## Domain vocabulary (Croatian)

Dialog fields, presets, and component names are in Croatian. Key terms, since they recur throughout `dialog_config.py`, `presets.py`, and component-name matching in `utils.py`:

| Term | Meaning | Term | Meaning |
|---|---|---|---|
| ormar(i) | wardrobe/cabinet(s) | fronta | door/front panel |
| sirina | width | polica / police | shelf / shelves |
| dubina | depth | pregrada | divider |
| visina | height | ukrute | stiffeners/braces |
| ploca | panel/board | cokla | plinth/kickboard |
| bok(ovi) | side panel(s) | ledja | back panel |
| debljina | thickness | napust | overhang |
| gornja / donja | top / bottom | lijevo / desno | left / right |
| upust / ofset | recess / offset | otvaranje | opening (of a door) |
