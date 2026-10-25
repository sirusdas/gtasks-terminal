#!/usr/bin/env python3
"""Unit tests for gtasks mandala command and data structures."""

from gtasks_cli.commands.mandala import MandalaSlice, THEMES, GEOMETRIES, GROUPINGS, load_saved_views, save_saved_views
from gtasks_cli.models.task import Task, TaskStatus, Priority

def test_mandala_slice_computations():
    slice_item = MandalaSlice("work", "🚀 Work")
    assert slice_item.total == 0
    assert slice_item.completion_pct == 0.0

    t1 = Task(id="1", title="Task 1", status=TaskStatus.PENDING)
    t2 = Task(id="2", title="Task 2", status=TaskStatus.COMPLETED)

    slice_item.tasks = [t1, t2]
    slice_item.pending_tasks = [t1]
    slice_item.completed_tasks = [t2]

    assert slice_item.total == 2
    assert slice_item.pending_count == 1
    assert slice_item.completed_count == 1
    assert slice_item.completion_pct == 50.0

def test_mandala_themes_and_geometries():
    assert "PADMA" in GEOMETRIES
    assert "SRI_YANTRA" in GEOMETRIES
    assert "CHAKRA" in GEOMETRIES

    assert "CYBERPUNK" in THEMES
    assert "GOLDEN_LOTUS" in THEMES
    assert "VEDIC_FIRE" in THEMES

    assert "spaces" in GROUPINGS
    assert "tags" in GROUPINGS
    assert "priority" in GROUPINGS
    assert "lists" in GROUPINGS

def test_saved_views_roundtrip(tmp_path, monkeypatch):
    test_file = tmp_path / "saved_views.json"
    monkeypatch.setattr("gtasks_cli.commands.mandala.get_saved_views_path", lambda: test_file)

    test_views = [
        {"id": "view_1", "title": "Focus Padma", "mandalaGrouping": "spaces", "mandalaGeometry": "PADMA", "mandalaTheme": "CYBERPUNK"}
    ]
    save_saved_views(test_views)
    loaded = load_saved_views()
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Focus Padma"
    assert loaded[0]["mandalaGeometry"] == "PADMA"

if __name__ == "__main__":
    test_mandala_slice_computations()
    test_mandala_themes_and_geometries()
    print("All mandala unit tests passed!")
