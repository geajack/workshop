from pathlib import Path
from datetime import datetime
import importlib
import importlib.metadata
import sys
import os
import shutil
import json
import pickle

loaded_results = []
output_directories = []

try:
    results_root = Path(os.environ["RESULTSROOT"]).resolve()
except KeyError:
    results_root = Path("results")

class ResultsDirectory(type(Path())):

    def json(self, path, data=None):
        if data is not None:
            with open(self / path, "w") as file:
                json.dump(data, file)
        else:
            with open(self / path, "r") as file:
                return json.load(file)

    def pickle(self, path, data=None):
        if data is not None:
            with open(self / path, "wb") as file:
                pickle.dump(data, file)
        else:
            with open(self / path, "rb") as file:
                return pickle.load(file)

    def numpy(self, path, data=None):
        import numpy
        if data is not None:
            numpy.save(self / path, data)
        else:
            return numpy.load(self / path)

    def binary(self, path, data=None):
        if data is not None:
            with open(self / path, "wb") as file:
                file.write(data)
        else:
            with open(self / path, "rb") as file:
                return file.read()

    def text(self, path, data=None):
        if data is not None:
            with open(self / path, "w") as file:
                file.write(data)
        else:
            with open(self / path, "r") as file:
                return file.read()
            

def find_source_code(code_root):
    modules = set()
    for name in sys.modules:
        module = sys.modules[name]
        try:
            module_file = Path(module.__file__)
            is_descendant = code_root in module_file.resolve().parents
            if is_descendant:
                modules.add(module_file.resolve())
        except (AttributeError, TypeError):
            pass
    return modules


def recursive_write_protect(root):
    file_read_only = 0o444
    directory_read_only = 0o555
    all_files = []
    all_dirs = []
    for root, dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(root, name)
            all_files.append(path)

        for name in dirs:
            path = os.path.join(root, name)
            all_dirs.append(path)

    for path in all_files:
        os.chmod(path, file_read_only)

    for path in all_dirs:
        os.chmod(path, directory_read_only)

    os.chmod(root, directory_read_only)


def create_results_directory(tag=None):
    try:
        code_root = Path(os.environ["CODEROOT"]).resolve()
    except KeyError:
        raise KeyError("Set CODEROOT environment variable to top directory containing your code. Any code used in this run under that directory will be copied into the results directory.")

    now = datetime.now().strftime("%d-%m-%y@%H:%M:%S")
    if tag is not None:
        output_directory_name = f"{tag}-{now}"
    else:
        output_directory_name = now
    
    output_directory = results_root / output_directory_name
    assert not output_directory.exists(), f"Output directory {output_directory} already exists."

    output_directory.mkdir(parents=True, exist_ok=True)
    
    details_directory = Path(output_directory) / "details"
    details_directory.mkdir(exist_ok=True, parents=True)

    code_directory = details_directory / "code"
    modules = find_source_code(code_root)
    for module_path in modules:
        target_path = code_directory / module_path.relative_to(code_root)
        target_path.parent.mkdir(exist_ok=True, parents=True)
        with open(target_path, "w") as file, open(module_path, "r") as source_file:
            file.write(source_file.read())

    with open(details_directory / "run.sh", "w") as file:
        print("python", *sys.argv, file=file)

    with open(details_directory / "requirements.txt", "w") as file:
        packages = importlib.metadata.distributions()
        for package in packages:
            name = package.metadata["Name"]
            version = package.metadata["Version"]
            print(f"{name}=={version}", file=file)

    if len(loaded_results) > 0:
        results_directory = details_directory / "results"
        results_directory.mkdir(exist_ok=True, parents=True)
        for result in loaded_results:
            shutil.copytree(result / "details", results_directory / result.name)

    recursive_write_protect(details_directory)
    
    directory = ResultsDirectory(output_directory)
    output_directories.append(directory)
    return directory


def load_results_directory(path):
    directory = ResultsDirectory(results_root / path)
    loaded_results.append(directory)

    read_only = 0o555
    full_access = 0o777
    for output_directory in output_directories:
        details_directory = output_directory / "details"
        os.chmod(details_directory, full_access)

        results_directory = details_directory / "results"
        results_directory.mkdir(exist_ok=True, parents=True)
        for result in loaded_results:
            shutil.copytree(result / "details", results_directory / result.name)

        recursive_write_protect(results_directory)
        os.chmod(details_directory, read_only)

    return directory