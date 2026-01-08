import ast
import os
from pathlib import Path


def check_documentation(directory: str):
    """
    Analyzes Python files in a directory to find missing docstrings.

    This script walks through the specified directory, parses each Python file
    (excluding migrations and __init__.py), and checks for the presence of
    docstrings in modules, classes, and functions.

    It prints a report of all undocumented items.
    """
    project_path = Path(directory)
    undocumented_items = []

    for py_file in project_path.rglob("*.py"):
        # Exclude migrations, venv, and __init__ files from the check
        if (
            "migrations" in py_file.parts
            or ".venv" in py_file.parts
            or py_file.name == "__init__.py"
        ):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            # Check for module-level docstring
            module_docstring = ast.get_docstring(tree)
            if not module_docstring:
                undocumented_items.append(f"Module docstring missing in: {py_file}")

            # Check for docstrings in functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        undocumented_items.append(
                            f"  Function '{node.name}' on line {node.lineno} in {py_file} is missing a docstring."
                        )
                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        undocumented_items.append(
                            f"  Class '{node.name}' on line {node.lineno} in {py_file} is missing a docstring."
                        )
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    if undocumented_items:
        print("Undocumented Items Found:")
        for item in undocumented_items:
            print(item)
    else:
        print("All checked items appear to be documented.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python doc_checker.py <directory_path>")
        sys.exit(1)

    target_directory = sys.argv[1]
    if not os.path.isdir(target_directory):
        print(f"Error: Directory not found at '{target_directory}'")
        sys.exit(1)

    check_documentation(target_directory)
