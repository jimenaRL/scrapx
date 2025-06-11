# Adapted from https://scrapfly.io/blog/how-to-scrape-twitter/ and
# https://github.com/microsoft/playwright-python

from __future__ import annotations
from typing import Type
from typing import Any

import csv
import json
import asyncio
from argparse import ArgumentParser
from playwright.async_api import async_playwright

async def getData(username: str, cookies: Iterable(dict) | None = None) -> None:
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
        if cookies:
            await context.add_cookies(cookies)
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

        imageUrl = data['data']['user']['result']['avatar']['image_url']
        with open(f"results/{username}.txt", 'w') as f:
            f.write(imageUrl)

        await browser.close()


ap = ArgumentParser()
ap.add_argument('--usernamesFile', type=str)
ap.add_argument('--cookies', type=str, required=False, default=None)
args = ap.parse_args()
usernamesFile = args.usernamesFile
cookies = args.cookies

with open(usernamesFile) as f:
    usernames = [l.replace("\n", "") for l in f.readlines()]

if cookies:
    with open(args.cookies) as f:
        cookies = list(map(json.loads, f.readlines()))

async def run_all() -> None:
    coroutines = []
    # prepare the coroutines
    for username in usernames:
        coroutines.append(getData(username, cookies))
    # and execute them all at once
    await asyncio.gather(*coroutines)

asyncio.run(run_all())
