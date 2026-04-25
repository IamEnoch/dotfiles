# Excalidraw Quality Checklist

Run through after rendering. If any item fails, fix and re-render.

## Depth & Evidence (Technical Diagrams)
1. Research done — actual specs, formats, event names looked up?
2. Evidence artifacts — code snippets, JSON examples, real data included?
3. Multi-zoom — summary flow + section boundaries + detail?
4. Real content — not just labeled boxes?
5. Educational value — could someone learn from this?

## Conceptual
6. Isomorphism — visual structure mirrors concept behavior?
7. Argument — shows something text alone couldn't?
8. Variety — different pattern per major concept?
9. No uniform card grids?

## Container Discipline
10. Minimal containers — could any boxed element work as free text?
11. Lines as structure — trees/timelines use lines + text, not boxes?
12. Typography hierarchy — font size and color create hierarchy?

## Structural
13. Every relationship has an arrow or line?
14. Clear visual flow path?
15. Important elements larger and more isolated?

## Technical JSON
16. `text` contains only readable words?
17. `fontFamily: 3`?
18. `roughness: 0` (unless hand-drawn requested)?
19. `opacity: 100` for all elements?
20. <30% text in containers?

## Visual Validation (Render Required)
21. Rendered to PNG and inspected?
22. No text overflow?
23. No overlapping elements?
24. Even spacing?
25. Arrows land correctly?
26. Readable at export size?
27. Balanced composition?
