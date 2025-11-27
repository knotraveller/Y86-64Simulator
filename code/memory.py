import datautils

class Mem:
    def __init__(self):
        # Dictionary mapping integer address -> integer byte (0-255)
        # self.mem = {addr: byte, ...}
        self.mem = datautils.load_code()

    def read_byte(self, addr):
        return self.mem.get(addr, 0)

    def write_byte(self, addr, val):
        self.mem[addr] = val & 0xFF

    def read_u64(self, addr):
        """Reads 8 bytes as unsigned 64-bit int (Little Endian)."""
        val = 0
        for i in range(8):
            val |= (self.read_byte(addr + i) << (8 * i))
        return val

    def write_u64(self, addr, val):
        """Writes 8 bytes (Little Endian)."""
        val = datautils.to_unsigned(val)
        for i in range(8):
            self.write_byte(addr + i, (val >> (8 * i)) & 0xFF)