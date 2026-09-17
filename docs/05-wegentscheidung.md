# Wegentscheidung: XYE statt XT

> **Summary (EN).** Why a fully decoded, verified, compiling implementation was
> put aside in favour of a different path — and what the comparison looks like
> in the end. The short version: the XT path can only write. It never learns
> what the unit is actually doing, it requires splicing into an occupied
> connector and building a level shifter, and the protocol work behind it, while
> genuinely interesting, turned out to be answering the wrong question. The
> better question was whether the manufacturer had already provided an
> interface. It had.

---

## Die Reihenfolge, in der es passiert ist

1. **Ausgangslage.** Fünf Innengeräte, Baujahr 2019 — also vor der Baureihe mit
   bidirektionaler UART-Schnittstelle. Zwei Community-Projekte
   (`remko2mqtt`) zeigten einen kabelgebundenen Weg über den XT-Pin der
   Anzeigeplatine, mit statischen Byte-Arrays je Funktion.
2. **Protokollarbeit.** Die Arrays wurden zurückdekodiert und stellten sich als
   Coolix heraus — ein in ESPHome eingebauter Codec. Ein eigener Encoder
   reproduzierte alle 24 Referenz-Arrays byte-genau. Eine External Component
   wurde geschrieben, die die Coolix-Timings als TTL-Pegel ausgibt. Sie
   kompiliert. Siehe [04-ir-protokoll-coolix.md](04-ir-protokoll-coolix.md).
3. **Die Rückfrage.** Was macht eigentlich die Kabelfernbedienung MCC-1, die
   Remko für diese Geräte anbietet? Antwort aus dem Handbuch: Sie hängt an
   Klemme **X, Y, E** auf der Adapterplatine — und sie **listet die Innengeräte
   mit ihrer Adresse im Display auf**. Das geht nur, wenn die Geräte antworten.
4. **Die Messung.** Gerät geöffnet, CN403 gefunden: bestückt, geschützt, frei.
   Transceiver identifiziert, Sendefreigabe gegen Masse gemessen — **nicht
   festgelegt**. Das Gerät kann senden. Siehe
   [01-hardware-analyse.md](01-hardware-analyse.md).
5. **Umschwenken.** Für den XYE-Bus existiert bereits eine gepflegte
   ESPHome-Komponente. Die eigene Arbeit an XT wurde damit überflüssig.

---

## Die Gegenüberstellung

| | **XYE / CN403** | XT / CN501 |
|---|---|---|
| Eingriffstiefe | Stecker, vom Hersteller vorgesehen | belegter Stecker, Y-Stück, Pegelwandler |
| Rückmeldung | **voll bidirektional** | keine (nur Mitschnitt der Fernbedienung über REC) |
| Ist-Temperaturen | Raum, Verdampfer, Verflüssiger, außen | nein |
| Kompressor, Abtaubetrieb | ja | nein |
| Fehlercodes | ja | nein |
| Follow-Me | ja | nein |
| Software | gepflegte Community-Komponente | selbstgeschriebene Komponente |
| Zusatzhardware | ein Kombiboard | Transistor, Widerstände, Steckbrett |
| Versorgung | **5 V aus CN403** | ggf. 5 V aus CN501 |
| Reversibilität | Stecker abziehen | Y-Stück zurückbauen |

Der einzige Punkt, in dem XT vorn liegt: Es hat einen **echten Auto-Modus**,
weil die Umschaltlogik dort im Gerät hinter der IR-Auswertung sitzt. Über XYE
kann das Innengerät nur HEAT oder COOL — die Umschaltung machte im Original der
Midea-Thermostat und muss als Automation nachgebaut werden.

---

## Die Lehren

**1. Bevor man ein Protokoll nachbaut, lohnt die Frage, ob der Hersteller nicht
längst eine Schnittstelle vorgesehen hat.** Der invasive Weg war hier nicht nur
schlechter — er war überflüssig. Gefunden wurde er nicht durch mehr Analyse,
sondern durch eine Frage an die Produktdokumentation.

**2. Eine Fünf-Minuten-Messung kann eine Woche Arbeit absichern.** Ob das ganze
Vorhaben überhaupt tragfähig war, hing an einem einzigen Pin des Transceivers.
Diese Messung stand am Anfang, nicht am Ende — und zwar bevor ein einziges
Bauteil bestellt war.

**3. Reverse Engineering endet nicht bei „es funktioniert".** Die Byte-Arrays
der Referenzprojekte funktionieren. Aber erst das Verständnis, *dass* sie eine
Pegel-Bitmap eines bekannten Codecs sind, brachte den vollen Temperaturbereich
(17–30 °C statt 17–24 °C) und machte jede Kommandotabelle im Code überflüssig.

**4. Zu wissen, was ein Bus *nicht* kann, ist genauso wertvoll.** Swing,
Displayhelligkeit und Piepton stehen nicht oder nur passiv auf dem XYE-Bus. Das
festzustellen hat 46 Statusframes und eine Durchsicht aller 30 Bytes gekostet —
und erspart jedem Nachbauer die Suche nach einem Fehler, der keiner ist. Siehe
[03-messprotokolle.md](03-messprotokolle.md).

---

## Warum die XT-Arbeit trotzdem im Repository liegt

Sie ist vollständig, verifiziert und kompiliert — siehe
[`../legacy-xt/`](../legacy-xt/). Drei Gründe, sie aufzuheben:

* **Als Plan B.** Geräte ohne bestückte Adapterplatine, oder Baureihen, die auf
  XYE nicht antworten, sind über XT trotzdem steuerbar.
* **Als Plan C ohne jeden Eingriff.** Dieselbe Logik geht über 38-kHz-IR aus dem
  Raum — für alle, die das Gerät gar nicht öffnen wollen.
* **Weil die Analyse den Wert hat, nicht der Code.** Die Kommandotabelle in
  [`../ir/`](../ir/) ist unabhängig vom gewählten Weg brauchbar: für eigene
  IR-Lösungen, für den Abgleich eines Mitschnitts, für jedes System außerhalb
  von ESPHome.

Die aufwendigste Einzelarbeit des Projekts war die Rückdekodierung mit dem
byte-genauen Gegenprüfen. Sie wegzuwerfen, nur weil ein besserer Weg gefunden
wurde, hieße, sie im Ernstfall zweimal zu machen.
