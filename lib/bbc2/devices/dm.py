from typing import Iterable

from desim.event import PostEventTypes
from desim.signal import (
    SIG_UNDEFINED, SIG_ZERO, EventValue, EventTime, TimeTypes, ValueTypes
)
from desim.device import Device


class Dev2(Device):
    """Some common helpers/extensions"""
    TIMES = {}
    STATES = []
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name)
        self.times = self.TIMES.copy()
        for time_name, time_value in self.TIMES.items():
            val = kwargs.pop(time_name, None)
            if val is not None:
                is_time = isinstance(val, (float, int))
                if is_time:
                    val_fixed = float(val)
                    is_time = val_fixed >= 0.0
                if not is_time:
                    msg = (
                        "Unexpected value or type for time-period argument: "
                        f"{time_name!r} = {val!r}, type {type(val)!r}."
                    )
                    raise ValueError(msg)
                time_value = val_fixed
            setattr(self, time_name, time_value)

    def change_state(
            self,
            opname: str,
            previous_state_s: str | list[str],
            new_state: str
    ):
        if isinstance(previous_state_s, str):
            previous_states = [previous_state_s]
        else:
            previous_states = list(previous_state_s)
        for name in previous_states + [new_state]:
            if not isinstance(name, str) or name not in self.STATES:
                msg = (
                    f"In operation {opname!r}, value {name!r} "
                    "is not the name of a known state."
                )
                raise ValueError(msg)
        self.check_validstate(name=opname, value_or_values=previous_states)
        self.state = new_state

    def act(
        self,
        time: TimeTypes,
        action_name: str,
        value: ValueTypes | None = None,
        context=None,
    ):
        """Add a little checking to the default implementation."""
        if action_name not in self.actions:
            msg = (
                f"In operation act({action_name!r}, {action_name!r} "
                "is not the name of a known action."
            )
            raise ValueError(msg)
        super().act(time, action_name, value, context)


class Dm(Dev2):
    STATES = [
        "idle",
        "address_changing",
        "reading",
        "read_done",
        "writing",
        "write_done",
        "deselecting"
    ]
    TIMES = {
        # Names and default values for periods.
        "t_address": 1.0,  # address change times
        "t_read": 5.0,  # fetch data (from select)
        "t_write": 5.0,  # send data
        "t_deselect": 2.0,  # address unlatch/write
    }
    def __init__(
            self,
            name: str,
            n_address_width: int,
            *,
            content: list[EventTime] | None = None,
            empty_value: ValueTypes = 0,
            **kwargs
    ):
        # Register name and capture time arguments
        super().__init__(name, **kwargs)
        self.n_address_width = n_address_width
        self.n_slots = 2 ** n_address_width
        self.empty_value = EventValue(empty_value)
        if content is None:
            content = [self.empty_value for _ in range(self.n_slots)]
        self.content = content
        self.add_output('output', SIG_ZERO)
        # Other state vars to be used
        self._address: int | None = None
        self._readval = None
        self._writeval = None

    @Device.input
    def inp_addr(self, time: EventTime, value: EventValue) -> PostEventTypes:
        self.change_state("inp_addr", "idle", "address_changing")
        self._address = int(value.value) & (2 ** self.n_address_width - 1)
        self.act(time + self.t_address, "act_address_settled")

    @Device.action
    def act_address_settled(self, time: EventTime) -> PostEventTypes:
        # Ok with this, settling again
        self.change_state("act_addr_settled", "address_changing", "idle")

    @Device.input
    def inp_select(self, time: EventTime, value: EventValue) -> PostEventTypes:
        self.change_state("inp_select", "idle", "reading")
        self.out("output", SIG_UNDEFINED)
        self.act(time + self.t_read, "act_read_done")

    @Device.action
    def act_read_done(self, time: EventTime) -> PostEventTypes:
        self.change_state("act_read_done", "reading", "read_done")
        self.out("output", self.content[self._address])

    @Device.input
    def inp_write(self, time: EventTime, value: EventValue) -> PostEventTypes:
        """
        Note: can only happen once, hence 'deselect' has 2 valid states:
        either "await_deselect" OR "written".
        """
        self.change_state("inp_write", "read_done", "writing")
        self._writeval = value
        self.act(time + self.t_write, "act_write_done")

    @Device.action
    def act_write_done(self, time: EventTime) -> PostEventTypes:
        self.content[self._address] = self._writeval
        self.change_state("act_read_done", "writing", "write_done")


    @Device.input
    def inp_deselect(self, time: EventTime, value: EventValue) -> PostEventTypes:
        self.change_state("inp_deselect", ["idle", "read_done", "write_done"], "deselecting")
        self.act(time + self.t_deselect, "act_deselected")

    @Device.action
    def act_deselected(self, time: EventTime) -> PostEventTypes:
        self.change_state("act_deselected", "deselecting", "idle")
