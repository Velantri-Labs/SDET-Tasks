# Design note — Test Run console

## The job

One person, mid-test-run, using this on their own machine while they work through a manual or semi-automated test pass. Their one job: go from "I have a list of tests to run" to "I can see, at a glance, whether this run passed" — without ever reading raw JSON.

What should feel true about the screen: it's a console, not a form wizard. Status is the first thing you see, always. Nothing here pretends to be more than what it is — an in-memory API with a screen on it.

## The path

1. **Empty page.** No runs exist yet. The only thing to do is create one.
2. **Create a run.** Name + test names. On success, the run appears in the run list and becomes the selected/active run.
3. **Record results.** For the active run, pick one of its tests, a status, a duration, submit. Repeat per test.
4. **Read the summary.** As results come in, the summary card (status, pass/fail/skip counts, pass rate, total duration) updates. Once every test has a result, status resolves to `passed` or `failed`.

Selecting a different run from the list at any point swaps steps 3-4 to that run; the create-run form is always available alongside the list, not gated behind a separate page.

## States

| State | What's shown |
|---|---|
| No runs yet | Run list shows one line of text ("No runs yet — create one to get started") instead of an empty table. Create-run form is already visible, not hidden behind an extra click. |
| Loading | Skeleton rows in the run list on first load. Submit buttons show a spinner and disable while a request is in flight; the rest of the form stays interactive-looking, not grayed out, so it doesn't read as "broken." |
| Validation error (client-side, before submit) | Sits directly under the offending field, red text, field border turns red. Doesn't block typing in other fields. Nothing is sent to the API. |
| API `400` | A banner directly above the form that was submitted, using the server's own error message. The field values the person typed are untouched — nothing clears. |
| API `404` | Only reachable if a selected run disappears mid-session (there's no delete endpoint today, so this is mostly a "the id in the URL doesn't exist" guard). Shown as a full-panel message in the active-run area — "This run wasn't found" — with a button back to the run list, because a 404 means the *thing itself* is gone, not that one field was wrong. |
| API `500` | Same banner placement as `400`, but deliberately generic copy ("Something went wrong on our end — try again") rather than surfacing server internals. Input is preserved so retry doesn't mean retyping. |
| `queued` | Status pill, blue, static. No results yet. |
| `running` | Status pill, amber, with a slow pulsing dot — the one animated state on the page, so "in progress" is never mistaken for "done." |
| `passed` | Status pill, green, static, plus a small checkmark glyph — not color alone. |
| `failed` | Status pill, red, static, plus a small "×" glyph — same reasoning. |

## Pass / fail / skip / pass rate at a glance

The summary card shows three plain numbers with labels — Passed, Failed, Skipped — not a pie chart or a wall of icons. Next to them, pass rate is shown two ways at once: as a percentage (`67%`) and as a short horizontal bar, so someone skimming the page catches it peripherally without reading the number. Duration is a single total, in seconds if >=1000ms, otherwise ms, formatted rather than raw.

## Pieces

- **RunList** — fetches `GET /api/runs`, renders id/name/status/pass rate per row, handles its own empty/loading states, and reports which run is selected. Doesn't know anything about creating runs or recording results.
- **CreateRunForm** — owns the name + dynamic test-name inputs (add/remove a row), client-side validation, and the `POST /api/runs` call. On success it hands the new run's id up so the page can select it.
- **ActiveRunPanel** — thin wrapper that shows the selected run's name/id and hosts the two pieces below it. Handles the 404 case for a stale/missing selected run.
- **RecordResultForm** — test dropdown scoped to *that* run's test list, status select, duration input, `POST /api/runs/{id}/results`. Owns its own field errors and the 400/500 banner for this specific action.
- **SummaryCard** — pure display component. Takes a summary object as a prop and renders it; re-fetches `GET /api/runs/{id}/summary` after every successful result submission (simplest correct approach — no websockets, no polling loop).
- **ErrorBanner** — one small reusable piece used by both forms, styled by kind (`400` vs `500`) but otherwise dumb: takes a message and a kind, renders itself.

## Desktop and phone width

Desktop: two columns. Left, narrower — run list + create-run form, stacked. Right, wider — the active run panel (record-result form + summary card).

Phone width: single column, stacked top to bottom in this order — **summary card first**, then record-result form, then create-run form, then run list at the bottom. Summary goes first on mobile specifically so the person doesn't have to scroll past two forms to see whether their run passed — that's the one piece of information they're most likely checking one-handed.

## What's left out on purpose

- No editing or deleting a run or a result — the API doesn't support it, so the screen doesn't pretend to either.
- No client-side router/URL-per-run — one page, one piece of local state for "which run is selected."
- No component library — plain HTML/CSS, no Bootstrap/MUI/etc. This is one screen; a library would be more code than the problem needs.
- No light/dark toggle — one mode (dark), chosen and committed to.
- No optimistic UI on result submission — wait for the response, then update. Simpler to reason about and to explain on a call than an optimistic-then-reconcile flow.

---

## Design system

### The idea

This is a working console for one person at a time, not a marketing surface. It should feel like an instrument panel: calm, legible, and quiet until something needs attention — at which point it says so plainly, in text as well as color.

### Color

| Name | Hex | Where it's used |
|---|---|---|
| `bg` | `#0b0d10` | Page background |
| `surface` | `#14171b` | Cards and panels |
| `border` | `#262b31` | Hairline borders on cards, fields, dividers |
| `text-primary` | `#e8eaed` | Headings, values, primary labels |
| `text-muted` | `#8b939d` | Field labels, helper text, secondary metadata |
| `accent` | `#4da3ff` | Primary buttons, links, focus rings — the only "click me" color |
| `status-queued` | `#4da3ff` (blue) | `queued` pill |
| `status-running` | `#e0a53d` (amber) | `running` pill + pulse dot |
| `status-passed` | `#3dd68c` (green) | `passed` pill + checkmark |
| `status-failed` | `#e35d5d` (red) | `failed` pill + banner text, `400`/`500` banners |

Status colors are never reused for anything else on the page (no incidental amber/green/red elsewhere), so a status color always means status.

### Type

One family for everything: the system UI stack (`-apple-system, "Segoe UI", Roboto, sans-serif`) for all prose, labels, and buttons. One monospace family (`ui-monospace, "SF Mono", Menlo, monospace`) for anything that's a token rather than a sentence — test names, run ids, durations, percentages. Two families total, on purpose: the contrast itself does work, marking "this is data" versus "this is UI copy" without an icon.

Sizes: `13px` (helper/meta text), `15px` (body/labels), `18px` (field values, list rows), `24px` (card headings), `32px` (the summary card's own status word). No sizes outside this set.

### Space

4px base scale: `4, 8, 12, 16, 24, 32, 48`. `4`/`8` for inside compact controls (padding inside a pill, gap between a field and its error text). `16`/`24` for the normal gaps between fields and between cards. `32`/`48` for separating the page's major regions. Nothing is spaced by eye — every gap is one of these seven numbers.

### Surface

Flat cards: `surface` fill, single `1px` `border`-colored hairline, `6px` corner radius, no shadow, no blur. Deliberate rejection of glassmorphism/blur here — this page's job is dense, precise status text, and blur softens exactly the thing that needs to stay crisp. Depth is communicated by the border and by spacing, not by elevation effects.

### Components (this page only)

**Field** (text input / select)
- Default: `surface` fill, `border`-colored 1px outline, `text-primary` value, `text-muted` label above it.
- Quiet (focused, valid): outline becomes `accent`, no other change — focus should be visible, not loud.
- Error/active: outline becomes `status-failed`, a line of `status-failed` text appears directly below at `13px`. Value is never cleared.

**Button**
- Default (primary action — Create run, Submit result): `accent` fill, dark text, `6px` radius.
- Quiet (secondary — e.g. "Back to run list"): transparent fill, `border` outline, `text-primary` text.
- Active/error: while a request is in flight, fill dims ~30% and a small inline spinner replaces the label; on failure the button returns to default and the error surfaces in the banner above it, not on the button itself.

**Status** (pill)
- Default: colored dot + label text, `status-*` color, on a `surface` background, `13px` label, rounded full.
- Quiet: none — status is never de-emphasized, it's the one thing on the page that's always at full contrast.
- Active: only `running` has an active variant — the dot pulses (opacity 1 → 0.4 → 1, ~1.6s loop). Every other status is static.

**List row** (run list item)
- Default: name (`15px`, `text-primary`) + status pill + pass rate (`13px`, `text-muted`, monospace), single line, `border`-bottom hairline between rows.
- Quiet (unselected, viewed among others): as above, no background.
- Error/active: selected row gets a left `3px` `accent` bar and a very slightly lighter `surface` background — "active" here means "currently selected," not an error state, since list rows themselves can't error.

**Summary** (card)
- Default: status word large (`32px`) and colored per status, three labeled counts (Passed/Failed/Skipped) in a row beneath it, pass rate as `NN%` next to a short horizontal bar, total duration bottom-right, all in monospace.
- Quiet: before any results exist (`queued`), counts show as `0` and the pass-rate bar is empty rather than hidden — the shape of the card doesn't change between states.
- Error/active: n/a — this component only ever reflects server data; it has no error state of its own (errors belong to the forms that feed it).

### Motion

The only intentional motion on the page is the `running` status pulse described above. Nothing else animates: no page-load fade-ins, no hover-lift on cards, no transition on the summary numbers changing (they just update). This is a deliberate minimum, and it respects `prefers-reduced-motion` by disabling even the pulse (falls back to a static amber dot) for anyone who's set that.

### Inspiration

- **GitHub Actions run list.** Kept: a compact, status-first single-line row is the fastest way to scan many runs. Refused: their color-only status dots — this page always pairs color with a text label and/or glyph.
- **Linear's issue list.** Kept: dense rows with a clear typographic hierarchy (one bold element, everything else quiet) rather than everything competing for attention. Refused: fully-rounded, low-contrast status pills that are hard to tell apart at a glance — this page's status colors are chosen to be distinguishable even in grayscale.

### Three decisions that are mine

1. **Status treatment** — colored pill + text label + glyph, with `running` getting the only animated state (a pulsing dot) specifically so "in progress" is never confusable with "done," including for a colorblind reader.
2. **Layout** — two-column desktop (list+create on the left, active run + results + summary on the right) that collapses to a single column on phone width with the **summary card pulled to the top** of that stack, ahead of the forms — the opposite of simply reflowing the desktop order.
3. **Type pairing** — one humanist sans for UI copy, one monospace strictly for data tokens (ids, test names, durations, percentages), used as a deliberate signal rather than a single font for everything.

---

## Proposed endpoint: `GET /api/runs`

Returns every run, newest first (by descending id), as a JSON array — no wrapper object, consistent with `tests` already being a bare array elsewhere in this API.

**Two runs, `login` created first then `checkout`:**

```json
[
  {
    "id": 2,
    "name": "checkout",
    "status": "queued",
    "total": 3,
    "pass_rate": 0.0
  },
  {
    "id": 1,
    "name": "login",
    "status": "running",
    "total": 2,
    "pass_rate": 1.0
  }
]
```

**No runs:**

```json
[]
```

Field order and reasoning:

- **`id`** — required to link into the run for recording results or fetching its full summary. Without it the list is just decoration.
- **`name`** — the actual thing a person is scanning for. First field after `id` because it's what they read first.
- **`status`** — lets someone find "the run I still need to finish" without opening every row. This is the entire point of a list endpoint over just linking to `/summary` fifty times.
- **`total`** — disambiguates two runs with the same name, and gives a sense of scale (the 3-test smoke run vs. the 20-test full pass) before clicking in.
- **`pass_rate`** — a one-glance health signal for a run that's already resolved, without a second request per row.

Deliberately **not** included: `passed`/`failed`/`skipped`/`duration_ms`. Those are meaningful once you're already looking at one run; putting all of `summary`'s fields here would make this a slower, heavier endpoint that just duplicates `GET /summary` for every row. This endpoint's job is triage and selection, not detail.

---

## AI usage — design phase

Asked Claude to draft this design note against the task brief, covering the required states, component breakdown, and a self-contained design system (color/type/space/surface/components/motion). Kept the state table, the endpoint field reasoning, and the component breakdown largely as drafted — they matched what the API actually returns. Adjusted by hand: the phone-width ordering (summary card first) and the two named "kept/refused" inspiration decisions, since those needed to reflect an actual opinion rather than a plausible-sounding default. The "AI usage — build phase" section (what was kept/changed in the actual code) will be added once the page is built, after this note gets comments.

---

## Stopping point

This is the design note only. No endpoint code and no page code in this PR yet — waiting on comments before building either.
