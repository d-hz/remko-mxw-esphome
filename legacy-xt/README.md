# Legacy: the wired XT path (Plan B)

Work that **functions but is not needed**. It did not fail — it was superseded.

The project started out aiming at the unidirectional **XT path**: the wire over
which the display board receives its demodulated IR command. The protocol was
fully decoded and an ESPHome component written for it. Only afterwards did it
turn out that the same unit exposes a **bidirectional bus**, unused and free, on
connector CN403 — the one the manufacturer's own central controller uses.

Kept as a fallback. If the XYE path fails on some variant of the hardware, a
complete second route is ready here.

## Contents

| Path | What it is | State |
|---|---|---|
| `components/remko_xt/` | ESPHome external component: emits Coolix timings as TTL levels instead of 38 kHz IR | compiles (esp32dev, RAM 26.6 %, flash 49.8 %) |
| `examples/xt-wired.yaml` | **Plan B** — TTL on CN501/XT | `esphome config` valid, never on hardware |
| `examples/ir-only.yaml` | **Plan C** — 38 kHz infrared, no intervention at all | `esphome config` valid, never on hardware |
| `examples/ir-capture.yaml` | records your remote, to confirm Coolix on your own unit | the fastest way to verify the protocol yourself |

The command table itself lives in [`../ir/`](../ir/) — it is useful regardless
of which path you take.

## How the component works

ESPHome separates the codec (`remote_base::CoolixProtocol`, which produces a
mark/space list) from the transmitter (`RemoteTransmitterBase`, which turns that
into levels). The stock `climate: platform: coolix` already produces exactly the
frames this unit expects, including the double transmission the original
interface board performs.

So nothing about the protocol needed reimplementing. The component is only a
second `RemoteTransmitterBase` that emits those timings **without the 38 kHz
carrier**, as TTL levels:

```
climate: platform: coolix
        |
        +-- transmitter_id: ir_tx    -> remote_transmitter  -> 38 kHz -> IR LED
        +-- transmitter_id: xt_tx    -> remko_xt            -> TTL    -> CN501/XT
```

One protocol implementation, two outputs, one line of YAML between them. And
the codec is the one ESPHome maintains, not a private copy.

Two details that matter:

**Absolute time base instead of a chain of `delayMicroseconds()`.** Over ~170
slots the loop overhead would otherwise accumulate to several percent of timing
error. A target timestamp is advanced instead, and waited on overflow-safely:

```cpp
target += length;
while ((int32_t) (micros() - target) < 0) { App.feed_wdt(); }
```

**`quantize: true` snaps to the bit grid.** The ESPHome Coolix codec works in
560 µs ticks, the original interface board shifts at 545 µs. With `quantize`,
every mark and space is rounded to the nearest integer multiple of `bit_time`
and emitted at that width — making the bit stream on XT identical to the
original board's. Without it the 560 µs timings go out; both work, the receiver
tolerates it, but 545 µs is closer to the original.

**Known quirk:** a transmission blocks for ~189 ms, and ESPHome logs
`Component ... took a long time for an operation`. That is cosmetic — Wi-Fi and
the API run in their own tasks on the ESP32, the watchdog is fed, and it only
happens on a user command. Getting rid of it would mean driving the RMT
peripheral with the carrier disabled: considerably more code, tied to the IDF
version, and the worse trade for this use case.

## What to watch out for if you revive this

* **CN501 is occupied.** The cable to the main board is plugged into it, so this
  path needs a Y-splice — distinctly more invasive than CN403.
* **The level shifter was never built.** The circuit is in
  [`../docs/04-ir-protokoll-coolix.md`](../docs/04-ir-protokoll-coolix.md); it is
  reasoned, not verified.
* **No state feedback.** This is the actual reason for the switch: Plan B and C
  control blind. Home Assistant never learns what the unit is really doing.
* **The Coolix finding was verified against an MXW 353 (2016).** The units this
  project ran on are 204/264/354/524 from 2019. Almost certainly identical —
  confirm it in five minutes with `examples/ir-capture.yaml`.
