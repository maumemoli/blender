import bpy
import numpy as np

class MeshProcessing:
    def __init__(self):
        pass

    def rename_objects(self, old_names, new_names):
        # Renames objects from old name to new name
        # Make sure the lists are the same length
        if len(old_names) != len(new_names):
            print("Error: lists are not the same length")
            return

        # Iterate through the lists and rename the objects
        for old_name, new_name in zip(old_names, new_names):
            # Get the object with the old name
            obj = bpy.data.objects.get(old_name)

            # Make sure the object exists
            if obj is not None:
                # Rename the object
                obj.name = new_name
            else:
                print(f"Error: object with name '{old_name}' not found")

    def rename_correctives(self, old_names, new_names):
        # Renames the object from old names to new name + _sculpt
        # Make sure the lists are the same length
        if len(old_names) != len(new_names):
            print("Error: lists are not the same length")
            return

        # Iterate through the lists and rename the objects
        for old_name, new_name in zip(old_names, new_names):
            # Get the object with the old name
            obj = bpy.data.objects.get(old_name)

            # Make sure the object exists
            if obj is not None:
                # Rename the object
                obj.name = new_name + ("_sculpt")
            else:
                print(f"Error: object with name '{old_name}' not found")

    def mesh_difference_old(self, A, B, difference):
        # Get the objects from the collection using their names
        object_A = bpy.data.objects[A]
        object_B = bpy.data.objects[B]
        object_difference = bpy.data.objects[difference]

        # Get the meshes from the objects
        mesh_A = object_A.data
        mesh_B = object_B.data
        mesh_difference = object_difference.data

        # Get the vertices of each mesh
        verts_A = mesh_A.vertices
        verts_B = mesh_B.vertices
        verts_difference = mesh_difference.vertices

        # Loop through the vertices and calculate the difference in position
        for i in range(len(verts_A)):
            vert_A = verts_A[i]
            vert_B = verts_B[i]
            vert_difference = verts_difference[i]

            # Check if the positions of the vertices are different between mesh_A and mesh_B
            if vert_A.co != vert_B.co:
                # Calculate the difference in position
                diff_x = vert_A.co.x - vert_B.co.x
                diff_y = vert_A.co.y - vert_B.co.y
                diff_z = vert_A.co.z - vert_B.co.z

                # Move the vertex on mesh_difference by the absolute difference in position
                vert_difference.co.x += diff_x
                vert_difference.co.y += diff_y
                vert_difference.co.z += diff_z

    def mesh_difference(self, A, B, difference):
        ob1 = bpy.data.objects[A]
        ob2 = bpy.data.objects[B]
        ob3 = bpy.data.objects[difference]

        verts1 = ob1.data.vertices
        verts2 = ob2.data.vertices
        verts3 = ob3.data.vertices

        arr1 = np.empty(len(verts1) * 3, dtype=float)
        arr2 = np.empty(len(verts2) * 3, dtype=float)
        arr3 = np.empty(len(verts2) * 3, dtype=float)

        verts1.foreach_get('co', arr1)
        verts2.foreach_get('co', arr2)
        verts3.foreach_get('co', arr3)
        verts3.foreach_set('co', arr3 - (arr2 - arr1))
        ob3.data.update()

    def remove_mesh(self, mesh_name):
        bpy.ops.object.select_all(action='DESELECT')
        # Get the mesh object with the given name
        mesh = bpy.data.objects.get(mesh_name)
        # Check if the mesh object exists
        if mesh is not None:
            # Select the mesh object
            mesh.select_set(True)
            # Remove the mesh object
            bpy.ops.object.delete()

    def duplicate_object(self, name=None):
        # Get the active object
        active_obj = bpy.context.active_object

        # Duplicate the active object
        new_obj = active_obj.copy()
        new_obj.data = active_obj.data.copy()

        # Add the duplicated object to the scene
        bpy.context.collection.objects.link(new_obj)

        # Set the name of the new object
        if name is not None:
            new_obj.name = name
        else:
            new_obj.name = active_obj.name + "_duplicate"

        # Create a new shape key from mix on the new object
        new_obj.shape_key_add(name="Mix")

        # Remove all the shape keys on the new object
        for key in new_obj.data.shape_keys.key_blocks:
            new_obj.shape_key_remove(key)

        # Get the bounding box size
        bounding_box_size = new_obj.dimensions[0]

        # Move the object by -1.2*bounding_box_size in the x direction
        new_obj.location.x -= 1 * bounding_box_size

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Make the new object active
        new_obj.select_set(True)

        bpy.context.view_layer.objects.active = new_obj

        return new_obj

    def duplicate_object_easy(self, name=None):
        # Get the active object
        active_obj = bpy.context.active_object

        # Duplicate the active object
        new_obj = active_obj.copy()
        new_obj.data = active_obj.data.copy()

        # Add the duplicated object to the scene
        bpy.context.collection.objects.link(new_obj)

        # Set the name of the new object
        if name is not None:
            new_obj.name = name
        else:
            shapekeys = [key.name for key in active_obj.data.shape_keys.key_blocks if abs(key.value) > 0.5]
            if shapekeys:
                if len(shapekeys) == 1:
                    new_obj.name = shapekeys[0]
                else:
                    # split shapekeys at '_'
                    shapekeys = [sk.split('_') for sk in shapekeys]
                    # flatten the list
                    shapekeys = [item for sublist in shapekeys for item in sublist]
                    # remove duplicates and remove any numerals from the list
                    shapekeys = [sk for sk in shapekeys if not sk.isnumeric()]
                    shapekeys = sorted(set(shapekeys))
                    new_obj.name = '_'.join(shapekeys)
            else:
                new_obj.name = active_obj.name + "_duplicate"

        # Create a new shape key from mix on the new object
        new_obj.shape_key_add(name="Mix")

        # Remove all the shape keys on the new object
        for key in new_obj.data.shape_keys.key_blocks:
            new_obj.shape_key_remove(key)

        bounding_box_size = new_obj.dimensions[0]

        # Move the object by -1.2*bounding_box_size in the x direction
        new_obj.location.x -= 1 * bounding_box_size

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Make the new object active
        new_obj.select_set(True)
        bpy.context.view_layer.objects.active = new_obj

        return new_obj


registry = [
]