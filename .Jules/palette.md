## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-24 - Smart Auto-Scrolling
**Learning:** Terminal output in the web client should implement 'Smart Scroll', where auto-scrolling only occurs if the user is currently at the bottom of the scroll container. To handle high-DPI sub-pixel scrolling differences safely, check if `Math.abs(scrollHeight - scrollTop - clientHeight) < 10`. Also when checking `settings.autoScroll` declared with `let` later, wrap the access in a `try...catch` block to safely handle Temporal Dead Zone errors.
**Action:** Always implement Smart Scroll checking for sub-pixel offsets and TDZ handling for auto-scrolling terminal elements.

## 2024-05-25 - Custom Toggle Switches
**Learning:** Custom toggle buttons (e.g., in settings modals) must implement semantic switch attributes including `role='switch'`, dynamic `aria-checked` states ('true' or 'false'), and explicit labels via `aria-labelledby` or `aria-label`. Otherwise, screen readers don't know the state of the toggle.
**Action:** Always ensure toggle buttons implement ARIA switch semantics.
## 2026-03-17 - WebSocket Connection State Feedback
**Learning:** In MUD terminal interfaces communicating via WebSockets, users must receive immediate and clear feedback regarding the connection state. Without explicitly disabling input controls and updating placeholders to communicate status (e.g., "Connecting...", "Disconnected"), users may unknowingly attempt to send commands that fail silently. This leads to user frustration and degrades accessibility.
**Action:** Always visually and programmatically disable interactive input elements (like text inputs, send buttons, and quick command buttons) during connection initialization and upon connection failure. Provide explanatory placeholders detailing the connection status. Use CSS `:not(:disabled)` pseudo-classes to prevent disabled elements from showing interactive hover/active effects, and style `:disabled` elements with reduced opacity and a `not-allowed` cursor.
