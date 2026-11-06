#!/usr/bin/env python3
"""Check Spanish-related filenames on a player's own European disc, read-only.

    python port/tools/spanish_disc_inventory.py DHD_EU.iso
    python port/tools/spanish_disc_inventory.py DHD_EU.iso --json

This is a *filename inventory*, not a language patch or a proof that the game
can boot from a European disc.  It never extracts, copies or prints game data.
The ISO 9660 walker is shared with release_compare.py (finding 100).
"""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

from release_compare import Iso, boot_name

EU_BOOT = 'SLES_522.02'
SPANISH_GROUPS = {
    'Menu español': 'SHELL/UIS.',
    'Tienda de bicicletas en español': 'SHELL/BIKESHPS.',
}
# Reported for information only; the actual localized text tables live in the
# European ELF .rodata and level/loading-screen images also contain text.
SPANISH_MOVIES = ('MOV/SPCOPYRT.PSS', 'MOV/SPSCEAPR.PSS')


@dataclass(frozen=True)
class Inventory:
    boot: str
    eu_disc: bool
    filenames_seen: int
    localized_groups: dict
    legal_movies: dict
    shell_names_present: bool
    message: str


def inventory(iso):
    """Accepts an Iso (or a synthetic object with .files/.read for tests)."""
    boot, _config = boot_name(iso)
    paths = {name.upper() for name in iso.files}
    groups = {label: sum(name.startswith(prefix) for name in paths)
              for label, prefix in SPANISH_GROUPS.items()}
    movies = {name: name in paths for name in SPANISH_MOVIES}
    eu = boot == EU_BOOT
    assets = eu and all(groups.values())
    msg = ('Se encontraron nombres de recursos gráficos españoles en la edición europea. '
           'NO verifica tablas de textos, fuentes, videos, arranque ni traducción completa.'
           if assets else
           'Los nombres esperados no están presentes o el disco no es SLES-52202; '
           'no se puede confirmar el conjunto gráfico español.')
    return Inventory(boot=boot, eu_disc=eu, filenames_seen=len(paths),
                     localized_groups=groups, legal_movies=movies,
                     shell_names_present=assets, message=msg)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('iso', type=Path, help='imagen propia de Downhill Domination Europa')
    parser.add_argument('--json', action='store_true', help='imprimir resultado estructurado')
    args = parser.parse_args(argv)
    try:
        disc = Iso(args.iso)
        try:
            result = inventory(disc)
        finally:
            disc.f.close()
    except (OSError, KeyError, ValueError, SystemExit) as error:
        parser.exit(2, f'No se pudo leer la imagen ISO 9660: {error}\n')

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f'Edición: {result.boot} | archivos indexados: {result.filenames_seen}')
        for group, count in result.localized_groups.items():
            print(f'  {group}: {count} archivos con el prefijo esperado')
        for name, seen in result.legal_movies.items():
            print(f'  {name}: {"presente" if seen else "no encontrado"} (informativo)')
        print(result.message)
    return 0 if result.shell_names_present else 1


if __name__ == '__main__':
    sys.exit(main())
