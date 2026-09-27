# Test Run console

Design and build a console for the Test Run API. The person using it creates a run, records results, and reads the summary. The API already exists. This task is the screen and the design system behind it.

Take the visual direction you actually want. You may look at existing systems, including glass, Material, or anything else. Use them as reference. The screen should show your own decisions, not a copy of a system you found.

## What you are designing

A single page that talks to the running API.

- Create a run: name and test names.
- Record a result: test, status, duration.
- Show the summary: status, counts, pass rate, duration.
- List existing runs once you add `GET /api/runs`.

The page has to make these states obvious without showing raw JSON:

- No runs yet
- Loading
- A mistake in the form, shown on the field
- API 400, 404, and 500, with the typed input still on the page
- `queued`, `running`, `passed`, `failed`
- Pass, fail, skip, and the pass rate readable at a glance

`running` and `passed` must not look the same. A phone-width layout is part of the design, not a later stretch.

## Design system

Write your system in this file before you polish the page. Keep it short enough that you can change it by hand.

Include:

- The idea in a few sentences. Who the screen is for, and what should feel true about it.
- Color: name each color and where it is used. Status colors are part of the system.
- Type: the families and sizes you actually use, and why.
- Space: the scale you use and what each step is for.
- Surface: background, cards or panels, borders, shadow, blur, or whatever your direction uses instead.
- The components on this page only: field, button, status, list row, summary. For each, the default, the quiet state, and the error or active state.
- Motion, if you use any: what moves, and when it must not run.
- Inspiration: name anything you looked at. For each, say the one decision you kept and the one you refused.
- Three decisions that are yours. A status treatment, a layout choice, and one more. These are the decisions you will be asked to change live.

A look borrowed whole from another system does not pass. A system you can explain and edit does.

## Backend piece

Add `GET /api/runs` so the page can list runs. Document the JSON here first: field names, order, and the body for an empty list. Say why each field is on the list. Then implement it with tests for an empty list and for two created runs.

## Build

After the system above is in this file, implement the page against the API. Use the system you wrote. A form that dumps JSON does not pass.

In the pull request, name the stack and why you chose it. A simple stack you can explain is enough.

AI is allowed for code and for visual drafts. At the bottom of this file, add:

- What you asked the tool for
- What it gave you that you kept
- What you changed by hand so the screen matched the three decisions above

## Out of scope

Login, a database, a component library for its own sake, and extra pages. One screen, one system.
