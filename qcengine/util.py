"""
Several import utilities
"""

import importlib
import io
import operator
import sys
import time
import traceback
from contextlib import contextmanager

from . import config

__all__ = ["compute_wrapper", "get_module_function"]

@contextmanager
def compute_wrapper(capture_output=True):
    """Wraps compute for timing, output capturing, and raise protection
    """

    ret = {"stdout": "", "stderr": ""}

    # Start timer
    comp_time = time.time()

    # Capture stdout/err
    new_stdout = io.StringIO()
    new_stderr = io.StringIO()
    if capture_output:

        old_stdout, sys.stdout = sys.stdout, new_stdout
        old_stderr, sys.stderr = sys.stderr, new_stderr

    try:
        yield ret
        ret["success"] = True
    except Exception as e:
        ret["error_message"] = "QCEngine Call Error:\n" + traceback.format_exc()
        ret["success"] = False

    # Place data
    ret["wall_time"] = time.time() - comp_time
    if capture_output:
        ret["stdout"] = new_stdout.getvalue()
        ret["stderr"] = new_stderr.getvalue()

        if ret["stdout"] == "":
            ret["stdout"] = "No stdout recieved."

        if ret["stderr"] == "":
            ret["stderr"] = "No stderr recieved."

        # Replace stdout/err
        if capture_output:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    else:
        ret["stdout"] = "stdout not captured"
        ret["stderr"] = "stderr not captured"

def get_module_function(module, func_name, subpackage=None):
    """Obtains a function from a given string

    Parameters
    ----------
    module : str
        The module to pull the function from
    func_name : str
        The name of the function to aquire, can be in a subpackage
    subpackage : None, optional
        Explicitly import a subpackage if required

    Returns
    -------
    ret : function
        The requested functions

    Example
    -------

    # Import numpy.linalg.eigh
    f = get_module_function("numpy", "linalg.eigh")
    f(np.ones((2, 2)))

    """
    # Will throw import error if we fail
    pkg = importlib.import_module(module, subpackage)

    return operator.attrgetter(func_name)(pkg)

def handle_output_metadata(output_data, metadata, raise_error=False):
    """
    Fuses general metadata and output together.
    """

    output_data["stdout"] = metadata["stdout"]
    output_data["stderr"] = metadata["stderr"]
    if metadata["success"] is not True:
        output_data["success"] = False
        output_data["error_message"] = metadata["error_message"]

    # Raise an error if one exists and a user requested a raise
    if raise_error and (output_data["success"] is not True):
        raise ValueError(output_data["error_message"])

    # Fill out provenance datadata
    if "provenance" in output_data:
        output_data["provenance"].update(config.get_provenance())
    else:
        output_data["provenance"] = config.get_provenance()

    output_data["provenance"]["wall_time"] = metadata["wall_time"]

    return output_data