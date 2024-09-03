import getopt
import sys
import time

from .core.mpu import MPU

def main():
    (opts, _) = getopt.getopt(sys.argv[1:], 'f:s:')

    start = 0
    program = None
    for (opt, arg) in opts:
        if opt == '-f':
            program = arg
        elif opt == '-s':
            start = int(arg, base=16)

    if program is None:
        raise RuntimeError("No program specified")

    c = MPU()
    c.load(program)
    c._pc.reg = start
    t0 = time.time()
    cycles = c.run()
    t1 = time.time()
    print(f'Performed {cycles} execution cycles in {t1 - t0:.08f} seconds')
    c.dump()

if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(e)
