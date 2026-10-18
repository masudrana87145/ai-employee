"""Tests for the greeting and integer-task API."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from api import SUPPORTED_TASKS, app, apply_task, greet

client = TestClient(app)


class TestGreetFunction(unittest.TestCase):
    def test_greet_masud(self) -> None:
        self.assertEqual(greet("Masud"), "Hi, Masud")

    def test_greet_strips_whitespace(self) -> None:
        self.assertEqual(greet("  Masud  "), "Hi, Masud")

    def test_greet_rejects_blank(self) -> None:
        with self.assertRaises(ValueError):
            greet("   ")


class TestHiEndpoint(unittest.TestCase):
    def test_hi_masud(self) -> None:
        response = client.get("/hi", params={"name": "Masud"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hi, Masud"})

    def test_hi_strips_whitespace(self) -> None:
        response = client.get("/hi", params={"name": "  Ada  "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Hi, Ada")

    def test_hi_rejects_blank_name(self) -> None:
        response = client.get("/hi", params={"name": "   "})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "name must not be empty")

    def test_hi_requires_name(self) -> None:
        response = client.get("/hi")

        self.assertEqual(response.status_code, 422)


class TestApplyTask(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(apply_task("add", 5, 4), "Sum of 5 and 4 is 9")

    def test_mult(self) -> None:
        self.assertEqual(apply_task("mult", 5, 4), "Product of 5 and 4 is 20")

    def test_sub(self) -> None:
        self.assertEqual(apply_task("sub", 5, 4), "Difference of 5 and 4 is 1")

    def test_sub_negative_result(self) -> None:
        self.assertEqual(apply_task("sub", 4, 5), "Difference of 4 and 5 is -1")

    def test_unknown_task_raises(self) -> None:
        with self.assertRaises(ValueError):
            apply_task("divide", 1, 2)


class TestTaskEndpoint(unittest.TestCase):
    def test_add(self) -> None:
        response = client.post("/task", json={"task": "add", "parm1": 5, "parm2": 4})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Sum of 5 and 4 is 9"})

    def test_mult(self) -> None:
        response = client.post("/task", json={"task": "mult", "parm1": 5, "parm2": 4})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Product of 5 and 4 is 20")

    def test_sub(self) -> None:
        response = client.post("/task", json={"task": "sub", "parm1": 5, "parm2": 4})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Difference of 5 and 4 is 1")

    def test_task_name_is_case_insensitive(self) -> None:
        cases = {
            "ADD": "Sum of 2 and 3 is 5",
            "Mult": "Product of 2 and 3 is 6",
            "sUb": "Difference of 2 and 3 is -1",
        }
        for task, expected in cases.items():
            with self.subTest(task=task):
                response = client.post(
                    "/task",
                    json={"task": task, "parm1": 2, "parm2": 3},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["message"], expected)

    def test_task_name_whitespace_is_ignored(self) -> None:
        response = client.post("/task", json={"task": "  add  ", "parm1": 1, "parm2": 1})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Sum of 1 and 1 is 2")

    def test_zero_and_negative_operands(self) -> None:
        response = client.post("/task", json={"task": "add", "parm1": -2, "parm2": 0})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Sum of -2 and 0 is -2")

    def test_unknown_task_lists_valid_tasks(self) -> None:
        response = client.post("/task", json={"task": "divide", "parm1": 5, "parm2": 4})

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"], "Unsupported task 'divide'.")
        self.assertEqual(
            body["valid_tasks"],
            [
                {"task": name, "purpose": purpose}
                for name, purpose in SUPPORTED_TASKS.items()
            ],
        )

    def test_unknown_task_any_case_still_errors(self) -> None:
        response = client.post("/task", json={"task": "DiViDe", "parm1": 1, "parm2": 2})

        self.assertEqual(response.status_code, 400)
        purposes = {item["task"]: item["purpose"] for item in response.json()["valid_tasks"]}
        self.assertEqual(purposes["add"], "Add two numbers")
        self.assertEqual(purposes["mult"], "Multiply two numbers")
        self.assertEqual(purposes["sub"], "Subtract the second number from the first")

    def test_blank_task_lists_valid_tasks(self) -> None:
        response = client.post("/task", json={"task": "   ", "parm1": 1, "parm2": 2})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported task", response.json()["error"])
        self.assertEqual(len(response.json()["valid_tasks"]), 3)

    def test_rejects_non_integer(self) -> None:
        response = client.post("/task", json={"task": "add", "parm1": 5.5, "parm2": 4})

        self.assertEqual(response.status_code, 422)

    def test_rejects_missing_field(self) -> None:
        response = client.post("/task", json={"task": "add", "parm1": 5})

        self.assertEqual(response.status_code, 422)

    def test_rejects_extra_field(self) -> None:
        response = client.post(
            "/task",
            json={"task": "add", "parm1": 5, "parm2": 4, "extra": 1},
        )

        self.assertEqual(response.status_code, 422)

    def test_rejects_boolean_as_integer(self) -> None:
        response = client.post("/task", json={"task": "add", "parm1": True, "parm2": 4})

        self.assertEqual(response.status_code, 422)


class TestRoot(unittest.TestCase):
    def test_root_lists_operations_and_sample_payload(self) -> None:
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "operations": [
                    {"task": name, "purpose": purpose}
                    for name, purpose in SUPPORTED_TASKS.items()
                ],
                "sample_payload": {"task": "add", "parm1": 5, "parm2": 4},
            },
        )


class TestHealth(unittest.TestCase):
    def test_health(self) -> None:
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ready(self) -> None:
        response = client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})


if __name__ == "__main__":
    unittest.main()
