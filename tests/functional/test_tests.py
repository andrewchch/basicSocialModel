def test_import_paths():
    import sys
    import os

    # Get the current working directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Get the parent directory (one level up)
    parent_dir = os.path.dirname(current_dir)

    # Add the parent directory to sys.path
    sys.path.append(parent_dir)
    # print("sys.path:", sys.path)

    # Check if the parent directory is in sys.path
    assert parent_dir in sys.path, "Parent directory not found in sys.path"