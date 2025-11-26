from memory import Mem
from datautils import STAT_AOK
import json
from cpu import CPUSimulator

def main():
    # Initialize Memory (implicitly loads from stdin via datautils)
    memory = Mem()
    
    # Initialize CPU and register memory
    cpu = CPUSimulator(memory)  
    
    output_log = []

    # Main Execution Loop
    while cpu.STAT == STAT_AOK:
        cpu.step()
        output_log.append(cpu.get_state())

    # Output JSON exactly as required [cite: 174, 177]
    print(json.dumps(output_log, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()