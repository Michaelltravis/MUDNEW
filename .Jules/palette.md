## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-24 - Smart Auto-Scrolling
**Learning:** Terminal output in the web client should implement 'Smart Scroll', where auto-scrolling only occurs if the user is currently at the bottom of the scroll container. To handle high-DPI sub-pixel scrolling differences safely, check if `Math.abs(scrollHeight - scrollTop - clientHeight) < 10`. Also when checking `settings.autoScroll` declared with `let` later, wrap the access in a `try...catch` block to safely handle Temporal Dead Zone errors.
**Action:** Always implement Smart Scroll checking for sub-pixel offsets and TDZ handling for auto-scrolling terminal elements.

## 2024-05-25 - Custom Toggle Switches
**Learning:** Custom toggle buttons (e.g., in settings modals) must implement semantic switch attributes including `role='switch'`, dynamic `aria-checked` states ('true' or 'false'), and explicit labels via `aria-labelledby` or `aria-label`. Otherwise, screen readers don't know the state of the toggle.
**Action:** Always ensure toggle buttons implement ARIA switch semantics.
## 2024-05-26 - Disabled State Styling and Semantics
**Learning:** Interactive elements like inputs and buttons in real-time applications (e.g., WebSocket-based clients) should visibly convey their active status. Failing to visually update elements to a disabled state (using CSS opacity and `cursor: not-allowed` combined with `disabled` HTML attributes) can lead users to attempt interactions that cannot succeed. Additionally, applying `:not(:disabled)` strictly to hover and active pseudo-classes ensures hover effects don't falsely suggest interactivity on disabled inputs.
**Action:** Always programmatically apply the `disabled` property to interaction elements when a service is disconnected, provide context via placeholders (e.g., "Connecting...", "Disconnected"), and pair it with explicit CSS styling utilizing `:not(:disabled)` to restrict interactive visual effects.
