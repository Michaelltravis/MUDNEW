# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## $(date +%Y-%m-%d) - Focus Visible Indicators
**Learning:** Custom button styles in `web_client.py` reset the default browser outline, requiring explicit `:focus-visible` styling to maintain keyboard accessibility.
**Action:** Implemented a global `button:focus-visible` rule using the design system's `--accent` and `--accent-glow` variables to ensure consistent and obvious focus indicators.
