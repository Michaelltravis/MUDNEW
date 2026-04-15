## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-24 - Smart Auto-Scrolling
**Learning:** Terminal output in the web client should implement 'Smart Scroll', where auto-scrolling only occurs if the user is currently at the bottom of the scroll container. To handle high-DPI sub-pixel scrolling differences safely, check if `Math.abs(scrollHeight - scrollTop - clientHeight) < 10`. Also when checking `settings.autoScroll` declared with `let` later, wrap the access in a `try...catch` block to safely handle Temporal Dead Zone errors.
**Action:** Always implement Smart Scroll checking for sub-pixel offsets and TDZ handling for auto-scrolling terminal elements.

## 2024-05-25 - Custom Toggle Switches
**Learning:** Custom toggle buttons (e.g., in settings modals) must implement semantic switch attributes including `role='switch'`, dynamic `aria-checked` states ('true' or 'false'), and explicit labels via `aria-labelledby` or `aria-label`. Otherwise, screen readers don't know the state of the toggle.
**Action:** Always ensure toggle buttons implement ARIA switch semantics.## 2024-05-24 - Disabled Interactive Elements During Connection States
**Learning:** Users can become confused or trigger errors if they interact with inputs and action buttons before a WebSocket connection is established or after it drops. Interactive visual effects (like hover) on disabled buttons can exacerbate this confusion.
**Action:** Programmatically disable all relevant inputs (text fields, send buttons, quick action buttons) when the connection is initializing or lost. Apply CSS `:not(:disabled)` to hover/active pseudo-classes to prevent false interactive cues, and update input placeholders to reflect the current state (e.g., 'Connecting...', 'Disconnected').
