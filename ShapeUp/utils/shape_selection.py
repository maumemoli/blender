import bpy


class ShapeSelection:
    def __init__(self):
        pass

    def get_active_shape_key_name(self):
        # Get the active object
        obj = bpy.context.active_object

        # Make sure the object has shape keys
        if not obj.data.shape_keys:
            print("This object does not have shape keys.")
            exit()

        # Get the active shape key
        active_shape_key = obj.active_shape_key

        # Print the name of the active shape key
        if active_shape_key:
            print(f"The Active shapekey is: {active_shape_key.name}")
            return active_shape_key.name
        else:
            print("No shape key is selected.")

    def shape_key_list_hero(self):
        # Get the active object
        obj = bpy.context.active_object

        # Make sure the object has shape keys
        if obj.data.shape_keys is None:
            return []

        # Return a list of shape key names
        return [key.name for key in obj.data.shape_keys.key_blocks if "_" not in key.name]

    def shape_key_list_all(self):
        # Returns a list of all the shape key names
        obj = bpy.context.active_object

        # Make sure the object has shape keys
        if obj.data.shape_keys is None:
            return []

        # Return a list of shape key names
        return [key.name for key in obj.data.shape_keys.key_blocks]

    def shape_key_names_list(self, obj_name):
        # Returns a list with all the shape key names on a specific object
        obj = bpy.data.objects[obj_name]
        shape_keys = obj.data.shape_keys.key_blocks
        shape_key_names = [key.name for key in shape_keys]
        return shape_key_names

    def shape_key_list_upstream(self):
        # Get the active object
        obj = bpy.context.active_object
        active_shape_key_name = obj.active_shape_key.name

        # Make sure the object has shape keys
        if obj.data.shape_keys is None:
            return []

        # Return a list of shape key names
        return [key.name for key in obj.data.shape_keys.key_blocks if
                key.name == active_shape_key_name or active_shape_key_name in key.name.split("_")]

    def shape_key_list_downstream(self):
        # Get the active object
        obj = bpy.context.active_object
        shape_keys = obj.data.shape_keys.key_blocks
        shape_key_names = [key.name for key in shape_keys]
        wanted = obj.active_shape_key.name

        # Make sure the object has shape keys
        if obj.data.shape_keys is None:
            return []

        downstream_combos = []
        if "_" in wanted:
            wanted_parts = set(wanted.split("_"))
            downstream_combos = [name for name in shape_key_names if
                                 all(part in wanted_parts for part in name.split("_")) and len(name.split("_")) < len(
                                     wanted.split("_"))]
        return downstream_combos if downstream_combos else []

    def find_stream(self, string_list, wanted):
        # Returns a list with downstream shapes + the shape in question
        downstream_combos = []
        downstream_combos.append(wanted)
        if "_" in wanted:
            wanted_parts = set(wanted.split("_"))
            downstream_combos = [name for name in string_list if
                                 all(part in wanted_parts for part in name.split("_")) and len(name.split("_")) < len(
                                     wanted.split("_"))]
        downstream_combos.append(wanted)
        return downstream_combos if downstream_combos else []

    def shape_key_exists(self, shape_names, object_name):
        # Get's a shape list, and returns a list with shapes that exist on the object in question,
        # if it's in the shape list. Seems to require actual shape objects in a list, and returns the same.
        obj = bpy.data.objects[object_name]

        if obj.data.shape_keys is not None:
            shape_keys = obj.data.shape_keys.key_blocks
            found_shape_names = []
            for shape_name in shape_names:
                if shape_name in shape_keys:
                    found_shape_names.append(shape_name)
            return found_shape_names
        return []

    def check_if_hero(self, shape_name):
        # Checks if not ends with N or if it's all letters
        if "_" not in shape_name and not shape_name.endswith("N") and str.isalpha(shape_name):
            return True
        else:
            return False

    def check_if_negative(self, shape_name):
        # Checks if it ends with N or if it's all letters
        if shape_name.endswith("N") and str.isalpha(shape_name):
            return True
        else:
            return False

    def check_if_combination(self, shape_name):
        # Split the shape name by the underscore
        name_parts = shape_name.split("_")

        # Check if the active object's name has an underscore and a string following it
        if len(name_parts) < 2 or name_parts[1] == "":
            #print(f"check_if_combination: not a combo {shape_name}")
            return False
        elif len(name_parts) == 2 and float(name_parts[1]):
            print(f"check_if_combination: not a combo cause number {shape_name}")
            return False
        else:
            return True
        # Commenting out because it was filtering inbetween combos. Might need that try/except, not sure
        # else:
        #     # Check if the string following the underscore is numeric
        #     try:
        #         len(name_parts) == 2 and float(name_parts[1])
        #         print(f"check_if_combination: not a combo {shape_name}")
        #         return False
        #     except ValueError:
        #         print(f"check_if_combination: yes a combo {shape_name}")
        #         return True

    def check_if_inbetween(self, shape_name):

        # Split the active shape name by the underscore
        name_parts = shape_name.split("_")

        # Check if the active object's name has an underscore and a string following it
        # the condition was < 2 but != seems more appropriate since 3 shapes would be a combo
        if len(name_parts) != 2 or name_parts[1] == "":
            return False
        else:
            # Check if the string following the underscore is numeric
            try:
                float(name_parts[1])
                return True
            except ValueError:
                return False

    def check_if_inbetween_combination(self, combo_to_check, existing_shape):
        # Work in progress

        split_string = combo_to_check.split("_")
        split_check_string = existing_shape.split("_")

        match_found = False

        for i in range(0, len(split_string), 2):
            if split_string[i] == split_check_string[0] and split_string[i + 1].isdigit() and split_string[i + 1] == \
                    split_check_string[1]:
                match_found = True
                break

        if match_found:
            return True
        else:
            return False

    def check_if_inbetween_combinations(self, combo_to_check, existing_shapes):
        split_string = combo_to_check.split("_")

        match_found = False
        for existing_shape in existing_shapes:
            split_check_string = existing_shape.split("_")

            for i in range(0, len(split_string), 2):
                if split_string[i] == split_check_string[0] and split_string[i + 1].isdigit() and split_string[i + 1] == \
                        split_check_string[1]:
                    match_found = True
                    break

            if match_found:
                return True

        return False

    def check_combos(self, list_combo, list_hero):
        # Gets a list of hero shape names, and a list of combo shapes,
        # and checks if the hero shapes exist for that combo.
        # May be more useful if it would return a list with valid combos which have all the heroes.
        # Currently, this would interrupt mass updates if encountering a missing hero.
        for string in list_combo:
            parts = string.split('_')
            for part in parts:
                if part not in list_hero:
                    return False
        return True

    def check_combos_list(self, list_combo, list_hero):
        # Gets a list of hero shape names, and a list of combo shapes,
        # and checks if the hero shapes exist for that combo.
        # Returns a full list of non-valid combos.
        false_combos = []
        for string in list_combo:
            parts = string.split('_')
            for part in parts:
                if part not in list_hero:
                    false_combos.append(string)
                    break
        return false_combos

    def find_downstream(self, string_list, wanted):
        downstream_combos = []
        if "_" in wanted:
            wanted_parts = set(wanted.split("_"))
            downstream_combos = [name for name in string_list if
                                 all(part in wanted_parts for part in name.split("_")) and len(name.split("_")) < len(
                                     wanted.split("_"))]
        return downstream_combos if downstream_combos else []

    def connected_inbetween_list(self, shape_list, object_name):
        # Returns a list with all connected inbetweens for a list of inbetweens.
        obj = bpy.data.objects.get(object_name)
        print(f"connected_inbetween_list getting {shape_list}")
        result = []

        # Iterate through the shape keys of the object
        for shape_key in obj.data.shape_keys.key_blocks:
            # Iterate through the items in the input list
            for shape_name in shape_list:
                # Check if the shape key name starts with the shape name from the list, followed by an underscore
                if shape_key.name.startswith(shape_name.split("_")[0] + "_") and shape_key.name != shape_name:
                    # Check if the shape key name is followed by a numeral
                    if shape_key.name[-1].isnumeric():
                        # Append the shape key name to the result list
                        result.append(shape_key.name)
        return result

    def missing_inbetween_list(self, names, obj_name):
        # Returns a list of hero shapes which do not have inbetweens
        obj = bpy.data.objects[obj_name]

        # Initialize an empty list to store the names of shape keys
        shape_key_names = []

        # Iterate through the names in the list
        for name in names:
            # Split the name by underscore and get the first element (the shape key base name)
            base_name = name.split("_")[0]

            # Check if a shape key with the base name exists on the object
            if base_name in obj.data.shape_keys.key_blocks:
                # Initialize a variable to track whether a shape key with the base name followed by an underscore and a numeral exists
                numeral_key_exists = False

                # Iterate through the shape keys on the object
                for shape_key in obj.data.shape_keys.key_blocks:
                    # Check if the shape key name starts with the base name followed by an underscore and a numeral
                    if shape_key.name.startswith(base_name + "_") and shape_key.name.split("_")[1].isdigit() and len(shape_key.name.split("_")) == 2:
                        # Set the numeral_key_exists variable to True
                        numeral_key_exists = True
                        break

                # If a shape key with the base name followed by an underscore and a numeral does not exist, append the name to the list
                if not numeral_key_exists:
                    shape_key_names.append(name)

        # Return the list of shape key names
        return shape_key_names

    def create_inbetween_dict(self, inbetweens):
        # Creates a dict for all inbetweens with the names as the key, and the values as the values
        my_dict = {}

        # Iterate over the names in the list
        for shape in inbetweens:
            # Split the name by '_'
            parts = shape.split('_')

            # Check if the name has a matching part before the '_' split and is followed by numerals
            if parts[0] in my_dict and shape[-1].isdigit():
                # Add the name to the list of values for the key
                my_dict[parts[0]].append(shape)
            else:
                # Create a new key and add the name as the first value
                my_dict[parts[0]] = [shape]

        for key, value in my_dict.items():
            for shape in value:
                if len(shape.split('_')) < 2:
                    my_dict[key].remove(shape)
        # Return the dictionary
        return my_dict

    def shape_name_value_dict(self, shape_name):
        # Takes a string and returns a dict with shape name and value pairs, based on naming.
        processed_strings = {}
        print(f"------shape_name_value_dict function getting {shape_name}")
        for string in shape_name:
            # Split on '_'
            split_string = string.split('_')
            for i, s in enumerate(split_string):

                # Check if the last character is a numeral
                if s[-1].isdigit():
                    # Extract the last 2 digits of the numeral
                    num = int(s[-2:]) / 100
                    # Check if the current string is not a key in the dictionary
                    if s not in processed_strings:
                        # Add the previous string as the key and the current string as the value
                        processed_strings[split_string[i - 1]] = num
                    else:
                        # Update the value of the current key
                        processed_strings[s] = num
                elif s[-1] == 'N':
                    new_name = s[:-1]
                    processed_strings.pop(s, None)
                    processed_strings[new_name] = -1
                else:
                    processed_strings[s] = 1
        return processed_strings

    def order_list(self, lst):
        # Create a set to remove duplicates
        s = set()

        # Create a new list with only the unique elements from lst, in the same order
        filtered_lst = [x for x in lst if x not in s and (s.add(x) or True)]

        # Sort the list based on the numerals in the name and the alphabetical order
        def extract_num_and_name(s):
            parts = s.split('_')
            name = parts[0]
            if len(parts) > 1:
                try:
                    num = int(parts[1])
                except ValueError:
                    num = float('inf')
            else:
                num = float('inf')
            return (name, num)

        sorted_lst = sorted(filtered_lst, key=extract_num_and_name)

        return sorted_lst

    def order_list_combos(self, lst):
        # Create a set to remove duplicates
        s = set()

        # Create a new list with only the unique elements from lst, in the same order
        filtered_lst = [x for x in lst if x not in s and (s.add(x) or True)]

        # Sort the list based on the numerals in the name, the number of underscores, and alphabetical order
        def extract_num_and_name(s):
            parts = s.split('_')
            name = parts[0]
            if len(parts) > 1:
                try:
                    num = int(parts[1])
                except ValueError:
                    num = float('inf')
            else:
                num = float('inf')
            return (name, num, len(parts) - 1)

        sorted_lst = sorted(filtered_lst, key=extract_num_and_name)

        return sorted_lst

    def get_combination_drivers(self, shape_name):
        # Gets a shape name and returns a list of shape names. 'A_B_10_C_20_D' -> ['A', 'B_10', 'C_20', 'D']
        elements = shape_name.split("_")
        results = []
        other_list = []
        for i in range(len(elements)):
            try:
                float(elements[i])
                results.append(elements[i - 1] + "_" + elements[i])
            except ValueError:
                pass
        for i in range(len(elements)):
            try:
                float(elements[i])
                other_list.append(elements[i - 1])
                other_list.append(elements[i])
            except ValueError:
                pass
        shapes = [shape for shape in elements if shape not in other_list] + results
        return shapes




registry = [

]