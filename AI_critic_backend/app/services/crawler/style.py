def collect_styles(page):

    # =========================================================
    # Helper
    # =========================================================

    def get_attr(element, name):
        return element.get_attribute(name)

    def get_computed_styles(element):
        return element.evaluate("""
            (el) => {

                const style = window.getComputedStyle(el);

                return {

                    // -------------------------------------------------
                    // Typography
                    // -------------------------------------------------

                    font_family: style.fontFamily,
                    font_size: style.fontSize,
                    font_weight: style.fontWeight,
                    font_style: style.fontStyle,
                    line_height: style.lineHeight,
                    letter_spacing: style.letterSpacing,
                    text_align: style.textAlign,
                    text_transform: style.textTransform,
                    text_decoration: style.textDecoration,

                    // -------------------------------------------------
                    // Colors
                    // -------------------------------------------------

                    color: style.color,
                    background_color: style.backgroundColor,

                    // -------------------------------------------------
                    // Display / visibility
                    // -------------------------------------------------

                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,

                    // -------------------------------------------------
                    // Position
                    // -------------------------------------------------

                    position: style.position,
                    z_index: style.zIndex,

                    // -------------------------------------------------
                    // Box model
                    // -------------------------------------------------

                    width: style.width,
                    height: style.height,

                    margin_top: style.marginTop,
                    margin_right: style.marginRight,
                    margin_bottom: style.marginBottom,
                    margin_left: style.marginLeft,

                    padding_top: style.paddingTop,
                    padding_right: style.paddingRight,
                    padding_bottom: style.paddingBottom,
                    padding_left: style.paddingLeft,

                    // -------------------------------------------------
                    // Border
                    // -------------------------------------------------

                    border_top: style.borderTop,
                    border_right: style.borderRight,
                    border_bottom: style.borderBottom,
                    border_left: style.borderLeft,

                    border_radius: style.borderRadius,

                    // -------------------------------------------------
                    // Overflow
                    // -------------------------------------------------

                    overflow: style.overflow,
                    overflow_x: style.overflowX,
                    overflow_y: style.overflowY,

                    // -------------------------------------------------
                    // Flexbox
                    // -------------------------------------------------

                    display_type: style.display,

                    flex_direction: style.flexDirection,
                    flex_wrap: style.flexWrap,
                    justify_content: style.justifyContent,
                    align_items: style.alignItems,
                    align_content: style.alignContent,
                    gap: style.gap,

                    // -------------------------------------------------
                    // Grid
                    // -------------------------------------------------

                    grid_template_columns:
                        style.gridTemplateColumns,

                    grid_template_rows:
                        style.gridTemplateRows,

                    column_gap:
                        style.columnGap,

                    row_gap:
                        style.rowGap,

                    // -------------------------------------------------
                    // Visual effects
                    // -------------------------------------------------

                    box_shadow: style.boxShadow,

                    transform: style.transform,

                    filter: style.filter,

                    // -------------------------------------------------
                    // Pointer / interaction
                    // -------------------------------------------------

                    cursor: style.cursor,

                    // -------------------------------------------------
                    // Clipping
                    // -------------------------------------------------

                    clip: style.clip,
                    clip_path: style.clipPath
                };
            }
        """)

    # =========================================================
    # Elements whose styles are important for HCI analysis
    #
    # We intentionally don't inspect every div on the page.
    # =========================================================

    styled_elements = page.locator("""
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

        dialog,

        [role="button"],
        [role="link"],
        [role="tab"],
        [role="menuitem"],
        [role="dialog"]
    """)

    element_data = []

    # =========================================================
    # Collect computed styles
    # =========================================================

    for i in range(styled_elements.count()):

        element = styled_elements.nth(i)

        tag = element.evaluate(
            "(el) => el.tagName.toLowerCase()"
        )

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

            # Prevent huge text values
            text = text[:300]

        styles = get_computed_styles(element)

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

            "visible": element.is_visible(),

            "styles": styles
        })

    # =========================================================
    # Typography-specific elements
    #
    # Useful for typography consistency analysis.
    # =========================================================

    typography_elements = page.locator("""
        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        p,
        a,
        button,
        label
    """)

    typography_data = []

    for i in range(typography_elements.count()):

        element = typography_elements.nth(i)

        styles = get_computed_styles(element)

        typography_data.append({

            "index": i,

            "tag": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "text": element.inner_text().strip()[:300],

            "font_family":
                styles["font_family"],

            "font_size":
                styles["font_size"],

            "font_weight":
                styles["font_weight"],

            "font_style":
                styles["font_style"],

            "line_height":
                styles["line_height"],

            "letter_spacing":
                styles["letter_spacing"],

            "text_align":
                styles["text_align"],

            "text_transform":
                styles["text_transform"],

            "text_decoration":
                styles["text_decoration"],

            "color":
                styles["color"],

            "visible":
                element.is_visible()
        })

    # =========================================================
    # Interactive styling
    #
    # Useful later for consistency and affordance rules.
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

        styles = get_computed_styles(element)

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

            "cursor":
                styles["cursor"],

            "color":
                styles["color"],

            "background_color":
                styles["background_color"],

            "font_size":
                styles["font_size"],

            "font_weight":
                styles["font_weight"],

            "text_decoration":
                styles["text_decoration"],

            "border":
                styles["border_top"],

            "border_radius":
                styles["border_radius"],

            "opacity":
                styles["opacity"],

            "visibility":
                styles["visibility"],

            "display":
                styles["display"],

            "visible":
                element.is_visible()
        })

    # =========================================================
    # Color information
    #
    # Collect colors actually used by important elements.
    # =========================================================

    color_elements = page.locator("""
        body,
        header,
        nav,
        main,
        section,
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
        textarea
    """)

    color_data = []

    for i in range(color_elements.count()):

        element = color_elements.nth(i)

        styles = get_computed_styles(element)

        color_data.append({

            "index": i,

            "tag": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "color":
                styles["color"],

            "background_color":
                styles["background_color"],

            "visible":
                element.is_visible()
        })

    # =========================================================
    # Style statistics
    # =========================================================

    statistics = {

        "styled_element_count":
            styled_elements.count(),

        "typography_element_count":
            typography_elements.count(),

        "interactive_element_count":
            interactive_elements.count(),

        "color_element_count":
            color_elements.count(),

        "visible_styled_elements":
            sum(
                1
                for element in element_data
                if element["visible"]
            )
    }

    # =========================================================
    # Final result
    # =========================================================

    return {

        "elements": {
            "count": len(element_data),
            "items": element_data
        },

        "typography": {
            "count": len(typography_data),
            "items": typography_data
        },

        "interactive": {
            "count": len(interactive_data),
            "items": interactive_data
        },

        "colors": {
            "count": len(color_data),
            "items": color_data
        },

        "statistics": statistics
    }