import asyncio
from playwright.async_api import async_playwright

async def mock_mud_server():
    server = await asyncio.start_server(lambda r, w: None, '127.0.0.1', 4000)
    return server

async def main():
    server = await mock_mud_server()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.add_init_script("window.localStorage.setItem('mudAutoScroll', 'false');")

        await page.goto("http://localhost:4003")

        await page.wait_for_selector("#command-input")

        # Wait until it is connected
        await page.wait_for_function("document.getElementById('status').textContent === 'Connected'")

        input_el = page.locator("#command-input")
        send_btn = page.locator("#send-btn")
        look_btn = page.locator('.quick-btn[data-cmd="look"]')
        north_btn = page.locator('.exit-btn[data-dir="north"]')

        input_disabled = await input_el.is_disabled()
        send_disabled = await send_btn.is_disabled()
        look_disabled = await look_btn.is_disabled()
        north_disabled = await north_btn.is_disabled()

        placeholder = await input_el.get_attribute("placeholder")

        print(f"Input disabled: {input_disabled}")
        print(f"Send disabled: {send_disabled}")
        print(f"Look disabled: {look_disabled}")
        print(f"North disabled: {north_disabled}")
        print(f"Placeholder: {placeholder}")

        assert input_disabled is False
        assert send_disabled is False
        assert look_disabled is False
        assert north_disabled is False
        assert placeholder == "Enter command..."

        await browser.close()
        print("Success: All connected UI verification passed")

    server.close()
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
