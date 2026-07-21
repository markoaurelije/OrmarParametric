# Dialog Preview Performance Design

## Goal

Keep the cabinet command dialog responsive in designs containing many cabinets while preserving optional live model feedback. Ordinary edits must stop triggering full-project recomputation.

## Current Behavior and Root Cause

Fusion fires `executePreview` after ordinary dialog input changes. The current preview handler discovers every cabinet and, for each one:

1. reseats free child occurrences;
2. writes every dialog-backed user parameter;
3. materializes lazy parts;
4. updates component visibility; and
5. walks and repaints the complete board tree.

This work runs even when one checkbox on one cabinet changed. Assigning unchanged parameter values can also ask Fusion to reevaluate dependent geometry unnecessarily. The cost therefore grows with the total number of cabinets and boards rather than with the edited cabinet.

## User Experience

The Projekt tab gains a `Pregled uživo` (`Live preview`) checkbox. It defaults to off each time the command opens so users can make several dialog edits without waiting for Fusion after each one.

Each cabinet tab gains an `Ažuriraj model` (`Update model`) button. The button applies only that cabinet's staged changes. It is useful in staged mode and remains available in live mode as an explicit retry.

Behavior by action:

- With live preview off, ordinary cabinet inputs only update dialog state and mark that cabinet dirty. Automatic `executePreview` performs no model work for those inputs.
- Pressing a cabinet's Update model button applies only that cabinet and clears its dirty state after success.
- With live preview on, an ordinary cabinet input change applies only the changed cabinet through the same update pipeline.
- Pressing OK applies every dirty cabinet, then performs the existing final persistence work. No staged edit can be lost because the user did not press Update model.
- Finish paint and edge-band selection remain immediate. Their purpose depends on direct visual feedback, and their existing code already scopes repainting to affected cabinets.
- Project-wide decor replacement may repaint multiple affected cabinets and marks or updates exactly that returned prefix set.
- Add/delete cabinet and Ultrabox actions retain their existing deferred materialization semantics.

The live-preview setting is session-only. It is not stored in the Fusion design or add-in configuration.

## Architecture

### Dirty Cabinet State

A command-session state object stores:

- whether live preview is enabled;
- the set of dirty cabinet prefixes;
- prefixes explicitly requested for update; and
- whether a project-level operation requires broader work.

`InputChangedHandler` derives a cabinet prefix from normal cabinet input IDs and marks only that prefix dirty. Project-tab controls and pure action buttons are excluded from this generic path.

The state is reset when the command is created and discarded when it is destroyed. It must not leak between dialog sessions.

### Shared Cabinet Update Pipeline

Preview, Update model, and final execute call one shared function for a supplied prefix set. For each prefix, it performs the established operations in the required order:

1. synchronize changed user parameters from dialog inputs;
2. materialize enabled lazy parts;
3. update component visibility;
4. reseat unjointed internal occurrences; and
5. apply board finishes.

The existing ordering is adjusted only where required by current dependencies: parameter synchronization must precede materialization and visibility. The shared function returns which prefixes completed successfully so dirty state is cleared only for those prefixes.

Final execute passes all dirty prefixes plus any prefixes required by pending structural operations. Existing cabinet creation/deletion and finish-override persistence remain execute responsibilities.

### Change-Aware Parameter Synchronization

Before assigning a Fusion user parameter, synchronization compares the requested dialog value with the parameter's current value or expression:

- value and dropdown inputs compare normalized expressions;
- boolean and group-checkbox inputs compare numeric values;
- integer inputs compare their effective integer value.

Assignments are skipped when the effective value is unchanged. This optimization applies in both preview and final execute and does not alter public parameter names or expressions.

### Preview Routing

The automatic preview handler chooses work from session state:

- staged mode with no explicit request: return immediately;
- live mode: process dirty prefixes only;
- explicit Update model request: process the requested prefix regardless of mode;
- structural project operation: preserve the operation's required prefix scope.

The handler must not call `get_prefixes()` merely to process an ordinary one-cabinet edit. Full prefix discovery remains appropriate for final execution and genuinely project-wide operations.

## Special Cases

Preset application changes many inputs programmatically. It marks the preset's cabinet dirty once; live preview applies that cabinet after the input changes settle, while staged mode waits for Update model or OK.

The `cokla`/`nogice` and door-opening mutual-exclusion handlers can change a second input. Both inputs share a cabinet prefix, so the dirty set naturally coalesces repeated notifications into one cabinet update.

If a scoped cabinet update raises an exception, the error is logged through the existing Fusion logger and the prefix remains dirty. The user can retry with Update model or OK. A failure in one prefix must not incorrectly clear another dirty prefix.

Cabinet deletion removes its prefix from dirty/update sets once deletion is committed. Newly materialized cabinets are included in final processing even if they did not originate from an ordinary cabinet input.

## Compatibility

The design preserves:

- all existing user parameter names and expressions;
- the one-tab-per-cabinet dialog structure;
- immediate finish-picker feedback;
- execute-time finish override persistence;
- deferred structural changes required by Fusion's command rollback behavior; and
- the final OK/Cancel command contract.

Cancel continues to discard command-managed model previews according to Fusion's command transaction behavior. Session-only dirty state and finish overrides are discarded on command destruction/open reset as they are today.

## Verification

There is no standalone `adsk` runtime or automated Fusion test harness. Verification consists of a Python syntax check where possible and manual testing in the open `jadranovo` design.

Manual matrix:

1. Open the dialog with 6-7 cabinets and confirm ordinary checkbox/value edits remain immediately interactive with live preview off.
2. Change `cokla` and `nogice` on one cabinet, press Update model, and verify only that cabinet visibly updates and mutual exclusion remains correct.
3. Enable live preview, change one cabinet, and verify immediate model feedback without visible recomputation of unrelated cabinets.
4. Make staged edits on multiple cabinets, press OK without Update model, and verify every edit is applied.
5. Apply a preset in both modes and verify all target-cabinet values and geometry update together.
6. Exercise front/door lazy materialization, shelves, legs, and visibility toggles to verify update ordering.
7. Paint a board, band an edge, and perform a project decor swap to verify finish feedback remains immediate and persists on OK.
8. Add and delete a cabinet and exercise Ultrabox controls to verify existing deferred behavior is unchanged.
9. Cancel after staged and live-preview edits and verify no session state leaks when reopening the dialog.

## Success Criteria

- With live preview off, changing ordinary inputs does not show Fusion's model-update wait cursor between edits.
- Live preview work scales with the number of affected cabinets, normally one, rather than all cabinets in the design.
- Unchanged user parameters are not reassigned.
- Update model and OK produce the same final cabinet geometry and finishes as the current full preview/execute pipeline.
- Existing structural and finish workflows continue to work.