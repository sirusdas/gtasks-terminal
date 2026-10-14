#!/usr/bin/env python3
"""
Unit tests for gtasks interactive mode Spaces & Sub-spaces features.
"""

import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from gtasks_cli.models.task import Task, TaskStatus, Priority
from gtasks_cli.utils.space_extractor import (
    extract_spaces_from_text,
    split_notes_and_metadata,
    combine_notes_and_metadata,
    parse_spaces_input,
    format_spaces_for_input,
)
from gtasks_cli.commands.interactive_utils.search import (
    apply_space_filter,
    apply_search_filter,
)
from gtasks_cli.commands.interactive_utils.update_spaces_commands import (
    _parse_space_spec,
    handle_update_spaces_command,
)
from gtasks_cli.commands.interactive_utils.space_commands import (
    collect_spaces_and_subspaces_from_tasks,
)


class TestInteractiveSpaces(unittest.TestCase):

    def setUp(self):
        self.t1 = Task(
            id="1",
            title="Deploy auth service",
            description="Work on oauth2\n\n---{spaces}\n{spa::work:(sub::backend,sub::security)}",
            notes="Work on oauth2\n\n---{spaces}\n{spa::work:(sub::backend,sub::security)}",
            spaces={"work": ["backend", "security"]},
            status=TaskStatus.PENDING,
            priority=Priority.HIGH,
        )
        self.t2 = Task(
            id="2",
            title="Fix CSS styling",
            description="Mobile responsive layout\n\n---{spaces}\n{spa::work:(sub::frontend)}",
            notes="Mobile responsive layout\n\n---{spaces}\n{spa::work:(sub::frontend)}",
            spaces={"work": ["frontend"]},
            status=TaskStatus.PENDING,
            priority=Priority.MEDIUM,
        )
        self.t3 = Task(
            id="3",
            title="Buy groceries",
            description="Milk, eggs\n\n---{spaces}\n{spa::personal:(sub::shopping)}",
            notes="Milk, eggs\n\n---{spaces}\n{spa::personal:(sub::shopping)}",
            spaces={"personal": ["shopping"]},
            status=TaskStatus.COMPLETED,
            priority=Priority.LOW,
        )
        self.t4 = Task(
            id="4",
            title="House chores",
            description="No subspace\n\n---{spaces}\n{spa::personal}",
            notes="No subspace\n\n---{spaces}\n{spa::personal}",
            spaces={"personal": []},
            status=TaskStatus.PENDING,
            priority=Priority.LOW,
        )
        self.tasks = [self.t1, self.t2, self.t3, self.t4]

    def test_apply_space_filter(self):
        # Filter by space 'work' -> t1, t2
        res_work = apply_space_filter(self.tasks, "work")
        self.assertEqual(len(res_work), 2)
        self.assertEqual([t.id for t in res_work], ["1", "2"])

        # Filter by space 'work' and subspace 'frontend' -> t2
        res_work_fe = apply_space_filter(self.tasks, "work", "frontend")
        self.assertEqual(len(res_work_fe), 1)
        self.assertEqual(res_work_fe[0].id, "2")

        # Filter by space 'personal' -> t3, t4
        res_personal = apply_space_filter(self.tasks, "personal")
        self.assertEqual(len(res_personal), 2)
        self.assertEqual([t.id for t in res_personal], ["3", "4"])

        # Filter by space 'personal' and subspace 'shopping' -> t3
        res_shopping = apply_space_filter(self.tasks, "personal", "shopping")
        self.assertEqual(len(res_shopping), 1)
        self.assertEqual(res_shopping[0].id, "3")

        # Non-matching
        res_none = apply_space_filter(self.tasks, "nonexistent")
        self.assertEqual(len(res_none), 0)

    def test_search_matches_spaces_and_subspaces(self):
        # Searching for 'backend' should match t1 because of subspace
        res_backend = apply_search_filter(self.tasks, "backend")
        self.assertIn("1", [t.id for t in res_backend])

        # Searching for 'personal' should match t3 and t4
        res_personal = apply_search_filter(self.tasks, "personal")
        self.assertEqual(set(t.id for t in res_personal), {"3", "4"})

    def test_parse_and_format_spaces_input(self):
        # Friendly format parsing
        parsed = parse_spaces_input("work:frontend,backend; personal")
        self.assertEqual(parsed, {"work": ["frontend", "backend"], "personal": []})

        # Formatting back
        formatted = format_spaces_for_input(parsed)
        self.assertIn("work:frontend,backend", formatted)
        self.assertIn("personal", formatted)

        # Raw format parsing
        parsed_raw = parse_spaces_input("{spa::work:(sub::dev)}")
        self.assertEqual(parsed_raw, {"work": ["dev"]})

    def test_parse_space_spec(self):
        # Space with subspaces
        spa, subs = _parse_space_spec("work:frontend,backend")
        self.assertEqual(spa, "work")
        self.assertEqual(subs, ["frontend", "backend"])

        # Space with sub:: prefix
        spa, subs = _parse_space_spec("work:sub::frontend,sub::backend")
        self.assertEqual(spa, "work")
        self.assertEqual(subs, ["frontend", "backend"])

        # Space without subspaces
        spa, subs = _parse_space_spec("personal")
        self.assertEqual(spa, "personal")
        self.assertEqual(subs, [])

    def test_collect_spaces_and_subspaces_from_tasks(self):
        space_to_tasks, subspace_to_tasks, all_spaces = collect_spaces_and_subspaces_from_tasks(self.tasks)
        self.assertIn("work", all_spaces)
        self.assertIn("personal", all_spaces)
        self.assertEqual(len(space_to_tasks["work"]), 2)
        self.assertEqual(len(subspace_to_tasks["work"]["frontend"]), 1)
        self.assertEqual(len(subspace_to_tasks["work"]["backend"]), 1)
        self.assertEqual(len(space_to_tasks["personal"]), 2)
        self.assertEqual(len(subspace_to_tasks["personal"]["shopping"]), 1)

    def test_update_spaces_add_and_del(self):
        class DummyTaskState:
            def __init__(self, tasks):
                self.tasks = tasks

            def get_task_by_number(self, num):
                if 1 <= num <= len(self.tasks):
                    return self.tasks[num - 1]
                return None

        task_manager = MagicMock()
        task_manager.account_name = "test"
        task_manager.update_task.return_value = True

        task_state = DummyTaskState([self.t1, self.t2])

        # Test ADD command: update-spaces ADD[2|work:backend]
        handle_update_spaces_command(
            task_state,
            task_manager,
            ["update-spaces", "ADD[2|work:backend]"],
            use_google_tasks=False,
        )

        # Verify update_task was called for task 2 with updated spaces
        self.assertTrue(task_manager.update_task.called)
        call_kwargs = task_manager.update_task.call_args[1]
        self.assertIn("backend", call_kwargs["spaces"]["work"])
        self.assertIn("frontend", call_kwargs["spaces"]["work"])

        # Reset mock
        task_manager.reset_mock()

        # Test DEL command: update-spaces DEL[1|work:security]
        handle_update_spaces_command(
            task_state,
            task_manager,
            ["update-spaces", "DEL[1|work:security]"],
            use_google_tasks=False,
        )
        self.assertTrue(task_manager.update_task.called)
        del_call_kwargs = task_manager.update_task.call_args[1]
        self.assertNotIn("security", del_call_kwargs["spaces"]["work"])
        self.assertIn("backend", del_call_kwargs["spaces"]["work"])

    def test_clean_notes_and_spaces_display(self):
        raw = "User notes line 1\nLine 2\n\n---\n[tag1]\n\n---{spaces}\n{spa::work:(sub::api)}"
        clean_notes, tags, spaces = split_notes_and_metadata(raw)
        self.assertEqual(clean_notes, "User notes line 1\nLine 2")
        self.assertEqual(tags, ["tag1"])
        self.assertEqual(spaces, {"work": ["api"]})

        recombined = combine_notes_and_metadata(clean_notes, tags, spaces)
        self.assertIn("User notes line 1", recombined)
        self.assertIn("---", recombined)
        self.assertIn("[tag1]", recombined)
        self.assertIn("---{spaces}", recombined)
        self.assertIn("{spa::work:(sub::api)}", recombined)


if __name__ == "__main__":
    unittest.main()
