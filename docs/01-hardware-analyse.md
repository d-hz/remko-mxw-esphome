# Hardware-Analyse der Adapterplatine

> **Summary (EN).** Teardown of the display/adapter board of a Remko MXW indoor
> unit (2019). The board carries a fully populated, protected RS-485 interface
> on connector **CN403** — the connector the manufacturer's own MCC-1 central
> controller uses — plus the address switches S1/S2. The transceiver was
> identified as a **TI SN65HVD3088E**, and its driver-enable pin was measured
> against ground: **not tied low**, which proves the indoor unit is able to
> transmit, not just listen. That single continuity check decided the whole
> project. Pinout `5V · E · Y · X`, with **X = A**, **Y = B**, **E = GND**,
> 4800 baud 8N1 half duplex.

**Geräte:** Remko MXW 204 / 264 / 354 / 524, Multisplit, Baujahr 2019 — also
die „alte" Baureihe vor 07/2021, die ab Werk keine bidirektionale
UART-Schnittstellenplatine hat.

---

## Die entscheidende Frage kam zuerst

Das Projekt begann mit dem Ziel, den unidirektionalen **XT-Pfad** anzuzapfen:
den Draht, über den die Anzeigeplatine ihr demoduliertes IR-Kommando bekommt.
Das hätte bedeutet: in ein belegtes Kabel schneiden, einen Pegelwandler bauen —
und **niemals erfahren, was das Gerät tut**.

Die Alternative stand die ganze Zeit daneben: **CN403**, der Anschluss für die
Kabelfernbedienung MCC-1. Das Remko-Handbuch beschreibt ihn als Klemme
**X, Y, E auf der Adapterplatine der Innengeräte**, mit Adressierung über
Drehschalter S2 und DIP-Schalter S1 (Adresse 0–63) und 120-Ω-Abschluss an den
Busenden. Das ist der **Midea-XYE-Bus** (CCM-Bus) — ein dokumentierter, gut
reverse-engineerter RS-485-Bus.

Der Beleg für Bidirektionalität steht im Handbuch selbst: „Nach erfolgreicher
Adressierung der Innengeräte erscheinen diese mit der jeweiligen Adresse im
Display des MCC-Controllers." Damit das funktioniert, **müssen die Innengeräte
antworten**.

> Das widerspricht der Notiz des `remko2mqtt`-Autors, der RS485-Baustein sei nur
> unidirektional angebunden. Auflösung vermutlich: dort wurde die
> *Schnittstellenplatine* mit dem SH79F161F untersucht, nicht die
> XYE-Adapterplatine. Entschieden hat am Ende die Messung, nicht die Notiz.

---

## Befund am geöffneten Gerät

Platine: `CE-KFR26G/DR-AB.D.01.XP1-1`, PCB-Datum 2014-08-22. Das ist **eine**
Platine, die Anzeige-, Adapter- und Busfunktion vereint — also genau die
„Adapterplatine an der Geräteblende" aus dem Handbuch.

![Adapterplatine eines Remko-MXW-Innengeraets](images/adapter-board.jpg)

*Die vollständige Platine. Links die Adressierung, rechts der Bus — dazwischen
der Anzeige-Controller. Die Seriennummer am unteren Rand ist geschwärzt.*

**Linker Teil — Adressierung und Anbindung:**

| Bauteil | Bedeutung |
|---|---|
| Blauer 2-fach-DIP-Schalter | **S1** aus dem Handbuch — Adressbank (0–15 / 16–31 / 32–47 / 48–63) |
| Schwarzer Drehschalter 0–9, A–F | **S2** — Adress-Offset innerhalb der Bank |
| **CN501**, 5-polig, **belegt** | Kabel zur Hauptplatine — hier liegt der XT-Pfad |
| Großer QFP-Mikrocontroller | Anzeige-Controller, SH79F161F-Klasse |

Die Kombination DIP plus Drehschalter ist der Beweis, dass diese Platine für die
zentrale Adressierung nach dem Handbuch ausgelegt ist.

**Rechter Teil — der XYE-Bus:**

| Bauteil | Bedeutung |
|---|---|
| **CN403**, 4-polig, **frei** | Silkscreen liest sich als `5V · E · Y · X` |
| **IC5**, SO-8, direkt daneben | der RS485-Transceiver |
| **TVS1 / TVS2** | Überspannungsschutz auf den Busleitungen — typisch RS-485 |
| **R110 / R38** | Serienwiderstände in den A/B-Leitungen |
| `SWITCH1/2`, `ON-OFF1/2` | potentialfreie Kontakteingänge, Werksbrücken gesetzt |

**Die Bestückung ist der eigentliche Befund.** Ein SO-8 direkt am Stecker, davor
zwei TVS-Dioden und zwei Serienwiderstände — das ist eine vollständige,
geschützte RS-485-Schnittstelle. Nicht ein unbestückter Footprint, sondern
fertig aufgebaut und ab Werk einsatzbereit.

Zwei Konsequenzen:

1. **CN403 ist frei — kein Löten, kein Auftrennen.** Nur ein Gegenstück
   aufstecken. Genau der Punkt, den auch der MCC-1 nutzt.
2. **CN501 ist belegt.** Der XT-Weg hätte bedeutet, in ein benutztes Kabel
   einzuschleifen oder ein Y-Stück zu bauen — deutlich invasiver als zunächst
   angenommen.

---

## IC5 identifiziert: TI SN65HVD3088E

Damit ist der Bus hardwareseitig belegt. Aus dem Datenblatt (SLLS562O):

| Eigenschaft | Bedeutung |
|---|---|
| Half-Duplex **RS-485**, TIA/EIA-485A | kein CAN, kein Sonderweg |
| „Industry-standard SN75176 footprint" | die Pinbelegung unten gilt verbindlich |
| **5-V-Versorgung** | erklärt den 5-V-Pin an CN403 |
| **Fail-safe receiver** (open / shorted / **idle**) | ein unbespielter Bus wird als sauberes Mark gelesen → **keine Bias-Widerstände nötig** |
| 1/8 Unit Load, bis 256 Knoten | ein zusätzlicher Knoten am Bus ist unkritisch |
| 0,3 mA aktiv, 15 kV ESD an den Buspins | fürs 5-V-Budget vernachlässigbar, gut geschützt |
| bis 20 Mbps | bei 4800 Baud Faktor 4000 Reserve |

```
  R    1 ┌───┐ 8  Vcc
 /RE    2 │   │ 7  B      <- Y
  DE    3 │   │ 6  A      <- X
  D     4 └───┘ 5  GND
```

---

## Die Messung, die über das Projekt entschieden hat

Ob CN403 nutzbar ist, hing an einer einzigen Frage: **Kann das Gerät auf dem Bus
antworten, oder darf es nur zuhören?** Das entscheidet ein Pin.

| Messung | Ergebnis | Bedeutung |
|---|---|---|
| CN403 „5V" → IC5 Pin 8 | Durchgang | 5-V-Pin identifiziert, speist den Transceiver |
| CN403-Pins → IC5 Pin 6 / Pin 7 | Durchgang | **X = A**, **Y = B** zugeordnet |
| CN403-Pin → Masse | Durchgang | **E** identifiziert |
| **IC5 Pin 3 (`DE`) → Masse** | **kein Durchgang** | **Sendefreigabe liegt am Mikrocontroller — das Gerät kann antworten** |
| IC5 Pin 2 (`/RE`) → Masse | Durchgang | Empfänger dauerhaft aktiv, normal |

Läge `DE` fest auf Masse, wäre der Bus für das Innengerät schreibgeschützt
gewesen und das ganze Vorhaben tot. **Fünf Minuten Durchgangsprüfer haben eine
Woche Bauzeit abgesichert** — bevor ein einziges Bauteil bestellt war.

---

## Buseigenschaften

Laut der [XYE-Protokolldokumentation](https://codeberg.org/xye/xye):
**X = A, Y = B, E = GND**, **4800 Baud 8N1**, halbduplex. Deckt sich mit allem,
was hier gemessen wurde.

Der Bus wird von einem **5-V**-Transceiver getrieben. Unkritisch: RS-485 ist
differenziell, die Empfängerschwelle liegt bei ±200 mV, 3,3-V- und
5-V-Transceiver mischen sich problemlos.

**Terminierung:** Bei einem Bus von 20 cm mit zwei Teilnehmern ist der
120-Ω-Abschluss verzichtbar. Hat das eigene Modul einen Jumper dafür, schadet er
nicht.

**Adressierung:** S1 und S2 vor dem Anfassen fotografieren und **nicht
verändern**. Mit `auto_discover: true` findet die ESPHome-Komponente die
eingestellte Adresse selbst.

---

## Nebenbefund: der Kontakteingang

Der Stecker mit `SWITCH1/2` und `ON-OFF1/2` nimmt potentialfreie Kontakte
entgegen. Damit ließe sich das Gerät mit einem simplen Relais ein- und
ausschalten — ohne Modus, ohne Temperatur. Als Notnagel gut zu wissen, für den
eigentlichen Zweck zu wenig.

---

## Was das für andere Geräte heißt

Das Handbuch zeigt die Adapterplatine als Standardausstattung der Baureihe
MXW 203–523. Die hier untersuchten Geräte sind 204/264/354/524 — eine benachbarte
Baureihe. Die Platine ist eine **Midea-OEM-Platine**; die gleiche Schaltung
findet sich unter vielen Markennamen wieder.

**Prüfen, bevor bestellt wird:** Geräteblende abnehmen (das ist *nicht* das
Öffnen des Geräts) und nach CN403 und den Schaltern S1/S2 suchen. Sitzt dort ein
SO-8 mit zwei TVS-Dioden davor, ist die Sache entschieden.
