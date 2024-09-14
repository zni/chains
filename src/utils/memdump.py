import string

def memdump(mem) -> None:
    for n in range(0, len(mem), 16):
        mem_slice = mem[n : n + 16]

        print(
            f"{n:04x}",
            " ".join(f"{x:02x}" for x in mem_slice), "|",
            "".join(chr(x) if chr(x) in "".join([string.digits, string.ascii_letters, string.punctuation]) else '.' for x in mem_slice)
        )