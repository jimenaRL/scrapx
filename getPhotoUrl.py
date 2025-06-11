# Adapted from https://scrapfly.io/blog/how-to-scrape-twitter/

from __future__ import annotations
import json
import asyncio
from argparse import ArgumentParser
from playwright.sync_api import sync_playwright, TimeoutError

def scrape_profile(url: str, cookies: Iterable(dict) | None = None) -> str:
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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        if cookies:
            context.add_cookies(cookies)
        page = context.new_page()

        # enable background request intercepting:
        page.on("response", intercept_response)
        # go to url and wait for the page to load
        page.goto(url)
        try:
            page.wait_for_selector(
                "[data-testid='swipe-to-dismiss']",
                timeout=2000)
        except TimeoutError as e:
            return

        # find all tweet background requests
        tweet_calls = [f for f in _xhr_calls if "UserBy" in f.url]
        for xhr in tweet_calls:
            data = xhr.json()
            return data['data']['user']['result']['avatar']['image_url']

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument('--username', type=str)
    ap.add_argument('--cookies', type=str, required=False, default=None)
    args = ap.parse_args()
    username = args.username
    cookies = args.cookies
    if cookies:
        with open(args.cookies) as f:
            cookies = list(map(json.loads, f.readlines()))
    print(scrape_profile(f"https://x.com/{username}/photo", cookies))