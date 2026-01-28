from desim.signal import SIG_UNDEFINED, EventTime, EventValue, TimeTypes
from desim.device import Device

class Pm(Device):
    def __init__(
            self,
            name: str,
            n_address_width: int,
            *,
            content: list[EventTime] | None = None,
            t_address: TimeTypes = 1.0,
            t_deselect: TimeTypes = 1.0,
            t_read: TimeTypes = 5.0,
    ):
        super().__init__(name)
        self.n_address_width = n_address_width
        self.n_slots = 2 ** n_address_width
        if content is None:
            content = [EventValue(0) for _ in range(self.n_slots)]
        self.content = content
        self.t_address = t_address
        self.t_deselect = t_deselect
        self.t_read = t_read
        self.add_output('output')
        self._address: int | None = None
        self.add_output('output', SIG_UNDEFINED)
    
    @Device.input
    def inp_addr(self, time: EventTime, value: EventValue):
        self.check_validstate('input:addr', 'idle')
        self._address = int(value.value) & (2 ** self.n_address_width - 1)
        self.state = "addressing"
        self.act(time + self.t_address, "act_addressed")
    
    @Device.action
    def act_addressed(self, time:EventTime):
        self.check_validstate('action:addressed', 'addressing')
        self.state = "read_ready"

    @Device.input
    def inp_read(self, time:EventTime, value:EventValue):
        self.check_validstate('input:read', 'read_ready')
        self.state = "reading"
        self.act(time + self.t_read, "act_value_out")
    
    @Device.action
    def act_value_out(self, time: EventTime):
        self.check_validstate('action:value_out', 'reading')
        value = self.content[self._address]
        self.out('output', value)
        self.state = "read_ready"

    @Device.input
    def inp_deselect(self, time: EventTime, value: EventValue):
        self.check_validstate('input:deselect', ['read_ready', 'idle'])
        self.state = "deselecting"
        self.act(time + self.t_deselect, "act_deselected")
    
    @Device.action
    def act_deselected(self, time:EventTime):
        self.check_validstate('action:deselected', 'deselecting')
        self.state = 'idle'
