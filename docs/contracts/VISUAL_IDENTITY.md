# ORION Visual Identity — Claude STRATA Pack

Status: **OWNER-ACCEPTED ASSET CONTRACT**

The ORION product uses the STRATA icon system supplied by Claude. Do not replace it with a generic placeholder, letter O, engineering-Remote mark, or unrelated launcher art without explicit owner approval.

## Source renderer

`ui/strata/icons/make_icons.py`

The renderer produces the accepted lattice-planet identity:
- deep-space background;
- cyan/ice planetary atmosphere;
- geometric lattice;
- tilted orbital ring;
- Orion-belt stars.

## Master PNGs

Generated in `ui/strata/icons/`:

- `orion-icon-1024.png` — opaque full-bleed app/store master;
- `orion-icon-rounded-1024.png` — rounded transparent-corner documentation/web asset;
- `orion-mark-transparent-1024.png` — transparent planet/ring mark.

## Web / STRATA

The STRATA page uses:
- `icons/favicon.ico`;
- `icons/apple-touch-icon.png`.

The complete generated size pack remains under `ui/strata/icons/sizes/`.

## Android

The Android package is `com.sadusor.orionv3`, product label **ORION**.

Launcher density mapping:
- mdpi → 48 px;
- hdpi → 72 px;
- xhdpi → 96 px;
- xxhdpi → 144 px;
- xxxhdpi → 192 px.

The opaque full-bleed icon is intentional because Android launchers apply their own mask/rounding.

## Generation / qualification

`scripts/apply_claude_icons.ps1` renders the source pack, installs web assets, and maps Android launcher resources.

The external TheHands engineering job may run this script and commit the generated binary assets into ORION-V3. TheHands does not own the assets or ORION product code.

PC smoke must prove favicon/apple-touch delivery. Android build must succeed with the launcher resources before qualification.
