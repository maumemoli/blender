import bpy


class ShapePrecessing:
    def __init__(self):
        pass

    def join_objects_as_shapes(self):
        bpy.ops.object.join_shapes()

    def join_as_shapes(self, shapes, active_shape):
        # Set the shapes in the list 'shapes' as shapekeys on the object 'active_shape'
        bpy.ops.object.select_all(action='DESELECT')
        for shape in shapes:
            bpy.data.objects[shape].select_set(True)

        # Make the mesh with the specified name active
        bpy.data.objects[active_shape].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[active_shape]

        # Join the selected meshes as shapes
        bpy.ops.object.join_shapes()

    def remove_shape_keys(self, shape_key_names, object_name):
        # Get the object with the specified name
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            print(f"Error: Object '{object_name}' not found.")
            return

        # Get the shape keys of the object
        shape_keys = obj.data.shape_keys.key_blocks
        print(f"remove_shape_keys function getting {shape_key_names} and {object_name}")
        # Iterate through the shape keys in reverse order
        for ind in reversed(range(len(shape_keys))):

            shape_key = shape_keys[ind]
            if shape_key.name in shape_key_names:
                print(f"remove_shape_keys function deleting{shape_key.name}")
                # Remove the shape key
                obj.active_shape_key_index = ind
                bpy.ops.object.shape_key_remove()

    def remove_shape_key_suffix(self, obj_name: str):
        # Using the remove shape keys function
        # Get the object with the given name
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            print(f"Object with name '{obj_name}' not found.")
            return

        # Get the shape keys of the object
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            print("Object does not have shape keys.")
            return

        # Create a list of shape key names to remove
        shape_key_names = []
        for shape_key in shape_keys.key_blocks:
            # Check if the shape key name ends with '_100'
            if shape_key.name.endswith("_100"):
                # Get the name before the '_100' suffix
                shape_key_name = shape_key.name[:-4]
                # Check if a shape key with that name exists
                if shape_key_name in shape_keys.key_blocks:
                    # Add the shape key name to the list of shape keys to remove
                    shape_key_names.append(shape_key_name)

        self.remove_shape_keys(shape_key_names, obj_name)
        for shape_key in shape_keys.key_blocks:
            # Check if the shape key name ends with '_100'
            if shape_key.name.endswith("_100"):
                shape_key.name = shape_key.name.rstrip("_100")

    def rename_negative_shapes(self, shapes: list, suffix='_temp'):
        obj = bpy.context.active_object

        for shape_key in obj.data.shape_keys.key_blocks:
            # Check if the shape key name ends with "N"
            if shape_key.name.endswith("N") and shape_key.name in shapes:
                # Rename the shape key to have "_temp" at the end
                shape_key.name = shape_key.name + suffix

    def set_shape_keys(self, shape_names, object_name):
        # Sets the shape key values on the object to 1
        obj = bpy.data.objects[object_name]

        # Set all shape keys to 0
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = 0

        # Set the shape keys with matching names to 1
        if len(shape_names) == 1:
            obj.data.shape_keys.key_blocks[shape_names[0]].value = 1
        else:
            for shape_name in shape_names:
                obj.data.shape_keys.key_blocks[shape_name].value = 1

    def set_additional_shape_keys(self, shape_names):
        # Sets shape keys from the list, but Does not zero out the rest
        obj = bpy.context.active_object

        # Set the shape keys with matching names to 1
        if len(shape_names) == 1:
            obj.data.shape_keys.key_blocks[shape_names[0]].value = 1
        else:
            for shape_name in shape_names:
                obj.data.shape_keys.key_blocks[shape_name].value = 1

    def set_active_shape_key(self, name):
        bpy.context.object.active_shape_key_index = bpy.context.object.data.shape_keys.key_blocks.keys().index(name)

    def set_shape_key_values_to_zero(self):
        # Sets every shape key value to zero
        obj = bpy.context.active_object

        # Iterate through the shape keys
        for shape_key in obj.data.shape_keys.key_blocks:
            # Set the shape key's value to 0
            shape_key.value = 0

    def set_shape_key_values(self, shape_key_values):
        # Sets shape key values based on a dict. Keys are shapekeys, values are values.
        obj = bpy.context.active_object
        print(f"---------------set_shape_key_values function got {shape_key_values}")
        # Set all shape keys to 0
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = 0

        # Set the shape keys with matching names to the values in the dictionary
        for shape_key_name, shape_key_value in shape_key_values.items():
            obj.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value

    def unmute_all_shapes(self):
        # Get the active object
        obj = bpy.context.active_object

        # Unmute all shapes on the object
        for shape in obj.data.shape_keys.key_blocks:
            shape.mute = False

    def swap_shapes_old(self, shape_key_name, obj):
        # swap_shapes("object", "shape key to swap")
        obj = bpy.data.objects[obj]
        # Set all shape keys to 0
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = 0

        # Create a new shape key from the mix
        obj.shape_key_add(name="Mix", from_mix=True)

        # Rename the shape key that matches the input string
        for shape_key in obj.data.shape_keys.key_blocks:
            if shape_key.name == shape_key_name:
                shape_key.name = shape_key_name + "_100"
                break

        # Rename the newly created shape key to the renamed shape key's name
        for shape_key in obj.data.shape_keys.key_blocks:
            if shape_key.name == "Mix":
                shape_key.name = shape_key_name
                break

    def swap_shapes(self, shape_key_name, obj):
        # swap_shapes("object", "shape key to swap")
        obj = bpy.data.objects[obj]
        # Set all shape keys to 0
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = 0

        # Create a new shape key from the mix
        obj.shape_key_add(name="Mix", from_mix=True)

        # Rename the newly created shape key to the renamed shape key's name
        for shape_key in obj.data.shape_keys.key_blocks:
            if shape_key.name == "Mix":
                shape_key.name = shape_key_name + "_100"
                break

    def set_shapekey_min_value(self, string):
        # Only working for negative shapes, or rather shapes ending with N, to be safe for now.
        if string.endswith("N"):
            shapekey_name = string[:-1]
            obj = bpy.context.active_object
            if shapekey_name in obj.data.shape_keys.key_blocks:
                shape_key = obj.data.shape_keys.key_blocks[shapekey_name]
                shape_key.slider_min = -1
            else:
                print(f"Shape key '{shapekey_name}' not found.")
        else:
            print("String does not end with N.")

    def create_shape_mix(self, object_name, mix_name="Mix"):
        # Creates a shapekey with a name from the current shapekey values
        obj = bpy.data.objects[object_name]

        obj.shape_key_add(name=mix_name)




registry = [

]