def collect_forms(page):

    # =========================================================
    # Helper
    # =========================================================

    def get_attr(element, name):
        return element.get_attribute(name)

    # =========================================================
    # Collect all forms
    # =========================================================

    forms = page.locator("form")

    form_data = []

    for i in range(forms.count()):

        form = forms.nth(i)

        # -----------------------------------------------------
        # Form information
        # -----------------------------------------------------

        form_info = {
            "index": i,

            "id": get_attr(
                form,
                "id"
            ),

            "name": get_attr(
                form,
                "name"
            ),

            "action": get_attr(
                form,
                "action"
            ),

            "method": get_attr(
                form,
                "method"
            ),

            "target": get_attr(
                form,
                "target"
            ),

            "autocomplete": get_attr(
                form,
                "autocomplete"
            ),

            "novalidate": form.has_attribute(
                "novalidate"
            ),

            "visible": form.is_visible()
        }

        # -----------------------------------------------------
        # Labels
        # -----------------------------------------------------

        labels = form.locator("label")

        label_data = []

        for j in range(labels.count()):

            label = labels.nth(j)

            label_data.append({

                "index": j,

                "text": label.inner_text().strip(),

                "for": get_attr(
                    label,
                    "for"
                ),

                "visible": label.is_visible()
            })

        labels_by_for = {
            label["for"]: label["text"]
            for label in label_data
            if label["for"] and label["text"]
        }

        # -----------------------------------------------------
        # Form controls
        # -----------------------------------------------------

        controls = form.locator(
            "input, select, textarea"
        )

        control_data = []

        for j in range(controls.count()):

            control = controls.nth(j)

            tag = control.evaluate(
                "(el) => el.tagName.toLowerCase()"
            )

            control_id = get_attr(control, "id")
            label_text = labels_by_for.get(control_id)
            if not label_text:
                wrapping_label = control.locator("xpath=ancestor::label[1]")
                if wrapping_label.count():
                    label_text = wrapping_label.inner_text().strip()
            control_info = {

                "index": j,

                "tag": tag,

                "type": get_attr(
                    control,
                    "type"
                ),

                "name": get_attr(
                    control,
                    "name"
                ),

                "id": control_id,

                "label": label_text,

                "value": get_attr(
                    control,
                    "value"
                ),

                "placeholder": get_attr(
                    control,
                    "placeholder"
                ),

                "autocomplete": get_attr(
                    control,
                    "autocomplete"
                ),

                "required": control.is_required(),

                "disabled": control.is_disabled(),

                "readonly": control.is_editable()
                is False,

                "visible": control.is_visible(),

                "aria_label": get_attr(
                    control,
                    "aria-label"
                ),

                "aria_labelledby": get_attr(
                    control,
                    "aria-labelledby"
                ),

                "aria_describedby": get_attr(
                    control,
                    "aria-describedby"
                ),

                "aria_invalid": get_attr(
                    control,
                    "aria-invalid"
                ),

                "role": get_attr(
                    control,
                    "role"
                ),

                "tabindex": get_attr(
                    control,
                    "tabindex"
                )
            }

            # -------------------------------------------------
            # Validation attributes
            # -------------------------------------------------

            validation = {

                "required": control.has_attribute(
                    "required"
                ),

                "min": get_attr(
                    control,
                    "min"
                ),

                "max": get_attr(
                    control,
                    "max"
                ),

                "minlength": get_attr(
                    control,
                    "minlength"
                ),

                "maxlength": get_attr(
                    control,
                    "maxlength"
                ),

                "pattern": get_attr(
                    control,
                    "pattern"
                ),

                "step": get_attr(
                    control,
                    "step"
                )
            }

            control_info["validation"] = validation

            # -------------------------------------------------
            # Input-specific information
            # -------------------------------------------------

            if tag == "input":

                control_info["checked"] = control.is_checked()

            # -------------------------------------------------
            # Select-specific information
            # -------------------------------------------------

            if tag == "select":

                options = control.locator("option")

                option_data = []

                for k in range(options.count()):

                    option = options.nth(k)

                    option_data.append({

                        "text": option.inner_text().strip(),

                        "value": get_attr(
                            option,
                            "value"
                        ),

                        "selected": option.is_checked()
                        if False
                        else get_attr(
                            option,
                            "selected"
                        ) is not None
                    })

                control_info["options"] = option_data

            # -------------------------------------------------
            # Textarea-specific information
            # -------------------------------------------------

            if tag == "textarea":

                control_info["rows"] = get_attr(
                    control,
                    "rows"
                )

                control_info["cols"] = get_attr(
                    control,
                    "cols"
                )

            control_data.append(control_info)

        # -----------------------------------------------------
        # Submit buttons
        # -----------------------------------------------------

        buttons = form.locator(
            'button, input[type="submit"], input[type="button"], input[type="reset"]'
        )

        button_data = []

        for j in range(buttons.count()):

            button = buttons.nth(j)

            button_tag = button.evaluate(
                "(el) => el.tagName.toLowerCase()"
            )

            button_data.append({

                "index": j,

                "tag": button_tag,

                "text": button.inner_text().strip()
                if button_tag == "button"
                else "",

                "value": get_attr(
                    button,
                    "value"
                ),

                "type": get_attr(
                    button,
                    "type"
                ),

                "name": get_attr(
                    button,
                    "name"
                ),

                "aria_label": get_attr(
                    button,
                    "aria-label"
                ),

                "role": get_attr(
                    button,
                    "role"
                ),

                "disabled": button.is_disabled(),

                "visible": button.is_visible()
            })

        # -----------------------------------------------------
        # Store form
        # -----------------------------------------------------

        form_info["labels"] = {
            "count": len(label_data),
            "items": label_data
        }

        form_info["controls"] = {
            "count": len(control_data),
            "items": control_data
        }

        form_info["buttons"] = {
            "count": len(button_data),
            "items": button_data
        }

        form_data.append(form_info)

    # =========================================================
    # Controls outside forms
    # =========================================================

    outside_form_controls = page.locator(
        "input:not(form input), "
        "select:not(form select), "
        "textarea:not(form textarea)"
    )

    outside_form_data = []
    all_labels = page.locator("label")
    labels_by_for = {}

    for label_index in range(all_labels.count()):
        label = all_labels.nth(label_index)
        control_id = get_attr(label, "for")
        label_text = label.inner_text().strip()
        if control_id and label_text:
            labels_by_for[control_id] = label_text

    for i in range(outside_form_controls.count()):

        control = outside_form_controls.nth(i)

        control_id = get_attr(control, "id")
        label_text = labels_by_for.get(control_id)
        if not label_text:
            wrapping_label = control.locator("xpath=ancestor::label[1]")
            if wrapping_label.count():
                label_text = wrapping_label.inner_text().strip()
        outside_form_data.append({

            "index": i,

            "tag": control.evaluate(
                "(el) => el.tagName.toLowerCase()"
            ),

            "type": get_attr(
                control,
                "type"
            ),

            "name": get_attr(
                control,
                "name"
            ),

            "id": control_id,

            "label": label_text,

            "placeholder": get_attr(
                control,
                "placeholder"
            ),

            "required": control.is_required(),

            "disabled": control.is_disabled(),

            "visible": control.is_visible(),

            "aria_label": get_attr(
                control,
                "aria-label"
            ),

            "aria_labelledby": get_attr(
                control,
                "aria-labelledby"
            )
        })

    # =========================================================
    # Overall form statistics
    # =========================================================

    statistics = {

        "form_count": forms.count(),

        "input_count": page.locator(
            "input"
        ).count(),

        "select_count": page.locator(
            "select"
        ).count(),

        "textarea_count": page.locator(
            "textarea"
        ).count(),

        "label_count": page.locator(
            "label"
        ).count(),

        "required_controls": page.locator(
            "input[required], "
            "select[required], "
            "textarea[required]"
        ).count(),

        "disabled_controls": page.locator(
            "input:disabled, "
            "select:disabled, "
            "textarea:disabled"
        ).count()
    }

    # =========================================================
    # Final result
    # =========================================================

    return {

        "forms": {
            "count": len(form_data),
            "items": form_data
        },

        "controls_outside_forms": {
            "count": len(outside_form_data),
            "items": outside_form_data
        },

        "statistics": statistics
    }
