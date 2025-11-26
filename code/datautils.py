import sys

# =================================================================================
# CONSTANTS
# =================================================================================
STAT_AOK = 1
STAT_HLT = 2
STAT_ADR = 3
STAT_INS = 4

REG_NAMES = [
    'rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi',
    'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'none'
]

REG_ID = {name: i for i, name in enumerate(REG_NAMES)}

# =================================================================================
# NUMERIC UTILS
# =================================================================================
def to_signed(n):
    """Convert unsigned 64-bit int to signed 64-bit int."""
    n &= 0xFFFFFFFFFFFFFFFF
    if n & (1 << 63):
        return n - (1 << 64)
    return n

def to_unsigned(n):
    """Convert signed int to unsigned 64-bit int."""
    return n & 0xFFFFFFFFFFFFFFFF

# =================================================================================
# LOADER UTILS
# =================================================================================
def load_code():
    lines = sys.stdin.readlines()
    mem = {}
    for line in lines:
        mem_update = parse_code(line)
        if mem_update:
            mem.update(mem_update)
    return mem

def parse_code(line):
    # Parse line: "0x000: 30f2... | comment"
    mem_update = {}
    parts = line.split('|')[0].strip().split(':')
    if len(parts) < 2: return None
    
    try:
        addr = int(parts[0], 16)
        data_str = parts[1].strip()
        if not data_str: return None

        # Write bytes to memory
        for i in range(0, len(data_str), 2):
            byte_val = int(data_str[i:i+2], 16)
            mem_update[addr + i//2] = byte_val
    except ValueError:
        return None
    return mem_update