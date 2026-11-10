# Freedom UI look — design notes for the boards

Read this before drawing the boards (SKILL.md, step 2). These tokens make a board read as Creatio rather than a generic web page. Match them; do not copy any client's real screens.

## Frame
- **App frame:** dark navy to almost black (`#0B1530` → `#05070D`), with a soft magenta glow in the top-right corner (`radial-gradient(… rgba(214,51,160,.35) …)`). The work area is a light grey sheet (`#F0F2F5`) with a 10 px top-left radius.
- **Top bar (TopBar, 48 px):** left to right:
  - 9-dot apps button;
  - client logo (white or full colour on dark);
  - round play and plus buttons;
  - search field (dark translucent, "Search…");
  - flexible gap;
  - chat status dot;
  - icons «ai», bell (with a red dot if the story has notifications), help, gear;
  - avatar.

  Icons are white, 20 px.
- **Left menu (AppNav):**
  - 220 px wide (`"nav_width": 220` in carousel.json);
  - "Search app…" field, then the workspace name with a ▾;
  - items with a 26 px coloured rounded-square icon (`nav[].color`) and a white label 14 px / 600;
  - the active item has a translucent white background.
  - Typical colours: green `#2E8B2E`, red-orange `#E0533B`, blue `#1565C0`, purple `#7B4DFF`, teal `#00897B`, amber `#F5A623`.

## Type
Montserrat (headings, buttons) and Roboto (body); 14 px body, 12 px labels in `#5B6576`; record titles 20–22 px / 500 in `#0D2E4E`.

## Record page
- **Header:** ← back arrow and the record title; to the right "Add tag", "Close and lock" and the action buttons (primary blue `#0050D8`).
- Under the title, a row of links or chips (owner, account, status).
- **DCM bar:** chevron stages; passed stages green `#2E8B2E` with white text; the current stage light green `#B9DDB9` / `#1B5E20`; future stages grey `#D9DCE1`.
- **Body:** a left column of fields (label above, value below, 8 px gaps); on the right, tabs in UPPERCASE 12 px / 500 blue `#1565C0`. The active tab has a 2 px orange-red underline `#E0533B`.
- **Cards:** white, 6 px radius, border `#E6E8EC`, shadow `0 1px 3px rgba(13,46,78,.06)`; card titles 15 px / 500 `#0D2E4E`.
- **Lists:** header row 12 px / 500 grey, rows 14 px, row border `#EEF0F3`. Status badges are coloured pills.

## Home page / dashboard
- **KPI tiles:** small grey caption above, a large value 28 px / 700 in the metric's colour (green good, red bad, blue neutral), and a sub-line with the period.
- List widgets have a coloured title strip. Charts sit in white cards.

## Creatio.ai panel
Right-hand panel, white, 360–400 px:
- **User message:** a "You · 10:42" meta line, then a light bubble with the text.
- **Agent reply:** plain text (no bubble) with a ✦ sparkle meta line («Creatio.ai · agent name»).
- **Chips:** purple outline (`#DCCDF7` / `#5B2DB3`).
- **Composer at the bottom:** a context chip (the open record, e.g. «Case: CS-1042»), an agent pill, and a send button.

## Phone (390 × 844)
- Status bar, then the app header with ← and the title.
- Fields full width, the label above each.
- A sticky primary action at the bottom.
- The same palette and type.

## Labels on the boards
Build labels (`tag t-ootb / t-cfg / t-new / t-cus / t-mock`) go right next to the element they describe, never on top of data. Keep them small (10 px uppercase) so they can be hidden with the "Build labels" toggle without changing the layout.

## More from real stands (0.6.0, after Philip Shatunov)
Defaults only: when a stand exists, read it first (`reference/stand-check.md`) and the stand wins. `tools/gen_lib.py` draws all of this.
- **Top-bar variants:** internal users get the full bar; **portal users** (dealers, customers) have no chat pill and no ai / agent / gear icons, only apps, bell, help and avatar. Draw them as `TopBar-<variant>.dc.html` and pick with `<dc-import name="TopBar" variant="portal">` (`gen_lib.topbars()`, `desk(..., topbar='portal')`).
- **Workplaces:** each role has its own menu (`navsets` in carousel.json); the first item is usually **Home**. A board picks it with `active="<Workplace>:<Item>"`.
- **Icon rail:** when a record opens with the Creatio.ai panel on the right, the menu collapses to a ~52 px rail (›, grid, coloured icons). Use `active="<Workplace>:<Item>|c"`.
- **Record header, row 2:** "Add tag" on the left; on the right, links that toggle side panels (Next steps, Feed, Attachments…). Object buttons sit left of "Close": green, blue or outlined, with an icon.
- **DCM colour per object:** green for opportunities and cases, violet for quotes, blue for orders, orange for leads and registrations. The current stage has ▾ (`gen_lib.dcm(..., color=…)`).
- **Left cards:** approvals with green ✓ / red ✕ and Positive / Negative / Pending counters; SLA cards with a green clock timer ("1d 22hr").
- **Lists:** toolbar (+ ⟳ ⋮ 🔍) and a summary line "Count · Quantity (Sum) · Total (Sum)".
- **Home pages:** title as the stand writes it ("<Name> home page"); uppercase 12 px tabs with a small icon; a greeting card "Hello <Name>!" with small outlined buttons on portal and partner homes; line, bar, donut and funnel widgets.
- **AI panel (400 px):** header icons; the empty state is an orange logo square with "Ask or build with AI"; the composer has a context chip, "Ask anything", an agent pill with an orange icon, mic and a round send (`gen_lib.twin`, `twin_empty`).
- **Gap and blocker badges:** red BLOCKER / amber GAP badges in the bottom-right corner of the screen (`gen_lib.flags`). They are what the **Gaps & blockers** button counts, together with the steps that have an `issue`.
- **Customer-facing pages** (landing pages, chat widgets) use the customer's brand, not the Creatio frame.
