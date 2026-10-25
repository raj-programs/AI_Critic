from playwright.sync_api import sync_playwright

from .crawler import crawl_website
from .safety import validate_public_http_url


def run_crawler(url: str):
    """Run one crawl with an isolated browser context and bounded timeouts."""
    validate_public_http_url(url)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
        )
        try:
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                service_workers="block",
            )
            context.set_default_timeout(30_000)
            context.set_default_navigation_timeout(30_000)

            def validate_navigation(route):
                if route.request.resource_type == "document":
                    try:
                        validate_public_http_url(route.request.url)
                    except ValueError:
                        route.abort()
                        return
                route.continue_()

            context.route("**/*", validate_navigation)
            page = context.new_page()
            try:
                return crawl_website(page, url)
            finally:
                context.close()
        finally:
            browser.close()
