def collect_interactive(page):

    # =========================================================
    # Helper: safely get an attribute
    # =========================================================

    def get_attr(element, name):
        return element.get_attribute(name)

    # =========================================================
    # Buttons
    # =========================================================

    buttons = page.locator("button")

    button_data = []

    for i in range(buttons.count()):

        button = buttons.nth(i)

        button_data.append({
            "index": i,

            "text": button.inner_text().strip(),

            "aria_label": get_attr(
                button,
                "aria-label"
            ),

            "aria_labelledby": get_attr(
                button,
                "aria-labelledby"
            ),

            "aria_describedby": get_attr(
                button,
                "aria-describedby"
            ),

            "role": get_attr(
                button,
                "role"
            ),

            "type": get_attr(
                button,
                "type"
            ),

            "title": get_attr(
                button,
                "title"
            ),

            "name": get_attr(
                button,
                "name"
            ),

            "visible": button.is_visible(),

            "enabled": button.is_enabled(),

            "disabled": button.is_disabled(),

            "focused": button.evaluate(
                "(el) => document.activeElement === el"
            ),

            "tabindex": get_attr(
                button,
                "tabindex"
            )
        })

    # =========================================================
    # Links
    # =========================================================

    links = page.locator("a")

    link_data = []

    for i in range(links.count()):

        link = links.nth(i)

        link_data.append({
            "index": i,

            "text": link.inner_text().strip(),

            "href": get_attr(
                link,
                "href"
            ),

            "aria_label": get_attr(
                link,
                "aria-label"
            ),

            "aria_labelledby": get_attr(
                link,
                "aria-labelledby"
            ),

            "role": get_attr(
                link,
                "role"
            ),

            "title": get_attr(
                link,
                "title"
            ),

            "target": get_attr(
                link,
                "target"
            ),

            "rel": get_attr(
                link,
                "rel"
            ),

            "visible": link.is_visible(),

            "enabled": link.is_enabled(),

            "focused": link.evaluate(
                "(el) => document.activeElement === el"
            ),

            "tabindex": get_attr(
                link,
                "tabindex"
            )
        })

    # =========================================================
    # Input controls
    # =========================================================

    inputs = page.locator(
        "input, select, textarea"
    )

    input_data = []

    for i in range(inputs.count()):

        element = inputs.nth(i)

        tag = element.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

        input_data.append({

            "index": i,

            "tag": tag,

            "type": get_attr(
                element,
                "type"
            ),

            "name": get_attr(
                element,
                "name"
            ),

            "value": get_attr(
                element,
                "value"
            ),

            "placeholder": get_attr(
                element,
                "placeholder"
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

            "role": get_attr(
                element,
                "role"
            ),

            "required": element.is_required() is not None,

            "disabled": element.is_disabled(),

            "visible": element.is_visible(),

            "focused": element.evaluate(
                "(el) => document.activeElement === el"
            ),

            "tabindex": get_attr(
                element,
                "tabindex"
            )
        })

    # =========================================================
    # Other interactive elements
    # =========================================================

    selects = page.locator("select")
    textareas = page.locator("textarea")

    checkboxes = page.locator(
        'input[type="checkbox"]'
    )

    radio_buttons = page.locator(
        'input[type="radio"]'
    )

    # =========================================================
    # Keyboard focusable elements
    # =========================================================

    focusable = page.locator("""
        a[href],
        button,
        input,
        select,
        textarea,
        [tabindex]:not([tabindex="-1"])
    """)

    focusable_data = []

    for i in range(focusable.count()):

        element = focusable.nth(i)

        focusable_data.append({

            "index": i,

            "tag": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "text": element.inner_text().strip()
            if element.evaluate(
                "(el) => ['A','BUTTON'].includes(el.tagName)"
            )
            else "",

            "tabindex": get_attr(
                element,
                "tabindex"
            ),

            "visible": element.is_visible(),

            "enabled": element.is_enabled()
        })

    # =========================================================
    # Interactive elements with ARIA roles
    # =========================================================

    aria_interactive = page.locator("""
        [role="button"],
        [role="link"],
        [role="checkbox"],
        [role="radio"],
        [role="tab"],
        [role="menuitem"],
        [role="option"],
        [role="switch"],
        [role="combobox"],
        [role="slider"],
        [role="dialog"]
    """)

    aria_data = []

    for i in range(aria_interactive.count()):

        element = aria_interactive.nth(i)

        aria_data.append({

            "index": i,

            "tag": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "role": get_attr(
                element,
                "role"
            ),

            "text": element.inner_text().strip(),

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

            "visible": element.is_visible(),

            "tabindex": get_attr(
                element,
                "tabindex"
            )
        })

    # =========================================================
    # Final result
    # =========================================================

    return {

        "buttons": {
            "count": len(button_data),
            "items": button_data
        },

        "links": {
            "count": len(link_data),
            "items": link_data
        },

        "inputs": {
            "count": len(input_data),
            "items": input_data
        },

        "controls": {
            "selects": selects.count(),
            "textareas": textareas.count(),
            "checkboxes": checkboxes.count(),
            "radio_buttons": radio_buttons.count()
        },

        "keyboard_navigation": {
            "focusable_count": focusable.count(),
            "elements": focusable_data
        },

        "aria_interactive": {
            "count": aria_interactive.count(),
            "elements": aria_data
        },

        "total_interactive_elements": (
            buttons.count()
            + links.count()
            + inputs.count()
            + aria_interactive.count()
        )
    }