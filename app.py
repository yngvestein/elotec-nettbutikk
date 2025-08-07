import csv
import io
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Elotec Nettbutikk", layout="wide")

csv.field_size_limit(10**7)

# Kart for fargekoder (nummer og bokstaver)
numeric_color_map = {
    "1": "white",
    "2": "black",
    "3": "fog",
    "4": "graphite",
    "5": "grey",
    "6": "ivory",
    "7": "olive",
    "8": "oyster"
}
known_letter_colors = {
    "B": "black",
    "W": "white",
    "G": "grey",
    "R": "red",
    "Y": "yellow"
}

# Fargekart for normalisering til norske verdier (som skal brukes i output)
color_to_norwegian = {
    "black": "Sort",
    "white": "Hvit",
    "grey": "Grå",
    "gray": "Grå",
    "red": "Rød",
    "green": "Grønn",
    "blue": "Blå",
    "yellow": "Gul",
    "fog": "Fog",
    "graphite": "Grafitt",
    "ivory": "Ivory",
    "olive": "Oliven",
    "oyster": "Oyster",
    "krom": "Krom",
    "stal": "Stål",
    "sort": "Sort",
    "hvit": "Hvit",
    "grå": "Grå",
    "rød": "Rød",
    "grønn": "Grønn",
    "blå": "Blå",
    "gul": "Gul",
    "grafitt": "Grafitt"
}
known_colors = set(numeric_color_map.values()).union(known_letter_colors.values()).union({
    "red", "green", "blue", "yellow", "white", "black", "anthracite", "grey", "gray",
    "orange", "fog", "graphite", "ivory", "olive", "oyster",
    "rød", "grønn", "blå", "gul", "hvit", "sort", "svart", "antrasitt", "grå", "oransje"
})

def extract_color_from_name(text):
    """Ekstraktér farge fra tekst og returner norsk navn"""
    text = text.lower()
    for color in known_colors:
        if f"({color})" in text or f" {color} " in text or text.endswith(f" {color}"):
            # Konverter til norsk navn
            return color_to_norwegian.get(color, color)
    return None

def extract_base_and_color(article_number, name_fields, farge_column):
    """Ekstraktér base artikelnummer og farge"""
    if not article_number:
        return None, None

    article_number = article_number.strip().upper()
    parts = article_number.split('-')
    last_part = parts[-1] if len(parts) > 1 else ""

    # Prioritér farge fra Farge-kolonnen (kolonne 18)
    if farge_column and farge_column.strip():
        normalized_color = normalize_color(farge_column.strip())
        if normalized_color:
            if last_part in numeric_color_map or last_part in known_letter_colors:
                return '-'.join(parts[:-1]), normalized_color
            else:
                return article_number, normalized_color

    # Fallback til eksisterende logikk - konverter til norske navn
    if last_part in numeric_color_map:
        english_color = numeric_color_map[last_part]
        norwegian_color = color_to_norwegian.get(english_color, english_color)
        return '-'.join(parts[:-1]), norwegian_color

    if last_part in known_letter_colors:
        english_color = known_letter_colors[last_part]
        norwegian_color = color_to_norwegian.get(english_color, english_color)
        return '-'.join(parts[:-1]), norwegian_color

    # Prøv å ekstraktere fra navn og konverter til norsk
    combined_text = " ".join(name_fields).lower()
    extracted_color = extract_color_from_name(combined_text)
    if extracted_color:
        return article_number, extracted_color

    return article_number, None

def normalize_color(color_text):
    """Normaliser farge til norsk verdi for output"""
    if not color_text:
        return None

    color_lower = color_text.lower().strip()

    # Sjekk mapping til norske verdier
    if color_lower in color_to_norwegian:
        return color_to_norwegian[color_lower]

    # Hvis det allerede er en norsk verdi, behold den
    norwegian_values = set(color_to_norwegian.values())
    if color_text in norwegian_values:
        return color_text

    return color_text  # Returnér original hvis ingen match

def is_valid_variant(row):
    """Sjekk om raden er en gyldig variant (ikke master)"""
    # Inkluder rader som ikke allerede er masters
    variantmaster = row.get('Variantmaster', '').lower()
    return variantmaster != 'true'

def clean_name(name):
    """Fjern kun fargeinformasjon fra navn, behold annen funksjonsinformasjon"""
    if not name:
        return ""

    # Start med original navn
    cleaned = name.strip()

    # Fjern kun farge i paranteser - ikke all informasjon i paranteser
    all_color_names = list(known_colors) + list(color_to_norwegian.values())

    for color in all_color_names:
        # Fjern farge i paranteser (case insensitive)
        pattern = rf"\s*\({re.escape(color)}\)"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    # Fjern farge på slutten av navnet - både engelske og norske navn
    for color in all_color_names:
        if cleaned.lower().endswith(f" {color.lower()}"):
            cleaned = cleaned[:-len(color)-1].strip()
            break
        elif cleaned.lower().endswith(f", {color.lower()}"):
            cleaned = cleaned[:-len(color)-2].strip()
            break

    cleaned = re.sub(r',\s*$', '', cleaned).strip()

    return cleaned

def process_csv(uploaded_file):
    """Prosesser CSV og returner strukturert data"""
    uploaded_file.seek(0)
    text = io.StringIO(uploaded_file.getvalue().decode('utf-8'))
    reader = csv.DictReader(text, delimiter=',')
    rows = list(reader)

    base_fieldnames = [
        'Nummer', 'Navn', 'Forvalgt variant', 'Varianter', 'Tilbehør',
        'Sider', 'Nyhet', 'Variantmaster', 'Variantprodukt', 'Ikke synlig i lister',
        'Attributtsett', 'elo.group.intermediate', 'elo.group.main', 'elo.group.sub',
        'elo.product.number', 'Tittel', 'Tittel (Norsk)', 'Farge'
    ]
    csv_fields = reader.fieldnames or []
    extra_fields = [f for f in csv_fields if f not in base_fieldnames]
    fieldnames = base_fieldnames + extra_fields
    desc_fieldnames = ['Nummer', 'Salgstekst (Norsk)', 'Beskrivelse (Norsk)']

    valid_rows = [r for r in rows if is_valid_variant(r)]

    product_groups = {}
    for row in valid_rows:
        artnum = row.get('elo.product.number', '').strip()
        name_fields = [row.get('Navn', ''), row.get('Tittel', ''), row.get('Tittel (Norsk)', '')]
        farge_column = row.get('Farge', '')
        base, color = extract_base_and_color(artnum, name_fields, farge_column)
        if not base or not color:
            continue
        if base not in product_groups:
            product_groups[base] = []
        product_groups[base].append((row, color))

    masters = []
    for base, variants in product_groups.items():
        if len(variants) < 2:
            continue  # Ikke lag master for enkeltstående

        master_row = {key: '' for key in fieldnames}
        master_row['Nummer'] = f"{base}-X"
        master_row['Navn'] = clean_name(variants[0][0].get('Navn'))
        master_row['Variantmaster'] = 'true'
        master_row['Variantprodukt'] = 'false'
        master_row['Ikke synlig i lister'] = 'false'
        master_row['Attributtsett'] = 'Farge'
        master_row['Nyhet'] = 'false'
        master_row['elo.product.number'] = ' / '.join([v[0]['elo.product.number'] for v in variants])
        master_row['Varianter'] = ','.join([v[0]['Nummer'] for v in variants])
        master_row['Forvalgt variant'] = variants[0][0]['Nummer']
        master_row['elo.group.intermediate'] = variants[0][0].get('elo.group.intermediate', '')
        master_row['elo.group.main'] = variants[0][0].get('elo.group.main', '')
        master_row['elo.group.sub'] = variants[0][0].get('elo.group.sub', '')
        master_row['Tittel'] = variants[0][0].get('Tittel', '')
        master_row['Tittel (Norsk)'] = variants[0][0].get('Tittel (Norsk)', '')
        master_row['Tilbehør'] = variants[0][0].get('Tilbehør', '')
        for f in extra_fields:
            master_row[f] = variants[0][0].get(f, '')

        all_pages = set()
        for v, _ in variants:
            if v.get('Sider'):
                all_pages.update([p.strip() for p in v['Sider'].split(',')])
        master_row['Sider'] = ','.join(sorted(all_pages))

        sales = variants[0][0].get('Salgstekst (Norsk)', '')
        desc = variants[0][0].get('Beskrivelse (Norsk)', '')
        desc_rows = [{'Nummer': master_row['Nummer'], 'Salgstekst (Norsk)': sales, 'Beskrivelse (Norsk)': desc}]

        variant_rows = []
        for v, color in variants:
            vr = {key: '' for key in fieldnames}
            vr['Nummer'] = v['Nummer']
            vr['Navn'] = v['Navn']
            vr['Variantmaster'] = 'false'
            vr['Variantprodukt'] = 'true'
            vr['Ikke synlig i lister'] = 'true'
            vr['Attributtsett'] = 'Farge'
            vr['Farge'] = color  # Legg til norsk fargeverdi
            for f in extra_fields:
                vr[f] = v.get(f, '')
            variant_rows.append(vr)
            desc_rows.append({'Nummer': v['Nummer'], 'Salgstekst (Norsk)': '', 'Beskrivelse (Norsk)': ''})

        masters.append({'base': base, 'master_row': master_row, 'variant_rows': variant_rows, 'desc_rows': desc_rows})

    return masters, fieldnames, desc_fieldnames, base_fieldnames


def generate_tsv(masters, selected_fields, desc_fieldnames):
    """Generer TSV-strenger fra valgte masterprodukter"""
    output_rows = []
    desc_output_rows = []
    for m in masters:
        output_rows.append(m['master_row'])
        output_rows.extend(m['variant_rows'])
        desc_output_rows.extend(m['desc_rows'])

    buffer_main = io.StringIO()
    # ``output_rows`` kan inneholde flere nøkler enn det brukeren har valgt å
    # inkludere i eksporten. ``csv.DictWriter`` kaster da en ``ValueError`` hvis
    # den møter ukjente felter. Ved å sette ``extrasaction='ignore'`` sørger vi
    # for at eventuelle ekstra felter blir ignorert i stedet for å forårsake feil
    # ved generering av TSV-filen.
    writer = csv.DictWriter(
        buffer_main,
        fieldnames=selected_fields,
        delimiter='\t',
        extrasaction='ignore',
    )
    writer.writeheader()
    writer.writerows(output_rows)
    main_tsv = buffer_main.getvalue()

    buffer_desc = io.StringIO()
    desc_writer = csv.DictWriter(
        buffer_desc,
        fieldnames=desc_fieldnames,
        delimiter='\t',
        extrasaction='ignore',
    )
    desc_writer.writeheader()
    desc_writer.writerows(desc_output_rows)
    desc_tsv = buffer_desc.getvalue()

    combined = main_tsv + "\n" + desc_tsv
    return main_tsv, desc_tsv, combined

def main():
    st.title("Elotec Nettbutikk")
    choice = st.sidebar.selectbox("Velg funksjon", ["Opprett masterprodukt"])
    uploaded_file = st.file_uploader("Last opp eksportfil", type=["csv"])

    if uploaded_file is None:
        return

    masters, fieldnames, desc_fieldnames, base_fieldnames = process_csv(uploaded_file)

    st.markdown("### Kolonner for eksport")
    cols = st.columns(len(fieldnames))
    selected_fields = []
    for i, f in enumerate(fieldnames):
        default = f in base_fieldnames
        disabled = f in base_fieldnames and choice == "Opprett masterprodukt"
        with cols[i]:
            if st.checkbox(f, value=default, disabled=disabled):
                selected_fields.append(f)
    for f in base_fieldnames:
        if f not in selected_fields:
            selected_fields.append(f)

    st.success("Fil behandlet. Velg masterprodukter som skal inkluderes.")

    selected = []
    for m in masters:
        label = f"{m['master_row']['Nummer']} - {m['master_row']['Navn']}"
        if st.checkbox(label, value=True, key=f"master_{m['base']}"):
            selected.append(m)
        df = pd.DataFrame([m['master_row']] + m['variant_rows'])
        st.table(df[selected_fields])

    main_tsv, desc_tsv, combined = generate_tsv(selected, selected_fields, desc_fieldnames)

    st.subheader("Generert TSV")
    st.text_area("Produktdata", main_tsv, height=200)
    st.text_area("Beskrivelse", desc_tsv, height=200)

    st.download_button(
        label="Last ned master/variant fil",
        data=combined,
        file_name="new_master_variant_products.tsv",
        mime="text/tab-separated-values",
    )

if __name__ == "__main__":
    main()
