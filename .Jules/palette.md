# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-24 - Smart Scroll UX Pattern
**Learning:** Log containers that append output rapidly can yank users away from what they are reading. "Smart Scroll" UX dictates that auto-scrolling should only happen if the user's scrollbar is already at the bottom (`scrollHeight - scrollTop <= clientHeight + padding`).
**Action:** Implement Smart Scroll for any dynamic log or chat container.
