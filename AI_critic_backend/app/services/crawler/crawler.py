
from pathlib import Path
from urllib.parse import urlparse
import re

from playwright.sync_api import Page


def crawl_website(page: Page, url: str):
    # Navigate to the website.
    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000
    )

    from .page_prepare import prepare_page_for_capture
    prepare_page_for_capture(page)

    # Collect evidence.
    from .metadata import collect_metadata
    metadata = collect_metadata(page, url)

    from .structure import collect_structure
    structure = collect_structure(page)

    from .interactive import collect_interactive
    interactive = collect_interactive(page)

    from .forms import collect_forms
    forms = collect_forms(page)

    from .accessibility import collect_accessibility
    accessibility = collect_accessibility(page)

    from .media import collect_media
    media = collect_media(page)

    from .layout import collect_layout
    layout = collect_layout(page)

    from .style import collect_styles
    styles = collect_styles(page)

    # Capture the full-page screenshot.
    screenshot_dir = Path("screenshots")
    screenshot_dir.mkdir(exist_ok=True)

    urlname = urlparse(url).netloc
    urlname = re.sub(r"[^a-zA-Z0-9.-]", "_", urlname)

    screenshot_path = screenshot_dir / f"{urlname}.png"

    page.screenshot(
        path=str(screenshot_path),
        full_page=True
    )

    # Return the complete crawler result.
    return {
        "url": url,
        "final_url": page.url,
        "title": metadata.get("title"),
        "metadata": metadata,
        "structure": structure,
        "interactive": interactive,
        "forms": forms,
        "accessibility": accessibility,
        "media": media,
        "layout": layout,
        "styles": styles,
        "screenshot": {
            "path": str(screenshot_path)
        }
    }
