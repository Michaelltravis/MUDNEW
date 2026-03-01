# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2026-03-01 - Terminal Smart Scroll
**Learning:** For terminal or chat interfaces, forcing a scroll to the bottom on every new message interrupts users who have scrolled up to read history.
**Action:** Always implement a "smart scroll" that checks if the user is already at the bottom (`Math.abs(el.scrollHeight - el.scrollTop - el.clientHeight) <= 5`) before auto-scrolling.
