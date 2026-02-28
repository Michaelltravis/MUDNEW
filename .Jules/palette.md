# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2026-02-27 - Smart Scroll for Terminals
**Learning:** Automatically scrolling to the bottom on every new log prevents users from reading past history. Auto-scroll should only trigger if the user is already at the bottom of the container.
**Action:** Implement 'Smart Scroll' logic (checking `scrollTop`, `scrollHeight`, and `clientHeight`) in all custom terminal implementations.
