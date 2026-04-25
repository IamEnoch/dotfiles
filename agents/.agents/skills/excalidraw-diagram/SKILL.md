---
name: excalidraw-diagram
description: >
  Use this skill when the user wants to create visual diagrams that argue a point, explain an
  architecture, or teach a concept. Trigger on: "excalidraw", "visual diagram", "draw an
  architecture", "whiteboard diagram", "visualize this system", "create a diagram showing",
  "concept diagram", or any request for editable hand-drawn-style diagrams. Also trigger when
  the user wants diagrams with code snippets, JSON examples, or evidence artifacts embedded —
  this skill excels at educational technical diagrams. Generates .excalidraw JSON files with
  Playwright-based render-and-validate loop.
version: 0.2.0
---

# Excalidraw Diagram Creator

Generate `.excalidraw` JSON files that **argue visually**, not just display information.

## Before You Start

Read `references/color-palette.md` — it's the single source of truth for all colors. To rebrand, edit only that file.

**First-time setup check:** If you haven't rendered before, run:
```bash
cd references && uv sync && uv run playwright install chromium
```
If this fails, you can still generate `.excalidraw` files — the user can open them in excalidraw.com or the VS Code extension.

---

## Core Philosophy

A diagram isn't formatted text. It's a visual argument showing relationships, causality, and flow that words alone can't express. The shape should BE the meaning.

**Isomorphism Test**: Remove all text — does the structure alone communicate the concept?
**Education Test**: Could someone learn something concrete from this, or does it just label boxes?

---

## Design Process

### Step 0: Assess Depth

| Simple/Conceptual | Comprehensive/Technical |
|-------------------|------------------------|
| Mental models, philosophies | Real systems, protocols, architectures |
| Abstract shapes, labels | Concrete examples, code snippets, real API names |
| ~30 seconds to explain | ~2-3 minutes of teaching |

For technical diagrams: research actual specs before drawing. Use real event names, method names, data formats — not generic placeholders.

### Step 1: Map Concepts to Visual Patterns

Each major concept uses a **different** pattern — no uniform grids:

| Concept behavior | Pattern |
|-----------------|---------|
| Spawns multiple outputs | **Fan-out** (radial arrows) |
| Combines inputs | **Convergence** (arrows merging) |
| Hierarchy/nesting | **Tree** (lines + free-floating text) |
| Sequence of steps | **Timeline** (line + dots + labels) |
| Loops/iteration | **Spiral/Cycle** (arrow returning) |
| Transforms input→output | **Assembly line** (before→process→after) |
| Compares options | **Side-by-side** (parallel) |

### Step 2: Plan Layout Before Generating JSON

Trace how the eye moves through the diagram. Hero elements (300x150) get the most whitespace. Flow left→right or top→bottom.

### Step 3: Generate JSON

Read `references/element-templates.md` for copy-paste templates. Pull colors from `references/color-palette.md`. Full schema: `references/json-schema.md`.

**Container discipline:** Default to free-floating text. Add shapes only when they carry meaning (decisions, processes, focal points). Aim for <30% of text inside containers.

### Step 4: Render & Validate

See the Render & Validate section below.

---

## Large Diagrams

Build JSON **one section at a time** — don't generate the entire file in one pass. Claude's ~32k token output limit makes this a hard constraint, and section-by-section produces better quality anyway.

1. Create base file with JSON wrapper + first section
2. Add one section per edit, using descriptive IDs (`"auth_rect"`, `"arrow_to_db"`)
3. Namespace seeds by section (section 1: 100xxx, section 2: 200xxx)
4. Update cross-section bindings as you go
5. Review the whole for spacing balance before rendering

---

## JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": { "viewBackgroundColor": "#ffffff", "gridSize": 20 },
  "files": {}
}
```

Defaults: `roughness: 0`, `opacity: 100`, `fontFamily: 3`, `fontSize: 16`. The `text` property contains ONLY readable words.

---

## Workspace

Save all intermediate and output artifacts to the skill's workspace directory:

```
.claude/skills/excalidraw-diagram/workspace/
```

Use this for `.excalidraw` JSON files and rendered `.png` outputs. Copy final deliverables to the user's requested location.

## Render & Validate

You can't judge a diagram from JSON. After generating, render to PNG and visually check.

```bash
cd references && uv run python render_excalidraw.py ../workspace/<file>.excalidraw
```

Then Read the PNG and check for:
- Text clipped or overflowing containers
- Elements overlapping
- Arrows crossing through elements or pointing to empty space
- Uneven spacing or lopsided composition
- Text too small to read

Fix issues (widen containers, adjust x/y, add arrow waypoints), re-render. Typically 2-4 iterations.

**Full quality checklist:** `references/quality-checklist.md`

---

## Shape Reference

| Concept | Shape |
|---------|-------|
| Labels, descriptions | free-floating text |
| Timeline markers | small ellipse (10-20px) |
| Start/end points | ellipse |
| Decisions | diamond |
| Processes/actions | rectangle |
| Abstract state | overlapping ellipses |
