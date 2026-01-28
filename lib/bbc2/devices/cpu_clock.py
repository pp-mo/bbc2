"""
A clock that cycles through specific phases.

The outputs are a simple 'tick', and a h
"""
from typing import Optional

from desim.signal import TimeTypes, ValueTypes
from desim.device import Device

class CpuClock(Device):
    """Device that regularly cycles through N "phase" states 0..(N-1).

    Each phase also has a name.
    Provides outputs 'out_phase_name' and 'out_phase_number', and N per-state decoded
    outputs named 'out_phase_<number>'.

    """
    RESET_STATE = -1

    def __init__(
        self,
        name: str,
        period: float = 10.,
        phase_names: list[str] = ["P0_@PM", "P1_=IR", "P2_=K", "P3_@DM", "P4_adc_sto"],
    ):
        """No means of stopping it."""
        super().__init__(name)
        self.period = float(period)
        self.phase_names = phase_names
        self.n_phases = len(phase_names)
        self.i_phase = -1  # Start with phase=0
        self.add_output("out_phase_number")
        self.add_output("out_phase_name")
        for i_bit in range(self.n_phases):
            self.add_output(f"out_phase_{i_bit}", 0)

    @Device.input
    def start(self, time: TimeTypes, value: ValueTypes | None = None):
        if self.state != -1:
            msg = "Already ticking : cannot restart"
            raise ValueError(msg)
        self.state = 0
        self.act(time, 'do_tick')

    @Device.action
    def do_tick(self, time: TimeTypes):
        i_phase = self.state
        self.out('out_phase_number', i_phase)
        self.out('out_phase_name', self.phase_names[i_phase])
        self.outputs[f"out_phase_{i_phase}"].update(time, 1)
        self.state = (i_phase + 1) % self.n_phases
        self.act(time + self.period, "do_tick")
