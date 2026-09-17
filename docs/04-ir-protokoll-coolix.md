# Das IR-/XT-Protokoll ist Coolix

> **Summary (EN).** Remko does not use a proprietary IR protocol. The 21-byte
> arrays published by the `remko2mqtt` projects are not protocol fields at all
> — they are a packed bitmap of the line level, shifted out LSB-first at one
> level per 545 µs slot. Strip that encoding and 24 payload bits remain, which
> match ESPHome's built-in **Coolix** codec exactly, including its known
> constants (`0xB27BE0` = `COOLIX_OFF`, `0xB5F5A5` = `COOLIX_LED`). An encoder
> written from that structure reproduces **all 24 reference arrays byte for
> byte**. Consequences: no command table is needed in code, `climate: platform:
> coolix` covers the whole entity out of the box, and the units accept
> **17–30 °C**, not just the 17–24 °C the reference projects listed. This
> document also corrects four mislabelled constants in those projects.

**Quellen der Rückdekodierung:** `andineise/remko2mqtt` und
`xn--nding-jua/remko2mqtt` (inhaltlich identischer Fork), gegengeprüft gegen
ESPHome `dev` (`coolix`, `remote_base`, `climate_ir`).

---

## 1. Der Kernbefund

Die 21-Byte-Arrays aus beiden Repos wurden zurückdekodiert. Nach dem Abziehen
der Bitraster-Kodierung bleiben pro Kommando **24 Nutzbits** übrig, die exakt
dem in ESPHome eingebauten **Coolix**-Codec entsprechen — inklusive der
bekannten Konstanten:

| Kommando | dekodiert | ESPHome-Konstante |
|---|---|---|
| `PowerOff` | `0xB27BE0` | `COOLIX_OFF` |
| `cmd_led` | `0xB5F5A5` | `COOLIX_LED` |

Daraufhin wurde ein Generator gebaut (Coolix-Encoder → 545-µs-Raster →
21 Byte) und gegen **alle 24 im Repo hinterlegten Arrays** geprüft:

```
VALIDATION: 24 match, 0 mismatch (of 24)
```

Jedes einzelne Byte wird byte-genau reproduziert. Damit ist das Protokoll nicht
„plausibel rekonstruiert", sondern geschlossen verifiziert.

**Konsequenzen:**

1. Es braucht **keine** Kommandotabelle im Code. Modus, Solltemperatur
   (17–30 °C, nicht nur 17–24), vier Lüfterstufen und Swing ergeben sich aus der
   Coolix-Kodierung — die Repos hatten schlicht nur einen Ausschnitt aufgenommen.
2. Die ESPHome-Plattform `climate: platform: coolix` deckt die komplette
   Entität bereits ab. Neu zu schreiben ist **nur die Ausgabestufe**.
3. Kabel und IR teilen sich damit von selbst dieselbe Logik: ein und dieselbe
   `coolix`-Plattform bekommt entweder den TTL-Sender oder den 38-kHz-Sender
   zugewiesen — eine Zeile YAML Unterschied.

---

## 2. Der Stecker CN501

Anzeigeplatine, Belegung laut Repo-Dokumentation: **GND · 5V · XT · REC · 5V**

| Pin | Signal | Richtung (aus ESP-Sicht) | Verwendung |
|---|---|---|---|
| 1 | GND | — | Masse, **zwingend** gemeinsam mit dem ESP |
| 2 | +5 V | ← | mögliche Versorgung |
| 3 | **XT** | **→ Ausgang** | hier legt der ESP die Kommandos auf |
| 4 | REC | ← Eingang | demoduliertes IR des Geräteempfängers |
| 5 | +5 V | ← | zweiter 5-V-Pin |

Im Minimalfall braucht der ESP **zwei** Leitungen: GND und XT.

> **CN501 ist am untersuchten Gerät belegt** — dort steckt das Kabel zur
> Hauptplatine. Dieser Weg erfordert also ein Y-Stück oder das Anzapfen eines
> benutzten Steckers, nicht einfach „anstecken".

> Die Pin-*Reihenfolge* stammt aus der Repo-Dokumentation, nicht aus eigener
> Messung. Vor dem Anschließen mit dem Multimeter verifizieren: GND gegen
> Gehäusemasse durchklingeln, die beiden 5-V-Pins messen, XT und REC bleiben
> übrig. Beide ruhen auf HIGH — REC zappelt beim Druck auf die Fernbedienung,
> XT nicht.

### Elektrische Parameter

| Parameter | Wert |
|---|---|
| Pegel | TTL 0 V / +5 V |
| Ruhepegel | **HIGH (+5 V)** |
| Bitzeit | **545 µs** (im Code; die README nennt 550 µs ≈ 1800 Baud) |
| Rahmenlänge | 168 Bitslots = 21 Byte = **91,6 ms** |
| Wiederholung | jedes Kommando wird **zweimal** gesendet, ~5,5 ms Pause |
| Gesamtdauer | **≈ 189 ms** pro Befehl |
| Richtung | **unidirektional**, reines Schreiben |

---

## 3. Wie die Byte-Arrays auf die Leitung gehen

Das ist der Punkt, an dem die Repo-Dokumentation missverständlich ist: **die
Bytes sind keine Protokollfelder.** Sie sind eine gepackte Bitmap des
Pegelverlaufs.

```c
digitalWrite(pin, bitRead(cmd[i/8], i % 8));   // remko_lib.ino, Z. 152
```

Es wird Byte für Byte, **LSB zuerst**, ein Pegel pro 545-µs-Slot herausgeschoben.
Deshalb tauchen in den Arrays auch nur die acht Werte
`AA AB AE BA BB EA EB EE` auf — genau die Bitmuster, die die
Pulsabstandskodierung erzeugen kann. **Die Byte-Grenzen liegen quer zu den
Datenbits und haben keine Bedeutung.**

Der Slot-Strom darüber ist eine klassische Pulsabstandskodierung:

```
Header      : 8 Slots LOW  (4,36 ms)  +  8 Slots HIGH (4,36 ms)
Datenbit 0  : 1 Slot  LOW              +  1 Slot  HIGH
Datenbit 1  : 1 Slot  LOW              +  3 Slots HIGH
Footer      : 1 Slot  LOW              +  Rest HIGH (Ruhepegel)
```

Die Rechnung geht auf: 16 (Header) + 48 Marks + 24·1 + 24·3 (Spaces — durch die
Komplementbytes werden immer exakt 24 Einsen und 24 Nullen übertragen) + 1
(Footer-Mark) = **161 Slots**, plus 7 Slots Leerlauf = **168 = 21 Byte**. Das
letzte Byte ist deshalb in *jedem* Kommando `0xFE`.

---

## 4. Die Nutzdaten (Coolix, 24 Bit)

Die 48 übertragenen Bits sind **3 Nutzbytes, jedes gefolgt von seinem bitweisen
Komplement**, jeweils **MSB zuerst**:

```
B2 4D | 5F A0 | 70 8F
^^ ^^   Nutzbyte, Komplement
```

Aufbau der drei Nutzbytes:

| Byte | Inhalt |
|---|---|
| 0 | `0xB2` (Normalbefehle) bzw. `0xB5` (Sonderbefehle) |
| 1 | `Lüfter << 4 \| 0x0F` |
| 2 | `Temperatur << 4 \| Modus << 2` (Bits 1–0 immer 0) |

**Modus** (Bits 3–2 von Byte 2):

| Modus | Nibble | `climate`-Modus |
|---|---|---|
| Kühlen | `0b0000` | `cool` |
| Entfeuchten / nur Lüften | `0b0100` | `dry` / `fan_only` |
| Automatik | `0b1000` | `heat_cool` |
| Heizen | `0b1100` | `heat` |

**Lüfter** (oberes Nibble von Byte 1):

| Stufe | Nibble | Byte 1 |
|---|---|---|
| Auto | `0xB` | `0xBF` |
| Stufe 1 (min) | `0x9` | `0x9F` |
| Stufe 2 (mittel) | `0x5` | `0x5F` |
| Stufe 3 (max) | `0x3` | `0x3F` |
| erzwungen in Auto/Entfeuchten | `0x1` | `0x1F` |

**Temperatur** (oberes Nibble von Byte 2) — Gray-Code, 17–30 °C:

| °C | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nibble | 0 | 1 | 3 | 2 | 6 | 7 | 5 | 4 | C | D | 9 | 8 | A | B |

Im Modus „nur Lüften" steht dort stattdessen die Sentinel `0xE`.

**Sonderkommandos** (vollständige 24 Bit, keine Felder):

| Funktion | Code |
|---|---|
| Aus | `0xB27BE0` |
| Swing umschalten | `0xB26BE0` |
| Display-LED umschalten | `0xB5F5A5` |
| Silence/Feel umschalten | `0xB5F5B6` |

---

## 5. Durchgerechnetes Beispiel — Kühlen, 22 °C, Lüfter mittel

```
Coolix 24 Bit  : 0xB25F70
Nutzbytes      : B2 5F 70
auf der Leitung: B2 4D  5F A0  70 8F      (je Byte + Komplement, MSB zuerst)

Slots (545 µs), 0 = LOW/Mark, 1 = HIGH/Space:
  Header  : (0,8) (1,8)
  1. Bit  : (0,1) (1,3)     Datenbit 1
  2. Bit  : (0,1) (1,1)     Datenbit 0
  ...
  Footer  : (0,1) + Leerlauf HIGH

21-Byte-Array (LSB zuerst, wie remko2mqtt es ausschiebt):
{0x00, 0xFF, 0xAE, 0xBB, 0xBA, 0xBA, 0xBA, 0xEB, 0xBA, 0xEE, 0xEE,
 0xEE, 0xBA, 0xAA, 0xBA, 0xBB, 0xAA, 0xAB, 0xEE, 0xEE, 0xFE}
```

Die vollständige Tabelle mit 148 Kommandos steht in
[`../ir/remko-coolix-codes.csv`](../ir/remko-coolix-codes.csv).

---

## 6. Korrekturen an den Repo-Angaben

Beim Dekodieren sind vier Fehler in `test_cmd.ino` aufgefallen — relevant für
jeden, der dort abschreibt:

| Bezeichner im Repo | tatsächlich |
|---|---|
| `cmd_turnon` = `0xB2BFE4` | **nicht** „Einschalten", sondern *nur Lüften, Lüfter auto*. Schaltet das Gerät zwar ein, aber in den Lüftungsbetrieb |
| `cmd_17` … `cmd_24` | sind **Heizen** 17–24 °C (Modusnibble `C`), nicht modusneutral |
| `cmd_followmeoff` | **byte-identisch** mit `cmd_24` (= Heizen 24 °C). Kein eigenes Kommando |
| `cmd_followmeon` = `0xBA504E` | passt in kein `0xB2`/`0xB5`-Schema. Ungetestet, würde ich ignorieren |

Die Tabelle in `remko_lib.ino` ist dagegen korrekt beschriftet (Index 1–8 =
Kühlen, 9–16 = Heizen). Ein echtes „Einschalten"-Kommando gibt es nicht: **jeder
normale Befehl (Modus + Temperatur) schaltet das Gerät ein.**

---

## 7. Pegelwandler 3,3 V → 5 V

Nur für den XT-Weg nötig. Invertierende Emitterschaltung mit BC337, wie im Repo:

```
                  +5 V  (CN501 Pin 2 oder 5)
                    │
                   ┌┴┐
                   │ │  R2  4,7 kΩ      Pull-up, siehe Hinweis
                   └┬┘
                    │
   XT (CN501 Pin 3) ┼───────────────┐
                    │               │
                    │           Kollektor
  GPIO25 ──[R1]─────┼──── Basis ──┤ BC337 (NPN)
           4,7 kΩ   │           Emitter
                    │               │
                  GND ──────────────┴──── ESP32 GND, CN501 Pin 1
```

| Bauteil | Wert | Begründung |
|---|---|---|
| R1 (Basis) | 4,7 kΩ | I_B = (3,3 V − 0,7 V) / 4,7 kΩ ≈ 0,55 mA; bei β > 100 sind das > 55 mA Senkstrom — um Größenordnungen mehr als nötig |
| R2 (Pull-up) | 4,7 kΩ | zieht XT im Ruhezustand auf 5 V; I_C ≈ 1,1 mA beim Durchschalten |
| T1 | BC337 (NPN) | jeder Kleinsignal-NPN tut es, 2N2222/BC547 ebenso |

**Polarität:** GPIO HIGH → Transistor leitet → XT = LOW = *Mark*. GPIO LOW →
Transistor sperrt → XT = HIGH (5 V) = *Space*, Ruhezustand. Die Stufe ist also
**invertierend**, und genau darauf ist die Komponente ausgelegt — im YAML steht
deshalb **kein** `inverted:` am Pin.

**Hinweis zum Pull-up:** Ob die Anzeigeplatine intern bereits einen Pull-up auf
XT hat, ist unbekannt. Vorgehen: XT gegen GND messen. Liegen ~5 V an, gibt es
einen internen Pull-up und R2 kann entfallen (schadet parallel aber nicht).
Misst man ~0 V oder etwas Undefiniertes, ist R2 **zwingend** — ohne ihn kommt
die Kollektorschaltung nie auf HIGH.

**Direkt vom 3,3-V-GPIO treiben** funktioniert nur, wenn die Eingangsschwelle
des SH79F161F unter 3,3 V liegt — bei 5-V-CMOS typisch 3,5 V, also
unzuverlässig. **Nicht empfohlen.** Wer es trotzdem tut, setzt
`inverted: true`.

---

## 8. REC: Kommando-Rückmeldung, nicht Zustands-Rückmeldung

`remko_lib.ino` enthält einen vollständigen **Empfangspfad** (`remko_rxd_*`),
der auf demselben 545-µs-Raster dieselben 21-Byte-Rahmen dekodiert. An REC liegt
also das **demodulierte Signal des geräteeigenen IR-Empfängers**: der ESP sieht
mit, **was jemand auf der Fernbedienung drückt**.

Das ist keine Zustandsmeldung, löst aber das praktisch wichtigste Problem des
XT-Wegs: Home Assistant läuft nicht mehr aus dem Tritt, wenn jemand die
Fernbedienung nimmt.

```
CN501 REC ──[10 kΩ]──┬── GPIO26
                     │
                  [15 kΩ]        5 V · 15/(10+15) = 3,0 V
                     │
                    GND
```

```yaml
remote_receiver:
  id: rec_rx
  pin: { number: GPIO26, inverted: true, mode: { input: true } }
  tolerance: 30%
  idle: 15ms
# und in climate:
  receiver_id: rec_rx
```

Die `coolix`-Plattform bringt den Dekoder mit; empfangene Codes aktualisieren
die Entität automatisch.

**Vorher verifizieren.** Dass REC ein *Ausgang* der Anzeigeplatine ist, ist aus
dem Repo-Code gut begründet, aber nicht nachgemessen. Test: REC über den Teiler
an den GPIO, `logger` auf `DEBUG`, `dump: all` — Fernbedienungstaste drücken.
Kommt `Received Coolix: 0x...`, ist es bestätigt. Kommt nichts, ist REC ein
Eingang und der Draht bleibt weg.

**Grenze, auch mit REC:** Schaltet sich das Gerät selbst ab — Timer, Störung,
Spannungsausfall — merkt Home Assistant das nicht. Genau das kann der XYE-Weg.

---

## 9. Muss die Original-Schnittstellenplatine raus?

Nur relevant, wenn eine verbaut ist. Falls ja: **ja, abziehen.** Der ESP treibt
XT über eine **Open-Collector**-Stufe, kann also nur nach LOW ziehen. Treibt die
Originalplatine XT gleichzeitig gegenphasig **push-pull** auf HIGH, fließt der
Strom durch deren Endstufe — Beschädigungsrisiko. Parallelbetrieb ist nur
unbedenklich, wenn auch die Originalplatine Open-Collector fährt; das ist nicht
dokumentiert und den Test nicht wert.

**Was dabei verloren geht: praktisch nichts.** Der Remko-WiFi-Stick unterstützt
ohnehin erst Geräte ab 08/2021 — an Geräten von 2019 funktioniert er nicht.

**Was erhalten bleibt: die Original-Fernbedienung.** Die geht über den
IR-Empfänger *auf der Anzeigeplatine selbst*, nicht über XT. Sie funktioniert in
jeder Variante unverändert weiter, auch parallel zu Home Assistant.

**Rückbau:** Platine beschriftet aufheben, dann ist der Originalzustand in fünf
Minuten wiederhergestellt.
