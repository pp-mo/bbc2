"""
A clock that cycles through specific phases.

The outputs are a simple 'tick', and a h
"""

from wirables import Device
from wirables.signal import TimeTypes, ValueTypes


class CpuClock(Device):
    """Device that regularly cycles through N "phase" states 0..(N-1).

    Each phase also has a name.
    Provides outputs 'out_phase_name' and 'out_phase_number', and N per-state decoded
    outputs named 'out_phase_<number>'.

    """

    STATES = ["idle", "ticking"]
    TIMINGS = {"t_period": 10.0}

    def __init__(
        self,
        name: str,
        phase_names: list[str] = ["P0_@PM", "P1_=IR", "P2_=K", "P3_@DM", "P4_adc_sto"],
        **kwargs,
    ):
        """No means of stopping it."""
        super().__init__(name, **kwargs)
        self.phase_names = phase_names
        self.n_phases = len(phase_names)
        self.i_phase = -1  # Start with phase=0
        self.add_output("out_phase_number", "-1")
        self.add_output("out_phase_name", "<stopped>")
        for i_bit in range(self.n_phases):
            self.add_output(f"out_phase_{i_bit}", 0)

    @Device.input
    def start(self, time: TimeTypes, value: ValueTypes | None = None):
        self.xto("idle", "ticking")
        self.i_phase = 0
        self.act("do_tick", time)

    @Device.action
    def do_tick(self, time: TimeTypes):
        i_phase = self.i_phase
        self.i_phase = (i_phase + 1) % self.n_phases
        self.out("out_phase_number", i_phase)
        self.out("out_phase_name", self.phase_names[i_phase])
        self.outputs[f"out_phase_{i_phase}"].update(time, 1)
        self.act("do_tick", time + self.t_period)
