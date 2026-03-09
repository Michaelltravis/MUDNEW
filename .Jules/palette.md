# Palette's Journal

## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2026-03-09 - Smart Scroll UX Pattern
**Learning:** Forcing scroll to bottom on every log event is highly disruptive to users who have scrolled up to read history.
**Action:** Implement a "Smart Scroll" pattern where auto-scrolling only engages if the scroll position is already at the bottom (calculating `Math.abs(scrollHeight - scrollTop - clientHeight) < 10` to handle sub-pixel scaling).
