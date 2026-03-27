import time
from playwright.sync_api import sync_playwright

def verify_settings_shortcuts():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Go to the app
        page.goto("http://localhost:4003")

        # Wait for settings button and click it
        page.click('#settings-btn')

        # Wait for modal to appear
        page.wait_for_selector('#settings-modal', state='visible')

        # Wait a bit for transition
        time.sleep(1)

        # Take screenshot
        page.screenshot(path="verification_shortcuts.png")
        print("Screenshot taken: verification_shortcuts.png")

        browser.close()

if __name__ == "__main__":
    verify_settings_shortcuts()
