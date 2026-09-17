# Documentation

The analysis is written in German; each document opens with an English summary
box that carries the substance of it. The configuration and code are English
throughout.

| Document | Contents |
|---|---|
| [01-hardware-analyse.md](01-hardware-analyse.md) | Teardown of the adapter board, CN403, the transceiver, and the continuity measurement that decided the project |
| [02-xye-inbetriebnahme.md](02-xye-inbetriebnahme.md) | Wiring, wire colours, pre-power checks, bring-up, reading the log, troubleshooting, safety |
| [03-messprotokolle.md](03-messprotokolle.md) | What was measured on a running unit: power budget, standby, frame statistics, what the bus does and does not carry |
| [04-ir-protokoll-coolix.md](04-ir-protokoll-coolix.md) | The IR/XT protocol decoded: it is Coolix. Bit encoding, field layout, command tables, corrections to the reference projects, level shifter |
| [05-wegentscheidung.md](05-wegentscheidung.md) | Why a finished, verified implementation was set aside for a different path |

Suggested reading order for someone who wants to build this: 01 → 02, with 03
as the reference for anything you want to re-measure yourself. Documents 04 and
05 are the protocol work and the retrospective — interesting, not required.
