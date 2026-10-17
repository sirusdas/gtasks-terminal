import unittest
from unittest.mock import MagicMock
from gtasks_cli.ai.tools import GTasksTools
from gtasks_cli.models.task import Task, Priority, TaskStatus

class TestMCPTools(unittest.TestCase):
    def setUp(self):
        self.mock_tm = MagicMock()
        self.mock_tm.use_google_tasks = False
        self.tools = GTasksTools(self.mock_tm, account_name='TestAcc')

    def test_add_task_with_spaces(self):
        created_task = Task(id='t-1', title='Build AI UI', priority=Priority.HIGH)
        self.mock_tm.create_task.return_value = created_task

        res = self.tools.add_task(
            title='Build AI UI',
            spaces={'work': ['frontend', 'ai']},
            tags=['v1', 'urgent'],
            priority='high',
            due='2026-10-20'
        )
        self.assertIn("Task created successfully", res)
        self.assertIn("work › frontend,ai", res)

        # Check call arguments
        call_args = self.mock_tm.create_task.call_args[1]
        self.assertEqual(call_args['title'], 'Build AI UI')
        self.assertIn("---{spaces}", call_args['description'])
        self.assertIn("{spa::work:(sub::frontend,sub::ai)}", call_args['description'])
        self.assertIn("[v1][urgent]", call_args['description'])

    def test_list_spaces(self):
        t1 = Task(id='1', title='Task 1', description="Notes\n\n---{spaces}\n{spa::work:(sub::dev)}")
        t2 = Task(id='2', title='Task 2', description="Notes\n\n---{spaces}\n{spa::work:(sub::ops)}\n{spa::personal}")
        self.mock_tm.list_tasks.return_value = [t1, t2]

        res = self.tools.list_spaces()
        self.assertIn("Active Spaces & Sub-spaces", res)
        self.assertIn("work**: dev, ops", res)
        self.assertIn("personal** (no sub-spaces)", res)

    def test_batch_reschedule(self):
        self.mock_tm.update_task.return_value = Task(id='1', title='T1')
        res = self.tools.batch_reschedule(['1', '2'], '2026-10-25')
        self.assertIn("2 rescheduled to 2026-10-25", res)

    def test_workflow_morning(self):
        self.mock_tm.list_tasks.return_value = []
        res = self.tools.execute_workflow('morning')
        self.assertIn("Morning Briefing", res)
        self.assertIn("Productivity Report", res)

if __name__ == '__main__':
    unittest.main()
