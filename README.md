# elotec-nettbutikk

Program for å kjøre handlinger i nettbutikken gjennom eksport/import.

## Streamlit-applikasjon

Denne repoen inneholder en Streamlit-applikasjon som kan lage master- og variantprodukter basert på eksport fra nettbutikken.

### Kjøring

1. Installer avhengigheter:
   ```bash
   pip install -r requirements.txt
   ```
2. Start applikasjonen:
   ```bash
   streamlit run app.py
   ```
3. I nettleseren: velg funksjonen **"Opprett masterprodukt"**, last opp eksportfilen (`.csv`) og last ned generert fil.
   Etter opplasting listes masterproduktene med tilhørende varianter slik at du kan huke av hvilke som skal med.
   De genererte TSV-dataene vises i to tekstfelt (produktdata og beskrivelser) som kan kopieres direkte.

Applikasjonen vil produsere en fil `new_master_variant_products.tsv` som inneholder de valgte master- og variantproduktene.
