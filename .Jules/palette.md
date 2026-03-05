# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.
## 2024-05-24 - Focus Visible Styles
**Learning:** Custom button styles often remove default browser outlines, making keyboard navigation difficult.
**Action:** Added `:focus-visible` styles using the `--accent` variable to ensure keyboard users can track their navigation focus across all custom buttons.
