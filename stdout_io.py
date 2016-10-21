"""Functions for interacting with the console."""
import sys

def update_stdout(data):
    """Print text to the same line of STDOUT repeatedly, overwriting previous."""
    sys.stdout.write("\r%s" % str(data))
    sys.stdout.flush()
