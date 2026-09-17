#include "remko_xt.h"

#include "esphome/core/application.h"
#include "esphome/core/log.h"

namespace esphome {
namespace remko_xt {

static const char *const TAG = "remko_xt";

void RemkoXtTransmitter::setup() {
  this->pin_->setup();
  // Ruhepegel: "space" -> Transistor sperrt -> XT liegt ueber den Pull-up auf 5 V.
  this->pin_->digital_write(false);
}

void RemkoXtTransmitter::dump_config() {
  ESP_LOGCONFIG(TAG, "Remko XT transmitter (wired TTL):");
  LOG_PIN("  Pin: ", this->pin_);
  ESP_LOGCONFIG(TAG, "  Bit time: %" PRIu32 " us", this->bit_time_);
  ESP_LOGCONFIG(TAG, "  Quantize to bit grid: %s", YESNO(this->quantize_));
}

void RemkoXtTransmitter::send_internal(uint32_t send_times, uint32_t send_wait) {
  const auto &data = this->temp_.get_data();
  if (data.empty())
    return;

  ESP_LOGV(TAG, "Sending %u timing items, %" PRIu32 "x", (unsigned) data.size(), send_times);

  for (uint32_t pass = 0; pass < send_times; pass++) {
    // Absolute Zeitbasis statt Aufsummieren von delayMicroseconds(): so
    // akkumuliert sich der Overhead der Schleife nicht ueber ~170 Bitslots auf.
    uint32_t target = micros();

    for (int32_t item : data) {
      const bool mark = item > 0;
      uint32_t length = mark ? (uint32_t) item : (uint32_t) (-item);

      if (this->quantize_) {
        // Die Originalplatine schiebt einen starren Bitstrom mit 545 us/Bit
        // heraus. Runden auf das Bitraster macht die Ausgabe bit-identisch.
        uint32_t slots = (length + this->bit_time_ / 2) / this->bit_time_;
        if (slots == 0)
          slots = 1;
        length = slots * this->bit_time_;
      }

      this->pin_->digital_write(mark);
      target += length;
      // Busy-Wait: Ueberlauf-sicher durch die vorzeichenbehaftete Differenz.
      while ((int32_t) (micros() - target) < 0) {
        App.feed_wdt();
      }
    }

    // Leitung definiert im Ruhepegel hinterlassen.
    this->pin_->digital_write(false);
    App.feed_wdt();

    if (pass + 1 < send_times && send_wait > 0)
      delay(send_wait / 1000);
  }
}

}  // namespace remko_xt
}  // namespace esphome
