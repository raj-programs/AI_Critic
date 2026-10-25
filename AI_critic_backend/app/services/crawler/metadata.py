def collect_metadata(page, url):

    metadata = page.evaluate("""
        () => {

            const getMeta = (selector, attribute = "content") => {
                const element = document.querySelector(selector);

                if (!element) {
                    return null;
                }

                return element.getAttribute(attribute);
            };

            return {
                "title": document.title || null,

                "language":
                    document.documentElement.lang || null,

                "description":
                    getMeta('meta[name="description"]'),

                "canonical":
                    getMeta('link[rel="canonical"]', "href"),

                "viewport":
                    getMeta('meta[name="viewport"]'),

                "robots":
                    getMeta('meta[name="robots"]'),

                "author":
                    getMeta('meta[name="author"]'),

                "keywords":
                    getMeta('meta[name="keywords"]'),

                "charset":
                    document.characterSet || null
            };
        }
    """)

    return {
        "url": page.url,
        **metadata
    }