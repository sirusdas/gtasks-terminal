#!/usr/bin/env python3
"""
Interactive Terminal Mandala Sacred Geometry TUI for Google Tasks CLI.

Provides radial, concentric sacred geometry views (Padma Lotus, Sri Yantra,
Chakra Wheel) with full keyboard navigation, slice drill-down, task completion,
and saved views management using Textual and Rich.
"""

import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.align import Align
from rich.box import DOUBLE, HEAVY, ROUNDED, SIMPLE
from rich.columns import Columns
from rich.console import RenderableType
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from gtasks_cli.core.task_manager import TaskManager
from gtasks_cli.models.task import Priority, Task, TaskStatus
from gtasks_cli.utils.logger import setup_logger
from gtasks_cli.utils.space_extractor import extract_spaces_from_text

logger = setup_logger(__name__)


# -----------------------------------------------------------------------------
# Sacred Themes & Geometries
# -----------------------------------------------------------------------------

THEMES = {
    "CYBERPUNK": {
        "name": "Cyberpunk Neon",
        "primary": "cyan",
        "secondary": "magenta",
        "accent": "bright_yellow",
        "bg": "grey11",
        "highlight": "bold bright_cyan on grey19",
        "dim": "dim cyan",
        "bar_complete": "bright_magenta",
        "bar_pending": "grey30",
        "glyph": "☸",
    },
    "GOLDEN_LOTUS": {
        "name": "Golden Lotus",
        "primary": "gold1",
        "secondary": "dark_orange",
        "accent": "bright_white",
        "bg": "grey11",
        "highlight": "bold gold1 on grey19",
        "dim": "dim gold3",
        "bar_complete": "gold1",
        "bar_pending": "grey27",
        "glyph": "❂",
    },
    "VEDIC_FIRE": {
        "name": "Vedic Fire",
        "primary": "bright_red",
        "secondary": "orange1",
        "accent": "yellow1",
        "bg": "grey11",
        "highlight": "bold bright_red on grey19",
        "dim": "dim red",
        "bar_complete": "orange1",
        "bar_pending": "grey27",
        "glyph": "ॐ",
    },
    "SACRED_GEOMETRY": {
        "name": "Sacred Geometry",
        "primary": "deep_sky_blue1",
        "secondary": "dodger_blue1",
        "accent": "bright_white",
        "bg": "grey11",
        "highlight": "bold deep_sky_blue1 on grey19",
        "dim": "dim dodger_blue1",
        "bar_complete": "deep_sky_blue1",
        "bar_pending": "grey27",
        "glyph": "✡",
    },
    "EMERALD_FOREST": {
        "name": "Emerald Forest",
        "primary": "spring_green1",
        "secondary": "sea_green1",
        "accent": "bright_white",
        "bg": "grey11",
        "highlight": "bold spring_green1 on grey19",
        "dim": "dim sea_green1",
        "bar_complete": "spring_green1",
        "bar_pending": "grey27",
        "glyph": "❀",
    },
}

GEOMETRIES = ["PADMA", "SRI_YANTRA", "CHAKRA"]
GROUPINGS = ["spaces", "tags", "priority", "lists"]


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

class MandalaSlice:
    def __init__(self, key: str, label: str, glyph: str = "✿"):
        self.key = key
        self.label = label
        self.glyph = glyph
        self.tasks: List[Task] = []
        self.pending_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []

    @property
    def total(self) -> int:
        return len(self.tasks)

    @property
    def pending_count(self) -> int:
        return len(self.pending_tasks)

    @property
    def completed_count(self) -> int:
        return len(self.completed_tasks)

    @property
    def completion_pct(self) -> float:
        if not self.tasks:
            return 0.0
        return (len(self.completed_tasks) / len(self.tasks)) * 100.0


# -----------------------------------------------------------------------------
# Saved Views Persistence
# -----------------------------------------------------------------------------

def get_saved_views_path() -> Path:
    config_dir = os.environ.get("GTASKS_CONFIG_DIR")
    if config_dir:
        base = Path(config_dir)
    else:
        base = Path.home() / ".gtasks"
    base.mkdir(parents=True, exist_ok=True)
    return base / "saved_views.json"


def load_saved_views() -> List[Dict[str, Any]]:
    path = get_saved_views_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Error loading saved views: {e}")
        return []


def save_saved_views(views: List[Dict[str, Any]]) -> None:
    path = get_saved_views_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(views, f, indent=2)
    except Exception as e:
        logger.error(f"Error persisting saved views: {e}")


# -----------------------------------------------------------------------------
# Visual Canvas Widget
# -----------------------------------------------------------------------------

class MandalaCanvasWidget(Widget):
    """Renders the sacred geometry ASCII/Unicode radial mandala."""

    slices: reactive[List[MandalaSlice]] = reactive([], layout=True)
    focused_index: reactive[int] = reactive(0, layout=True)
    active_theme: reactive[str] = reactive("CYBERPUNK", layout=True)
    active_geometry: reactive[str] = reactive("PADMA", layout=True)
    active_grouping: reactive[str] = reactive("spaces", layout=True)
    drill_path: reactive[List[str]] = reactive([], layout=True)
    is_fullscreen: reactive[bool] = reactive(False, layout=True)

    def render(self) -> RenderableType:
        theme = THEMES.get(self.active_theme, THEMES["CYBERPUNK"])
        slices = self.slices
        if not slices:
            return Panel(
                Align.center(Text("\n\n✦ No tasks found in active mandala view ✦\n\n", style=f"bold {theme['primary']}")),
                border_style=theme["primary"],
                box=ROUNDED,
                title=f" Mandala • {self.active_grouping.title()} ",
            )

        total_tasks = sum(s.total for s in slices)
        total_pending = sum(s.pending_count for s in slices)
        total_completed = sum(s.completed_count for s in slices)
        overall_pct = (total_completed / total_tasks * 100.0) if total_tasks > 0 else 0.0

        if self.focused_index < 0:
            self.focused_index = 0
        elif self.focused_index >= len(slices):
            self.focused_index = len(slices) - 1

        focused = slices[self.focused_index]

        # Dispatch to specific geometry renderer
        if self.active_geometry == "PADMA":
            content = self._render_padma(slices, focused, theme, total_tasks, total_pending, overall_pct)
        elif self.active_geometry == "SRI_YANTRA":
            content = self._render_sri_yantra(slices, focused, theme, total_tasks, total_pending, overall_pct)
        else:
            content = self._render_chakra(slices, focused, theme, total_tasks, total_pending, overall_pct)

        # Header / breadcrumb
        path_str = "Mandala"
        if self.drill_path:
            path_str += " › " + " › ".join(self.drill_path)

        geom_label = f"[{self.active_geometry}]"
        theme_label = f"[{theme['name']}]"
        group_label = f"[{self.active_grouping.upper()}]"

        title_text = f" {theme['glyph']} {path_str} • {geom_label} {group_label} {theme_label} "
        if self.is_fullscreen:
            title_text = f" ❂ FULLSCREEN MANDALA NAVIGATION • Press 'f' to exit ❂ "

        return Panel(
            content,
            border_style=theme["primary"],
            box=DOUBLE if not self.is_fullscreen else HEAVY,
            title=title_text,
            title_align="center",
            padding=(0, 1),
        )

    def _render_padma(self, slices: List[MandalaSlice], focused: MandalaSlice, theme: Dict[str, str], total: int, pending: int, pct: float) -> RenderableType:
        """Renders Padma Lotus radial ring with petals arranged around central core."""
        p_color = theme["primary"]
        s_color = theme["secondary"]
        a_color = theme["accent"]

        # Center core table
        center_text = Text()
        center_text.append(f"\n   {theme['glyph']}  CENTER CORE  {theme['glyph']}   \n", style=f"bold {a_color}")
        center_text.append(f"   Total: {total} Tasks   \n", style=f"bold {p_color}")
        center_text.append(f"   Pending: {pending} | Done: {total - pending}   \n", style=s_color)
        center_text.append(f"   Completion: {pct:4.1f}%   \n", style=f"bold {theme['bar_complete']}")

        # Progress bar string
        bar_len = 16
        filled = int((pct / 100.0) * bar_len) if pct > 0 else 0
        bar_str = "█" * filled + "░" * (bar_len - filled)
        center_text.append(f"   [{bar_str}]   \n", style=theme["bar_complete"])

        center_panel = Panel(Align.center(center_text), border_style=p_color, box=ROUNDED, padding=(0, 1))

        # Radial Petal Cards Grid
        petal_cards = []
        for i, s in enumerate(slices):
            is_active = (i == self.focused_index)
            border = DOUBLE if is_active else ROUNDED
            style = theme["highlight"] if is_active else f"bold {s_color}"
            box_style = f"bold {a_color}" if is_active else theme["dim"]

            card_text = Text()
            marker = " ▶ " if is_active else "   "
            marker_end = " ◀ " if is_active else "   "
            card_text.append(f"{marker}{s.glyph} {s.label}{marker_end}\n", style=style)
            card_text.append(f"Tasks: {s.pending_count} pending / {s.total} total\n", style=f"{p_color}" if is_active else "white")

            s_bar_len = 12
            s_filled = int((s.completion_pct / 100.0) * s_bar_len) if s.completion_pct > 0 else 0
            s_bar = "█" * s_filled + "░" * (s_bar_len - s_filled)
            card_text.append(f"[{s_bar}] {s.completion_pct:3.0f}%\n", style=theme["bar_complete"] if is_active else "dim white")

            petal_cards.append(
                Panel(
                    Align.center(card_text),
                    border_style=f"bold {a_color}" if is_active else theme["dim"],
                    box=border,
                    padding=(0, 1),
                )
            )

        # Layout petals in top, center row, bottom
        half = len(petal_cards) // 2
        top_petals = petal_cards[:max(1, half)]
        bottom_petals = petal_cards[max(1, half):]

        grid = Table.grid(expand=True)
        grid.add_column(justify="center")

        grid.add_row(Align.center(Columns(top_petals, equal=True, expand=False)))
        grid.add_row(Align.center(center_panel))
        if bottom_petals:
            grid.add_row(Align.center(Columns(bottom_petals, equal=True, expand=False)))

        return grid

    def _render_sri_yantra(self, slices: List[MandalaSlice], focused: MandalaSlice, theme: Dict[str, str], total: int, pending: int, pct: float) -> RenderableType:
        """Renders Sri Yantra concentric nested geometric levels."""
        p_color = theme["primary"]
        s_color = theme["secondary"]
        a_color = theme["accent"]

        content = Table.grid(expand=True)
        content.add_column(justify="center")

        # Bindu center
        bindu = Text()
        bindu.append(f"▲ BINDU CENTER CORE ▲\n", style=f"bold {a_color}")
        bindu.append(f"Overall Progress: {pct:.1f}% ({pending} pending / {total} total)\n", style=f"bold {p_color}")
        content.add_row(Align.center(Panel(bindu, border_style=a_color, box=DOUBLE)))

        # Concentric triangles list
        triangles_table = Table(box=SIMPLE, expand=True, show_header=True, header_style=f"bold {a_color}")
        triangles_table.add_column("Level / Node", justify="left")
        triangles_table.add_column("Slice", justify="left")
        triangles_table.add_column("Tasks", justify="center")
        triangles_table.add_column("Progress", justify="center")
        triangles_table.add_column("Bar", justify="left")

        for idx, s in enumerate(slices):
            is_active = (idx == self.focused_index)
            prefix = "▶▶ " if is_active else "   "
            row_style = theme["highlight"] if is_active else "white"
            glyph = "△" if idx % 2 == 0 else "▽"

            s_bar_len = 14
            s_filled = int((s.completion_pct / 100.0) * s_bar_len) if s.completion_pct > 0 else 0
            bar = "█" * s_filled + "░" * (s_bar_len - s_filled)

            triangles_table.add_row(
                Text(f"{prefix}{glyph} Ring {idx + 1}", style=row_style),
                Text(f"{s.glyph} {s.label}", style=f"bold {p_color}" if is_active else s_color),
                Text(f"{s.pending_count}/{s.total}", style=row_style),
                Text(f"{s.completion_pct:4.1f}%", style=f"bold {theme['bar_complete']}"),
                Text(bar, style=theme["bar_complete"] if is_active else "dim white"),
            )

        content.add_row(triangles_table)
        return content

    def _render_chakra(self, slices: List[MandalaSlice], focused: MandalaSlice, theme: Dict[str, str], total: int, pending: int, pct: float) -> RenderableType:
        """Renders Chakra radial energy wheel spokes."""
        p_color = theme["primary"]
        s_color = theme["secondary"]
        a_color = theme["accent"]

        content = Table.grid(expand=True)
        content.add_column(justify="center")

        # Radial wheel center
        wheel_head = Text()
        wheel_head.append(f"☸ CHAKRA ENERGY WHEEL ☸\n", style=f"bold {a_color}")
        wheel_head.append(f"{total} Total Tasks • {pending} Active Vibrations\n", style=f"bold {p_color}")
        content.add_row(Align.center(Panel(wheel_head, border_style=p_color, box=ROUNDED)))

        # Radial Spokes representation
        spokes = Table(box=ROUNDED, expand=True, show_header=True, header_style=f"bold {a_color}")
        spokes.add_column("Spoke", justify="center", width=8)
        spokes.add_column("Chakra Ray / Focus", justify="left")
        spokes.add_column("Vibrations (Tasks)", justify="center")
        spokes.add_column("Harmony %", justify="center")

        chakra_glyphs = ["🔴 Muladhara", "🟠 Svadhisthana", "🟡 Manipura", "🟢 Anahata", "🔵 Vishuddha", "🟣 Ajna", "⚪ Sahasrara"]

        for idx, s in enumerate(slices):
            is_active = (idx == self.focused_index)
            c_label = chakra_glyphs[idx % len(chakra_glyphs)]
            style = theme["highlight"] if is_active else "white"
            spoke_sym = f"⚡ Ray {idx + 1}" if not is_active else f"▶ ⚡ RAY {idx + 1} ◀"

            spokes.add_row(
                Text(spoke_sym, style=f"bold {a_color}" if is_active else "dim white"),
                Text(f"{s.glyph} {s.label} ({c_label})", style=style),
                Text(f"{s.pending_count} pending ({s.total} total)", style=style),
                Text(f"{s.completion_pct:4.1f}%", style=f"bold {theme['bar_complete']}"),
            )

        content.add_row(spokes)
        return content


# -----------------------------------------------------------------------------
# Saved Views Modal Screen
# -----------------------------------------------------------------------------

class SavedViewsModal(ModalScreen[Optional[Dict[str, Any]]]):
    """Modal screen to select, save, rename, or delete Mandala views."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Cancel"),
        Binding("q", "dismiss(None)", "Close"),
    ]

    def __init__(self, current_state: Dict[str, Any]):
        super().__init__()
        self.current_state = current_state
        self.saved_views = load_saved_views()

    def compose(self) -> ComposeResult:
        with Vertical(id="saved_views_dialog"):
            yield Label("🔖 Saved Mandala Views & Custom Tabs", id="saved_title")
            yield Label("Select a view to apply, or save current view below:", id="saved_subtitle")

            with Horizontal(id="save_input_row"):
                yield Input(placeholder="Enter view title (e.g. Sprint Core)", id="view_name_input")
                yield Button("Save Current View", variant="primary", id="btn_save_current")

            yield ListView(id="saved_views_list")
            with Horizontal(id="saved_actions_row"):
                yield Button("Apply Selected", variant="success", id="btn_apply")
                yield Button("Delete Selected", variant="error", id="btn_delete")
                yield Button("Close", variant="default", id="btn_close")

    def on_mount(self) -> None:
        self._populate_list()

    def _populate_list(self) -> None:
        lv = self.query_one("#saved_views_list", ListView)
        lv.clear()
        if not self.saved_views:
            lv.append(ListItem(Label("(No saved views yet - Save current view above)")))
            return

        for idx, v in enumerate(self.saved_views):
            title = v.get("title", f"View #{idx + 1}")
            grouping = v.get("mandalaGrouping", "spaces")
            geom = v.get("mandalaGeometry", "PADMA")
            theme = v.get("mandalaTheme", "CYBERPUNK")
            text = f"🕉️ {title}  •  [{grouping.upper()}] • [{geom}] • [{theme}]"
            lv.append(ListItem(Label(text)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_close":
            self.dismiss(None)
        elif event.button.id == "btn_save_current":
            inp = self.query_one("#view_name_input", Input)
            name = inp.value.strip() or f"Mandala {datetime.now().strftime('%b %d %H:%M')}"
            new_view = {
                "id": f"saved_view_{int(datetime.now().timestamp() * 1000)}",
                "title": name,
                "viewMode": "mandala",
                "mandalaGrouping": self.current_state.get("grouping", "spaces"),
                "mandalaGeometry": self.current_state.get("geometry", "PADMA"),
                "mandalaTheme": self.current_state.get("theme", "CYBERPUNK"),
                "date": datetime.now().isoformat(),
            }
            self.saved_views.append(new_view)
            save_saved_views(self.saved_views)
            inp.value = ""
            self._populate_list()
            self.notify(f"View saved: {name} 🔖")
        elif event.button.id == "btn_apply":
            self._apply_selected()
        elif event.button.id == "btn_delete":
            lv = self.query_one("#saved_views_list", ListView)
            if lv.index is not None and 0 <= lv.index < len(self.saved_views):
                deleted = self.saved_views.pop(lv.index)
                save_saved_views(self.saved_views)
                self._populate_list()
                self.notify(f"Deleted view: {deleted.get('title')}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._apply_selected()

    def _apply_selected(self) -> None:
        lv = self.query_one("#saved_views_list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self.saved_views):
            chosen = self.saved_views[lv.index]
            self.dismiss(chosen)


# -----------------------------------------------------------------------------
# Main Mandala TUI Application
# -----------------------------------------------------------------------------

class MandalaApp(App):
    """Interactive Sacred Geometry Mandala TUI for Google Tasks."""

    CSS = """
    Screen {
        background: #111116;
        color: #e0e0e8;
    }
    #main_container {
        width: 100%;
        height: 100%;
    }
    #body_split {
        width: 100%;
        height: 1fr;
    }
    #canvas_container {
        width: 60%;
        height: 100%;
    }
    #tasks_panel {
        width: 40%;
        height: 100%;
        border-left: heavy #33334d;
        background: #161622;
        padding: 0 1;
    }
    #fullscreen_canvas {
        width: 100%;
        height: 100%;
    }
    #tasks_title {
        font-weight: bold;
        color: #00ffff;
        margin-bottom: 1;
        text-align: center;
    }
    #tasks_list {
        height: 1fr;
    }
    ListItem {
        padding: 0 1;
    }
    ListItem:hover {
        background: #252538;
    }
    #saved_views_dialog {
        width: 70;
        height: 30;
        background: #1c1c2b;
        border: heavy #00ffff;
        padding: 1 2;
        align: center middle;
    }
    #saved_title {
        font-weight: bold;
        color: #00ffff;
        text-align: center;
        margin-bottom: 0;
    }
    #saved_subtitle {
        color: #a0a0b8;
        text-align: center;
        margin-bottom: 1;
    }
    #save_input_row {
        height: 3;
        margin-bottom: 1;
    }
    #view_name_input {
        width: 1fr;
    }
    #saved_views_list {
        height: 1fr;
        border: solid #33334d;
        margin-bottom: 1;
    }
    #saved_actions_row {
        height: 3;
        align: center middle;
    }
    #saved_actions_row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("left,h", "prev_slice", "Rotate Left", show=True),
        Binding("right,l", "next_slice", "Rotate Right", show=True),
        Binding("up,k", "prev_task", "Up Task", show=False),
        Binding("down,j", "next_task", "Down Task", show=False),
        Binding("enter,space", "drill_or_toggle", "Drill / Select", show=True),
        Binding("escape,u,backspace", "drill_up", "Up Level", show=True),
        Binding("g", "cycle_grouping", "Group Mode", show=True),
        Binding("m", "cycle_geometry", "Geometry", show=True),
        Binding("t", "cycle_theme", "Theme", show=True),
        Binding("c", "toggle_task_complete", "Complete Task", show=True),
        Binding("s", "open_saved_views", "Saved Views", show=True),
        Binding("f", "toggle_fullscreen", "Fullscreen", show=True),
        Binding("r", "refresh_data", "Reload", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    grouping_mode: reactive[str] = reactive("spaces")
    geometry_mode: reactive[str] = reactive("PADMA")
    theme_name: reactive[str] = reactive("CYBERPUNK")
    focused_slice_index: reactive[int] = reactive(0)
    drill_path: reactive[List[str]] = reactive([])
    is_fullscreen: reactive[bool] = reactive(False)

    def __init__(self, account_name: Optional[str] = None):
        super().__init__()
        self.account_name = account_name
        self.task_manager = TaskManager(storage_backend="sqlite", account_name=account_name)
        self.all_tasks: List[Task] = []
        self.computed_slices: List[MandalaSlice] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main_container"):
            with Horizontal(id="body_split"):
                with Container(id="canvas_container"):
                    yield MandalaCanvasWidget(id="mandala_canvas")
                with Vertical(id="tasks_panel"):
                    yield Label("✦ Sliced Tasks ✦", id="tasks_title")
                    yield ListView(id="tasks_list")
        yield Footer()

    def on_mount(self) -> None:
        self.load_data()

    def load_data(self) -> None:
        try:
            self.all_tasks = self.task_manager.list_tasks() or []
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            self.all_tasks = []

        self.recompute_slices()
        self.update_canvas()
        self.update_tasks_panel()

    def recompute_slices(self) -> None:
        """Groups tasks based on active grouping mode and drill path."""
        tasks = self.all_tasks

        # Apply drill-path filter if any
        if self.drill_path:
            parent_filter = self.drill_path[-1]
            if self.grouping_mode == "spaces":
                tasks = [
                    t for t in tasks
                    if parent_filter in extract_spaces_from_text(t.notes or t.description or "")
                ]
            elif self.grouping_mode == "tags":
                tasks = [t for t in tasks if parent_filter in (t.tags or [])]
            elif self.grouping_mode == "priority":
                tasks = [t for t in tasks if (t.priority.value if hasattr(t.priority, 'value') else str(t.priority or '')).lower() == parent_filter.lower()]
            elif self.grouping_mode == "lists":
                tasks = [t for t in tasks if (t.list_title or "Default List") == parent_filter]

        slice_map: Dict[str, MandalaSlice] = {}

        if self.grouping_mode == "spaces":
            # Extract workspaces & sub-workspaces
            discovered: Dict[str, List[Task]] = defaultdict(list)
            for t in tasks:
                raw = t.notes or t.description or ""
                sp = extract_spaces_from_text(raw)
                if not sp:
                    discovered["General"].append(t)
                else:
                    for s_name in sp.keys():
                        clean = s_name.strip()
                        if clean:
                            discovered[clean].append(t)

            glyphs = ["🚀", "🎨", "💰", "🏠", "⚡", "🔬", "🛡️", "🌱"]
            for idx, (sp_name, sp_tasks) in enumerate(sorted(discovered.items())):
                ms = MandalaSlice(sp_name, sp_name, glyph=glyphs[idx % len(glyphs)])
                ms.tasks = sp_tasks
                ms.pending_tasks = [t for t in sp_tasks if t.status != TaskStatus.COMPLETED]
                ms.completed_tasks = [t for t in sp_tasks if t.status == TaskStatus.COMPLETED]
                slice_map[sp_name] = ms

        elif self.grouping_mode == "tags":
            tag_tasks: Dict[str, List[Task]] = defaultdict(list)
            for t in tasks:
                tags = t.tags or []
                if not tags:
                    tag_tasks["untagged"].append(t)
                else:
                    for tag in tags:
                        tag_tasks[tag.strip()].append(t)

            for idx, (tag_name, t_tasks) in enumerate(sorted(tag_tasks.items())):
                ms = MandalaSlice(tag_name, f"#{tag_name}", glyph="🏷️")
                ms.tasks = t_tasks
                ms.pending_tasks = [t for t in t_tasks if t.status != TaskStatus.COMPLETED]
                ms.completed_tasks = [t for t in t_tasks if t.status == TaskStatus.COMPLETED]
                slice_map[tag_name] = ms

        elif self.grouping_mode == "priority":
            p_order = [("critical", "🔥 Critical", "🔴"), ("high", "⚡ High", "🟠"), ("medium", "🟡 Medium", "🟡"), ("low", "🟢 Low", "🟢")]
            for p_key, p_lbl, p_glyph in p_order:
                p_tasks = [t for t in tasks if (t.priority.value if hasattr(t.priority, 'value') else str(t.priority or '')).lower() == p_key]
                ms = MandalaSlice(p_key, p_lbl, glyph=p_glyph)
                ms.tasks = p_tasks
                ms.pending_tasks = [t for t in p_tasks if t.status != TaskStatus.COMPLETED]
                ms.completed_tasks = [t for t in p_tasks if t.status == TaskStatus.COMPLETED]
                slice_map[p_key] = ms

        elif self.grouping_mode == "lists":
            l_tasks: Dict[str, List[Task]] = defaultdict(list)
            for t in tasks:
                l_title = t.list_title or "Default List"
                l_tasks[l_title].append(t)

            for idx, (l_title, lst_tasks) in enumerate(sorted(l_tasks.items())):
                ms = MandalaSlice(l_title, l_title, glyph="📋")
                ms.tasks = lst_tasks
                ms.pending_tasks = [t for t in lst_tasks if t.status != TaskStatus.COMPLETED]
                ms.completed_tasks = [t for t in lst_tasks if t.status == TaskStatus.COMPLETED]
                slice_map[l_title] = ms

        self.computed_slices = list(slice_map.values())
        if not self.computed_slices:
            fallback = MandalaSlice("all", "All Tasks", glyph="✦")
            fallback.tasks = tasks
            fallback.pending_tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED]
            fallback.completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            self.computed_slices = [fallback]

        if self.focused_slice_index >= len(self.computed_slices):
            self.focused_slice_index = 0

    def update_canvas(self) -> None:
        canvas = self.query_one("#mandala_canvas", MandalaCanvasWidget)
        canvas.slices = self.computed_slices
        canvas.focused_index = self.focused_slice_index
        canvas.active_geometry = self.geometry_mode
        canvas.active_grouping = self.grouping_mode
        canvas.active_theme = self.theme_name
        canvas.drill_path = self.drill_path
        canvas.is_fullscreen = self.is_fullscreen

    def update_tasks_panel(self) -> None:
        if self.is_fullscreen:
            return

        title_lbl = self.query_one("#tasks_title", Label)
        lv = self.query_one("#tasks_list", ListView)
        lv.clear()

        if not self.computed_slices or self.focused_slice_index >= len(self.computed_slices):
            title_lbl.update("✦ Sliced Tasks (0) ✦")
            return

        cur_slice = self.computed_slices[self.focused_slice_index]
        title_lbl.update(f"✦ {cur_slice.glyph} {cur_slice.label} ({cur_slice.pending_count}/{cur_slice.total}) ✦")

        theme = THEMES.get(self.theme_name, THEMES["CYBERPUNK"])
        p_color = theme["primary"]

        for t in cur_slice.tasks:
            is_done = (t.status == TaskStatus.COMPLETED)
            check = "✓" if is_done else " "
            prio_val = (t.priority.value if hasattr(t.priority, 'value') else str(t.priority or '')).upper()
            prio_str = f"[{prio_val[:4]}]" if prio_val else ""

            txt = Text()
            txt.append(f"[{check}] ", style="bold green" if is_done else "bold yellow")
            txt.append(f"{t.title} ", style="strike dim white" if is_done else "bold white")
            if prio_str:
                txt.append(f"{prio_str} ", style="bold red" if "CRIT" in prio_str or "HIGH" in prio_str else "dim cyan")
            if t.due:
                txt.append(f"⏰ {str(t.due)[:10]} ", style="dim magenta")
            if t.tags:
                txt.append(f"#" + " #".join(t.tags[:2]), style="dim blue")

            item = ListItem(Label(txt))
            item.set_class(True, f"task_id_{t.id}")
            lv.append(item)

    # -------------------------------------------------------------------------
    # Actions & Key Handlers
    # -------------------------------------------------------------------------

    def action_prev_slice(self) -> None:
        if not self.computed_slices:
            return
        self.focused_slice_index = (self.focused_slice_index - 1 + len(self.computed_slices)) % len(self.computed_slices)
        self.update_canvas()
        self.update_tasks_panel()

    def action_next_slice(self) -> None:
        if not self.computed_slices:
            return
        self.focused_slice_index = (self.focused_slice_index + 1) % len(self.computed_slices)
        self.update_canvas()
        self.update_tasks_panel()

    def action_prev_task(self) -> None:
        if self.is_fullscreen:
            return
        lv = self.query_one("#tasks_list", ListView)
        if lv.index is not None and lv.index > 0:
            lv.index -= 1

    def action_next_task(self) -> None:
        if self.is_fullscreen:
            return
        lv = self.query_one("#tasks_list", ListView)
        if lv.index is not None and lv.index < len(lv.children) - 1:
            lv.index += 1

    def action_drill_or_toggle(self) -> None:
        if not self.computed_slices or self.focused_slice_index >= len(self.computed_slices):
            return
        cur_slice = self.computed_slices[self.focused_slice_index]

        # If not drilled yet into this slice, drill into it
        if not self.drill_path or self.drill_path[-1] != cur_slice.label:
            self.drill_path = self.drill_path + [cur_slice.label]
            self.focused_slice_index = 0
            self.recompute_slices()
            self.update_canvas()
            self.update_tasks_panel()
            self.notify(f"Drilled into {cur_slice.label} 🔍")
        else:
            # Already drilled, toggle highlighted task completion
            self.action_toggle_task_complete()

    def action_drill_up(self) -> None:
        if self.drill_path:
            self.drill_path = self.drill_path[:-1]
            self.focused_slice_index = 0
            self.recompute_slices()
            self.update_canvas()
            self.update_tasks_panel()
            self.notify("Drilled up to parent level ⬆")
        elif self.is_fullscreen:
            self.action_toggle_fullscreen()

    def action_cycle_grouping(self) -> None:
        idx = (GROUPINGS.index(self.grouping_mode) + 1) % len(GROUPINGS)
        self.grouping_mode = GROUPINGS[idx]
        self.drill_path = []
        self.focused_slice_index = 0
        self.recompute_slices()
        self.update_canvas()
        self.update_tasks_panel()
        self.notify(f"Grouping: {self.grouping_mode.upper()} 🔄")

    def action_cycle_geometry(self) -> None:
        idx = (GEOMETRIES.index(self.geometry_mode) + 1) % len(GEOMETRIES)
        self.geometry_mode = GEOMETRIES[idx]
        self.update_canvas()
        self.notify(f"Geometry: {self.geometry_mode} ☸")

    def action_cycle_theme(self) -> None:
        theme_keys = list(THEMES.keys())
        idx = (theme_keys.index(self.theme_name) + 1) % len(theme_keys)
        self.theme_name = theme_keys[idx]
        self.update_canvas()
        self.update_tasks_panel()
        self.notify(f"Theme: {THEMES[self.theme_name]['name']} 🎨")

    def action_toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        tasks_panel = self.query_one("#tasks_panel", Vertical)
        canvas_cont = self.query_one("#canvas_container", Container)

        if self.is_fullscreen:
            tasks_panel.display = False
            canvas_cont.styles.width = "100%"
            self.notify("Fullscreen Mandala Navigation active (Press 'f' to exit) ❂")
        else:
            tasks_panel.display = True
            canvas_cont.styles.width = "60%"
            self.update_tasks_panel()

        self.update_canvas()

    def action_toggle_task_complete(self) -> None:
        if not self.computed_slices or self.focused_slice_index >= len(self.computed_slices):
            return
        cur_slice = self.computed_slices[self.focused_slice_index]
        lv = self.query_one("#tasks_list", ListView)

        task_idx = lv.index if lv.index is not None and 0 <= lv.index < len(cur_slice.tasks) else 0
        if not cur_slice.tasks or task_idx >= len(cur_slice.tasks):
            return

        target_task = cur_slice.tasks[task_idx]
        is_completed = (target_task.status == TaskStatus.COMPLETED)
        new_status = TaskStatus.PENDING if is_completed else TaskStatus.COMPLETED
        completed_at = None if is_completed else datetime.utcnow().isoformat()

        try:
            self.task_manager.update_task(target_task.id, status=new_status, completed_at=completed_at)
            target_task.status = new_status
            target_task.completed_at = completed_at
            status_text = "reopened ↺" if is_completed else "completed! ✓"
            self.notify(f"Task '{target_task.title}' {status_text}")
            self.load_data()
        except Exception as e:
            logger.error(f"Error toggling task completion: {e}")
            self.notify(f"Error updating task: {e}", severity="error")

    def action_open_saved_views(self) -> None:
        current_state = {
            "grouping": self.grouping_mode,
            "geometry": self.geometry_mode,
            "theme": self.theme_name,
        }
        self.push_screen(SavedViewsModal(current_state), self._on_saved_view_applied)

    def _on_saved_view_applied(self, result: Optional[Dict[str, Any]]) -> None:
        if not result:
            return
        new_grouping = result.get("mandalaGrouping", self.grouping_mode)
        new_geometry = result.get("mandalaGeometry", self.geometry_mode)
        new_theme = result.get("mandalaTheme", self.theme_name)

        if new_grouping in GROUPINGS:
            self.grouping_mode = new_grouping
        if new_geometry in GEOMETRIES:
            self.geometry_mode = new_geometry
        if new_theme in THEMES:
            self.theme_name = new_theme

        self.drill_path = []
        self.focused_slice_index = 0
        self.recompute_slices()
        self.update_canvas()
        self.update_tasks_panel()
        self.notify(f"Applied Saved View: {result.get('title', 'Saved View')} 🔖")

    def action_refresh_data(self) -> None:
        self.load_data()
        self.notify("Reloaded tasks from database ↻")


# -----------------------------------------------------------------------------
# Click Command
# -----------------------------------------------------------------------------

@click.command(name="mandala")
@click.option("--grouping", "-g", type=click.Choice(GROUPINGS), default="spaces", help="Grouping dimension (spaces, tags, priority, lists)")
@click.option("--geometry", "-m", type=click.Choice(GEOMETRIES), default="PADMA", help="Sacred geometry layout (PADMA, SRI_YANTRA, CHAKRA)")
@click.option("--theme", "-t", type=click.Choice(list(THEMES.keys())), default="CYBERPUNK", help="Color theme")
@click.option("--fullscreen", "-f", is_flag=True, help="Start directly in fullscreen navigation mode")
@click.option("--account", "-a", help="Account name for multi-account support")
@click.pass_context
def mandala(ctx, grouping, geometry, theme, fullscreen, account):
    """
    Launch interactive Sacred Geometry Mandala Terminal TUI.

    Provides radial petal navigation (Padma, Sri Yantra, Chakra), slice drill-down,
    task completion with checkmarks, saved views, and full keyboard navigation.
    """
    account_name = account or ctx.obj.get("account_name")
    app = MandalaApp(account_name=account_name)
    app.grouping_mode = grouping
    app.geometry_mode = geometry
    app.theme_name = theme
    app.is_fullscreen = fullscreen
    app.run()


if __name__ == "__main__":
    mandala()
