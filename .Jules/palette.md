## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-24 - Smart Auto-Scrolling
**Learning:** Terminal output in the web client should implement 'Smart Scroll', where auto-scrolling only occurs if the user is currently at the bottom of the scroll container. To handle high-DPI sub-pixel scrolling differences safely, check if `Math.abs(scrollHeight - scrollTop - clientHeight) < 10`. Also when checking `settings.autoScroll` declared with `let` later, wrap the access in a `try...catch` block to safely handle Temporal Dead Zone errors.
**Action:** Always implement Smart Scroll checking for sub-pixel offsets and TDZ handling for auto-scrolling terminal elements.

## 2024-05-25 - Custom Toggle Switches
**Learning:** Custom toggle buttons (e.g., in settings modals) must implement semantic switch attributes including `role='switch'`, dynamic `aria-checked` states ('true' or 'false'), and explicit labels via `aria-labelledby` or `aria-label`. Otherwise, screen readers don't know the state of the toggle.
**Action:** Always ensure toggle buttons implement ARIA switch semantics.