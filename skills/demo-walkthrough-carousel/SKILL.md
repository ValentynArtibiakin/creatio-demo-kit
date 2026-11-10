---
name: demo-walkthrough-carousel
description: Turn a Creatio demo script into a clickable walkthrough carousel before anything is built — one screen per demo step drawn as Creatio Freedom UI (client logo, app menu, real data from the script), build labels OOTB / Config / New / Custom / Demo mock, steps per screen (who, Do, What happens, Say, Attention, Issue), a use-case switcher, open questions for the SE, comments right on the screens, published as one Artifact link to discuss the scenario with the SE and then hand it to the consultants. Use when someone hands over a demo script and wants to see or agree how the demo will look, says "прототип", "карусель", "walkthrough", "покажи як це виглядатиме", or wants to check a script with the SE before the build.
---

# Demo walkthrough carousel

You turn a demo script into a clickable prototype: one board per screen, glued by `make_carousel.py` into one page and published as an Artifact. Reviewers can comment on any element, change a screen with Claude, and edit the step text right on the page. There are no sample screens in the plugin: client screens never leave the user's computer.
Talk to the user in their language (Ukrainian by default). On the screens and in the notes, use the language of the demo.

The carousel serves two moments, with the same link:
- **Discussion**: the screens, plus open questions for the SE on the screens where something is unclear, and the gaps and blockers marked on the screens.
- **Handover**: once the SE has agreed, the questions are answered and removed, and the consultant leads the demo from the steps above each screen.

Folder of this skill = SKILL_DIR. Work in a new folder WORK, for example `<demo folder>\Build\walkthrough\`, never inside SKILL_DIR.
The screen generator, the edit layer, the gap badges, the workplace menus and the icon rail come from Philip Shatunov's mock-up skill (0.6.0).

## 1. Read the script and plan the screens
- Read the whole script. For a .docx, extract the text of word/document.xml with python zipfile. Read the mockups and page layouts too, if it has them.
- Make the **screen list**: one screen per distinct Creatio page the presenter shows, in story order. A list and its record page are two screens. A phone step is its own screen (390×844). The first screen is `Main`: the story, a tile per use case linking to its first screen, the label legend, and "Agreed / open questions" when there is a call to agree on.
- For each screen write down: `id` (CamelCase, no spaces), use case (`UC1`…), a short thumb name, a caption title and one line of description, the **workplace** whose menu it shows (Sales, Service, Portal…), and which elements need which label:
  - **OOTB**: standard Creatio, used as is;
  - **Config**: no-code fields, tabs, lists, captions, page rules;
  - **New**: a new object, lookup or process;
  - **Custom**: beyond no-code, such as a tree grid or a PDF viewer;
  - **Demo mock**: hardcoded or visual only.
- Group the use cases into **areas** when the script has them (Marketing / Sales / Service, or the script's own sections). They become the use-case switcher above the screen.
- For each screen write its **steps**, in the script's order. A screen with several script steps gets several steps:
  - `who`: who acts (role, e.g. "Service manager", "Customer"); leave it out when it is the same presenter throughout;
  - `do`: what the presenter does on this screen, with the exact UI names. Quote verbatim any value they type or line they say to the system;
  - `happens`: what the audience sees as a result;
  - `say` (optional): one or two sentences of talk track. Use the script's own talk track when it has one, and never explain the build;
  - `attention` (optional): a real caveat for the presenter, e.g. a background job that takes 10 s, or a step that must be done in a set order;
  - `issue` (optional): a gap or blocker in this step, still open on the build side. Mark the same issue on the screen with a GAP / BLOCKER badge (step 2).
- For a long script, put the steps in separate card files per section instead of carousel.json (`cards`, see step 4). Each step then carries `"screen": "<id>"`.
- Collect **open questions for the SE** per screen: everything the script leaves open or contradictory, everything a mockup cannot settle, every "to confirm" in the script. One question per line, answerable by the SE, with no build jargon. A screen without doubts has no questions.
- Show the user the screen list (a short table: screen, UC, what it shows, number of open questions, gaps) and wait for an OK before drawing. This is the cheap moment to cut or merge screens.

### Optional: read the stand first
When a demo stand with a similar configuration already exists and the user wants the screens to follow it, read it **read-only** before drawing: `SKILL_DIR\reference\stand-check.md` (clio for structure, the browser pane for the look). Ask the user first; they sign in themselves. What the stand shows wins over DESIGN-NOTES; differences from the script become Attention or Issue.

## 2. Draw the boards
**Read `SKILL_DIR\DESIGN-NOTES.md` first.** It holds the Freedom UI tokens that make a board read as Creatio.

### Default: the screen generator
Write `WORK\gen.py`, one `write()` per screen, with the building blocks in `SKILL_DIR\tools\gen_lib.py` (frame, top bars, workplace menu or icon rail, record and home headers, DCM bar, cards, fields, tabs, tables, pills, KPI tiles, charts, timeline, the Creatio.ai panel, GAP / BLOCKER badges):
```python
import sys; sys.path.insert(0, r"<SKILL_DIR>\tools"); import gen_lib as G
G.OUT = r"<WORK>\boards"; import os; os.makedirs(G.OUT, exist_ok=True)
G.topbars()                                    # TopBar.dc.html + TopBar-portal.dc.html (pass logo_html for the client logo)
G.write('CaseRec', 'UC1 · Case at L1', G.desk('Service:Cases|c',
        G.page(G.rec_head('CS-1042'), G.dcm(['New', 'L1', 'Resolved'], 1), G.flags(('gap', 'Telemetry sample missing')))
        + G.twin([G.me('Summarise this case'), G.ai('Arm fault E-4417.', 'Service agent')], 'Service agent', 'Case: CS-1042')))
G.save_canvas('<Client> walkthrough')
```
Run it with `python -I -X utf8 "<WORK>\gen.py"`. Read the function list at the top of `gen_lib.py`; add your own helpers in gen.py rather than editing gen_lib. Rerun after every change; the boards are regenerated.

### Alternative: a Design canvas
When the user wants to draw and adjust the screens visually: `Artifact` with `action: "quickstart"`, `intent: "design"`, create the design from its type and follow its instructions. Shared components drawn once: `TopBar` (and `TopBar-<variant>` for portal users) and `AppNav`, which the builder draws from carousel.json. Then export: `Artifact` `read` with the design's `url` and `paths` = every `<id>.dc.html`, the `TopBar*.dc.html` files and `canvas.json`; copy the saved files into `WORK\boards\`.

### Board rules (both routes)
- Desktop boards are 1440 wide, phone boards 390×844.
- **Data comes from the script**: names, numbers, statuses and sample records exactly as the script gives them. No lorem ipsum, no empty fields, no 0.00.
- **Menu**: `<dc-import name="AppNav" active="<Workplace>:<Item>">` (or `active="<Item>"` with a single `nav`). Add `|c` for the icon rail when the Creatio.ai panel is open. **Top bar**: `<dc-import name="TopBar">`, or `variant="portal"` for portal users.
- **Labels**: `<span class="tag t-ootb">OOTB</span>` (also `t-cfg`, `t-new`, `t-cus`, `t-mock`) next to the element. Put `{{tagsClass}}` on the board's root.
- **Gaps and blockers**: `<div class="k-flags"><span class="k-flag k-blk">BLOCKER · …</span><span class="k-flag k-gap">GAP · …</span></div>` (`gen_lib.flags`), matching the `issue` of the step.
- **Clickable path**: every element the presenter clicks is a link `href="<NextScreenId>.dc.html"`. Each board should have at least one link forward.
- **Static HTML only**: no scripts, no event handlers, no `<sc-for>` loops and no `{{…}}` bindings other than `{{tagsClass}}`.
- **Styles** in each board's `<helmet><style>`. The builder scopes them to that screen: `body` becomes the screen root, `@media` / `@supports` are scoped too, `@keyframes` and `@font-face` are kept, any other at-rule is reported. Any class names are fine on boards; the shell's own classes all start with `wk-`.
- Show the user a few key screens (the browser pane on the built page, step 4) and take their edits before going on.

## 3. carousel.json
Write `WORK\carousel.json` as JSON:
- `title`: the Artifact name, e.g. "<Client> Demo Walkthrough";
- `brand_line` and `headline`: the two lines at the top;
- `screens[]`: `id`, `uc`, `short`, and optionally `area`, `title`, `desc`, `kind` (`phone` / `desk`), `steps` (list of `{who, do, happens, say, attention, issue}`), `questions` (open questions for the SE). The older `click` (list) and `say` (text) per screen still work;
- `cards` (optional): card files, relative to carousel.json, each a JSON list of steps with `"screen": "<id>"`;
- `uc_titles` (optional): `{"UC1": "The robot", …}`, the short names on the use-case buttons;
- `step_blocks` (optional): which step blocks to show, e.g. `["who","do","happens"]`. The default is all six;
- `layout` (optional): `"bottom-nav"` puts Prev / counter / Next under the screen;
- `navsets`: one menu per workplace, `{"Service": {"title": "Service", "items": [{"label": "Home", "target": "Main", "color": "#1F6FD6"}, …]}, …}`; a board's `active="Service:Home"` picks it. A single-menu demo can use `app_name` + `nav[]` instead (`label`, `target`, optional SVG `icon` path, `color`);
- `nav_width` (optional): the menu width in px, 220 by default;
- `seed_dir`: `"seed"`. The builder writes the editable source of every screen there (`screens-seed/`, `steps-seed/`) for the edit layer.

Then run:
```
python -I -X utf8 "<SKILL_DIR>\make_carousel.py" "<WORK>\boards" "<WORK>\carousel.json" "<WORK>\<Client>-walkthrough.html"
```
It prints the number of steps, use cases and open questions, the seed batches, and the screens that have no steps yet. It reports every problem by name: a missing board, a loop, a broken link, a nav target that is not a screen, a missing top-bar variant, a step for an unknown screen, an unknown step field, a step with neither `do` nor `happens`. Fix and run again until it says `ok`.

## 4. Check
- Open the html in the browser pane. Click through the whole path with ← → and with the screen links. Check the phone screens, the use-case buttons, the steps above each screen, the open questions, **Gaps & blockers** (it walks the screens with an issue or a badge), and the toggles. Show clickable and Build labels start unchecked.
- **Mock test of the edit layer, before every first publish and after any change to the shell:**
  ```
  python -I -X utf8 "<SKILL_DIR>\tools\mock_test.py" "<WORK>\<Client>-walkthrough.html" "<WORK>\seed"
  python -I -m http.server 8765 --bind 127.0.0.1 -d "<WORK>\seed"      (in the background)
  ```
  Open `http://localhost:8765/.test-mock.html?run=1#<a screen with steps>` and run the contents of `SKILL_DIR\tools\mock_check.js` in the page: it must return `pass: true`. It changes a screen, undoes it, edits the steps, and throws hostile HTML and CSS at the page (event handlers, `javascript:` links, iframes, `@import`, `url()`) from Claude and from the db; none of it may survive. Then `?run=2&can=false` (no Edit button; Claude's change stays local with a note) and `?run=3&fail=1` (the orange bar with Discard). Stop the server and run `mock_test.py --clean "<WORK>\seed"`.

## 5. Publish, seed, share
- Load the `artifact-capabilities` skill, then publish with `Artifact` (publish, `file_path` = the html, icon `slides`, `capabilities` = the contents of `SKILL_DIR\reference\capabilities.json`). That turns on:
  - **comments**: a **💬 Comment** button; the viewer clicks a field, a table row, a KPI, a DCM stage, a step block or a question line and comments on exactly that;
  - **db**: screens and step texts live in the artifact's database, so changes show for everyone without a rebuild. Write access is `interact` (Contributor);
  - **user** and **sample**: **Change with Claude** on each screen runs on the viewer's own Claude, with voice input, autosave, Undo and Versions, and **Edit step text** for a manual edit.

  If a capability is refused as unavailable, drop it and publish again: without `db` the page is a static carousel with comments; without `customAnchors` comments use the default anchoring.
- **Seed the db** with `ArtifactData` on the new URL, in batches as the builder printed them: for every screen `set screens/<id>` and `set screens_original/<id>` with the content of `seed\screens-seed\<id>.json`, then `set steps/<id>` with `seed\steps-seed\<id>.json`. Read one screen back to check. Until the seed is written the page shows the built screens and the edit buttons have nothing to save into.
- **Sharing:** by default the user shares the link from the Share menu with **specific people** at **Contributor (Can interact)**, so they can comment and change screens; reviewers who should only look get Commenter or Viewer. Org-wide access only when the user asks for it. Claude never changes sharing itself.
- Fill `SKILL_DIR\reference\HOW-TO-EDIT.md` (title, link, demo, numbers of use cases and screens) into `WORK\HOW-TO-EDIT.md` and give the user its text to send with the link.
- Give the user the link and one line: how many open questions and how many gaps / blockers there are to go through with the SE.

## 6. After the SE call: answers in, then the handover
- Reviewers may have changed screens and steps on the page already; those live in the db. To make a change yourself, follow `SKILL_DIR\reference\EDIT-SCREENS.md` (ArtifactData, with a `screen_versions` copy first). Read comments with `ArtifactComments`. Sort each comment: a concrete change goes into the screen or the steps; an answer to an open question goes in and the question is removed from `carousel.json`; anything ambiguous, contradictory or changing the scope goes back to the user as a list. A question the SE could not answer stays. Do not reply to or resolve threads in the user's name; offer reply texts instead.
- **Rebuild only when the frame, a menu, the questions or the screen list change.** First read every `screens/<id>` and `steps/<id>` back and carry the edits into gen.py / the boards and carousel.json, because a rebuild starts from them. Publish to the same URL **without** `capabilities` (that keeps the db and its rules), and seed only the new screens.
- When the open-question counter reaches 0 and the user says the scenario is agreed, the carousel is the **consultant version**. Check that every screen has steps, and that the remaining gaps are real. Give the user the link for the consultants and one line: the consultant leads the demo with the use-case buttons and ← →, and reads the steps above each screen.

## Feedback
At the end, add one line for the user. Feedback on the carousel goes to the plugin repository `ValentynArtibiakin/creatio-demo-kit` as an issue with the «Carousel feedback» template: what was wrong, the screen ids, and the kind of demo. The repository is public, so no customer names, people, stand URLs or links to client-confidential carousels. With `gh` installed, Claude can draft it: `gh issue create -R ValentynArtibiakin/creatio-demo-kit --template carousel-feedback.yml`.

## Where the files live
WORK (gen.py, boards, carousel.json, seed, stand-specs, the built html) stays on the user's computer, in the demo folder. Never commit client screens, scripts or stand notes to the plugin repository.

## Never
- Real stand screenshots, credentials or customer personal data in the screens.
- Scripts, event handlers or external URLs in a screen: the page strips them, and they have no place in a prototype.
- Changing the stand during the read-only pass, or typing a password.
- «DRAFT» or «UNVERIFIED» stamps in the title or on the screens. Open questions go in `questions`, gaps in `issue` and the badges.
