
from datautils import *

class Raw_CPU:
    def __init__(self, mem):
        self.STAT = STAT_AOK
        self.CC = {'ZF': 1, 'SF': 0, 'OF': 0}
        self.PC = 0         # Start at address 0
        self.reg = [0] * 16 # Use list for indexed access
        self.reg_names = REG_NAMES
        self.mem = mem
    def fetch(self):
        raise NotImplementedError('fetch method need to be implemented')
    def decode(self):
        raise NotImplementedError('decode method need to be implemented')
    def execute(self):
        raise NotImplementedError('execute method need to be implemented')
    def memory_stage(self):
        raise NotImplementedError('memory_stage method need to be implemented')
    def write_back(self):
        raise NotImplementedError('write_back method need to be implemented')
    def pc_update(self):
        raise NotImplementedError('pc_update method need to be implemented')
    def step(self):
        raise NotImplementedError('step method need to be implemented')

class CPUSimulator(Raw_CPU):
    def __init__(self, mem):
        super().__init__(mem)
        
        # state between stages
        self.icode = 0
        self.ifun = 0
        self.rA = 15        # 'none'
        self.rB = 15        # 'none'
        self.valC = 0
        self.valP = 0
        self.valA = 0
        self.valB = 0
        self.srcA = 15
        self.srcB = 15
        self.valE = 0
        self.valM = 0
        self.cnd = False

    def fetch(self):
        """
        Fetch stage: Reads instruction, extracts icode/ifun, registers, constant, and next PC.
        """
        # Read instruction byte
        icode_ifun = self.mem.read_byte(self.PC)
        self.icode = (icode_ifun >> 4) & 0xF
        self.ifun = icode_ifun & 0xF
        
        # Valid instruction check could happen here, but STAT_INS logic is usually end of cycle
        
        self.rA = 15
        self.rB = 15
        self.valC = 0
        self.valP = self.PC + 1
        
        # Determine instruction layout
        # cmov, irmov, rmmov, mrmov, op, push, pop
        need_reg = self.icode in [2, 3, 4, 5, 6, 10, 11]
        # irmov, rmmov, mrmov, jxx, call
        need_valC = self.icode in [3, 4, 5, 7, 8]
        
        if need_reg:
            regs = self.mem.read_byte(self.valP)
            self.rA = (regs >> 4) & 0xF
            self.rB = regs & 0xF
            self.valP += 1
            
        if need_valC:
            self.valC = self.mem.read_u64(self.valP)
            self.valP += 8
            
        # Check for invalid instruction (simple check based on valid icodes)
        if self.icode > 11:
            self.STAT = STAT_INS

    def decode(self):
        """
        Decode stage: Reads operands from registers.
        """
        # Determine srcA
        self.srcA = 15
        if self.icode in [2, 4, 6, 10]: self.srcA = self.rA
        elif self.icode in [9, 11]: self.srcA = REG_ID['rsp'] # %rsp
        
        # Determine srcB
        self.srcB = 15
        if self.icode in [4, 5, 6]: self.srcB = self.rB
        elif self.icode in [8, 9, 10, 11]: self.srcB = REG_ID['rsp'] # %rsp
        
        # Read registers
        self.valA = self.reg[self.srcA] if self.srcA != 15 else 0
        self.valB = self.reg[self.srcB] if self.srcB != 15 else 0

    def execute(self):
        """
        Execute stage: ALU operations and Condition Code (CC) updates.
        """
        self.valE = 0
        self.cnd = False
        
        # ALU Logic
        if self.icode == 6: # OPq
            a = to_signed(self.valA)        # the operator are applied on signed values
            b = to_signed(self.valB)
            res = 0
            
            if self.ifun == 0: res = b + a    # addq
            elif self.ifun == 1: res = b - a  # subq
            elif self.ifun == 2: res = b & a  # andq
            elif self.ifun == 3: res = b ^ a  # xorq
            else:
                self.STAT = STAT_INS
                return
            
            self.valE = to_unsigned(res)
            
            # Set CC
            self.CC['ZF'] = 1 if self.valE == 0 else 0
            self.CC['SF'] = 1 if to_signed(self.valE) < 0 else 0
            self.CC['OF'] = 0
            
            # Overflow logic
            if self.ifun == 0: # add
                if (a < 0) == (b < 0) and (to_signed(self.valE) < 0) != (a < 0): 
                    self.CC['OF'] = 1
            elif self.ifun == 1: # sub (b - a)
                if (a < 0) != (b < 0) and (to_signed(self.valE) < 0) != (b < 0): 
                    self.CC['OF'] = 1
                    
        elif self.icode in [2, 7]: # cmovXX, jXX
            zf = self.CC['ZF']; sf = self.CC['SF']; of = self.CC['OF']
            # Determine Cnd based on ifun
            if self.ifun == 0: self.cnd = True              # rrmovq / jmp
            elif self.ifun == 1: self.cnd = (sf ^ of) or zf # le
            elif self.ifun == 2: self.cnd = (sf ^ of)       # l
            elif self.ifun == 3: self.cnd = zf              # e
            elif self.ifun == 4: self.cnd = not zf          # ne
            elif self.ifun == 5: self.cnd = not (sf ^ of)   # ge
            elif self.ifun == 6: self.cnd = not (sf ^ of) and not zf # g
            
            self.valE = self.valA # For cmovXX pass valA through

        elif self.icode == 3: # irmovq
            self.valE = self.valC
            
        elif self.icode in [4, 5]: # rmmovq, mrmovq
            # Address calculation
            self.valE = to_unsigned(to_signed(self.valB) + to_signed(self.valC))
            
        elif self.icode in [8, 10]: # call, pushq
            self.valE = to_unsigned(to_signed(self.valB) - 8)
            
        elif self.icode in [9, 11]: # ret, popq
            self.valE = to_unsigned(to_signed(self.valB) + 8)

    def memory_stage(self):
        """
        Memory stage: Reads or writes memory.
        """
        self.valM = 0
        
        # Check for Address Error logic (Basic check for negative addresses)
        # Note: In a real Dict memory, only negative keys are conceptually "out of bounds" for valid addr
        check_addr = -1
        if self.icode in [4, 10, 8]: check_addr = self.valE # Writes
        elif self.icode in [5]: check_addr = self.valE # Reads
        elif self.icode in [9, 11]: check_addr = self.valA # Reads
        
        check_addr = to_signed(check_addr)
        if check_addr < 0 and check_addr != -1:
            self.STAT = STAT_ADR
            return

        # Write Logic
        if self.icode in [4, 10]: # rmmovq, pushq
            self.mem.write_u64(self.valE, self.valA)
        elif self.icode == 8: # call
            self.mem.write_u64(self.valE, self.valP)
            
        # Read Logic
        if self.icode == 5: # mrmovq
            self.valM = self.mem.read_u64(self.valE)
        elif self.icode in [9, 11]: # ret, popq
            self.valM = self.mem.read_u64(self.valA)

    def write_back(self):
        """
        Write Back stage: Updates registers.
        """
        dstE = 15
        dstM = 15
        
        # Determine dstE
        if self.icode == 2 and self.cnd: dstE = self.rB
        elif self.icode == 3: dstE = self.rB
        elif self.icode == 6: dstE = self.rB
        elif self.icode in [8, 9, 10, 11]: dstE = 4 # %rsp
        
        # Determine dstM
        if self.icode in [5, 11]: dstM = self.rA
        
        # Execute Write
        if dstE != 15: self.reg[dstE] = self.valE
        if dstM != 15: self.reg[dstM] = self.valM

    def pc_update(self):
        """
        PC Update stage: Sets the PC for the next cycle.
        """
        if self.icode == 0: # halt
            self.STAT = STAT_HLT
        elif self.icode == 7 and self.cnd: # Taken branch
            self.PC = self.valC
        elif self.icode == 8: # call
            self.PC = self.valC
        elif self.icode == 9: # ret
            self.PC = self.valM
        else:
            self.PC = self.valP

    def step(self):
        """
        Executes one cycle of the CPU.
        """
        if self.STAT != STAT_AOK:
            return

        # Execute stages in order
        self.fetch()
        if self.STAT != STAT_AOK: return
        
        self.decode()
        self.execute()
        self.memory_stage()
        self.write_back()
        if self.STAT != STAT_AOK: return
        
        self.pc_update()

    def get_state(self):
        """
        Returns the current state of the CPU and Memory strictly formatted for JSON output.
        Reference:  "Memory: Non-zero 8-byte aligned words, interpreted as signed decimal"
        """
        # Registers: Output as signed decimal
        reg_out = {}
        for i, name in enumerate(REG_NAMES):
            if name != 'none':
                reg_out[name] = to_signed(self.reg[i])

        # Memory: Non-zero 8-byte aligned words
        mem_out = {}
        # Identify all 8-byte aligned start addresses that contain data in the sparse dict
        # We look for keys in memory, floor them to 8-byte align, and read the u64
        touched_bases = set()
        for k in self.mem.mem.keys():
            base = k - (k % 8)
            touched_bases.add(base)
            
        for base in touched_bases:
            val = self.mem.read_u64(base)
            if val != 0:
                # Key must be string of address, Value is signed decimal
                mem_out[str(base)] = to_signed(val)

        return {
            "CC": self.CC.copy(),
            "MEM": mem_out,
            "PC": self.PC,
            "REG": reg_out,
            "STAT": self.STAT
        }