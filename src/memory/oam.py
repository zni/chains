from memory.ram import RAM

class OAMEntry:
    def __init__(self):
        self.y = 0
        self.tile_num = 0
        self.attributes = 0
        self.x = 0

class OAMRAM(RAM):
    def __init__(self):
        super().__init__(256)

    def read(self, loc) -> OAMEntry:
        oam_entry = OAMEntry()
        oam_loc = loc * 4

        oam_entry.y = self.store[oam_loc]
        oam_entry.tile_num = self.store[oam_loc + 1]
        oam_entry.attributes = self.store[oam_loc + 2]
        oam_entry.x = self.store[oam_loc + 3]

        return oam_entry

    def write(self, loc, data):
        self.store[(loc & 0xFF)] = data