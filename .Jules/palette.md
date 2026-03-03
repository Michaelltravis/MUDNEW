# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-23 - Custom Button Focus
**Learning:** When creating custom button styles that remove default browser outlines (e.g. `border: none; background: none;`), it breaks keyboard navigation accessibility because the current focus becomes invisible.
**Action:** Always add a `button:focus-visible` rule using existing design tokens (like `--accent`) to ensure keyboard users can see where they are navigating.
