# Excalidraw JSON Schema

## Element Types

| Type | Use For |
|------|---------|
| `rectangle` | Processes, actions, components |
| `ellipse` | Entry/exit points, external systems |
| `diamond` | Decisions, conditionals |
| `arrow` | Connections between shapes |
| `text` | Labels inside or outside shapes |
| `line` | Non-arrow connections, structural lines |
| `frame` | Grouping containers |

## Common Properties

All elements share these:

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier (use descriptive names like `"auth_rect"`) |
| `type` | string | Element type |
| `x`, `y` | number | Position in pixels |
| `width`, `height` | number | Size in pixels |
| `strokeColor` | string | Border color (hex) |
| `backgroundColor` | string | Fill color (hex or `"transparent"`) |
| `fillStyle` | string | `"solid"`, `"hachure"`, `"cross-hatch"` |
| `strokeWidth` | number | 1, 2, or 4 |
| `strokeStyle` | string | `"solid"`, `"dashed"`, `"dotted"` |
| `roughness` | number | 0 (smooth), 1 (default), 2 (rough) |
| `opacity` | number | 0-100 (always use 100) |
| `seed` | number | Random seed for roughness rendering |
| `angle` | number | Rotation in radians (usually 0) |
| `version` | number | Element version (1) |
| `versionNonce` | number | Version nonce (random int) |
| `isDeleted` | boolean | `false` |
| `groupIds` | array | Group membership IDs |
| `boundElements` | array/null | Elements bound to this one |
| `link` | string/null | URL link |
| `locked` | boolean | `false` |

## Text-Specific Properties

| Property | Description |
|----------|-------------|
| `text` | The display text (ONLY readable words) |
| `originalText` | Same as `text` |
| `fontSize` | Size in pixels (16-20 recommended) |
| `fontFamily` | 3 for monospace (use this) |
| `textAlign` | `"left"`, `"center"`, `"right"` |
| `verticalAlign` | `"top"`, `"middle"`, `"bottom"` |
| `containerId` | ID of parent shape (null for free-floating) |
| `lineHeight` | 1.25 |

## Arrow-Specific Properties

| Property | Description |
|----------|-------------|
| `points` | Array of `[x, y]` coordinates relative to element origin |
| `startBinding` | Connection to start shape |
| `endBinding` | Connection to end shape |
| `startArrowhead` | `null`, `"arrow"`, `"bar"`, `"dot"`, `"triangle"` |
| `endArrowhead` | `null`, `"arrow"`, `"bar"`, `"dot"`, `"triangle"` |

## Binding Format

```json
{
  "elementId": "shapeId",
  "focus": 0,
  "gap": 2
}
```

## Container boundElements

When a text element is inside a shape, the shape needs:
```json
"boundElements": [{"id": "text_id", "type": "text"}]
```

## Rectangle Roundness

```json
"roundness": { "type": 3 }
```
