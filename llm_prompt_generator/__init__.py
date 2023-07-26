import ast
import toml
from pathlib import Path
import logging
import tap


# Write logging info to stdout
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)


class Arguments(tap.Tap):
    """Arguments to be passed to the script."""

    root_dir: Path  # Path to the root directory of the Python package.
    output: Path = Path("prompt.txt")  # Path to the output file.


def create_llm_prompt(
    package_name: str,
    package_description: str,
    function_names: list[str],
    function_descriptions: list[str],
):
    """
    Create a Long-Form Language (LLM) prompt for a Python package.

    Args:
        package_name (str): The name of the Python package.
        package_description (str): A brief description of the package.
        function_names (list of str): List of function names in the package.
        function_descriptions (list of str): List of function descriptions corresponding to function_names.

    Returns:
        str: LLM prompt for the Python package.
    """
    prompt = f"# Package: {package_name}\n\n"
    prompt += f"{package_description}\n\n"

    for func_name, func_desc in zip(function_names, function_descriptions):
        prompt += f"## Function: {func_name}\n\n"
        prompt += f"{func_desc}\n\n"

    return prompt


def extract_package_info(root_dir: Path):
    """
    Extract package name and description from pyproject.toml using Poetry.

    Returns:
        tuple: A tuple containing the package name and description.
    """
    try:
        with open("pyproject.toml", "r") as toml_file:
            pyproject_data = toml.load(toml_file)
            package_name = pyproject_data["tool"]["poetry"]["name"]
            package_description = pyproject_data["tool"]["poetry"]["description"]
    except (FileNotFoundError, KeyError):
        raise FileNotFoundError(
            "pyproject.toml not found. Please run the script from the root directory of the Python package."
        )

    return package_name, package_description


def extract_function_info(filename: Path):
    """
    Extract function names and descriptions from Python code using AST.

    Returns:
        tuple: A tuple containing lists of function names and descriptions.
    """
    try:
        with open(filename, "r") as python_file:
            code = python_file.read()
    except UnicodeDecodeError:
        with open(filename, "r", encoding="utf-8") as python_file:
            code = python_file.read()

    function_names = []
    function_descriptions = []

    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
            description = ast.get_docstring(node)
            if description is not None:
                function_descriptions.append(description)

            function_descriptions.append(ast.unparse(node))

        if isinstance(node, ast.ClassDef):
            function_names.append(node.name)
            description = ast.get_docstring(node)
            if description is not None:
                function_descriptions.append(description)

            function_descriptions.append(ast.unparse(node))

    return function_names, function_descriptions


def list_candidate_files(root_dir: Path):
    """
    List all Python files in the package.
    Do not consider path in the files .gitignore and .gptignore

    Returns:
        list: A list of Path objects corresponding to Python files in the package.
    """
    filenames = list(root_dir.rglob("*.py"))

    # Discard files in .gitignore and .gptignore
    ignore_patterns = []
    for ignore_file in [".gitignore", ".gptignore"]:
        try:
            with open(root_dir / ignore_file, "r") as ignore:
                ignore_patterns.extend(ignore.read().splitlines())
        except FileNotFoundError:
            continue

    for pattern in ignore_patterns:
        filenames = [
            filename
            for filename in filenames
            if not match_file_pattern(pattern, filename)
        ]

    return filenames


def match_file_pattern(pattern: str, filename: Path):
    """
    Check if the pattern (following .gitignore conventions) matches the filename.
    """
    if pattern.startswith("#"):
        return False
    if pattern == "":
        return False

    if pattern.endswith("/"):
        return filename.is_dir() and pattern[:-1] in filename.as_posix()

    if pattern.startswith("**"):
        pattern = pattern[2:]
        return pattern in filename.name

    if pattern.startswith("*"):
        pattern = pattern[1:]
        return pattern in filename.as_posix()

    parts = [p.name for p in filename.parents] + [filename.name]

    if pattern.endswith("*"):
        pattern = pattern[:-1]
        return any(pattern in part for part in parts)

    return any(pattern == part for part in parts)


if __name__ == "__main__":
    args = Arguments().parse_args()

    package_name, package_description = extract_package_info(args.root_dir)

    filenames = list_candidate_files(args.root_dir)
    logging.info(f"Found {len(filenames)} Python files.")

    function_names = []
    function_descriptions = []

    for filename in filenames:
        function_names_, function_descriptions_ = extract_function_info(filename)
        function_names.extend(function_names_)
        function_descriptions.extend(function_descriptions_)

    llm_prompt = create_llm_prompt(
        package_name, package_description, function_names, function_descriptions
    )

    with open(args.output, "w") as output_file:
        output_file.write(llm_prompt)
