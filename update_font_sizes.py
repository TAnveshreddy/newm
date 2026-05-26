"""
Script to update font sizes in Revuri_Nikitha_Project_FINAL_3.docx
to match the font sizes from Likith_prroject_doc.docx (reference document).

ONLY font sizes (w:sz and w:szCs) are changed. All other properties are preserved.

Reference analysis:
  Likith style sizes:
    Heading1: sz=16pt, szCs=16pt  (Revuri has 14pt)
    Heading2: sz=14pt, szCs=14pt  (Revuri has 13pt)
    Heading3: sz=12pt, szCs=12pt  (Revuri has none)
    Heading7: sz=12pt, szCs=12pt  (Revuri has none)
    Heading8: sz=12pt, szCs=12pt  (Revuri has 10pt)
    Heading9: sz=None, szCs=None  (Revuri has 10pt → remove explicit size)
    Heading1Char: sz=16pt, szCs=16pt  (Revuri has 14pt)
    Heading2Char: sz=13pt -> wait, Likith has sz=16 for H1Char only
    Heading3Char: sz=12pt, szCs=12pt
    Heading7Char: sz=12pt, szCs=12pt
    Heading8Char: sz=12pt, szCs=12pt
    Heading9Char: sz=None  (remove)
    Title: sz=18pt, szCs=18pt  (Revuri has 26pt)
    TitleChar: sz=18pt, szCs=18pt  (Revuri has 26pt)
    Subtitle: sz=14pt, szCs=12pt  (Revuri has 12pt/12pt)
    SubtitleChar: sz=14pt, szCs=12pt  (Revuri has 12pt/12pt)

  Run-level changes:
    24pt → 16pt (Architecture Diagram labels, Likith uses 16pt for same content)
"""

import zipfile
import shutil
import io
import os
from lxml import etree

# Paths
SOURCE_PATH = '/root/.claude/uploads/ad88ba69-f561-4d4c-98e6-7d7077e2af00/5efb5158-Revuri_Nikitha_Project_FINAL_3.docx'
OUTPUT_PATH = '/home/user/newm/Revuri_Nikitha_Project_FINAL_3_updated.docx'

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = W_NS

def w(tag):
    return f'{{{W_NS}}}{tag}'

def set_sz(rpr_el, sz_half_pts, szCs_half_pts, parent_el=None):
    """
    Set or update w:sz and w:szCs in an rPr element.
    If sz_half_pts is None, removes the sz element.
    If rpr_el is None and sz_half_pts is not None, creates rPr under parent_el.
    """
    if rpr_el is None:
        if sz_half_pts is None and szCs_half_pts is None:
            return  # Nothing to do
        # Create rPr element
        rpr_el = etree.SubElement(parent_el, w('rPr'))

    # Handle w:sz
    sz_el = rpr_el.find(w('sz'))
    if sz_half_pts is not None:
        if sz_el is None:
            sz_el = etree.SubElement(rpr_el, w('sz'))
        sz_el.set(w('val'), str(int(sz_half_pts)))
    else:
        if sz_el is not None:
            rpr_el.remove(sz_el)

    # Handle w:szCs
    szCs_el = rpr_el.find(w('szCs'))
    if szCs_half_pts is not None:
        if szCs_el is None:
            szCs_el = etree.SubElement(rpr_el, w('szCs'))
        szCs_el.set(w('val'), str(int(szCs_half_pts)))
    else:
        if szCs_el is not None:
            rpr_el.remove(szCs_el)


# Style-level mappings: styleId → (new_sz_half_pts, new_szCs_half_pts)
# None means "remove the element if present"
STYLE_SIZE_MAP = {
    # Paragraph styles
    'Heading1':   (32, 32),   # 16pt * 2
    'Heading2':   (28, 28),   # 14pt * 2
    'Heading3':   (24, 24),   # 12pt * 2 (add - currently absent in Revuri)
    'Heading7':   (24, 24),   # 12pt * 2 (add - currently absent in Revuri)
    'Heading8':   (24, 24),   # 12pt * 2 (was 10pt)
    'Heading9':   (None, None),  # Likith has no explicit size, remove
    # Character styles (linked to paragraph styles)
    'Heading1Char': (32, 32),  # 16pt * 2
    'Heading2Char': (28, 28),  # 14pt * 2
    'Heading3Char': (24, 24),  # 12pt * 2
    'Heading7Char': (24, 24),  # 12pt * 2
    'Heading8Char': (24, 24),  # 12pt * 2 (was 10pt)
    'Heading9Char': (None, None),  # remove
    # Title / Subtitle
    'Title':       (36, 36),  # 18pt * 2
    'TitleChar':   (36, 36),  # 18pt * 2
    'Subtitle':    (28, 24),  # sz=14pt, szCs=12pt (matching Likith exactly)
    'SubtitleChar': (28, 24), # sz=14pt, szCs=12pt
}

# Run-level size remapping: old_half_pts → new_half_pts
# Only for explicit run-level sizes, applied to w:sz and w:szCs
RUN_SIZE_REMAP = {
    48: 32,   # 24pt → 16pt (Architecture Diagram labels)
}

def update_styles_xml(styles_xml_bytes):
    """Update style-level font sizes in styles.xml."""
    root = etree.fromstring(styles_xml_bytes)
    changes = []

    for style_el in root.findall(f'.//{w("style")}'):
        style_id = style_el.get(w('styleId'))
        if style_id not in STYLE_SIZE_MAP:
            continue

        new_sz, new_szCs = STYLE_SIZE_MAP[style_id]

        # Find or handle rPr under the style element (direct child rPr, not nested)
        # Styles have: w:style/w:rPr (direct, not inside pPr)
        rpr_el = style_el.find(w('rPr'))

        if new_sz is None and new_szCs is None:
            # Remove sz/szCs from rPr if present
            if rpr_el is not None:
                sz_el = rpr_el.find(w('sz'))
                szCs_el = rpr_el.find(w('szCs'))
                old_sz = sz_el.get(w('val')) if sz_el is not None else None
                old_szCs = szCs_el.get(w('val')) if szCs_el is not None else None
                if sz_el is not None:
                    rpr_el.remove(sz_el)
                if szCs_el is not None:
                    rpr_el.remove(szCs_el)
                if old_sz or old_szCs:
                    changes.append(f"  Style '{style_id}': removed sz={old_sz}, szCs={old_szCs}")
        else:
            if rpr_el is None:
                # Check if there's already an rPr - might need to check what currently exists
                # Only add if new size is being set
                rpr_el = etree.SubElement(style_el, w('rPr'))
                changes.append(f"  Style '{style_id}': created rPr, set sz={new_sz/2}pt, szCs={new_szCs/2}pt")
            else:
                sz_el = rpr_el.find(w('sz'))
                szCs_el = rpr_el.find(w('szCs'))
                old_sz = sz_el.get(w('val')) if sz_el is not None else None
                old_szCs = szCs_el.get(w('val')) if szCs_el is not None else None
                changes.append(f"  Style '{style_id}': sz {old_sz}→{new_sz}, szCs {old_szCs}→{new_szCs}")

            # Set sz
            sz_el = rpr_el.find(w('sz'))
            if new_sz is not None:
                if sz_el is None:
                    sz_el = etree.SubElement(rpr_el, w('sz'))
                sz_el.set(w('val'), str(new_sz))
            else:
                if sz_el is not None:
                    rpr_el.remove(sz_el)

            # Set szCs
            szCs_el = rpr_el.find(w('szCs'))
            if new_szCs is not None:
                if szCs_el is None:
                    szCs_el = etree.SubElement(rpr_el, w('szCs'))
                szCs_el.set(w('val'), str(new_szCs))
            else:
                if szCs_el is not None:
                    rpr_el.remove(szCs_el)

    print("Style changes made:")
    for c in changes:
        print(c)

    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def update_document_xml(doc_xml_bytes):
    """Update run-level font sizes in document.xml."""
    root = etree.fromstring(doc_xml_bytes)
    run_changes = {}

    # Process all runs in the document
    for run in root.findall(f'.//{w("r")}'):
        rpr_el = run.find(w('rPr'))
        if rpr_el is None:
            continue

        # Check w:sz
        sz_el = rpr_el.find(w('sz'))
        if sz_el is not None:
            val = int(sz_el.get(w('val')))
            if val in RUN_SIZE_REMAP:
                new_val = RUN_SIZE_REMAP[val]
                sz_el.set(w('val'), str(new_val))
                key = (val, new_val)
                run_changes[key] = run_changes.get(key, 0) + 1

        # Check w:szCs
        szCs_el = rpr_el.find(w('szCs'))
        if szCs_el is not None:
            val = int(szCs_el.get(w('val')))
            if val in RUN_SIZE_REMAP:
                new_val = RUN_SIZE_REMAP[val]
                szCs_el.set(w('val'), str(new_val))

    print("\nRun-level changes made:")
    for (old, new), count in run_changes.items():
        print(f"  {old/2}pt → {new/2}pt: {count} runs updated")
    if not run_changes:
        print("  (none)")

    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def main():
    print(f"Reading source: {SOURCE_PATH}")

    # Read all parts from source docx (handling CRC errors gracefully -
    # but Revuri has no CRC issues, so this is just safe practice)
    with open(SOURCE_PATH, 'rb') as f:
        source_data = f.read()

    source_zf = zipfile.ZipFile(io.BytesIO(source_data), 'r')

    # Build output zip
    output_buffer = io.BytesIO()
    with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as out_zf:
        for item in source_zf.infolist():
            try:
                data = source_zf.read(item.filename)
            except Exception as e:
                print(f"Warning: could not read {item.filename}: {e}")
                continue

            if item.filename == 'word/styles.xml':
                print(f"\nProcessing {item.filename}...")
                data = update_styles_xml(data)
            elif item.filename == 'word/document.xml':
                print(f"\nProcessing {item.filename}...")
                data = update_document_xml(data)

            out_zf.writestr(item, data)

    source_zf.close()

    # Write output file
    print(f"\nWriting output: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'wb') as f:
        f.write(output_buffer.getvalue())

    print(f"\nDone! Output file size: {os.path.getsize(OUTPUT_PATH):,} bytes")

    # Verify by reading back
    print("\nVerification - reading back updated document styles:")
    from lxml import etree

    with zipfile.ZipFile(OUTPUT_PATH, 'r') as vf:
        styles_data = vf.read('word/styles.xml')

    root = etree.fromstring(styles_data)
    W_NS2 = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

    for style_el in root.findall(f'.//{{{W_NS2}}}style'):
        style_id = style_el.get(f'{{{W_NS2}}}styleId')
        if style_id in STYLE_SIZE_MAP:
            rpr_el = style_el.find(f'{{{W_NS2}}}rPr')
            sz_el = rpr_el.find(f'{{{W_NS2}}}sz') if rpr_el is not None else None
            szCs_el = rpr_el.find(f'{{{W_NS2}}}szCs') if rpr_el is not None else None
            sz = int(sz_el.get(f'{{{W_NS2}}}val'))/2 if sz_el is not None else None
            szCs = int(szCs_el.get(f'{{{W_NS2}}}val'))/2 if szCs_el is not None else None
            print(f"  Style '{style_id}': sz={sz}pt, szCs={szCs}pt")


if __name__ == '__main__':
    main()
