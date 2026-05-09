## 2024-05-23 - Terminal Accessibility
**Learning:** Terminal-like interfaces in web clients need `role="log"` and `aria-live="polite"` to be announced by screen readers.
**Action:** Always check `div`s used as terminals for these attributes.

## 2024-05-24 - Smart Auto-Scrolling
**Learning:** Terminal output in the web client should implement 'Smart Scroll', where auto-scrolling only occurs if the user is currently at the bottom of the scroll container. To handle high-DPI sub-pixel scrolling differences safely, check if `Math.abs(scrollHeight - scrollTop - clientHeight) < 10`. Also when checking `settings.autoScroll` declared with `let` later, wrap the access in a `try...catch` block to safely handle Temporal Dead Zone errors.
**Action:** Always implement Smart Scroll checking for sub-pixel offsets and TDZ handling for auto-scrolling terminal elements.

## 2024-05-25 - Custom Toggle Switches
**Learning:** Custom toggle buttons (e.g., in settings modals) must implement semantic switch attributes including `role='switch'`, dynamic `aria-checked` states ('true' or 'false'), and explicit labels via `aria-labelledby` or `aria-label`. Otherwise, screen readers don't know the state of the toggle.
**Action:** Always ensure toggle buttons implement ARIA switch semantics.## 2024-05-09 - Accessible Stepper Controls in Settings
**Learning:** For custom numeric steppers in settings modals (like font size controls), developers often implement JavaScript boundaries without synchronizing the HTML `disabled` state or providing visual cues. This leaves screen readers unaware of the limits and can confuse keyboard/mouse users who keep clicking unreactive buttons. Additionally, the value display itself often lacks `aria-live` making changes silent to screen readers.
**Action:** Always add `aria-live="polite"` to the value display element of a stepper. In the JavaScript update function, explicitly toggle the `disabled` property on the boundary buttons (e.g., `decreaseBtn.disabled = true;`) and synchronize visual feedback using inline styles (e.g., `opacity: 0.5` and `cursor: not-allowed`) if no existing CSS utility classes exist.
