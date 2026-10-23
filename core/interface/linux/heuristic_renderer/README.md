# Comprehensive Reference Guide: The `heuristic_grid_renderer()` & `render_live_frame()` Engine

The `heuristic_grid_renderer()` module implements an absolute 2D grid compositor and text-wrapping engine for terminal dashboards. By separating UI rendering from decision logic, it enables multi-panel layouts, Z-index sorting, relative stacking flows, and dynamic auto-height resolution.

---

## 1. Core Functions & Signatures

### `heuristic_grid_renderer()`
```python
def heuristic_grid_renderer(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
    width: int | str = 80,
    height: int | str = "auto",
    wrap_text: bool = True,
) -> str:
```

* **`schema`**: A blueprint dictionary defining metadata, absolute/relative section coordinates (`x, y, w, h`), border styles, and entry formatting protocols.
* **`state`**: The transient session state; used for data injection into fields during discovery.
* **`width`**: Column width of the virtual terminal canvas, or `"auto"` to adapt to default sizing.
* **`height`**: Row height of the virtual canvas, or `"auto"` to dynamically compute bounds.
* **`wrap_text`**: If `True`, automatically wraps text exceeding box or section boundaries.

### `render_live_frame()`
```python
def render_live_frame(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
    width: int | str = 80,
    height: int | str = "auto",
    clear_below: int = 0,
) -> str:
```

* **`schema`**: Blueprint dictionary defining layout metadata and sections.
* **`state`**: Transient session state for live telemetry data injection.
* **`width`**: Absolute column width or `"auto"`.
* **`height`**: Absolute row height or `"auto"`.
* **`clear_below`**: Number of extra lines below the canvas to forcefully clear and pad, preventing ghost artifacts.

---

## 2. Predefined Border Styles Matrix

The engine includes built-in character configurations for standard box-drawing frames via `border_styles`:

| Style Name | Top-Left (`tl`) | Top-Right (`tr`) | Bottom-Left (`bl`) | Bottom-Right (`br`) | Horizontal (`h`) | Vertical (`v`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `"single"` | `┌` | `┐` | `└` | `┘` | `─` | `│` |
| `"double"` | `╔` | `╗` | `╚` | `╝` | `═` | `║` |
| `"rounded"` | `╭` | `╮` | `╰` | `╯` | `─` | `│` |
| `"ascii"` | `+` | `+` | `+` | `+` | `-` | `\|` |
| `"heavy"` | `┏` | `┓` | `┗` | `┛` | `━` | `┃` |

---

## 3. Execution Pipeline & Architecture

1. **Z-Index Layer Sorting**: 
   * Sections are sorted by their `z_index` property (defaulting to `0`) before computing dimensions and rendering, allowing precise overlap management.
2. **Relative Stacking Flow (`stack_below`)**: 
   * Automatically resolves dynamic coordinates relative to previous parent bounds when a `stack_below_id` reference is provided.
3. **Dynamic Dimension Resolution (`h="auto"`, `w="auto"`)**: 
   * Calculates content line-wrapping and required heights or widths dynamically to scale containers automatically.
4. **Opaque Masking**: 
   * Clears the exact rectangular footprint of each section prior to rendering text, preventing background bleed-through.
5. **ANSI Line Purging & Live Streaming**: 
   * `render_live_frame()` appends clear-line sequences (`\033[K`) and cursor-homing sequences (`\033[H`) to facilitate flicker-free UI updates.

---

## 4. Practical Code Examples

### Basic Grid Renderer Usage
```python
from interface.heuristic_grid_renderer import heuristic_grid_renderer

schema = {
    "metadata": {
        "task_msg": "System Status Dashboard",
        "info_msg": "All services nominal",
        "prompt": "Press [q] to quit"
    },
    "sections": [
        {
            "id": "sec1",
            "label": "Metrics",
            "x": 2,
            "y": 3,
            "w": 40,
            "h": "auto",
            "border_style": "rounded",
            "entries": [
                {"hotkey": "1", "label": "CPU Usage", "state_ref": "cpu"},
                {"hotkey": "2", "label": "Memory Load", "state_ref": "mem"}
            ]
        }
    ]
}

state = {"cpu": "14%", "mem": "42%"}
output = heuristic_grid_renderer(schema, state=state, width=80, height=20)
print(output)
```

### Relative Stacking (`stack_below`)
```python
schema = {
    "metadata": {"task_msg": "Multi-Panel Dashboard"},
    "sections": [
        {
            "id": "panel_top",
            "label": "Primary Panel",
            "x": 2, "y": 2, "w": 50, "h": 5,
            "border_style": "single",
            "entries": [{"label": "Status: Active"}]
        },
        {
            "id": "panel_bottom",
            "label": "Secondary Panel",
            "stack_below": "panel_top",  # Automatically places this box 1 row below panel_top
            "w": 50, "h": 5,
            "border_style": "heavy",
            "entries": [{"label": "Logs: Clean"}]
        }
    ]
}

print(heuristic_grid_renderer(schema))
```

### Live Flicker-Free Telemetry Loop
```python
import time
from interface.heuristic_grid_renderer import render_live_frame

schema = {
    "metadata": {"task_msg": "Live Telemetry Feed"},
    "sections": [
        {
            "label": "Counter",
            "x": 2, "y": 2, "w": 30, "h": 4,
            "entries": [{"label": "Ticks", "state_ref": "ticks"}]
        }
    ]
}

# Emits ANSI-escaped frames designed for in-place terminal updates
for i in range(5):
    state = {"ticks": str(i)}
    frame = render_live_frame(schema, state=state, width=60, height=10)
    print(frame, end="", flush=True)
    time.sleep(1)
```