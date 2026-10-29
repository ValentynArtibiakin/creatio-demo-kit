---
name: demo-walkthrough-carousel
description: Turn a Creatio demo script into a clickable walkthrough carousel before anything is built — one screen per demo step drawn as Creatio Freedom UI (client logo, app menu, real data from the script), build labels OOTB / Config / New / Custom / Demo mock, captions per step, published as one Artifact link to review the scope with the SE. Use when someone hands over a demo script and wants to see or agree how the demo will look, says "прототип", "карусель", "walkthrough", "покажи як це виглядатиме", or wants to check a script with the SE before the build.
---

# Demo walkthrough carousel

You turn a demo script into a clickable prototype: a Design canvas with one board per screen, glued by `make_carousel.py` into one page, published as an Artifact. There are no sample screens in the plugin: client screens never leave the user's computer. The board format is described in step 2.
Talk to the user in their language (Ukrainian by default). On the screens, use the language of the demo.

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
- Show the user the screen list (a short table) and wait for an OK before drawing. This is the cheap moment to cut or merge screens.

## 2. Draw the boards (Design canvas)
- `Artifact` with `action: "quickstart"`, `intent: "design"`. Then create the design from its type and follow that type's instructions.
- **Shared components**, drawn once and imported on every desktop board:
  - `TopBar` (46 px): the client logo, the global search, the user avatar;
  - `AppNav` (200 px left menu): the app sections.
  Desktop boards are 1440 wide; phone boards are 390×844.
- **The look of Creatio Freedom UI**:
  - dark gradient app frame, light grey work area, white cards with 6 px radius;
  - Montserrat/Roboto, blue links, tabs in upper case;
  - a stage path for DCM;
  - lists with column headers;
  - the Creatio.ai panel as a white card with purple chips.
- **Data comes from the script**: names, numbers, statuses and sample records exactly as the script gives them. No lorem ipsum, no empty fields, no 0.00.
- **Labels**: `<span class="tag t-ootb">OOTB</span>` (also `t-cfg`, `t-new`, `t-cus`, `t-mock`) next to the element. Put `{{tagsClass}}` on the board's root so the canvas can hide them.
- **Clickable path**: every element the presenter clicks is a link `href="<NextScreenId>.dc.html"`. Each board should have at least one link forward.
- **Static HTML only**: no `<sc-for>` loops and no `{{…}}` bindings other than `{{tagsClass}}`. Write table rows out. The builder refuses anything else.
- Show the canvas to the user, take their edits, and only then go on.

## 3. Export the boards to WORK\boards
`Artifact` with `action: "read"`, the design's `url`, and `paths` = every `<id>.dc.html`, plus `TopBar.dc.html`, `AppNav.dc.html` and `canvas.json`. Copy the files it saves into `WORK\boards\`.

## 4. carousel.json and build
Write `WORK\carousel.json` as JSON:
- `title`: the Artifact name, e.g. "<Client> Demo Walkthrough";
- `brand_line` and `headline`: the two lines at the top;
- `app_name`: the name in the left menu;
- `screens[]`: `id`, `uc`, `short`, and optionally `title`, `desc`, `kind` (`phone` / `desk`);
- `nav[]`: `label` (the same text as `active` in the board's AppNav import), `target` screen id, optional SVG `icon` path.

Example shape: `{"title":"Contoso Demo Walkthrough","brand_line":"Contoso × Creatio · prototype","headline":"…","app_name":"Contoso Service","screens":[{"id":"Main","uc":"Start","short":"Story"},{"id":"CaseList","uc":"UC1","short":"Cases","title":"UC1 · …","desc":"…"}],"nav":[{"label":"Cases","target":"CaseList"}]}`

Then run:
```
python -I -X utf8 "<SKILL_DIR>\make_carousel.py" "<WORK>\boards" "<WORK>\carousel.json" "<WORK>\<Client>-walkthrough.html"
```
It reports every board problem by name: a missing file, a loop, a broken link, a nav target that is not a screen. Fix the boards or the config and run it again until it says `ok`.

## 5. Check and publish
- Open the html in the browser pane. Click through the whole path with ← → and with the outlined elements. Check the phone screens and switch the "Build labels" toggle.
- Publish it with `Artifact` (publish, `file_path` = the html, icon `slides`). Give the user the link and one line on what to review with the SE.
- On changes: edit the board in the design, export it again, rebuild, and publish to the same file path so the link stays the same.

## Feedback
At the end, add one line for the user. Feedback on the carousel goes to the plugin repository `ValentynArtibiakin/creatio-demo-kit` as an issue with the «Carousel feedback» template: what was wrong, the screen ids, and the kind of demo. The repository is public, so no customer names, people, stand URLs or links to client-confidential carousels. With `gh` installed, Claude can draft it: `gh issue create -R ValentynArtibiakin/creatio-demo-kit --template carousel-feedback.yml`.

## Where the files live
WORK (boards, carousel.json, the built html) stays on the user's computer, in the demo folder. Never commit client screens or scripts to the plugin repository.

## Never
- Real stand screenshots, credentials or customer personal data in the screens.
- «DRAFT» or «UNVERIFIED» stamps in the title or on the screens. The open questions go on the Main screen as "Open questions".
