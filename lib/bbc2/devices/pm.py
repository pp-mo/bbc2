from wirables import Device, SIG_UNDEFINED, EventTime, EventValue


class Pm(Device):
    TIMINGS = {
        "t_address": 1.0,
        "t_deselect": 1.0,
        "t_read": 5.0,
    }
    STATES = ["idle", "addressing", "read_ready", "reading", "deselecting"]

    def __init__(
        self,
        name: str,
        n_address_width: int,
        *,
        content: list[EventValue] | None = None,
    ):
        super().__init__(name)
        self.n_address_width = n_address_width
        self.n_slots = 2**n_address_width
        if content is None:
            content = [EventValue(0) for _ in range(self.n_slots)]
        self.content = content
        self.add_output("output")
        self._address: int = -1
        self.add_output("output", SIG_UNDEFINED)

    @Device.input
    def inp_addr(self, time: EventTime, value: EventValue):
        self.xto("idle", "addressing")
        self._address = int(value.value) & (2**self.n_address_width - 1)
        self.act("act_addressed", time + self.t_address)

    @Device.action
    def act_addressed(self, time: EventTime):
        self.xto("addressing", "read_ready")

    @Device.input
    def inp_read(self, time: EventTime, value: EventValue):
        self.xto("read_ready", "reading")
        self.act("act_value_out", time + self.t_read)

    @Device.action
    def act_value_out(self, time: EventTime):
        self.xto("reading", "read_ready")
        value = self.content[self._address]
        self.out("output", value)

    @Device.input
    def inp_deselect(self, time: EventTime, value: EventValue):
        self.xto(["read_ready", "idle"], "deselecting")
        self.act("act_deselected", time + self.t_deselect)

    @Device.action
    def act_deselected(self, time: EventTime):
        self.xto("deselecting", "idle")
