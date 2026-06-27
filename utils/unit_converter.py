def convert_to_base(quantity, selected_unit, base_unit):

    quantity = float(quantity)

    if base_unit == "kg":
        if selected_unit == "g":
            return quantity / 1000
        return quantity

    if base_unit == "litre":
        if selected_unit == "ml":
            return quantity / 1000
        return quantity

    return quantity