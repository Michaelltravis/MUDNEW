# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-23 - Smart Scrolling UX
**Learning:** Terminal interfaces that auto-scroll unconditionally can frustrate users trying to read history when new text arrives. Checking if the scroll position is already at the bottom before auto-scrolling solves this without needing complex state management.
**Action:** Implement "Smart Scroll" (checking `scrollHeight - clientHeight <= scrollTop + 1`) in text-heavy interfaces rather than unconditional auto-scrolling.
