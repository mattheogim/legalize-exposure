#!/usr/bin/env python3
"""Apply all patches needed for US Federal support.

Usage:
    cd ~/legalize/legalize-Canada/legalize-ca-pipeline
    python apply_us_patches.py

This script modifies:
  1. legalize_ca/models.py     — adds US_FEDERAL to Jurisdiction enum
  2. legalize_ca/utils.py      — adds get_bytes() to ThrottledClient
  3. legalize_ca/fetchers/__init__.py — registers USFederalFetcher
  4. legalize_ca/cli.py        — adds 'us-federal' subcommand
"""

import re
import sys
from pathlib import Path

BASE = Path("legalize_ca")
CHANGED = []
FAILED = []


def patch_file(path: Path, description: str, patches: list[tuple[str, str, str]]):
    """Apply regex-based patches to a file.

    patches: list of (pattern, replacement, label)
    """
    if not path.exists():
        FAILED.append(f"  ✗ {path} — file not found")
        return

    text = path.read_text()
    original = text

    for pattern, replacement, label in patches:
        new_text = re.sub(pattern, replacement, text, count=1)
        if new_text == text:
            # Check if already patched
            if replacement.strip().split('\n')[0].strip() in text:
                print(f"  ⏭  {label} — already applied")
            else:
                FAILED.append(f"  ✗ {label} — pattern not found in {path}")
        else:
            text = new_text
            print(f"  ✓ {label}")

    if text != original:
        path.write_text(text)
        CHANGED.append(str(path))


def patch_models():
    """Add US_FEDERAL to Jurisdiction enum."""
    print("\n[1/4] models.py — Jurisdiction enum")
    path = BASE / "models.py"

    patches = [
        # Add US_FEDERAL after the last Canadian jurisdiction
        # Match the pattern: BC = "bc" (or last enum member before the class ends)
        (
            r'(class Jurisdiction\(.*?Enum\):.*?)((\n    \w+ = "[^"]+"\n)(?=\n|class|\Z))',
            r'\1\2    US_FEDERAL = "us-federal"\n',
            'Add US_FEDERAL = "us-federal" to Jurisdiction enum',
        ),
    ]

    # Fallback: try simpler pattern if the above doesn't match
    if not path.exists():
        FAILED.append(f"  ✗ {path} — file not found")
        return

    text = path.read_text()

    if 'US_FEDERAL' in text:
        print('  ⏭  US_FEDERAL already in Jurisdiction enum')
        return

    # Find the Jurisdiction enum and add US_FEDERAL
    # Strategy: find the last enum value line and add after it
    lines = text.split('\n')
    new_lines = []
    in_jurisdiction = False
    added = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        if 'class Jurisdiction' in line:
            in_jurisdiction = True
            continue

        if in_jurisdiction and not added:
            # Look for the last enum member (line with = "...")
            # Next line is either empty, a comment, or a new class
            is_enum_val = re.match(r'\s+\w+\s*=\s*"', line)
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            next_is_not_enum = not re.match(r'\s+\w+\s*=\s*"', next_line)

            if is_enum_val and next_is_not_enum:
                new_lines.append('    US_FEDERAL = "us-federal"')
                added = True
                in_jurisdiction = False

    if added:
        path.write_text('\n'.join(new_lines))
        CHANGED.append(str(path))
        print('  ✓ Added US_FEDERAL = "us-federal" to Jurisdiction enum')
    else:
        FAILED.append('  ✗ Could not find insertion point in Jurisdiction enum')


def patch_utils():
    """Add get_bytes() method to ThrottledClient."""
    print("\n[2/4] utils.py — ThrottledClient.get_bytes()")
    path = BASE / "utils.py"

    if not path.exists():
        FAILED.append(f"  ✗ {path} — file not found")
        return

    text = path.read_text()

    if 'get_bytes' in text:
        print('  ⏭  get_bytes() already exists')
        return

    # Find ThrottledClient class and add get_bytes after get_text or get_xml
    method_code = '''
    def get_bytes(self, url: str) -> bytes:
        """GET request returning raw bytes (for zip downloads)."""
        self._throttle()
        resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
'''

    # Try to insert after get_text or get_xml method
    # Find the last method in ThrottledClient
    patterns = [
        (r'(    def get_xml\(self.*?(?=\n    def |\nclass |\Z))', 'after get_xml'),
        (r'(    def get_text\(self.*?(?=\n    def |\nclass |\Z))', 'after get_text'),
        (r'(    def get\(self.*?(?=\n    def |\nclass |\Z))', 'after get'),
    ]

    for pattern, label in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            insert_pos = match.end()
            text = text[:insert_pos] + '\n' + method_code + text[insert_pos:]
            path.write_text(text)
            CHANGED.append(str(path))
            print(f'  ✓ Added get_bytes() {label}')
            return

    # Fallback: append before end of class
    # Find "class ThrottledClient" and append method at the end
    if 'class ThrottledClient' in text:
        # Just append to the file (assumes ThrottledClient is the last class)
        text = text.rstrip() + '\n' + method_code + '\n'
        path.write_text(text)
        CHANGED.append(str(path))
        print('  ✓ Added get_bytes() at end of file')
    else:
        FAILED.append('  ✗ ThrottledClient class not found in utils.py')


def patch_fetchers_init():
    """Register USFederalFetcher in fetchers/__init__.py."""
    print("\n[3/4] fetchers/__init__.py — register import")
    path = BASE / "fetchers" / "__init__.py"

    if not path.exists():
        FAILED.append(f"  ✗ {path} — file not found")
        return

    text = path.read_text()

    if 'us_federal' in text or 'USFederalFetcher' in text:
        print('  ⏭  USFederalFetcher already imported')
        return

    # Add import line
    import_line = 'from .us_federal import USFederalFetcher'

    # Insert after the last existing import
    if 'from .bc' in text:
        text = text.replace(
            'from .bc import BCFetcher',
            'from .bc import BCFetcher\n' + import_line
        )
    elif 'from .federal' in text:
        text = re.sub(
            r'(from \.federal import \w+)',
            r'\1\n' + import_line,
            text
        )
    else:
        # Just append
        text = text.rstrip() + '\n' + import_line + '\n'

    path.write_text(text)
    CHANGED.append(str(path))
    print(f'  ✓ Added: {import_line}')


def patch_cli():
    """Add us-federal subcommand to cli.py."""
    print("\n[4/4] cli.py — add us-federal subcommand")
    path = BASE / "cli.py"

    if not path.exists():
        FAILED.append(f"  ✗ {path} — file not found")
        return

    text = path.read_text()

    if 'us-federal' in text or 'us_federal' in text:
        print('  ⏭  us-federal command already exists')
        return

    # Build the CLI command code block
    cli_code = '''

@cli.command("us-federal")
@click.option("--output-dir", required=True, type=click.Path(), help="Output directory for US law files")
@click.option("--local-xml", type=click.Path(exists=True), help="Local directory with USLM XML files")
@click.option("--titles", type=str, default=None, help="Comma-separated title numbers (e.g. 1,5,18)")
def us_federal(output_dir: str, local_xml: str | None, titles: str | None):
    """Fetch US Code (USLM XML) and write to Markdown."""
    from .fetchers.us_federal import USFederalFetcher
    from .writer import write_laws
    from pathlib import Path

    fetcher = USFederalFetcher()

    title_list = None
    if titles:
        title_list = [int(t.strip()) for t in titles.split(",")]

    if local_xml:
        docs = fetcher.fetch_from_local_xml(Path(local_xml))
    else:
        docs = fetcher.fetch_all(titles=title_list)

    write_laws(docs, Path(output_dir))
'''

    # Find the last @cli.command block and append after it
    # Look for the last function decorated with @cli.command
    # Strategy: append before `if __name__` or at the end
    if 'if __name__' in text:
        text = text.replace(
            'if __name__',
            cli_code + '\nif __name__'
        )
    else:
        text = text.rstrip() + '\n' + cli_code + '\n'

    # Make sure click is imported
    if 'import click' not in text:
        text = 'import click\n' + text

    path.write_text(text)
    CHANGED.append(str(path))
    print('  ✓ Added us-federal CLI command')


def main():
    # Check we're in the right directory
    if not BASE.exists():
        print(f"Error: {BASE}/ not found.")
        print("Run this from the legalize-ca-pipeline root directory:")
        print("  cd ~/legalize/legalize-Canada/legalize-ca-pipeline")
        print("  python apply_us_patches.py")
        sys.exit(1)

    print("=" * 50)
    print("Applying US Federal patches")
    print("=" * 50)

    patch_models()
    patch_utils()
    patch_fetchers_init()
    patch_cli()

    print("\n" + "=" * 50)
    if CHANGED:
        print(f"✅ Modified {len(CHANGED)} file(s):")
        for f in CHANGED:
            print(f"   {f}")
    if FAILED:
        print(f"\n⚠️  {len(FAILED)} issue(s):")
        for f in FAILED:
            print(f)
    if not CHANGED and not FAILED:
        print("Everything already up to date.")
    print("=" * 50)


if __name__ == "__main__":
    main()
