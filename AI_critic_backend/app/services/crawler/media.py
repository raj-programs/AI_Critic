def collect_media(page):

    # =========================================================

    # Helper

    # =========================================================

    def get_attr(element, name):

        return element.get_attribute(name)

    def get_dimensions(element):

        return element.evaluate("""

            (el) => {

                const rect = el.getBoundingClientRect();

                return {

                    rendered_width: rect.width,

                    rendered_height: rect.height,

                    natural_width: el.naturalWidth ?? null,

                    natural_height: el.naturalHeight ?? null

                };

            }

        """)

    # =========================================================

    # Images

    # =========================================================

    images = page.locator("img")

    image_data = []

    for i in range(images.count()):

        image = images.nth(i)

        dimensions = get_dimensions(image)

        rendered_width = dimensions["rendered_width"]

        rendered_height = dimensions["rendered_height"]

        if rendered_height > 0:

            rendered_aspect_ratio = (

                rendered_width / rendered_height

            )

        else:

            rendered_aspect_ratio = None

        image_data.append({

            "index": i,

            "src": get_attr(

                image,

                "src"

            ),

            "srcset": get_attr(

                image,

                "srcset"

            ),

            "sizes": get_attr(

                image,

                "sizes"

            ),

            "width_attribute": get_attr(

                image,

                "width"

            ),

            "height_attribute": get_attr(

                image,

                "height"

            ),

            "rendered_width": rendered_width,

            "rendered_height": rendered_height,

            "natural_width": dimensions[

                "natural_width"

            ],

            "natural_height": dimensions[

                "natural_height"

            ],

            "rendered_aspect_ratio":

                rendered_aspect_ratio,

            "loading": get_attr(

                image,

                "loading"

            ),

            "decoding": get_attr(

                image,

                "decoding"

            ),

            "visible": image.is_visible(),

            "loaded": image.evaluate(

                "(el) => el.complete && el.naturalWidth > 0"

            ),

            "broken": image.evaluate(

                "(el) => el.complete && el.naturalWidth === 0"

            )

        })

    # =========================================================

    # Videos

    # =========================================================

    videos = page.locator("video")

    video_data = []

    for i in range(videos.count()):

        video = videos.nth(i)

        dimensions = get_dimensions(video)

        video_data.append({

            "index": i,

            "src": get_attr(

                video,

                "src"

            ),

            "poster": get_attr(

                video,

                "poster"

            ),

            "width_attribute": get_attr(

                video,

                "width"

            ),

            "height_attribute": get_attr(

                video,

                "height"

            ),

            "rendered_width":

                dimensions["rendered_width"],

            "rendered_height":

                dimensions["rendered_height"],

            "controls": get_attr(video, "controls") is not None,

            "autoplay": get_attr(video, "autoplay") is not None,

            "muted": get_attr(video, "muted") is not None,

            "loop": get_attr(video, "loop") is not None,

            "playsinline": get_attr(video, "playsinline") is not None,

            "preload": get_attr(

                video,

                "preload"

            ),

            "visible": video.is_visible(),

            "ready_state": video.evaluate(

                "(el) => el.readyState"

            )

        })

    # =========================================================

    # Audio

    # =========================================================

    audio = page.locator("audio")

    audio_data = []

    for i in range(audio.count()):

        element = audio.nth(i)

        audio_data.append({

            "index": i,

            "src": get_attr(

                element,

                "src"

            ),

            "controls": get_attr(element, "controls") is not None,

            "autoplay": get_attr(element, "autoplay") is not None,

            "muted": get_attr(element, "muted") is not None,

            "loop": get_attr(element, "loop") is not None,

            "preload": get_attr(

                element,

                "preload"

            ),

            "visible": element.is_visible(),

            "ready_state": element.evaluate(

                "(el) => el.readyState"

            )

        })

    # =========================================================

    # SVG

    # =========================================================

    svgs = page.locator("svg")

    svg_data = []

    for i in range(svgs.count()):

        svg = svgs.nth(i)

        dimensions = get_dimensions(svg)

        svg_data.append({

            "index": i,

            "viewBox": get_attr(

                svg,

                "viewBox"

            ),

            "width_attribute": get_attr(

                svg,

                "width"

            ),

            "height_attribute": get_attr(

                svg,

                "height"

            ),

            "rendered_width":

                dimensions["rendered_width"],

            "rendered_height":

                dimensions["rendered_height"],

            "visible": svg.is_visible()

        })

    # =========================================================

    # Canvas

    # =========================================================

    canvas = page.locator("canvas")

    canvas_data = []

    for i in range(canvas.count()):

        element = canvas.nth(i)

        dimensions = get_dimensions(element)

        canvas_data.append({

            "index": i,

            "width_attribute": get_attr(

                element,

                "width"

            ),

            "height_attribute": get_attr(

                element,

                "height"

            ),

            "rendered_width":

                dimensions["rendered_width"],

            "rendered_height":

                dimensions["rendered_height"],

            "visible": element.is_visible()

        })

    # =========================================================

    # Iframes

    # =========================================================

    iframes = page.locator("iframe")

    iframe_data = []

    for i in range(iframes.count()):

        iframe = iframes.nth(i)

        dimensions = get_dimensions(iframe)

        iframe_data.append({

            "index": i,

            "src": get_attr(

                iframe,

                "src"

            ),

            "title": get_attr(

                iframe,

                "title"

            ),

            "name": get_attr(

                iframe,

                "name"

            ),

            "width_attribute": get_attr(

                iframe,

                "width"

            ),

            "height_attribute": get_attr(

                iframe,

                "height"

            ),

            "rendered_width":

                dimensions["rendered_width"],

            "rendered_height":

                dimensions["rendered_height"],

            "loading": get_attr(

                iframe,

                "loading"

            ),

            "allow": get_attr(

                iframe,

                "allow"

            ),

            "visible": iframe.is_visible()

        })

    # =========================================================

    # Media statistics

    # =========================================================

    statistics = {

        "image_count": images.count(),

        "loaded_images": page.locator(

            "img"

        ).evaluate_all("""

            elements =>

                elements.filter(

                    img => img.complete &&

                           img.naturalWidth > 0

                ).length

        """),

        "broken_images": page.locator(

            "img"

        ).evaluate_all("""

            elements =>

                elements.filter(

                    img => img.complete &&

                           img.naturalWidth === 0

                ).length

        """),

        "video_count": videos.count(),

        "audio_count": audio.count(),

        "svg_count": svgs.count(),

        "canvas_count": canvas.count(),

        "iframe_count": iframes.count()

    }

    # =========================================================

    # Final result

    # =========================================================

    return {

        "images": {

            "count": len(image_data),

            "items": image_data

        },

        "videos": {

            "count": len(video_data),

            "items": video_data

        },

        "audio": {

            "count": len(audio_data),

            "items": audio_data

        },

        "svg": {

            "count": len(svg_data),

            "items": svg_data

        },

        "canvas": {

            "count": len(canvas_data),

            "items": canvas_data

        },

        "iframes": {

            "count": len(iframe_data),

            "items": iframe_data

        },

        "statistics": statistics

    }
