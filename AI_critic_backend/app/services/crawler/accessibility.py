def collect_accessibility(page):
    # Helper
    def get_attr(element, name):
        return element.get_attribute(name)
    
    # Page level accessibility information
    html = page.locator("html")
    document = {
        "lang": get_attr(html, "lang"),
        "dir": get_attr(html, "dir"),
        "role": get_attr(html, "role"),
        "aria_label": get_attr(html, "aria-label"),
        "aria_labelledby": get_attr(html, "aria-labelledby"),
        "aria_describedby": get_attr(html, "aria-describedby"),
        "title": page.title()
    }
    
    #Images
    images = page.locator("img")
    
    image_data = []
    
    for i in range(images.count()):
        image = images.nth(i)
        
        image_data.append({
            "index": i,
            "src": get_attr(
                image,
                "src"
            ),
            
            "alt": get_attr(
                image,
                "alt"
            ),
            
            "role": get_attr(
                image,
                "role"
            ),
            
            "aria_label": get_attr(
                image,
                "aria-label"
            ),
            
            "aria_labelledby": get_attr(
                image,
                "aria-labelledby"
            ),
            
            "aria_hidden": get_attr(
                image,
                "aria-hidden"
            ),
            
            "width": get_attr(
                image,
                "width"
            ),
            
            "height": get_attr(
                image,
                "height"
            ),
            
            "loading": get_attr(
                image,
                "loading"
            ),
            
            "visible": image.is_visible()
        })
        
           # Interactive Elements
    interactive_elements = page.locator(
        """
        a,
        button,
        input,
        select,
        textarea,
        [role="button"],
        [role="link"],
        [role="checkbox"],
        [role="radio"],
        [role="switch"],
        [role="tab"],
        [role="menuitem"],
        [role="combobox"],
        [role="slider"]
        """
    )

    interactive_data = []

    for i in range(interactive_elements.count()):

        element = interactive_elements.nth(i)

        tag = element.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

        interactive_data.append({

            "index": i,

            "tag": tag,

            "text": element.inner_text().strip()
            if tag in ["a", "button"]
            else "",

            "role": get_attr(
                element,
                "role"
            ),

            "aria_label": get_attr(
                element,
                "aria-label"
            ),

            "aria_labelledby": get_attr(
                element,
                "aria-labelledby"
            ),

            "aria_describedby": get_attr(
                element,
                "aria-describedby"
            ),

            "aria_hidden": get_attr(
                element,
                "aria-hidden"
            ),

            "aria_disabled": get_attr(
                element,
                "aria-disabled"
            ),

            "aria_expanded": get_attr(
                element,
                "aria-expanded"
            ),

            "aria_pressed": get_attr(
                element,
                "aria-pressed"
            ),

            "aria_selected": get_attr(
                element,
                "aria-selected"
            ),

            "aria_controls": get_attr(
                element,
                "aria-controls"
            ),

            "tabindex": get_attr(
                element,
                "tabindex"
            ),

            "title": get_attr(
                element,
                "title"
            ),

            "visible": element.is_visible()
        })

    # ARIA Elements
    aria_elements = page.locator(
        """
        [role],
        [aria-label],
        [aria-labelledby],
        [aria-describedby],
        [aria-hidden],
        [aria-live],
        [aria-expanded],
        [aria-controls],
        [aria-current],
        [aria-pressed],
        [aria-selected]
        """
    )

    aria_data = []

    for i in range(aria_elements.count()):

        element = aria_elements.nth(i)

        aria_data.append({

            "index": i,

            "tag": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "role": get_attr(
                element,
                "role"
            ),

            "aria_label": get_attr(
                element,
                "aria-label"
            ),

            "aria_labelledby": get_attr(
                element,
                "aria-labelledby"
            ),

            "aria_describedby": get_attr(
                element,
                "aria-describedby"
            ),

            "aria_hidden": get_attr(
                element,
                "aria-hidden"
            ),

            "aria_live": get_attr(
                element,
                "aria-live"
            ),

            "aria_expanded": get_attr(
                element,
                "aria-expanded"
            ),

            "aria_controls": get_attr(
                element,
                "aria-controls"
            ),

            "aria_current": get_attr(
                element,
                "aria-current"
            ),

            "aria_pressed": get_attr(
                element,
                "aria-pressed"
            ),

            "aria_selected": get_attr(
                element,
                "aria-selected"
            ),

            "tabindex": get_attr(
                element,
                "tabindex"
            ),

            "visible": element.is_visible()
        })

    # Landmarks
    landmarks = page.locator(
        """
        header,
        nav,
        main,
        aside,
        footer,
        [role="banner"],
        [role="navigation"],
        [role="main"],
        [role="complementary"],
        [role="contentinfo"],
        [role="search"],
        [role="region"]
        """
    )

    landmark_data = []

    for i in range(landmarks.count()):

        landmark = landmarks.nth(i)

        landmark_data.append({

            "index": i,

            "tag": landmark.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "role": get_attr(
                landmark,
                "role"
            ),

            "aria_label": get_attr(
                landmark,
                "aria-label"
            ),

            "aria_labelledby": get_attr(
                landmark,
                "aria-labelledby"
            ),

            "visible": landmark.is_visible()
        })

    # Keyboard Navigation
    tabindex_elements = page.locator(
        "[tabindex]"
    )

    tabindex_data = []

    for i in range(tabindex_elements.count()):

        element = tabindex_elements.nth(i)

        tabindex_data.append({

            "index": i,

            "tag": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "tabindex": get_attr(
                element,
                "tabindex"
            ),

            "role": get_attr(
                element,
                "role"
            ),

            "aria_label": get_attr(
                element,
                "aria-label"
            ),

            "visible": element.is_visible()
        })

    # Live Regions
    live_regions = page.locator(
        "[aria-live]"
    )

    live_region_data = []

    for i in range(live_regions.count()):

        region = live_regions.nth(i)

        live_region_data.append({

            "index": i,

            "tag": region.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "aria_live": get_attr(
                region,
                "aria-live"
            ),

            "aria_atomic": get_attr(
                region,
                "aria-atomic"
            ),

            "aria_relevant": get_attr(
                region,
                "aria-relevant"
            ),

            "text": region.inner_text().strip(),

            "visible": region.is_visible()
        })

    # Accessibility Statistics
    statistics = {

        "has_lang": bool(
            get_attr(html, "lang")
        ),

        "image_count": images.count(),

        "images_missing_alt": page.locator(
            "img:not([alt])"
        ).count(),

        "images_empty_alt": page.locator(
            "img[alt='']"
        ).count(),

        "interactive_element_count":
            interactive_elements.count(),

        "aria_element_count":
            aria_elements.count(),

        "landmark_count":
            landmarks.count(),

        "tabindex_count":
            tabindex_elements.count(),

        "positive_tabindex_count":
            page.locator(
                "[tabindex]:not([tabindex='0']):not([tabindex='-1'])"
            ).count(),

        "live_region_count":
            live_regions.count(),

        "aria_hidden_count":
            page.locator(
                "[aria-hidden='true']"
            ).count()
    }

    # Final Result
    return {

        "document": document,

        "images": {
            "count": len(image_data),
            "items": image_data
        },

        "interactive": {
            "count": len(interactive_data),
            "items": interactive_data
        },

        "aria": {
            "count": len(aria_data),
            "items": aria_data
        },

        "landmarks": {
            "count": len(landmark_data),
            "items": landmark_data
        },

        "keyboard_navigation": {
            "count": len(tabindex_data),
            "items": tabindex_data
        },

        "live_regions": {
            "count": len(live_region_data),
            "items": live_region_data
        },

        "statistics": statistics
    }