import getopt
import sys
import time

from core.system import System

def main():
    (opts, _) = getopt.getopt(sys.argv[1:], 'f:')

    program = None
    for (opt, arg) in opts:
        if opt == '-f':
            program = arg

    if program is None:
        raise RuntimeError("No program specified")

    system = System()
    system.load(program)
    system.start(trace=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
