import pytest
from playwright.sync_api import Page

@pytest.fixture
def desktop_page(page: Page):
    page.set_viewport_size({
        "width": 1440,
        "height": 900
    })
    
    return page

@pytest.fixture
def mobile_page(page: Page):
    page.set_viewport_size({
        "width": 390,
        "height": 844
    })
    
    return page
