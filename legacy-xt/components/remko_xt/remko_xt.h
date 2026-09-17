#pragma once

#include "esphome/components/remote_base/remote_base.h"
#include "esphome/core/component.h"
#include "esphome/core/hal.h"

#include <cinttypes>

namespace esphome {
namespace remko_xt {

/// Sender, der Mark/Space-Timings als TTL-Pegel statt als 38-kHz-IR ausgibt.
///
/// Pegel-Konvention (identisch zur Originalplatine):
///   Mark  (positiver Wert im Timing-Array) -> XT = LOW  (0 V)
///   Space (negativer Wert)                 -> XT = HIGH (5 V, Ruhepegel)
///
/// Mit dem invertierenden BC337-Pegelwandler entspricht ein Mark einem HIGH am
/// GPIO -> `inverted:` am Pin bleibt daher aus. Wird XT ausnahmsweise direkt
/// vom 3,3-V-GPIO getrieben, ist `inverted: true` zu setzen.
class RemkoXtTransmitter : public remote_base::RemoteTransmitterBase, public Component {
 public:
  explicit RemkoXtTransmitter(InternalGPIOPin *pin) : remote_base::RemoteTransmitterBase(pin) {}

  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  void set_bit_time(uint32_t bit_time_us) { this->bit_time_ = bit_time_us; }
  void set_quantize(bool quantize) { this->quantize_ = quantize; }

 protected:
  void send_internal(uint32_t send_times, uint32_t send_wait) override;

  uint32_t bit_time_{545};
  bool quantize_{true};
};

}  // namespace remko_xt
}  // namespace esphome
