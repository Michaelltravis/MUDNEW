## 2026-02-24 - MUD Web Client Accessibility

**Learning:** Real-time text interfaces (like MUD clients) are often inaccessible to screen readers because they don't announce incoming text automatically. A simple `innerHTML +=` approach also destroys and recreates the DOM, which can cause the screen reader to lose its place or re-read the entire buffer.

**Action:** Always use `aria-live="polite"` and `role="log"` for terminal-like output containers. Use `insertAdjacentHTML('beforeend', ...)` instead of `innerHTML +=` to preserve the existing DOM nodes and ensure that only the new content is announced.
