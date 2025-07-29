import bpy


class Drivers:
    def __init__(self):
        pass

    def create_shape_key_driver(self, obj, shapename, expression="", driver_names=[]):
        # Driver are the hero shapes driving the combo, shapename is the combo
        for driver in driver_names:
            new_driver = obj.data.shape_keys.key_blocks[shapename].driver_add(
                "value")
            new_driver.driver.expression = expression

            driver_variable = new_driver.driver.variables.new()

            driver_variable.name = driver
            driver_variable.type = 'SINGLE_PROP'
            driver_variable.targets[0].id_type = "KEY"
            driver_variable.targets[0].id = obj.data.shape_keys
            driver_variable.targets[0].data_path = 'key_blocks["' + driver + '"].value'

            # Forces update dependencies
            new_driver.driver.expression += " "
            new_driver.driver.expression = new_driver.driver.expression[:-1]

    def create_inbetween_driver(self, obj, shapename, driver_name, expression=""):
        # Driver are the hero shapes driving the combo, shapename is the combo

        new_driver = obj.data.shape_keys.key_blocks[shapename].driver_add(
            "value")
        new_driver.driver.expression = expression

        driver_variable = new_driver.driver.variables.new()

        driver_variable.name = driver_name
        driver_variable.type = 'SINGLE_PROP'
        driver_variable.targets[0].id_type = "KEY"
        driver_variable.targets[0].id = obj.data.shape_keys
        driver_variable.targets[0].data_path = 'key_blocks["' + driver_name + '"].value'

        # Forces update dependencies
        new_driver.driver.expression += " "
        new_driver.driver.expression = new_driver.driver.expression[:-1]

    def average_expression(self, values):
        # Needs to be passed the driver names. sin(pi/2*A)*sin(pi/2*B)
        parts = []
        for value in values:
            parts.append(f"(sin(pi/2*{value}))")
        expression = " * ".join(parts)
        return f"({expression})"

    def average_expression_B(self, values):
        # Needs to be passed the driver names. A*B if A>0 and B>0 else 0
        expression = " * ".join(values)
        conditional = []
        for value in values:
            conditional.append(f"{value}>0")

        conditionals = " and ".join(conditional)
        return f"({expression} if {conditionals} else 0)"

    def average_expression_C(self, values):
        # Needs to be passed the driver names (A*B)**0.5
        expression = " * ".join(values)
        return f"(({expression}) ** {1 / len(values)})"

    def average_expression_N(self, values):
        # Negative shape expression. Needs to be passed the driver names. A*B if A>0 and B>0 else 0
        expression = " * ".join(values)
        conditional = []
        for value in values:
            conditional.append(f"{value}!=0")

        conditionals = " and ".join(conditional)
        return f"(abs({expression}) if {conditionals} else 0)"

    def disconnect_shape_key_drivers(self, shape_key_names, object_name):
        # Get the object with the matching name
        obj = bpy.data.objects.get(object_name)

        # Iterate through the shape keys
        for shape_key in obj.data.shape_keys.key_blocks:
            # Check if the shape key's name is in the list
            if shape_key.name in shape_key_names:
                # Disconnect the shape key's driver
                shape_key.driver_remove('value')

    def inbetween_expression(self, driver_shape, shape_keys):
        expressions = []
        # Sort the shape keys by the values at the end of their name
        shape_keys.sort(key=lambda x: int(x.split("_")[1]))

        min_for_100 = int(shape_keys[-2].split("_")[1])
        print(f"inbetween_expression function - first shape is {shape_keys[0]}")
        # Iterate over the shape keys
        for i in range(len(shape_keys)):
            # Extract the number at the end of the shape key name
            #    number = int(shape_keys[i][-2:])
            number = int(shape_keys[i].split("_")[1])

            # Calculate the max and min values for this shape key

            max_val = number / 100
            print(f"inbetween_expression function - i is {i}, number is {number}, max is {max_val}")

            if i == 0:
                # for the first number in the list, min value will be 0
                min_val = 0
            if len(shape_keys) > 1:
                if i == len(shape_keys) - 1:
                    # for the last value in the list, min value will be second to last
                    min_val = min_for_100 / 100
                elif i == 0:
                    min_val = 0
                else:
                    min_val = int(shape_keys[i - 1].split("_")[1]) / 100
                    # max_val = (number + 25) / 100
            # Generate the expression for this shape key
            expressions.append(f"max(min(({driver_shape}-{min_val})/({max_val}-{min_val}), 1.0), 0.0)")
        # Return the list of expressions
        return expressions

    def inbetweens_smaller(self, s: str, strings: list) -> list:
        # Extract the numeral from the string passed to the function
        numeral = int(s.split("_")[1])

        # Initialize an empty result list
        result = []

        # Iterate through the list of strings
        for string in strings:

            if "_" in string:
                # Extract the numeral from the current string
                current_numeral = int(string.split("_")[1])

                # If the current numeral is greater than the numeral from the single string passed to the function, add it to the result list
                if current_numeral > numeral:
                    result.append(string)

        return result

    def disconnect_active_shape_key_driver(self):
        # Get the object and actuve shapekey
        obj = obj = bpy.context.active_object
        active_shape_key = obj.active_shape_key

        # Remove the driver
        active_shape_key.driver_remove('value')
        print(f"disconnect_active_shape_key_driver function - Removed the driver on {active_shape_key.name}")

    def refresh_drivers(self):
        # Get the active object
        obj = bpy.context.active_object

        # Check if the active object has shape keys
        if obj.data.shape_keys:
            # Get the shape key block
            shape_keys = obj.data.shape_keys.key_blocks

            # Iterate over the shape key names in the list
            for name in shape_keys:
                bpy.context.evaluated_depsgraph_get()


registry = [
]