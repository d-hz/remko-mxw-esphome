"""Remko XT - kabelgebundener TTL-"IR"-Sender fuer Remko-/Midea-Innengeraete.

Stellt einen ESPHome-`remote_transmitter`-kompatiblen Sender bereit, der die
Mark/Space-Timings NICHT auf einen 38-kHz-Traeger moduliert, sondern direkt als
TTL-Pegel auf einen GPIO ausgibt. Damit laesst sich jede vorhandene
`climate_ir`-Plattform (hier: `coolix`) unveraendert ueber die Kabelverbindung
zum Stecker CN501 der Anzeigeplatine betreiben.

  climate: platform coolix  --> transmitter_id: <remote_transmitter>  (38 kHz IR)
                            --> transmitter_id: <remko_xt>            (TTL an XT)
"""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.components import remote_base
from esphome.const import CONF_ID, CONF_PIN

CODEOWNERS = ["@d-hz"]
AUTO_LOAD = ["remote_base"]
MULTI_CONF = True

remko_xt_ns = cg.esphome_ns.namespace("remko_xt")
RemkoXtTransmitter = remko_xt_ns.class_(
    "RemkoXtTransmitter", cg.Component, remote_base.RemoteTransmitterBase
)

CONF_BIT_TIME = "bit_time"
CONF_QUANTIZE = "quantize"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(RemkoXtTransmitter),
        # Der GPIO, der (ueber den BC337-Pegelwandler) an CN501/XT geht.
        cv.Required(CONF_PIN): pins.internal_gpio_output_pin_schema,
        # Bitzeit der Original-Schnittstellenplatine: 545 us (~1800 Baud).
        cv.Optional(CONF_BIT_TIME, default="545us"): cv.positive_time_period_microseconds,
        # Rastet jedes Mark/Space auf ein ganzzahliges Vielfaches von bit_time.
        # Damit ist der Bitstrom byte-identisch mit dem der Originalplatine.
        cv.Optional(CONF_QUANTIZE, default=True): cv.boolean,
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    pin = await cg.gpio_pin_expression(config[CONF_PIN])
    var = cg.new_Pvariable(config[CONF_ID], pin)
    await cg.register_component(var, config)
    cg.add(var.set_bit_time(config[CONF_BIT_TIME].total_microseconds))
    cg.add(var.set_quantize(config[CONF_QUANTIZE]))
