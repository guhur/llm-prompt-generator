import unittest
from io import StringIO
import contextlib

from .llm_prompt_generator import (
    create_llm_prompt,
    extract_package_info,
    extract_function_info,
)


class TestLLMPromptGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_pyproject_toml = """
[tool.poetry]
name = "example_package"
description = "This is a Python package for performing various tasks."
"""
        self.mock_python_code = """
def function_one():
    \"\"\"Function One performs task A.\"\"\"
    pass

def function_two():
    \"\"\"Function Two does task B and returns the result.\"\"\"
    pass

def function_three():
    \"\"\"Function Three takes inputs X and Y and produces output Z.\"\"\"
    pass
"""

    def test_extract_package_info_with_valid_toml(self):
        with open("pyproject.toml", "w") as toml_file:
            toml_file.write(self.mock_pyproject_toml)

        package_name, package_description = extract_package_info()
        self.assertEqual(package_name, "example_package")
        self.assertEqual(
            package_description,
            "This is a Python package for performing various tasks.",
        )

    def test_extract_package_info_with_missing_toml(self):
        package_name, package_description = extract_package_info()
        self.assertEqual(package_name, "example_package")
        self.assertEqual(
            package_description,
            "This is a Python package for performing various tasks.",
        )

    def test_extract_function_info(self):
        with open("your_package_file.py", "w") as python_file:
            python_file.write(self.mock_python_code)

        function_names, function_descriptions = extract_function_info()
        expected_names = ["function_one", "function_two", "function_three"]
        expected_descriptions = [
            "Function One performs task A.",
            "Function Two does task B and returns the result.",
            "Function Three takes inputs X and Y and produces output Z.",
        ]
        self.assertEqual(function_names, expected_names)
        self.assertEqual(function_descriptions, expected_descriptions)

    def test_create_llm_prompt(self):
        package_name = "example_package"
        package_description = "This is a Python package for performing various tasks."
        function_names = ["function_one", "function_two", "function_three"]
        function_descriptions = [
            "Function One performs task A.",
            "Function Two does task B and returns the result.",
            "Function Three takes inputs X and Y and produces output Z.",
        ]

        expected_prompt = (
            "# Package: example_package\n\n"
            "This is a Python package for performing various tasks.\n\n"
            "## Function: function_one\n\nFunction One performs task A.\n\n"
            "## Function: function_two\n\nFunction Two does task B and returns the result.\n\n"
            "## Function: function_three\n\nFunction Three takes inputs X and Y and produces output Z.\n\n"
        )

        llm_prompt = create_llm_prompt(
            package_name, package_description, function_names, function_descriptions
        )
        self.assertEqual(llm_prompt, expected_prompt)


if __name__ == "__main__":
    unittest.main()
