Alles klar! Ich erstelle dir einen **detaillierten Projektplan**, Schritt für Schritt, sodass jemand ohne tiefere Programmierkenntnisse den gesamten Workflow aufsetzen kann. Ich erkläre die Schritte klar, inklusive Ordnerstruktur, Logik, Docker, Script-Funktion und Tests.

---

# **Projektplan: Automatisches Duplex-PDF-Merging mit WF‑3820DWF**

---

## **1️⃣ Ziel**

* WF‑3820DWF scannt **einseitig per ADF**
* Workflow:

  1. Vorderseiten scannen → in `import-doppelseitig/`
  2. Rückseiten scannen → in `import-doppelseitig/`
* Script erkennt Reihenfolge, kehrt Rückseiten um, **interleaved Merge** → fertige Duplex-PDF
* Ergebnis landet im Paperless `import/`-Ordner
* Vollautomatischer Ablauf in einem Docker-Container, alle 30 Sekunden Prüfung

---

## **2️⃣ Verzeichnisstruktur**

```
Es soll 2 ordner geben. einmal den import ordner wo die Duplex dateien liegen und dann noch den Output ordner, wo die dateien dann nach dem merge hingeschoben werden sollen. Die sollen per mountpoint in der docker compose definierbar sein
```

**Erklärung:**

* `import-doppelseitig/` → Scanner speichert hier
* `import/` → Paperless überwacht diesen Ordner
* Docker-Container mountet beide Ordner und führt das Script aus

---

## **3️⃣ Docker-Setup**

1. **Base-Image:** Python 3.12 slim
2. **Libraries:**

   * `pypdf` → PDF Merging, Reverse, Interleaving
   * `watchdog` (optional für eventbasiert, wir nutzen Intervall)
3. **Mounts:**

```yaml
volumes:
  - ./import-doppelseitig:/app/import-doppelseitig
  - ./import:/app/import
```

4. **Entrypoint:** `entrypoint.sh` → Endlosschleife alle 30 Sekunden, Script `merge_duplex.py` aufrufen

---

## **4️⃣ Script Logik (`merge_duplex.py`)**

1. **Ordner prüfen:** `import-doppelseitig/`
2. **Alle PDFs sortieren nach Erstellungszeit** (`mtime`)
3. **Gruppieren:** Immer zwei Dateien → erste = Vorderseiten, zweite = Rückseiten
4. **Rückseiten-PDF umdrehen** → Seiten in umgekehrter Reihenfolge
5. **Merge / Interleave:**

   ```
   merged_pages = [V1, R1, V2, R2, ...]
   ```
6. **Fertige PDF ins `import/` verschieben**
7. **Alte PDFs archivieren / löschen** (`processed/`)
8. **30-Sekunden Intervall prüfen** → neue Dateien erkannt? → Repeat

---

## **5️⃣ Scanner-Einstellungen**

* Kontakt für SMB-Scan: `import-doppelseitig/`
* **Dateiformat:** `PDF mehrseitig`
* Jede ADF-Runde → PDF pro Durchgang
* Vorderseiten: Seiten 1,3,5…
* Rückseiten: Seiten 2,4,6… → manuell umgedreht → PDF vom Scanner enthält Seiten in umgekehrter Reihenfolge

---

## **6️⃣ Docker Container Ablauf**

1. Container starten
2. Script überwacht `import-doppelseitig/`
3. Neue PDF-Dateien erkannt → gruppiert → Merge + Interleave
4. Fertige PDF → `import/` für Paperless
5. Original-PDFs → archiviert oder gelöscht
6. Alle 30 Sekunden wiederholen

---

## **7️⃣ Zusätzliche Hinweise**

* **Timeout / Fehler:**

  * Wenn nur eine Datei da ist → Script wartet auf zweite (Rückseiten)
* **Dateiname:**

  * Optional: `scan_%Y%m%d_%H%M%S.pdf`
* **Logging:**

  * Merge-Prozesse protokollieren → hilfreich bei Fehlern
* **Testlauf:**

  1. 3 Seiten Vorderseiten → Scan
  2. 3 Seiten Rückseiten → Scan
  3. Prüfen, ob PDF richtig zusammengefügt (1V,1R,2V,2R,3V,3R)

---

## **8️⃣ Schritt-für-Schritt-Umsetzung**

### Schritt 1: Ordner erstellen

```bash
mkdir -p /paperless/import /paperless/import-doppelseitig /paperless/docker-duplex-merge
```

### Schritt 2: Script erstellen (`merge_duplex.py`)

* Script prüft Ordner, sortiert PDFs, dreht Rückseiten, interleaved Merge
* Mit `pypdf` → Python Script, das jeder nachvollziehen kann

### Schritt 3: Entrypoint erstellen (`entrypoint.sh`)

```bash
#!/bin/bash
while true; do
    python merge_duplex.py
    sleep 30
done
```

### Schritt 4: Dockerfile erstellen

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY merge_duplex.py .
COPY entrypoint.sh .
RUN pip install pypdf
CMD ["bash","entrypoint.sh"]
```

### Schritt 5: Docker bauen und starten

```bash
cd docker-duplex-merge
docker build -t duplex-merge .
docker run -d --name duplex-merge \
  -v /paperless/import-doppelseitig:/app/import-doppelseitig \
  -v /paperless/import:/app/import \
  duplex-merge
```


Anmerkung: Die Dateinamen sind in dem format: 20200130_172331.pdf

Es soll dann einfach die beiden letzten dateien nehmen. Also die, die am nächsten zusammen liegen anfangend von dem ältesten und das dann mit dem 2. ältesten Dokument mergen. Da das ja das dokument ist, was als nächstes gedruckt wurde.


Stelle alle fragen, die du für das Projekt brachst

Der ordner für paperless duplex liegt unter: /mnt/hdd/paperless/Import-Duplex. 
  Der ordner wo das fertige Dokument rein soll, liegt unter 
  /mnt/hdd/paperless/Import. Diese Ordner ist auf deinem aktuellen system nicht 
  vorhanden, soll aber in Produktion genutzt werden. Nutze also erstmal ./Import 
  und ./Import-Duplex

  Der scanner, der scannt, packt die dateien direkt in den Ordner Import_Duplex. Dafür dürfen keine unterordner genutzt werden, sondern es muss in dem Ordner erkannt werden