def collect_structure(page):

    # ---------------------------------------------------------
    # Build an HCI-oriented DOM tree
    # ---------------------------------------------------------

    dom_tree = page.locator("body").evaluate("""
    (body) => {
        const IMPORTANT_TAGS = new Set([
            "header",
            "nav",
            "main",
            "section",
            "article",
            "aside",
            "footer",

            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",

            "p",
            "a",
            "button",

            "form",
            "input",
            "select",
            "option",
            "textarea",
            "label",

            "img",
            "video",
            "audio",

            "dialog"
        ]);

        const TEXT_TAGS = new Set([
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "a",
            "button",
            "label",
            "option"
        ]);

        function cleanText(text) {

            if (!text) {
                return "";
            }

            return text
                .replace(/\\s+/g, " ")
                .trim()
                .slice(0, 300);
        }

        function getAttributes(element, tag) {

            const attributes = {};

            // ID
            if (element.id) {
                attributes.id = element.id;
            }

            // Classes
            if (
                typeof element.className === "string" &&
                element.className.trim()
            ) {
                attributes.class = element.className
                    .trim()
                    .slice(0, 300);
            }

            // Accessibility attributes
            const accessibilityAttributes = [
                "role",
                "aria-label",
                "aria-labelledby",
                "aria-describedby",
                "aria-hidden",
                "tabindex"
            ];

            for (const attr of accessibilityAttributes) {

                const value = element.getAttribute(attr);

                if (value !== null) {
                    attributes[attr] = value;
                }
            }

            // Links
            if (tag === "a") {

                const href = element.getAttribute("href");

                if (href !== null) {
                    attributes.href = href;
                }
            }

            // Images
            if (tag === "img") {

                const alt = element.getAttribute("alt");

                attributes.alt = alt !== null ? alt : null;

                const src = element.getAttribute("src");

                if (src !== null) {
                    attributes.src = src;
                }
            }

            // Forms / inputs
            if (
                tag === "input" ||
                tag === "select" ||
                tag === "textarea"
            ) {

                const type = element.getAttribute("type");

                if (type !== null) {
                    attributes.type = type;
                }

                const name = element.getAttribute("name");

                if (name !== null) {
                    attributes.name = name;
                }

                const placeholder =
                    element.getAttribute("placeholder");

                if (placeholder !== null) {
                    attributes.placeholder = placeholder;
                }

                attributes.required =
                    element.hasAttribute("required");
            }

            // Disabled state
            if (
                tag === "button" ||
                tag === "input" ||
                tag === "select" ||
                tag === "textarea"
            ) {
                attributes.disabled =
                    element.hasAttribute("disabled");
            }

            return attributes;
        }

        function buildTree(element) {

            const tag = element.tagName.toLowerCase();

            // Ignore irrelevant elements
            if (!IMPORTANT_TAGS.has(tag)) {

                const children = [];

                for (const child of element.children) {

                    const result = buildTree(child);

                    if (result !== null) {
                        children.push(result);
                    }
                }

                // If this element itself is irrelevant,
                // return its relevant descendants.
                if (children.length === 1) {
                    return children[0];
                }

                if (children.length > 1) {
                    return {
                        tag: "group",
                        children: children
                    };
                }

                return null;
            }

            const node = {
                tag: tag
            };

            // Text
            if (TEXT_TAGS.has(tag)) {

                const text = cleanText(
                    element.innerText
                );

                if (text) {
                    node.text = text;
                }
            }

            // Attributes
            const attributes =
                getAttributes(element, tag);

            if (Object.keys(attributes).length > 0) {
                node.attributes = attributes;
            }

            // Visibility
            const style =
                window.getComputedStyle(element);

            node.visible =
                style.display !== "none" &&
                style.visibility !== "hidden" &&
                element.getBoundingClientRect().width > 0 &&
                element.getBoundingClientRect().height > 0;

            // Children
            const children = [];

            for (const child of element.children) {

                const result = buildTree(child);

                if (result !== null) {
                    children.push(result);
                }
            }

            if (children.length > 0) {
                node.children = children;
            }

            return node;
        }

        return buildTree(body);
    }
    """)

    # ---------------------------------------------------------
    # Heading information
    # ---------------------------------------------------------

    headings = page.locator(
        "h1, h2, h3, h4, h5, h6"
    )

    heading_data = []

    for i in range(headings.count()):

        element = headings.nth(i)

        heading_data.append({
            "level": element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),
            "text": element.inner_text().strip(),
            "visible": element.is_visible()
        })

    # ---------------------------------------------------------
    # Heading counts
    # ---------------------------------------------------------

    heading_counts = {
        "h1": page.locator("h1").count(),
        "h2": page.locator("h2").count(),
        "h3": page.locator("h3").count(),
        "h4": page.locator("h4").count(),
        "h5": page.locator("h5").count(),
        "h6": page.locator("h6").count()
    }

    # ---------------------------------------------------------
    # Semantic landmarks
    # ---------------------------------------------------------

    landmarks = {
        "header": page.locator("header").count(),
        "nav": page.locator("nav").count(),
        "main": page.locator("main").count(),
        "section": page.locator("section").count(),
        "article": page.locator("article").count(),
        "aside": page.locator("aside").count(),
        "footer": page.locator("footer").count()
    }

    # ---------------------------------------------------------
    # General structural statistics
    # ---------------------------------------------------------

    statistics = {
        "total_elements": page.locator("*").count(),

        "links": page.locator("a").count(),

        "buttons": page.locator("button").count(),

        "forms": page.locator("form").count(),

        "inputs": page.locator(
            "input, select, textarea"
        ).count(),

        "images": page.locator("img").count(),

        "videos": page.locator("video").count(),

        "iframes": page.locator("iframe").count()
    }

    # ---------------------------------------------------------
    # Final structure evidence
    # ---------------------------------------------------------

    return {
        "dom_tree": dom_tree,

        "headings": {
            "items": heading_data,
            "counts": heading_counts
        },

        "landmarks": landmarks,

        "statistics": statistics
    }