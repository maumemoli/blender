import bpy


class MeshSelection:
    def __init__(self):
        pass

    def get_active_mesh(self):
        # Print the active object, if it is a mesh
        active_object = bpy.context.active_object
        if active_object and active_object.type == 'MESH':
            print("Active mesh:", active_object.name)

        return active_object

    def get_selected_meshes(self):
        # Get the active object
        active_object = bpy.context.active_object

        # Initialize the list of selected objects
        selected_objects = []

        # Add the names of the selected objects that are meshes to the list,
        # but only if they are not the same as the active object
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH' and obj.name != active_object.name:
                selected_objects.append(obj.name)

        return selected_objects

    def select_meshes_by_name(self, names):
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Iterate over the objects in the scene
        for obj in bpy.context.scene.objects:
            # Check if the object is a mesh with a matching name
            if obj.type == 'MESH' and obj.name in names:
                # Select the object
                obj.select_set(True)

    def select_and_activate_mesh(self, name):
        # Get the object with the specified name
        obj = bpy.data.objects.get(name)

        # Make sure the object is a mesh
        if obj and obj.type == 'MESH':
            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # Select the object
            obj.select_set(True)

            # Set the object as the active object
            bpy.context.view_layer.objects.active = obj
        else:
            print(f"Object with name '{name}' not found or is not a mesh.")


registry = [

]