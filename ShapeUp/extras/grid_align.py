import bpy


class ShapeEditor_OT_GridAlign(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "shapeup.gridalign"
    bl_label = "Grid Align"
    bl_options = {'REGISTER', 'UNDO'}

    pos_x: bpy.props.FloatProperty(
        name = "Translate_X",
        description = "Translation X"
    )
    pos_y: bpy.props.FloatProperty(
        name = "Translate_Y",
        description = "Translation Y"
    )
    def execute(self, context):
        # Get the selected objects
        objects = bpy.context.selected_objects

        # Calculate the number of rows and columns
        # based on the number of objects
        num_objects = len(objects)
        num_columns = int(num_objects ** 0.5)
        num_rows = num_objects // num_columns
        if num_objects % num_columns > 0:
            num_rows += 1

        # Calculate the space between the objects
        # based on the bounding box of the first object
        bounding_box = objects[0].bound_box
        min_x = min([v[0] for v in bounding_box])
        max_x = max([v[0] for v in bounding_box])
        min_z = min([v[2] for v in bounding_box])
        max_z = max([v[2] for v in bounding_box])
        space_x = self.pos_x * (max_x - min_x)
        space_z = self.pos_y * (max_z - min_z)

        # Align the objects
        current_x = 0
        current_z = 0
        max_height = 0
        for i, obj in enumerate(objects):
            # Set the object's location
            obj.location = (current_x, 0, current_z)
            # Update the current position
            current_x += obj.dimensions[0] + space_x
            # Check if we need to move to the next row
            if (i + 1) % num_columns == 0:
                current_x = 0
                current_z += max_height + space_z
                max_height = 0
            # Update the maximum height
            max_height = max(max_height, obj.dimensions[2])



        return {'FINISHED'}


registry = [
    ShapeEditor_OT_GridAlign,
]