# Mimir – teljes változat (publikáció)

A TDK-dolgozat 2026. novemberi teljes, 8 fejezetes változata (commit `0f4ad29`), amely a tudományos
részen túl a rendszer jelenlegi állapotát, a megfelelési (GDPR, MI-rendelet) megvalósítást és a
fejlesztési döntést is tartalmazza. A TDK-ra beadott, csak a tudományos részt tartalmazó változat a
`tdk/` mappában van.

Fordítás: `latexmk -pdf main.tex` (pdfLaTeX + Biber). A számok forrása a `tdk/elemzes/` mappa.

Az `otdk_fuggelekek.tex` a 38. OTDK Informatikatudományi Szekció kötelező függelékeit tartalmazza
(rezümé, MI-használati nyilatkozat, eredménynyilatkozat, az adatok forrása) a TDK-változat
szóhasználatával. A kari TDK-ra nem kell; az OTDK-ra beküldött változatban a `tdk/fejezetek/fuggelek.tex`
után kell beilleszteni (az OTDK szabályai szerint ezek a függelékek utólag hozzáfűzhetők).
