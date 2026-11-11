# Editing a published walkthrough from Claude (ArtifactData)

For a carousel published with the edit layer (`reference/capabilities.json`). The page draws every screen and every step text from the artifact's database, so an edit shows for everyone at once; nothing is rebuilt or republished. You need edit access to the artifact.

## Collections
| Collection | Document id | Body |
|---|---|---|
| `screens` | screen id, e.g. `CaseRec` | `{html, css}`: the board source (before the top bar and menu are filled in) and its stylesheet |
| `steps` | screen id | `{cards: [{who, do, happens, say, attention, issue}]}`: the text above the screen |
| `screen_versions` | `<screenId>--<YYYYMMDDTHHMMSSmmmZ>` | `{screen, savedAt, html, css, steps, by}`: a copy before each change (Undo, Versions) |
| `screens_original` | screen id | the first version of every screen; owner only |
| `answers` | `<item key>--<UTC time>` | `{key, screen, kind: question\|issue\|blk\|gap, item, step, answer, by, at, status: pending\|open\|resolved, summary, reason}`: an answer given on the page |
| `resolved` | item key, e.g. `question-CaseRec-1yv5e45` | `{screen, kind, item, answer, summary, by, at}`: the item is settled; the page hides a question with this key |

The item key is `<kind>-<screen>-<hash>`, where the hash is computed by the page from the item text; take keys from `answers`, never compute them by hand. To reopen a settled question, delete its `resolved/<key>`.

## Change a screen
1. `get` `screens/<id>` (and `steps/<id>`).
2. Keep a copy: `set` `screen_versions/<id>--<UTC time>` with `{screen, savedAt, html, css, steps}`.
3. Write the new `screens/<id>` (and `steps/<id>` when the text changes). Prefer a batch.
4. Rules, or the screen breaks or is cleaned away by the page:
   - static HTML only: no `<script>`, `<iframe>`, `<form>`, `<object>`, event handler attributes or `javascript:` links; the page's sanitiser strips them anyway;
   - CSS: plain rules and `@media`; no `@import`, no `url()` other than `data:image`; selectors are scoped to the screen;
   - keep `<dc-import name="TopBar" …>` (with its `variant="…"`) and `<dc-import name="AppNav" active="<Workplace>:<Item>">` as they are. A trailing `|c` draws the icon rail used when the Creatio.ai panel is open. Only `active` values that existed at build time have a menu in the page; a new one needs a rebuild;
   - keep the root `<div class="{{tagsClass}}" …>`, the build labels `<span class="tag t-…">` and the gap markers `<span class="k-flag k-blk|k-gap">` unless the gap is resolved;
   - links to other screens are `href="<ScreenId>.dc.html"`;
   - desktop screens are 1440 wide, phones 390 × 844.
5. Look: `DESIGN-NOTES.md`; copy patterns from a screen of the same kind in the same carousel.

## Rebuild (only when the frame, the menu or the screen list changes)
Read every `screens/<id>` back first and write it into the board source (or into the generator), because the db holds edits the boards do not. Then rebuild with `make_carousel.py` and publish to the same URL **without** `capabilities`, so the database and its rules are kept. Seed only new screens.
