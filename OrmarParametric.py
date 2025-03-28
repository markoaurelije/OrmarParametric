# Assuming you have not changed the general structure of the template no modification is needed in this file.
# import traceback
import os
import sys
from . import commands
from .lib import fusionAddInUtils as futil

addin_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.join(addin_path, "lib")
if lib_path not in sys.path:
    sys.path.append(lib_path)


def run(context):
    try:
        commands.start()
    except:
        futil.handle_error("run")


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()

    except:
        futil.handle_error("stop")
