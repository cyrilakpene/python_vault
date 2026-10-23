from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# DATA MODEL ENGINE: MENU ENTRY & ROW MAPPING COMPOSITOR
# This dataclass represents an individual menu item, link, or data row.
# By managing optional hotkeys and runtime state bindings, it provides a structured
# configuration schema for UI section entries.
@dataclass
class Entry:
    """Represents an individual menu item or data row."""

    label: str = ""
    hotkey: str | None = None
    state_ref: str | None = None

    # DICTIONARY SERIALIZATION & EXPORT COMPOSITOR ENGINE
    # This utility converts the runtime dataclass instance into a clean dictionary mapping.
    # By filtering out undefined optional attributes, it ensures serialized payloads remain
    # lightweight and compatible with downstream structural components.
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the active instance attributes into a dictionary representation,
        omitting unpopulated optional fields.

        Returns:
            dict[str, Any]: A filtered dictionary mapping of active instance properties.
        """
        # DICTIONARY FILTERING & PURGING ENGINE
        # Iterates through instance attributes, filtering out fields containing None
        # to prevent null reference pollution in downstream layout schemas.
        return {k: v for k, v in self.__dict__.items() if v is not None}


# DATA MODEL ENGINE: UI SECTION & CONTAINER FRAME COMPOSITOR
# This dataclass manages the structural properties of an individual UI section or bounding box.
# By coordinating layout geometry, z-index layers, border styling, and entry collections,
# it encapsulates all configuration needed for absolute grid rendering.
@dataclass
class Section:
    """Represents a UI section or bounding container box."""

    id: str | None = None
    label: str = ""
    entries: list[Entry] = field(default_factory=list[Entry])
    w: int | str = 40
    h: int | str = 10
    x: int = 0
    y: int = 2
    z_index: int = 0
    stack_below: str | None = None
    has_box: bool = True
    border_style: str = "rounded"
    cols: int = 1
    raw_block: bool = False
    id_type: str = "auto_int"
    row_template: str = "{key}. {label}: {val}"

    # DICTIONARY SERIALIZATION & NESTED COMPOSITION ENGINE
    # This utility converts the section instance and its child entry objects into a fully
    # serialized dictionary structure, ensuring seamless integration with legacy layout engines.
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the section and its child entries into a plain dictionary layout.

        Returns:
            dict[str, Any]: A complete dictionary representation of the section configuration.
        """
        # NESTED SERIALIZATION MAPPING
        # Copies active attributes and recursively converts any nested Entry objects
        # into their respective dictionary forms.
        d = self.__dict__.copy()
        d["entries"] = [e.to_dict() for e in self.entries]
        return d


# DATA MODEL ENGINE: TELEMETRY METADATA & BANNER COMPOSITOR
# This dataclass manages top-level telemetry status messages, informational banners,
# and ingress command prompts for the terminal canvas.
@dataclass
class Metadata:
    """Represents top-level telemetry messages and prompts."""

    task_msg: str | None = None
    info_msg: str | None = None
    prompt: str | None = None

    # DICTIONARY SERIALIZATION & EXPORT COMPOSITOR ENGINE
    # This utility transforms metadata properties into a clean dictionary, dropping
    # unassigned optional strings.
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes active metadata attributes into a filtered dictionary mapping.

        Returns:
            dict[str, Any]: A dictionary representation of active telemetry messages.
        """
        # DICTIONARY FILTERING & PURGING ENGINE
        # Filters out unassigned metadata properties to maintain clean configuration payloads.
        return {k: v for k, v in self.__dict__.items() if v is not None}


# DATA MODEL ENGINE: ROOT SCHEMA CONTAINER COMPOSITOR
# This root dataclass aggregates metadata configuration and section lists into a unified,
# strongly-typed schema model ready for renderer consumption.
@dataclass
class Schema:
    """Root container holding layout metadata and sections."""

    metadata: Metadata = field(default_factory=Metadata)
    sections: list[Section] = field(default_factory=list[Section])

    # ROOT PAYLOAD SERIALIZATION & EXPORT ENGINE
    # This utility compiles the root schema, cascading serialization calls down to
    # metadata and section sub-components.
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the complete root schema hierarchy into a layout dictionary.

        Returns:
            dict[str, Any]: A fully assembled dictionary mapping of metadata and sections.
        """
        # COMPOSITE SERIALIZATION MAPPING
        # Recursively invokes serialization methods across metadata and section collections.
        return {
            "metadata": self.metadata.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
        }


# TRANSIENT 2D OVERLAY CONFIGURATION SCHEME
# Defines default layout bounds, prompt positioning, and lifecycle execution flags
# for the transient overlay rendering engine.
@dataclass
class OverlayConfig:
    """Configuration settings for transient 2D overlay rendering.

    Attributes:
        prompt: Custom footer prompt displayed at the bottom of the overlay frame.
        align_prompt: Layout alignment for the footer prompt within the frame bounds ("center", "left", "right").
        width: Virtual terminal column width.
        height: Virtual terminal row height, or 'auto' to auto-calculate required space.
        padding_x: Developer layout parameter for horizontal padding around content.
        padding_y: Developer layout parameter for vertical padding around content.
        timer: Duration in seconds before auto-clearing (optional).
        auto_clear: If True, wipes the spatial bounds of the overlay upon exit.
    """

    # PROMPT AND FOOTER LAYOUT ATTRIBUTES
    prompt: str = "Press [ENTER] to wipe display..."
    align_prompt: Literal["center", "left", "right"] = "center"

    # SPATIAL CANVAS AND PADDING PARAMETERS
    width: int = 80
    height: int | str = "auto"
    padding_x: int = 1
    padding_y: int = 1

    # LIFECYCLE AND TIMED CLEARING CONTROLS
    timer: int | None = None
    auto_clear: bool = True


# EXECUTION DISPATCH ENGINE: ABSOLUTE GRID RENDER WRAPPER
# This configuration wrapper encapsulates execution parameters for the heuristic grid renderer,
# providing an object-oriented invocation interface.
@dataclass
class GridRenderOptions:
    """Configuration wrapper for heuristic_grid_renderer."""

    schema: Schema
    state: dict[str, Any] | None = None
    width: int = 80
    height: int | str = "auto"
    wrap_text: bool = True

    # POLYMORPHIC EXECUTION DISPATCHER
    # This method triggers the grid rendering pipeline, passing structured parameters
    # to the underlying absolute canvas compositor engine.
    def execute(self) -> str:
        """
        Executes the grid rendering pipeline using the configured schema and runtime state.

        Returns:
            str: The consolidated multi-line string representing the rendered 2D terminal buffer.
        """
        # LAUNCH DISPATCH INVOCATION
        # Imports and invokes the core grid renderer with serialized schema payloads.
        from .core import heuristic_grid_renderer  # type: ignore[import-not-found]

        return heuristic_grid_renderer(
            schema=self.schema.to_dict(),
            state=self.state,
            width=self.width,
            height=self.height,
            wrap_text=self.wrap_text,
        )


# EXECUTION DISPATCH ENGINE: LINEAR UI RENDER WRAPPER
# This configuration wrapper encapsulates execution parameters for the linear multi-column
# UI compositor engine.
@dataclass
class UIRenderOptions:
    """Configuration wrapper for heuristic_ui_renderer."""

    schema: Schema
    state: dict[str, Any] | None = None

    # POLYMORPHIC EXECUTION DISPATCHER
    # This method triggers the linear UI rendering pipeline using object-oriented configuration.
    def execute(self) -> str:
        """
        Executes the linear UI rendering pipeline using the configured schema and runtime state.

        Returns:
            str: A consolidated multi-line string representing the linear text-based UI buffer.
        """
        # LAUNCH DISPATCH INVOCATION
        # Imports and invokes the core linear UI renderer with serialized schema payloads.
        from .core import heuristic_ui_renderer  # type: ignore[import-not-found]

        return heuristic_ui_renderer(schema=self.schema.to_dict(), state=self.state)
