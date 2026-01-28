from bbc2.devices.dm import Dm

from desim.event import Event
from desim.sequencer import Sequencer

dm = Dm(
    'dm8',
    n_address_width=3,
    content=[1, 5, 2, 6, 3, 7, 4, 0],
)
dm.trace("*")

seq = Sequencer()
seq.verbose = True
seq.add([
    Event(1.0, dm.inp_addr, 3),
    Event(10.0, dm.inp_select, 0),
    Event(20.0, dm.inp_deselect, 0),

    Event(50.0, dm.inp_addr, 2),
    Event(52.0, dm.inp_select, 0),
    Event(60.0, dm.inp_write, 7),
    Event(70.0, dm.inp_deselect, 0),
])

# seq.verbose = True
dm.trace("*")
# dm.untrace("out")
# dm.untrace("act")
seq.run()