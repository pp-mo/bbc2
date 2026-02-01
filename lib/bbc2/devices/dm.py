from wirables import (
    Device,
    SIG_UNDEFINED,
    SIG_ZERO,
    EventValue,
    EventTime,
)
from wirables.signal import ValueTypes


class Dm(Device):
    STATES = [
        "idle",
        "address_changing",
        "reading",
        "read_done",
        "writing",
        "write_done",
        "deselecting",
    ]
    TIMINGS = {
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
        content: list[EventValue] | None = None,
        empty_value: ValueTypes = SIG_ZERO,
        **kwargs,
    ):
        # Register name and capture time arguments
        super().__init__(name, **kwargs)
        self.n_address_width: int = n_address_width
        self.n_slots = 2**n_address_width
        self.empty_value = EventValue(empty_value)
        if content is None:
            content = [self.empty_value for _ in range(self.n_slots)]
        self.content: list[int] = content
        self.add_output("output", SIG_ZERO)
        # Other state vars to be used
        self._address: int = -1
        self._readval: int = -1
        self._writeval: int = -1

    @Device.input
    def inp_addr(self, time: EventTime, value: EventValue):
        self.xto("idle", "address_changing")
        self._address = int(value.value) & (2**self.n_address_width - 1)
        self.act("act_address_settled", time + self.t_address)

    @Device.action
    def act_address_settled(self, time: EventTime):
        # Ok with this, settling again
        self.xto("address_changing", "idle")

    @Device.input
    def inp_select(self, time: EventTime, value: EventValue):
        self.xto("idle", "reading")
        self.out("output", SIG_UNDEFINED)
        self.act("act_read_done", time + self.t_read)

    @Device.action
    def act_read_done(self, time: EventTime):
        self.xto("reading", "read_done")
        self.out("output", self.content[self._address])
        self.content[self._address] = 0  # destructive reads !

    @Device.input
    def inp_write(self, time: EventTime, value: EventValue):
        """
        Note: can only happen once, hence 'deselect' has 2 valid states:
        either "read_done" OR "write_done".
        """
        self.xto("read_done", "writing")
        self._writeval = int(value.value)
        self.act("act_write_done", time + self.t_write)

    @Device.action
    def act_write_done(self, time: EventTime):
        self.content[self._address] = self._writeval
        self.xto("writing", "write_done")

    @Device.input
    def inp_deselect(self, time: EventTime, value: EventValue):
        self.xto(["idle", "read_done", "write_done"], "deselecting")
        self.act("act_deselected", time + self.t_deselect)

    @Device.action
    def act_deselected(self, time: EventTime):
        self.xto("deselecting", "idle")
