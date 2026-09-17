# ESPHome configuration

| File | Purpose |
|---|---|
| `packages/remko-xye-base.yaml` | **the shared package** — every setting lives here |
| `example-room.yaml` | per-unit file: device name and display name, nothing else |
| `secrets.yaml.example` | template for `secrets.yaml` (git-ignored) |

## Use

```bash
cp secrets.yaml.example secrets.yaml   # then fill in the values
cp example-room.yaml ac-livingroom.yaml
esphome run ac-livingroom.yaml
```

One file per indoor unit, each with its own `device_name`. Make changes in the
**package**, not in the room files.

## Running from the ESPHome dashboard

The dashboard wants one self-contained file per device and does not handle the
`packages: !include` layout well. `tools/build-standalone-configs.py` resolves
the include and writes one flat file per room, ready to drop into
`/config/esphome/`. The same three secret keys have to exist in
`/config/esphome/secrets.yaml` on the Home Assistant host.

## Home Assistant

Connection is the ESPHome native API with encryption — no MQTT, no broker.
Home Assistant usually finds the device over mDNS. If the device sits in a
separate VLAN, mDNS often will not cross it: add the ESPHome integration by IP
and port `6053` manually, then paste the encryption key.

Per unit you get a `climate` entity plus outdoor temperature, both coil
temperatures, actual fan speed, compressor state, defrost state, error and
protection flags, the discovered XYE address, uptime, Wi-Fi signal and the
reset reason.
