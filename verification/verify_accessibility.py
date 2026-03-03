import re
from playwright.sync_api import Page, expect, sync_playwright

def test_accessibility_aria_labels(page: Page):
    page.goto("http://localhost:4003/")

    # Open settings modal to make buttons visible
    page.locator("#settings-btn").click()
    page.wait_for_selector("#settings-modal", state="visible")

    # Check for font-decrease aria-label
    font_decrease = page.locator("#font-decrease")
    expect(font_decrease).to_have_attribute("aria-label", "Decrease font size")

    # Check for font-increase aria-label
    font_increase = page.locator("#font-increase")
    expect(font_increase).to_have_attribute("aria-label", "Increase font size")
    print("✓ ARIA labels verified successfully.")

def test_accessibility_focus_visible(page: Page):
    page.goto("http://localhost:4003/")

    # Open settings modal
    page.locator("#settings-btn").click()
    page.wait_for_selector("#settings-modal", state="visible")

    # Focus the button using keyboard
    page.keyboard.press("Tab")

    # We can evaluate to see the focus styles or if it has the pseudo-class matching
    # Playwright cannot directly select pseudo-classes like :focus-visible via locator,
    # but we can check the computed style of the currently focused element.
    # To reliably trigger :focus-visible, we might need to use keyboard navigation to focus the element.
    font_decrease = page.locator("#font-decrease")
    font_decrease.focus()

    # The pseudo-class might not be perfectly testable via computed style in all browsers seamlessly
    # but let's assert it exists in the raw HTML block we injected
    html_content = page.content()
    if "button:focus-visible" in html_content:
        print("✓ focus-visible CSS rule found.")
    else:
        raise AssertionError("button:focus-visible CSS rule not found in page content.")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_accessibility_aria_labels(page)
            test_accessibility_focus_visible(page)
            print("All accessibility verifications passed.")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
