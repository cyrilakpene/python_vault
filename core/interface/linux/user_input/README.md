# Comprehensive Reference Guide: The `user_input()` Engine

The `user_input()` function serves as an architectural gatekeeper and sanitization firewall for human-to-machine data transfer. By decoupling data definitions (the schema) from collection logic, it ensures that all inbound state changes are validated, type-casted, and normalized before reaching core application logic.

---

## 1. Core Function Signature & Parameters

```python
def user_input(
    schema: list[dict[str, Any]], silent: bool = False, critical: bool = False
) -> dict[str, Any]:
```

* **`schema`**: A list of dictionaries defining the structure, type, and rules for each required input.
* **`silent`**: A global boolean override that suppresses non-essential feedback during the collection process.
* **`critical`**: An enforcement flag where the engine loops indefinitely until valid data is provided for required fields if set to `True`.

---

## 2. Schema Key & Option Matrix

Every field dictionary within the schema list can accept a combination of core identifiers, type casting definitions, input handlers, boundary limits, and dynamic parameters.

### Core Identification & Behavior Keys
* **`key`**: Unique identifier string for the resulting dictionary field (defaults to `"unknown"`).
* **`label`**: Human-readable label displayed during the terminal prompt (defaults to the value of `key`).
* **`default`**: Fallback value applied if the user input is empty or if casting fails in non-critical mode.
* **`critical`**: Field-level enforcement flag that overrides the global function-level critical setting.

### Type Casting Options (`cast`)
The `cast` key determines how the input string is parsed and transformed. Supported options include:
* Primitive types: `"str"`, `"int"`, `"float"`, `"bool"`
* Collections: `"list_str"`, `"list_int"`, `"list_float"`, `"tuple_str"`, `"tuple_int"`, `"tuple_float"`
* Specialized types: `"path"`, `"timestamp"`, `"password"`

### Input Handlers (`input`) & Layout Keys
The `input` key selects the interactive mechanism used to gather data.
* `"default"`: Standard terminal text input.
* `"password"`: Hidden text prompt using `getpass`.
* `"select"`: Interactive 2D grid arrow/WASD option selector.

### Validation & Boundary Keys
* **`min`**: Lower bound constraint for numeric magnitudes, string lengths, or collection sizes.
* **`max`**: Upper bound constraint for numeric magnitudes, string lengths, or collection sizes.
* **`choices`**: List of discrete permitted values which can be scalars or dictionaries with a `"name"` key.

### Dynamic Caster Parameters (Advanced Reflection)
Because the engine uses signature reflection (`_resolve_caster`), any keyword argument accepted by a specific underlying caster function can be passed directly inside the schema dictionary. 
* For **paths (`cast="path"`)**:
  * **`is_file`**: Boolean enforcement ensuring the target path points to an actual file rather than a directory.
* For **passwords (`cast="password"`)**:
  * **`min_len`**: Minimum character length required.
  * **`is_new`**: Flag indicating whether to enforce creation complexity rules or authentication attempt limits.
  * **`attempt`**: 1-indexed counter tracking active password verification attempts.
  * **`max_retries`**: Maximum allowable authentication retries before raising a terminal error.
  * **`require_uppercase`**: Flag mandating at least one uppercase letter for new credentials.
  * **`require_number`**: Flag mandating at least one numeric digit for new credentials.
  * **`require_special`**: Flag mandating at least one special character for new credentials.
  * **`store_hash`**: Flag returning a salted PBKDF2 hash instead of plaintext.
  * **`verifier`**: Optional custom callable taking a password string and returning a boolean verification status.
* For **select options (`input="select"`)**:
  * **`cols`** Takes the number of rows the option menu should be rendered with.

---

## 3. Comprehensive Schema Examples

The following examples demonstrate how to construct schema dictionaries utilizing every available feature:

### Core Identification, Labeling, and Defaults
```python
{
    "key": "username",
    "label": "Enter your username",
    "cast": "str",
    "default": "guest_user",
    "critical": False
}
```

### Complete Range of Casting Types (`cast`)
```python
# Strings, Numbers, and Booleans
{"key": "name", "cast": "str"}
{"key": "age", "cast": "int", "default": 25}
{"key": "score", "cast": "float", "default": 98.6}
{"key": "agree", "cast": "bool", "default": True}

# Collections (Lists and Tuples)
{"key": "tags", "cast": "list_str", "default": ["python", "code"]}
{"key": "ids", "cast": "list_int", "default": [1, 2, 3]}
{"key": "coordinates", "cast": "list_float", "default": [10.5, 20.1]}
{"key": "slice_range", "cast": "tuple_int", "default": (0, 10)}
{"key": "bounds", "cast": "tuple_float", "default": (0.0, 1.0)}
{"key": "options_tuple", "cast": "tuple_str", "default": ("opt1", "opt2")}

# Advanced Systems and Formats
{"key": "config_file", "cast": "path", "default": "/etc/config.json"}
{"key": "start_time", "cast": "timestamp", "default": "01:30:00"}
{"key": "secret", "cast": "password"}
```

### Interactive Selector with Grid Layout (`input="select"`)
```python
{
    "key": "environment",
    "label": "Select deployment environment",
    "cast": "str",
    "input": "select",
    "choices": ["development", "staging", "production"],
    "cols": 3,
    "default": "development"
}
```

### Boundary and Constraint Enforcement (`min`, `max`, `choices`)
```python
{
    "key": "age_limit",
    "cast": "int",
    "min": 18,
    "max": 99,
    "choices": [18, 21, 25, 30, 99]
}
```

### Advanced Path Validation (`is_file`)
```python
{
    "key": "input_file",
    "label": "Select data file",
    "cast": "path",
    "is_file": True  # Enforces that the path must be a regular file, not a directory
}
```

### Advanced Password Policy & Hashing Configuration
```python
{
    "key": "new_password",
    "label": "Create a secure password",
    "cast": "password",
    "input": "password",
    "is_new": True,
    "min_len": 12,
    "require_uppercase": True,
    "require_number": True,
    "require_special": True,
    "store_hash": True,
    "max_retries": 3,
    "verifier": lambda pwd: len(pwd) > 0  # Optional verification callback
}
```

---

## 4. Runtime Behavior, Special States, & Exceptions

Beyond schema configuration, `user_input()` features built-in execution states and automatic handling:

### Special Return States & Error Handling
* **`__status__ = "MAX_RETRIES_EXCEEDED"`**: Injected into the result dictionary if a critical or password field breaches its maximum retry attempts limit.
* **Empty Dictionary `{}`**: Returned immediately if the inbound schema structural check fails where `schema` is not a list.
* **`UserCancelError`**: Raised safely when the user inputs an explicit interrupt signal via `Ctrl+C` or `SIGINT`.

### Automatically Injected Runtime Metadata
Through runtime reflection (`_resolve_caster`), the engine automatically handles context injection behind the scenes:
* **`attempt`**: Automatically tracked and incremented during retry sequences.
* **`field` / `current_field`**: Bound automatically to collection parsers such as `_parse_list_int` or `_parse_tuple_int` to handle positional array overlays against pre-existing defaults.

> **Note on Fail-safes:** In non-critical mode, if a casting or validation exception occurs, the engine automatically falls back to an explicit schema default or an architectural fallback constant such as `None` or an empty list to preserve runtime flow.