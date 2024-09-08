import getopt
import sys
import time

from core.system import System

def main():
    (opts, _) = getopt.getopt(sys.argv[1:], 'f:t')

    program = None
    trace = False
    for (opt, arg) in opts:
        if opt == '-f':
            program = arg
        elif opt == '-t':
            trace = True

    if program is None:
        raise RuntimeError("No program specified")

    system = System()
    system.load(program)
    system.start(trace=trace)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise e
