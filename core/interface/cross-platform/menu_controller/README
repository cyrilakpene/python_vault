# Comprehensive Reference Guide: The `menu_controller()` & `menu_router()` Engine

The `menu_controller()` and `menu_router()` functions serve as the primary navigation hub and lifecycle orchestrator for the terminal interface. By decoupling UI rendering from functional dispatch, they ensure that application flows remain modular, state-aware, and resilient to signature mismatches.

---

## 1. Core Functions & Signatures

### `menu_controller()`
```python
def menu_controller(
    options: dict[str, Callable[..., Any]],
    title: str = "System Orchestrator",
    state: dict[str, Any] | None = None,
    critical: bool = True,
    shorthand: bool = False,
    batch: bool = False,
    template: str | None = None,
    ui_config: dict[str, Any] | None = None,
    allow_back: bool = False,
    renderer: Callable[..., str] = heuristic_ui_renderer,
) -> Any:
```

* **`options`**: A mapping of symbolic keys to resolution vectors (lambdas).
* **`title`**: The primary objective header for the visual buffer.
* **`state`**: Real-time telemetry dictionary for interpolation.
* **`critical`**: If `True`, the controller loops until a valid selection is made.
* **`shorthand`**: Toggle for high-density mnemonic display modes (Grid).
* **`batch`**: Enables multi-selection, returning a list of resolved values.
* **`template`**: The visual blueprint for individual row construction.
* **`ui_config`**: Optional override dictionary for manual UI blueprinting (e.g., column counts, id types, spatial bounds).
* **`allow_back`**: If `True`, dynamically appends a back-navigation option returning a sentinel string `"BACK"` on invocation.
* **`renderer`**: The callable function responsible for rendering the visual buffer.

### `menu_router()`
```python
def menu_router(
    options: dict[str, Callable[..., Any]] | Callable[[], dict[str, Callable[..., Any]]],
    is_main_menu: bool = False,
    returns_value: bool = False,
    **kwargs: Any,
) -> Any:
```

* **`options`**: A mapping of symbolic keys or a parameterless callable factory returning a mapping on every turn.
* **`is_main_menu`**: If `True`, disables back-navigation defaults and handles exit signals.
* **`returns_value`**: If `True`, exits the loop immediately after executing an action and returns its result.
* **`**kwargs`**: Arbitrary keyword arguments forwarded directly to the underlying `menu_controller()`.

---

## 2. Configuration & Parameter Matrix

| Parameter / Key | Type | Default | Description & Behavior |
| :--- | :--- | :--- | :--- |
| `options` | `dict` or `Callable` | *Required* | Maps menu options to functions or resolution lambdas. |
| `title` | `str` | `"System Orchestrator"` | Primary header displayed in the UI buffer metadata. |
| `state` | `dict` or `None` | `None` | Telemetry passed to state-seeking action functions. |
| `critical` | `bool` | `True` | Forces the controller to loop until valid user ingress is provided. |
| `shorthand` | `bool` | `False` | Triggers mnemonic hotkey extraction and 2D grid layouts. |
| `batch` | `bool` | `False` | Allows multi-selection input (e.g., `1, 2` or mnemonic lists). |
| `ui_config` | `dict` or `None` | `None` | Custom overrides for layout properties like `cols`, `id_type`, `w`, `h`, and `acronyms`. |
| `allow_back` | `bool` | `False` | Automatically appends a back-navigation entry (`[b]ack` or `Go Back`). |

---

## 3. Execution Pipeline & Architectural Gates

1. **Null-Set Verification**: 
   * Validates that the `options` mapping is not empty. 
   * Aborts ingress with a warning log if empty, returning `None`.
2. **Mnemonic & Casing Resolution**: 
   * Detects shorthand mode or mnemonic `id_type` configurations. 
   * Extracts hotkeys from brackets (e.g., `[E]xtract`) and processes titles via casing gates and optional `acronym_map` overrides.
3. **UI Blueprinting & Rendering**: 
   * Synthesizes section specifications and layout defaults. 
   * Introspects the renderer's signature to dynamically inject supported arguments (`schema`, `state`, `width`, `height`).
4. **Ingress Validation**: 
   * Delegates data capture to `user_input()`, configuring validation boundaries (`min`/`max` for ordinal numbers, `choices` for mnemonics).
5. **Introspective Functional Dispatch**: 
   * Inspects target function signatures via `inspect.signature`. 
   * Automatically detects if a function wants telemetry state (`wants_state`) and injects the `state` dictionary accordingly.

---

## 4. Practical Code Examples

### Basic Menu Controller Implementation
```python
from interface.menu_controller import menu_controller

def handle_start():
    print("Starting process...")
    return "SUCCESS"

def handle_stop():
    print("Stopping process...")
    return "STOPPED"

options = {
    "Start Service": handle_start,
    "Stop Service": handle_stop,
}

result = menu_controller(options, title="Service Management")
```

### Persistent Sub-Menu with Back Navigation and Batching
```python
from interface.menu_controller import menu_router

def sub_menu_options():
    return {
        "View Status": lambda: print("Status: OK"),
        "Run Diagnostics": lambda: print("Running diagnostics..."),
    }

# menu_router manages infinite looping and stack unwinding via allow_back=True
menu_router(
    options=sub_menu_options,
    title="Diagnostics Menu",
    batch=True,
    shorthand=True
)
```

### Advanced `ui_config` and State Injection
```python
from interface.menu_controller import menu_controller

def state_aware_action(state):
    return f"Processed user: {state.get('user', 'guest')}"

options = {
    "[P]rocess User": state_aware_action,
}

# Advanced configuration blueprint overriding layout defaults
config = {
    "cols": 2,
    "id_type": "mnemonic",
    "width": 80,
    "acronyms": {"User": "USR"}
}

result = menu_controller(
    options=options,
    title="Admin Panel",
    state={"user": "admin_alice"},
    ui_config=config,
    allow_back=True
)
```