from bbc2.devices.pm import Pm

from wirables import Event, Sequencer


pm = Pm(
    "pm8",
    n_address_width=3,
    content=["zero", "one", "two", "three", "four", "five", "six", "seven"],
)
pm.trace("output")

seq = Sequencer()
seq.add(
    [
        Event(1.0, pm.inp_addr, 2),
        Event(3.0, pm.inp_read, 0),
        Event(10.0, pm.inp_deselect, 0),
        Event(20.0, pm.inp_addr, 5),
        Event(22.0, pm.inp_read, 0),
    ]
)

# seq.verbose = True
pm.trace("*")
# pm.untrace("out")
# pm.untrace("act")
seq.verbose = True
seq.run()
