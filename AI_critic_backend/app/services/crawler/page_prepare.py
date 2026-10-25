def prepare_page_for_capture(page):
    # Wait for the initial page layout to settle.
    page.wait_for_timeout(1000)

    # Trigger lazy-loaded content and scroll-based animations.
    page.evaluate("""
        async () => {
            const delay = ms =>
                new Promise(resolve => setTimeout(resolve, ms));

            const step = Math.max(
                300,
                Math.floor(window.innerHeight * 0.7)
            );

            const documentHeight = Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            );
            const maxHeight = Math.min(
                documentHeight,
                step * 30
            );

            for (let y = 0; y < maxHeight; y += step) {
                window.scrollTo(0, y);
                await delay(150);
            }

            window.scrollTo(0, 0);
            await delay(1000);
        }
    """)

    # Allow fonts to finish loading.
    page.evaluate("""
        async () => {
            if (document.fonts) {
                await document.fonts.ready;
            }
        }
    """)
