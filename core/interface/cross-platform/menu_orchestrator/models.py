from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


# DATA MODEL ENGINE: MENU ENTRY METADATA COMPOSITOR
# This dataclass represents an individual menu entry or interactive option.
# By coordinating label text, hotkeys, action identifiers, and state reference keys,
# it encapsulates all configuration parameters needed for option preprocessing and dispatch.
@dataclass
class MenuEntry:
    """Represents an individual menu option or entry item."""

    label: str = ""
    hotkey: str = ""
    action_key: str = ""
    state_ref: str | None = None

    # DICTIONARY SERIALIZATION & EXPORT COMPOSITOR ENGINE
    # Converts the dataclass instance into a clean dictionary payload compatible with
    # underlying preprocessing and dispatcher functions.
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes instance properties into a plain dictionary mapping.

        Returns:
            dict[str, Any]: Filtered dictionary representation of the entry configuration.
        """
        # DICTIONARY FILTERING & PURGING ENGINE
        # Iterates through active properties, removing unassigned optional attributes
        # to prevent null reference pollution downstream.
        return {k: v for k, v in self.__dict__.items() if v is not None}


# DATA MODEL ENGINE: UI LAYOUT & SPATIAL CONFIGURATION
# This dataclass encapsulates layout metrics, spatial constraints, column counts,
# and acronym lookup maps for customization of terminal menu displays.
@dataclass
class UIConfig:
    """Encapsulates custom layout rules, spatial constraints, and text formatting parameters."""

    id_type: str = "auto_int"
    cols: int = 1
    row_template: str | None = None
    width: int = 80
    height: int | str = "auto"
    wrap_text: bool = True
    acronyms: dict[str, str] = field(default_factory=lambda: dict[str, str]())
    has_box: bool = True
    border_style: str = "rounded"

    # DICTIONARY SERIALIZATION & EXPORT COMPOSITOR ENGINE
    # Converts layout configuration into a dictionary structure consumed by schema builders.
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes UI layout options into a plain dictionary layout.

        Returns:
            dict[str, Any]: Complete dictionary mapping of UI rules and spatial properties.
        """
        # SERIALIZATION COMPOSITOR
        # Returns active configuration attributes as a raw dictionary.
        return self.__dict__.copy()


# DATA MODEL ENGINE: MENU CONTROLLER CONFIGURATION & EXECUTION WRAPPER
# This dataclass aggregates interactive menu operational flags, UI configuration parameters,
# and option callback mappings into a unified schema model ready for controller invocation.
@dataclass
class MenuConfig:
    """Root configuration model encapsulating interactive menu execution options."""

    options: dict[str, Callable[..., Any]] = field(
        default_factory=lambda: dict[str, Callable[..., Any]]()
    )
    title: str = "System Orchestrator"
    state: dict[str, Any] | None = None
    critical: bool = True
    shorthand: bool = False
    batch: bool = False
    template: str | None = None
    ui_config: UIConfig | dict[str, Any] | None = None
    allow_back: bool = False
    renderer: Callable[..., str] | None = None

    # POLYMORPHIC EXECUTION DISPATCHER
    # Triggers the menu controller pipeline, passing structured parameters
    # to the underlying interactive menu orchestration engine.
    def execute(self) -> Any:
        """
        Executes the interactive menu orchestration pipeline using configured options.

        Returns:
            Any: The execution result of the selected option(s), "BACK", or None upon abort.
        """
        # LAUNCH DISPATCH INVOCATION
        # Lazy loads and invokes the core menu_controller with structured parameter mappings.
        from .controller import menu_controller  # type: ignore[import-not-found]

        # UI CONFIGURATION RESOLUTION
        # Normalizes UIConfig dataclass instances or dictionary maps into dictionary form.
        resolved_ui_config = (
            self.ui_config.to_dict()
            if isinstance(self.ui_config, UIConfig)
            else self.ui_config
        )

        kwargs: dict[str, Any] = {
            "options": self.options,
            "title": self.title,
            "state": self.state,
            "critical": self.critical,
            "shorthand": self.shorthand,
            "batch": self.batch,
            "template": self.template,
            "ui_config": resolved_ui_config,
            "allow_back": self.allow_back,
        }

        # CONDITIONAL RENDERER INJECTION
        # Only injects renderer if explicitly passed, preserving default controller settings.
        if self.renderer is not None:
            kwargs["renderer"] = self.renderer

        return menu_controller(**kwargs)


# DATA MODEL ENGINE: PERSISTENT MENU ROUTER WRAPPER
# Encapsulates persistent lifecycle routing parameters for nested menu loops.
@dataclass
class RouterOptions:
    """Configuration wrapper for menu_router persistent lifecycle execution."""

    options: (
        dict[str, Callable[..., Any]] | Callable[[], dict[str, Callable[..., Any]]]
    )
    is_main_menu: bool = False
    returns_value: bool = False
    controller_config: MenuConfig | None = None

    # POLYMORPHIC LIFECYCLE ROUTER DISPATCHER
    # Executes the persistent menu router lifecycle loop.
    def execute(self) -> Any:
        """
        Executes the persistent menu routing lifecycle loop using object-oriented configuration.

        Returns:
            Any: The execution result if `returns_value` is enabled, or None upon session termination.
        """
        # LAUNCH DISPATCH INVOCATION
        # Lazy loads and invokes menu_router with resolved keyword arguments.
        from .router import menu_router  # type: ignore[import-not-found]

        kwargs: dict[str, Any] = {
            "is_main_menu": self.is_main_menu,
            "returns_value": self.returns_value,
        }

        if self.controller_config:
            # UNPACK CONTROLLER PARAMETERS
            # Extracts configuration values from the embedded MenuConfig dataclass.
            cfg = self.controller_config
            resolved_ui_config = (
                cfg.ui_config.to_dict()
                if isinstance(cfg.ui_config, UIConfig)
                else cfg.ui_config
            )

            kwargs.update(
                {
                    "title": cfg.title,
                    "state": cfg.state,
                    "critical": cfg.critical,
                    "shorthand": cfg.shorthand,
                    "batch": cfg.batch,
                    "template": cfg.template,
                    "ui_config": resolved_ui_config,
                    "allow_back": cfg.allow_back,
                }
            )

            if cfg.renderer is not None:
                kwargs["renderer"] = cfg.renderer

        return menu_router(self.options, **kwargs)
