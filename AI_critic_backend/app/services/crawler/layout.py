def collect_layout(page):

    # =========================================================
    # Helper
    # =========================================================

    def get_attr(element, name):
        return element.get_attribute(name)

    def get_box(element):
        return element.evaluate("""
            (el) => {
                const rect = el.getBoundingClientRect();

                return {
                    x: rect.x,
                    y: rect.y,
                    top: rect.top,
                    right: rect.right,
                    bottom: rect.bottom,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                };
            }
        """)

    # =========================================================
    # Viewport and document dimensions
    # =========================================================

    viewport = page.evaluate("""
        () => ({
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,

            document_width:
                document.documentElement.scrollWidth,

            document_height:
                document.documentElement.scrollHeight,

            body_width:
                document.body
                    ? document.body.scrollWidth
                    : null,

            body_height:
                document.body
                    ? document.body.scrollHeight
                    : null,

            device_pixel_ratio:
                window.devicePixelRatio
        })
    """)

    viewport_width = viewport["viewport_width"]
    viewport_height = viewport["viewport_height"]

    document_width = viewport["document_width"]
    document_height = viewport["document_height"]

    # =========================================================
    # Overflow
    # =========================================================

    overflow = {
        "horizontal": document_width > viewport_width,
        "vertical": document_height > viewport_height,

        "horizontal_overflow":
            max(
                0,
                document_width - viewport_width
            ),

        "vertical_overflow":
            max(
                0,
                document_height - viewport_height
            )
    }

    # =========================================================
    # Elements to inspect
    #
    # We don't collect every div because that can create a
    # massive evidence object.
    # =========================================================

    layout_elements = page.locator("""
        header,
        nav,
        main,
        section,
        article,
        aside,
        footer,

        h1,
        h2,
        h3,
        h4,
        h5,
        h6,

        p,

        a,
        button,

        input,
        select,
        textarea,

        img,
        video,
        audio,

        svg,
        canvas,

        iframe,

        [role="button"],
        [role="link"],
        [role="dialog"],
        [role="alert"],
        [role="tab"],
        [role="menuitem"]
    """)

    element_data = []

    # =========================================================
    # Collect element geometry
    # =========================================================

    for i in range(layout_elements.count()):

        element = layout_elements.nth(i)

        tag = element.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

        box = get_box(element)

        # -----------------------------------------------------
        # Visibility
        # -----------------------------------------------------

        visible = element.is_visible()

        # -----------------------------------------------------
        # Position relative to viewport
        # -----------------------------------------------------

        completely_inside_viewport = (
            box["left"] >= 0
            and box["top"] >= 0
            and box["right"] <= viewport_width
            and box["bottom"] <= viewport_height
        )

        outside_left = box["left"] < 0

        outside_right = box["right"] > viewport_width

        outside_top = box["top"] < 0

        outside_bottom = box["bottom"] > viewport_height

        # -----------------------------------------------------
        # Element-level overflow
        # -----------------------------------------------------

        horizontal_overflow = (
            box["width"] > viewport_width
        )

        vertical_overflow = (
            box["height"] > viewport_height
        )

        # -----------------------------------------------------
        # Text
        # -----------------------------------------------------

        text = ""

        if tag in [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "a",
            "button"
        ]:

            text = element.inner_text().strip()

            # Avoid enormous text values
            text = text[:300]

        # -----------------------------------------------------
        # Element data
        # -----------------------------------------------------

        element_data.append({

            "index": i,

            "tag": tag,

            "id": get_attr(
                element,
                "id"
            ),

            "class": get_attr(
                element,
                "class"
            ),

            "role": get_attr(
                element,
                "role"
            ),

            "text": text,

            "visible": visible,

            # Geometry
            "box": box,

            # Viewport relationship
            "inside_viewport":
                completely_inside_viewport,

            "outside_left":
                outside_left,

            "outside_right":
                outside_right,

            "outside_top":
                outside_top,

            "outside_bottom":
                outside_bottom,

            # Overflow
            "horizontal_overflow":
                horizontal_overflow,

            "vertical_overflow":
                vertical_overflow
        })

    # =========================================================
    # Important layout containers
    # =========================================================

    containers = page.locator("""
        header,
        nav,
        main,
        section,
        article,
        aside,
        footer
    """)

    container_data = []

    for i in range(containers.count()):

        container = containers.nth(i)

        box = get_box(container)

        container_data.append({

            "index": i,

            "tag": container.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "id": get_attr(
                container,
                "id"
            ),

            "class": get_attr(
                container,
                "class"
            ),

            "role": get_attr(
                container,
                "role"
            ),

            "box": box,

            "visible": container.is_visible()
        })

    # =========================================================
    # Interactive element dimensions
    #
    # Useful later for touch target / click target rules.
    # =========================================================

    interactive_elements = page.locator("""
        a[href],
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
        [role="menuitem"]
    """)

    interactive_data = []

    for i in range(interactive_elements.count()):

        element = interactive_elements.nth(i)

        box = get_box(element)

        tag = element.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

        text = ""

        if tag in ["a", "button"]:
            text = element.inner_text().strip()[:200]

        interactive_data.append({

            "index": i,

            "tag": tag,

            "role": get_attr(
                element,
                "role"
            ),

            "text": text,

            "box": box,

            "width": box["width"],

            "height": box["height"],

            "visible": element.is_visible(),

            "disabled": (
                element.is_disabled()
                if tag in [
                    "button",
                    "input",
                    "select",
                    "textarea"
                ]
                else False
            )
        })

    # =========================================================
    # Fixed and sticky elements
    # =========================================================

    positioned_elements = page.locator("""
        header,
        nav,
        button,
        a,
        [role="button"],
        [role="dialog"],
        [style*="position"]
    """)

    positioned_data = []

    for i in range(positioned_elements.count()):

        element = positioned_elements.nth(i)

        position = element.evaluate("""
            (el) => {
                const style = window.getComputedStyle(el);

                return {
                    position: style.position,
                    z_index: style.zIndex
                };
            }
        """)

        if position["position"] in [
            "fixed",
            "sticky",
            "absolute"
        ]:

            box = get_box(element)

            positioned_data.append({

                "index": i,

                "tag": element.evaluate(
                    "(el) => el.tagName.toLowerCase()"
                ),

                "id": get_attr(
                    element,
                    "id"
                ),

                "class": get_attr(
                    element,
                    "class"
                ),

                "position":
                    position["position"],

                "z_index":
                    position["z_index"],

                "box":
                    box,

                "visible":
                    element.is_visible()
            })

    # =========================================================
    # Layout statistics
    # =========================================================

    statistics = {

        "total_layout_elements":
            layout_elements.count(),

        "visible_layout_elements":
            sum(
                1
                for element in element_data
                if element["visible"]
            ),

        "elements_outside_left":
            sum(
                1
                for element in element_data
                if element["outside_left"]
            ),

        "elements_outside_right":
            sum(
                1
                for element in element_data
                if element["outside_right"]
            ),

        "elements_outside_top":
            sum(
                1
                for element in element_data
                if element["outside_top"]
            ),

        "elements_outside_bottom":
            sum(
                1
                for element in element_data
                if element["outside_bottom"]
            ),

        "interactive_element_count":
            interactive_elements.count(),

        "positioned_element_count":
            len(positioned_data),

        "horizontal_overflow":
            overflow["horizontal"],

        "vertical_overflow":
            overflow["vertical"]
    }

    # =========================================================
    # Final result
    # =========================================================

    return {

        "viewport": viewport,

        "overflow": overflow,

        "elements": {
            "count": len(element_data),
            "items": element_data
        },

        "containers": {
            "count": len(container_data),
            "items": container_data
        },

        "interactive": {
            "count": len(interactive_data),
            "items": interactive_data
        },

        "positioned": {
            "count": len(positioned_data),
            "items": positioned_data
        },

        "statistics": statistics
    }