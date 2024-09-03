import getopt
import sys
import time

from core.mpu import MPU
from header.ines import INESHeader

def main():
    (opts, _) = getopt.getopt(sys.argv[1:], 'f:')

    program = None
    for (opt, arg) in opts:
        if opt == '-f':
            program = arg

    if program is None:
        raise RuntimeError("No program specified")

    nes = INESHeader(program)
    nes.read()
    nes.dump()

    c = MPU()
    c.load(program, prg_size=nes.prg_rom)
    c.reset()
    t0 = time.time()
    cycles = c.run(trace=True)
    t1 = time.time()
    print(f'Performed {cycles} execution cycles in {t1 - t0:.08f} seconds')
    c.dump()

if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(e)
