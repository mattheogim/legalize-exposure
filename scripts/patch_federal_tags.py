#!/usr/bin/env python3
"""Replace federal.py with the version that handles all XML tags.

New tags handled (previously dropped):
  _extract_text(): DefinitionRef (226), AmendedText (60), FormulaTerm/Text/Definition/Connector
  _section_to_md(): Introduction (31), ContinuedParagraph (29), ContinuedSubparagraph (6),
                    Item (48), Formula, Subparagraph/Clause/Subclause (already applied)
  _body_to_md(): Oath (4), List (2)

Run from pipeline root:
  python3 patch_federal_tags.py

Or just copy the file directly:
  cp /path/to/federal.py legalize_ca/fetchers/federal.py
"""

import shutil
import sys
from pathlib import Path

TARGET = Path("legalize_ca/fetchers/federal.py")
# The updated file should be in the same directory as this script
SOURCE = Path(__file__).parent / "federal.py"

if not TARGET.exists():
    print(f"ERROR: {TARGET} not found. Run from pipeline root directory.")
    sys.exit(1)

if not SOURCE.exists():
    print(f"ERROR: {SOURCE} not found. Make sure federal.py is next to this script.")
    sys.exit(1)

# Backup
backup = TARGET.with_suffix(".py.bak")
shutil.copy2(TARGET, backup)
print(f"✅ Backed up to {backup}")

# Copy
shutil.copy2(SOURCE, TARGET)
new_size = TARGET.stat().st_size
print(f"✅ Updated {TARGET} ({new_size} bytes)")

# Verify key tags are present
src = TARGET.read_text()
checks = [
    ("DefinitionRef", "inline definition references"),
    ("AmendedText", "amendment text"),
    ("FormulaTerm", "formula components"),
    ("ContinuedParagraph", "continued paragraphs"),
    ("ContinuedSubparagraph", "continued subparagraphs"),
    ("Introduction", "introduction/preamble"),
    ("Item", "list items"),
    ("Subparagraph", "subparagraphs"),
    ("Clause", "clauses"),
    ("Subclause", "subclauses"),
    ("Oath", "oaths"),
    ('"List"', "lists"),
]

print("\nTag handling verification:")
all_ok = True
for tag, desc in checks:
    found = tag in src
    status = "✅" if found else "❌"
    print(f"  {status} {desc} ({tag})")
    if not found:
        all_ok = False

if all_ok:
    print(f"\n✅ All {len(checks)} tag handlers verified!")
else:
    print("\n⚠️  Some tags missing — check the file.")
