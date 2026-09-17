# IR / XT command table

`remko-coolix-codes.csv` — 148 commands for the Remko MXW series, each in two
representations.

The table is **generated**, not captured: an encoder was written from the
decoded Coolix structure and verified byte-for-byte against all 24 reference
arrays published by the `remko2mqtt` projects (24 match, 0 mismatch). The
derivation is in [`docs/04-ir-protokoll-coolix.md`](../docs/04-ir-protokoll-coolix.md).

## Columns

| Column | Meaning |
|---|---|
| `function` | human-readable label |
| `mode` | `off`, `cool`, `heat`, `dry`, `fan_only`, `heat_cool`, `swing`, `led`, `silence` |
| `fan` | `low`, `medium`, `high`, `auto`, or `auto (forced)` where the mode pins it |
| `temp_c` | setpoint in °C, `-` for commands without one |
| `coolix` | the 24-bit Coolix payload, e.g. `0xB25F70` |
| `xt_frame` | the ready-made 21-byte level bitmap for the wired XT path |

## What you can do with it

* **Send over IR.** Feed the `coolix` value to any Coolix-capable transmitter.
  In ESPHome that is `remote_transmitter.transmit_coolix: { first: 0xB25F70 }`,
  or simply `climate: platform: coolix`, which builds these codes itself.
* **Send over the wired XT pin.** Shift the `xt_frame` bytes out LSB-first at
  545 µs per bit. That is exactly what the display board's own interface does.
* **Check your own unit.** Capture your remote with `remote_receiver` and
  `dump: all`, then look the received code up in this table.

## Coverage

Power off · toggle swing · toggle display LED · toggle silence/feel ·
fan only × 4 fan steps · cool × 4 fan steps × 17–30 °C ·
heat × 4 fan steps × 17–30 °C · auto and dry × 17–30 °C (fan forced).

The published reference projects only ever listed 17–24 °C. The full
**17–30 °C** range falls straight out of the Coolix encoding and is included
here.

## Caveat

Decoded against arrays captured on an **MXW 353 (2016)**. The units this
project was built on are 204/264/354/524 from 2019. Almost certainly identical,
but the wired XT path was never put on hardware — the bidirectional XYE bus
made it unnecessary. Confirm on your own unit in five minutes with
[`legacy-xt/examples/ir-capture.yaml`](../legacy-xt/examples/ir-capture.yaml).
