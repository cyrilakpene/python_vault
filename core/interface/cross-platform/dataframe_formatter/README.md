# Comprehensive Reference Guide: The `format_dataframe()` Engine

The `format_dataframe()` function is a high-performance stringification and display engine that converts heterogeneous tabular data—such as pandas DataFrames, lists of dictionaries, or nested sequences—into aligned, terminal-ready ASCII text tables. 

---

## 1. Core Function Signature & Parameters

```python
def format_dataframe(
    df: TabularData,
    col_width: int | dict[str, int] | Literal["auto"] = "auto",
    align: Literal["<", ">", "^", "auto"] | dict[str, str] = "auto",
    padding: int = 2,
    strip_index: bool = False,
    headers: Sequence[str] | Literal["auto"] = "auto",
) -> str:
```

* **`df`**: The target tabular dataset (pandas DataFrame, iterable of dictionaries, or iterable of sequences/tuples).
* **`col_width`**: Column width specifier (`"auto"`, uniform integer, or a column-mapped dictionary).
* **`align`**: Text alignment specifier (`"<"`, `">"`, `"^"`, `"auto"`, or a column-mapped dictionary).
* **`padding`**: Horizontal spacing (in characters) inserted between adjacent columns.
* **`strip_index`**: If `True`, excludes the DataFrame index (applies exclusively to pandas DataFrames).
* **`headers`**: Column header names used when passing sequences without inherent keys (`"auto"` or an explicit sequence).

---

## 2. Parameter Configuration & Type Matrix

| Parameter | Accepted Types | Default | Description & Behavior |
| :--- | :--- | :--- | :--- |
| `df` | `TabularData` (`pd.DataFrame`, `Iterable[Mapping]`, `Iterable[Sequence]`) | *Required* | Raw tabular dataset to be normalized and rendered. |
| `col_width` | `int`, `dict`, or `Literal["auto"]` | `"auto"` | Controls column widths; can be uniform, auto-fitted to content, or explicitly mapped. |
| `align` | `str` (`<`, `>`, `^`, `auto`) or `dict` | `"auto"` | Manages cell text justification; auto-aligns numeric data to the right and text to the left. |
| `padding` | `int` | `2` | Number of spaces separating columns horizontally. |
| `strip_index` | `bool` | `False` | Omits the pandas index column from output when set to `True`. |
| `headers` | `Sequence[str]` or `Literal["auto"]` | `"auto"` | Provides custom headers for sequence-based data structures. |

---

## 3. Execution Pipeline & Architectural Logic

1. **Initialization & Safeguards**:
   * Logs task initialization via `report_status()`.
   * Performs runtime capability checks for `pandas` without forcing global top-level imports.
2. **Data Normalization & Branching**:
   * **Pandas DataFrame Branch**: Audits empty datasets, processes `strip_index`, extracts column headers, identifies numeric dtypes for auto-alignment, and vectorizes rows into string matrices.
   * **Dictionary Mappings Branch**: Iterates through iterable dictionaries, dynamically discovers keys to establish a unified schema, and infers numeric columns by auditing data types.
   * **Positional Sequences Branch**: Handles nested lists/tuples, evaluates maximum column width, assigns or generates fallback headers (`col_0`, `col_1`), and infers numeric fields.
3. **Width & Alignment Calculation**:
   * Evaluates `col_width` rules to determine character budgets per column using uniform constraints, manual mappings, or content-aware auto-fitting.
   * Resolves text justification rules (`<`, `>`, `^`), defaulting numeric columns to right-alignment (`>`) and text strings to left-alignment (`<`).
4. **Cell Formatting & Assembly**:
   * Truncates overflowing text cells with an ellipsis (`…`) if they exceed column boundaries.
   * Compiles header rows and body matrix rows, separating them with the designated horizontal padding before returning a unified multiline ASCII string.

---

## 4. Practical Code Examples

### Formatting a Pandas DataFrame
```python
import pandas as pd
from interface.format_dataframe import format_dataframe

df = pd.DataFrame({
    "Product": ["Widget A", "Gadget B", "Tool C"],
    "Price": [19.99, 150.50, 5.75],
    "Stock": [120, 45, 300]
})

# Automatically aligns numeric columns (Price, Stock) to the right and text to the left
output = format_dataframe(df, padding=3)
print(output)
```

### Formatting a List of Dictionaries with Custom Widths
```python
from interface.format_dataframe import format_dataframe

records = [
    {"user": "alice", "role": "admin", "active": True},
    {"user": "bob", "role": "engineer", "active": False}
]

# Explicit column widths and custom alignment mapping
widths = {"user": 10, "role": 12, "active": 8}
alignments = {"user": "<", "role": "<", "active": "^"}

output = format_dataframe(
    records, 
    col_width=widths, 
    align=alignments, 
    padding=2
)
print(output)
```

### Formatting Positional Sequences with Custom Headers
```python
from interface.format_dataframe import format_dataframe

rows = [
    ["US-EAST", "Healthy", 12],
    ["EU-WEST", "Degraded", 4],
    ["AP-SOUTH", "Healthy", 18]
]

output = format_dataframe(
    rows, 
    headers=["Region", "Status", "Nodes"], 
    col_width="auto", 
    align="auto"
)
print(output)
```