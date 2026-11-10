# Spur-N Gleisplaner

Installierbare Web-App (PWA) zum Planen von Spur-N-Gleisanlagen.
Läuft im Browser, lässt sich auf dem Handy installieren und funktioniert danach auch ohne Internet.

## Adresse

**https://josefoehreneder.github.io/MoBa_TrackPlaner/**

(GitHub Pages: Settings → Pages → Branch `main`, Ordner `/ (root)`)

## Auf dem Handy installieren

- **Android (Chrome):** Seite öffnen → Plan → **App installieren**
  (oder Menü ⋮ → „App installieren“).
- **iPhone (Safari):** Seite öffnen → Teilen → **Zum Home-Bildschirm**.

Beim ersten Öffnen mit Internet werden App und 3D-Ansicht für den Offline-Betrieb gespeichert.

## Updates

Änderungen in `tools/spur-n-gleisplaner.html` vornehmen, dann `python3 tools/build.py` ausführen und alles committen.
Die installierte App meldet dann „Neue Version verfügbar“ → **Neu laden**.

## Pläne sichern

Plan → **Als Datei speichern** legt eine `.json`-Datei an (auf Android über das Teilen-Menü,
z. B. in Google Drive oder per WhatsApp). **Datei öffnen** lädt sie wieder.
Pläne aus der Claude-Vorschau übernimmst du mit „Plan kopieren“ und „Plan-Text einfügen“.
