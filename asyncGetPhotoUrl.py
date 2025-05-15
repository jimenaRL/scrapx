# Adapted from https://scrapfly.io/blog/how-to-scrape-twitter/

import json
from argparse import ArgumentParser
import asyncio
from playwright.async_api import async_playwright

async def main(username: str) -> dict:
    """
    Scrape the url profile bio at x.com
    """
    _xhr_calls = []

    def intercept_response(response):
        """capture all background requests and save them"""
        # we can extract details from background requests
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    url = f"https://x.com/{username}/photo"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 640, "height": 360})
        page = await context.new_page()

        # enable background request intercepting:
        page.on("response", intercept_response)
        # go to url and wait for the page to load
        await page.goto(url)
        await page.wait_for_selector("[data-testid='swipe-to-dismiss']")

        # select appropiated tweet background request
        tweet_calls = [f for f in _xhr_calls if "UserByScreenName" in f.url]
        xhr = tweet_calls[0]
        data = await xhr.json()

        with open(f"{username}.txt", 'w') as file:
            file.write(json.dumps(data))

        await browser.close()

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument('--username', type=str)
    args = ap.parse_args()
    username = args.username
    asyncio.run(main(username))
