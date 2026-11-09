---
name: demo-walkthrough-carousel
description: Turn a Creatio demo script into a clickable walkthrough carousel before anything is built — one screen per demo step drawn as Creatio Freedom UI (client logo, app menu, real data from the script), build labels OOTB / Config / New / Custom / Demo mock, steps per screen (who, Do, What happens, Say, Attention, Issue), a use-case switcher, open questions for the SE, comments right on the screens, published as one Artifact link to discuss the scenario with the SE and then hand it to the consultants. Use when someone hands over a demo script and wants to see or agree how the demo will look, says "прототип", "карусель", "walkthrough", "покажи як це виглядатиме", or wants to check a script with the SE before the build.
---

# Demo walkthrough carousel

You turn a demo script into a clickable prototype: a Design canvas with one board per screen, glued by `make_carousel.py` into one page, published as an Artifact. There are no sample screens in the plugin: client screens never leave the user's computer. The board format is described in step 2.
Talk to the user in their language (Ukrainian by default). On the screens and in the notes, use the language of the demo.

The carousel serves two moments, with the same link:
- **Discussion**: the screens, plus open questions for the SE on the screens where something is unclear.
- **Handover**: once the SE has agreed, the questions are answered and removed, and the consultant leads the demo from the steps above each screen.

Folder of this skill = SKILL_DIR. Work in a new folder WORK, for example `<demo folder>\Build\walkthrough\`, never inside SKILL_DIR.

## 1. Read the script and plan the screens
- Read the whole script. For a .docx, extract the text of word/document.xml with python zipfile. Read the mockups and page layouts too, if it has them.
- Make the **screen list**: one screen per distinct Creatio page the presenter shows, in story order. A list and its record page are two screens. A phone step is its own screen (390×844). The first screen is `Main`: the story, a tile per use case linking to its first screen, the label legend, and "Agreed / open questions" when there is a call to agree on.
- For each screen write down: `id` (CamelCase, no spaces), use case (`UC1`…), a short thumb name, a caption title and one line of description, and which elements need which label:
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
  - `issue` (optional): a known gap or risk in this step, still open on the build side.
- For a long script, put the steps in separate card files per section instead of carousel.json (`cards`, see step 4). Each step then carries `"screen": "<id>"`.
- Collect **open questions for the SE** per screen: everything the script leaves open or contradictory, everything a mockup cannot settle, every "to confirm" in the script. One question per line, answerable by the SE, with no build jargon. A screen without doubts has no questions.
- Show the user the screen list (a short table: screen, UC, what it shows, number of open questions) and wait for an OK before drawing. This is the cheap moment to cut or merge screens.

## 2. Draw the boards (Design canvas)
- `Artifact` with `action: "quickstart"`, `intent: "design"`. Then create the design from its type and follow that type's instructions.
- **Read `SKILL_DIR\DESIGN-NOTES.md` first.** It holds the Freedom UI tokens that make a board read as Creatio: frame, top bar, menu, record page, DCM bar, KPI tiles, Creatio.ai panel, phone.
- **Shared components**, drawn once and imported on every desktop board:
  - `TopBar` (48 px): 9-dot apps button, client logo, play / plus, search, ai / bell / help / gear, avatar;
  - `AppNav`: the app sections. The builder draws it from `nav` in carousel.json, at `nav_width` (220 recommended) with coloured icons from `nav[].color`.
  Desktop boards are 1440 wide; phone boards are 390×844.
- **Data comes from the script**: names, numbers, statuses and sample records exactly as the script gives them. No lorem ipsum, no empty fields, no 0.00.
- **Labels**: `<span class="tag t-ootb">OOTB</span>` (also `t-cfg`, `t-new`, `t-cus`, `t-mock`) next to the element. Put `{{tagsClass}}` on the board's root so the canvas can hide them.
- **Clickable path**: every element the presenter clicks is a link `href="<NextScreenId>.dc.html"`. Each board should have at least one link forward.
- **Static HTML only**: no `<sc-for>` loops and no `{{…}}` bindings other than `{{tagsClass}}`. Write table rows out. The builder refuses anything else.
- **Styles**: put each board's CSS in its `<helmet><style>`. The builder scopes it to that screen: `body` becomes the screen root, and `@media` / `@supports` are scoped too. `@keyframes` and `@font-face` are kept, and any other at-rule is reported and left out. Any class names are fine on boards, because the shell's own classes all start with `wk-` and never touch the screens.
- Show the canvas to the user, take their edits, and only then go on.

## 3. Export the boards to WORK\boards
`Artifact` with `action: "read"`, the design's `url`, and `paths` = every `<id>.dc.html`, plus `TopBar.dc.html`, `AppNav.dc.html` and `canvas.json`. Copy the files it saves into `WORK\boards\`.

## 4. carousel.json and build
Write `WORK\carousel.json` as JSON:
- `title`: the Artifact name, e.g. "<Client> Demo Walkthrough";
- `brand_line` and `headline`: the two lines at the top;
- `app_name`: the name in the left menu;
- `screens[]`: `id`, `uc`, `short`, and optionally `area`, `title`, `desc`, `kind` (`phone` / `desk`), `steps` (list of `{who, do, happens, say, attention, issue}`), `questions` (list of open questions for the SE). The older `click` (list) and `say` (text) per screen still work;
- `cards` (optional): card files, relative to carousel.json. Each is a JSON list of steps with `"screen": "<id>"`. They are appended to that screen's steps;
- `uc_titles` (optional): `{"UC1": "The robot", …}`, the short names on the use-case buttons;
- `step_blocks` (optional): which step blocks to show, e.g. `["who","do","happens"]` when the reviewers want only Do / What happens. The default is all six;
- `layout` (optional): `"bottom-nav"` puts Prev / counter / Next under the screen, next to the strip;
- `nav[]`: `label` (the same text as `active` in the board's AppNav import), `target` screen id, optional SVG `icon` path, optional `color` (rounded-square icon background);
- `nav_width` (optional): the menu width in px, 200 by default, 220 as in DESIGN-NOTES.

Example shape: `{"title":"Contoso Demo Walkthrough","brand_line":"Contoso × Creatio · prototype","headline":"…","app_name":"Contoso Service","screens":[{"id":"Main","uc":"Start","short":"Story"},{"id":"CaseList","uc":"UC1","short":"Cases","title":"UC1 · …","desc":"…","area":"Service","steps":[{"who":"Remote L1","do":"Open Cases, click CS-1042","happens":"The case opens with its SLA timer","say":"…"}],"questions":["Is the L1 queue per site or global?"]}],"nav":[{"label":"Cases","target":"CaseList","color":"#E0533B"}],"nav_width":220,"uc_titles":{"UC1":"Triage"}}`

Then run:
```
python -I -X utf8 "<SKILL_DIR>\make_carousel.py" "<WORK>\boards" "<WORK>\carousel.json" "<WORK>\<Client>-walkthrough.html"
```
It prints the number of steps, use cases and open questions, and lists the screens that have no steps yet. It also reports every problem by name: a missing board, a loop, a broken link, a nav target that is not a screen, a step for an unknown screen, an unknown step field, and a step with neither `do` nor `happens`. Fix the boards or the config and run it again until it says `ok`.

## 5. Check and publish
- Open the html in the browser pane. Click through the whole path with ← → and with the outlined elements. Check the phone screens, the use-case buttons, the steps above each screen and the "Open questions" block, and the toggles (Build labels, Presenter notes, Open questions).
- Publish it with `Artifact` (publish, `file_path` = the html, icon `slides`, `capabilities: {"comments": {"composer_only": true, "customAnchors": true}}`). The capability turns on the comment layer: a **💬 Comment** button; the viewer clicks a field, a table row, a KPI, a DCM stage or a step block (Who / Do / What happens / Say / Attention / Issue), a question line and comments on exactly that. Each comment carries its screen id, block, row and element text, so you know where it belongs. If the publish is refused with `capabilities.comments: unavailable`, drop `"customAnchors": true` and publish again (comments then use the shell's own anchoring, and the button stays hidden).
- Give the user the link and one line: how many open questions there are to go through with the SE. Add that only people the link is shared with at comment level or above can comment, and that sharing is done from the Share menu.
- On changes: edit the board in the design, export it again, rebuild, and publish to the same file path so the link stays the same.

## 6. After the SE call: answers in, then the handover
- The user brings the SE's answers, or asks you to apply the comments on the carousel. To read comments, use the `ArtifactComments` tool on the carousel's URL. Sort each comment: a concrete change goes into the board or the notes; an answer to an open question goes in and the question is removed from `carousel.json`; anything ambiguous, contradictory or changing the scope goes back to the user as a list, not into the boards. A question the SE could not answer stays. Do not reply to or resolve threads in the user's name; offer reply texts instead.
- Rebuild and republish to the same link. When the open-question counter reaches 0 and the user says the scenario is agreed, the carousel is the **consultant version**. Check that every screen has steps (the build prints the screens without them), and fill any that are missing.
- Give the user the link for the consultants and one line: the consultant leads the demo with the use-case buttons and ← →, and reads the steps above each screen.

## Feedback
At the end, add one line for the user. Feedback on the carousel goes to the plugin repository `ValentynArtibiakin/creatio-demo-kit` as an issue with the «Carousel feedback» template: what was wrong, the screen ids, and the kind of demo. The repository is public, so no customer names, people, stand URLs or links to client-confidential carousels. With `gh` installed, Claude can draft it: `gh issue create -R ValentynArtibiakin/creatio-demo-kit --template carousel-feedback.yml`.

## Where the files live
WORK (boards, carousel.json, the built html) stays on the user's computer, in the demo folder. Never commit client screens or scripts to the plugin repository.

## Never
- Real stand screenshots, credentials or customer personal data in the screens.
- «DRAFT» or «UNVERIFIED» stamps in the title or on the screens. Open questions go in `questions` on their screen, never as stamps.
