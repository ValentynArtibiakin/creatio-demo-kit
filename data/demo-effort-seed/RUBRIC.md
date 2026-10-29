# Scope rubric — how to count a demo script

Read the whole script: for a .docx, extract the text of word/document.xml with python zipfile, plus any object, process or page specs next to it. Read-only.

Count what has to be BUILT to run the script. A scope file (`scopes/<demo>.json`) holds these keys; give a number for each, 0 when absent:
- `use_cases`, `new_objects`, `extended_objects`, `lookups`, `pages`, `mobile_pages`, `dashboards`;
- `processes`, `dcm`, `ai_skills`, `studio_agents`, `studio_tools`;
- `landings`, `emails`, `printables`, `custom_components`, `csharp` (0/1), `integrations`;
- `second_language` (0/1), `rtl` (0/1).
Plus `demo` (a short label), `era` (`plugin` / `team` / `pre-plugin`), `risks` (keys from `catalogue.json` → `risks`), `co_builder` (true/false), and `_notes` (uncertain counts).

## Counting rules v2 (2026-10-22) — apply exactly, to history and to new scripts alike
Count what has to be BUILT to run the script, by build intent, not by mockup granularity. When the script and its build spec disagree, the build spec wins; note the disagreement.

- **use_cases**: as the script numbers them. Sub-parts (2a/2b, 4a/4b) are not separate.
- **new_objects**: new entity schemas that store records, incl. detail and junction objects. A pair (template + item) = 2. Not lookups. A stock object reused as is = 0.
- **extended_stock_objects**: stock objects that get new columns or details.
- **new_lookups**: new reference lists only (name + a few fields, managed under Lookups) that the build spec names, plus dropdowns whose values are listed as a NEW list. A dropdown on an existing/stock lookup = 0. Adding values to an existing lookup = 0. A Yes/No field = 0.
- **new_pages**: Freedom UI form, list and modal/dialog pages that are created or substantially changed. A new section = list + form = 2. A tab added to an existing page = 0 (it is part of that page).
- **mobile_pages**: mobile app pages (one per object screen set).
- **dashboards_homepages**: dashboards and home pages. A kanban board is a custom component unless it is a stock kanban view.
- **business_processes**: each named process (P1, P2…) = 1. Each [Auto] behaviour or button action that needs its own process and is not covered by a named one = 1. Branches, rules and steps inside one process = 0. Page business rules = 0.
- **dcm_cases**: each DCM case schema.
- **ai_skills**: each distinct Creatio.ai skill as the build spec lists them (A1, A2…). One skill with two buttons = 1 unless the spec splits it.
- **studio_agents / studio_tools**: AI Studio agents; MCP or process tools published for them.
- **landing_pages_or_portals, email_templates, printables**: templates explicitly required. In-app notifications = 0.
- **custom_components**: UI that stock Freedom UI components plus configuration cannot render: tree grids, PDF viewer with highlight, live countdown widgets, custom kanban, dynamic forms generated from templates, step-by-step mobile wizards. One per distinct component, even if used on several pages.
- **csharp**: true if any C# source schema is needed.
- **integrations**: external systems or channels (telephony, WhatsApp, voice, external APIs) and file-import pipelines (Excel/CSV import into objects). An AI skill reading an attachment is part of that skill, not an integration.
- **mobile offline / barcode scan, demo-mode row limit, cloned stand**: these are risks, not counts. Put them in notes.
