from bbc2.devices.cpu_clock import CpuClock

from desim.event import Event
from desim.sequencer import Sequencer

clk = CpuClock("clk", period=10)
clk.trace("*")
# clk.trace("out_phase_number")
# clk.trace("out_phase_name")
for i_bit in range(5):
    clk.trace(f"out_phase_{i_bit}")

seq = Sequencer()
seq.verbose = True
seq.add(Event(time=0.1, call=clk.start))
seq.until(100.0)
# seq.step(10)
