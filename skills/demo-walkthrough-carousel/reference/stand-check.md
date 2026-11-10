# Optional: read the demo stand before drawing (read-only)

Use it when a stand with the client's or a golden configuration already exists, so the screens follow what the stand really shows. Nothing on the stand is changed.

## A. clio (structure and data)
- `list-environments`, pick the stand. Credentials are stored in clio; you never see or type them. If the stand is not registered, ask the user to register it.
- Read clio's `get-guidance` core-rules and routing first.
- `get-page` gives the merged page bundle: header buttons, DCM stages, columns, cards with fields, tabs, widgets, list columns.
- Record ids and values: `odata-read` with structured filters, `select` and `top`.
- For a big stand, brief read-only subagents per area: never compile, install, run processes or open a browser; write compact specs (< 120 lines each) into `WORK\stand-specs\<PageSchema>.md`, marking guesses `[unv]`.

## B. Browser pass (look)
- Open the stand in the browser pane and ask the user to sign in. Never type passwords and never sign out; if a second user is needed (a portal user, for example), the user switches accounts.
- Viewport 1440 × 900. Write `WORK\stand-specs\visual-notes.md` page by page: frame, header buttons, DCM colours, left cards, tabs, widgets with their values, list columns and first rows.
- Safe: open pages, switch tabs, open and close side panels, read text. **Not safe:** Save, Start, Launch, Approve / Reject, anything that creates a record or a session, changing list folders or saved filters on a shared login, Run process.

## C. What goes into the walkthrough
- Menus, page titles, tab names, button and field captions, DCM stages and colours, widget titles, record names and numbers as the stand shows them.
- Differences from the script (another caption, a missing tab or column, conflicting numbers) become an **Attention** or **Issue** on the step and a GAP / BLOCKER badge on the screen (`gen_lib.flags`).
- A gap the stand disproves is removed.
- `WORK\stand-specs\` stays on the user's computer, like the rest of WORK.
