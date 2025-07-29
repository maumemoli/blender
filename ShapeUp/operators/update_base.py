import bpy

from ..utils.shape_processing import ShapePrecessing

shape_processing = ShapePrecessing()


class ShapeEditor_OT_UpdateBase(bpy.types.Operator):
    """Replace the 'Basis' shape key with the currently selected shape key"""
    bl_idname = "shapeeditor.updateintermediate"
    bl_label = "Apply Selected Shapekey as Basis"

    def execute(self, context):

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.object.select_set(True)

        # ____________________________
        # Generate copy of object
        # ____________________________
        originalName = bpy.context.object.name
        bpy.ops.object.duplicate_move()
        bpy.context.object.name = originalName + "_Applied_Shape_Key"

        shapeKeyToBeApplied_name = bpy.context.object.active_shape_key.name

        listOfKeys = []

        # __________________________________________________
        # Store all shape keys in a list
        # __________________________________________________

        for s_key in bpy.context.object.data.shape_keys.key_blocks:

            if s_key.name == shapeKeyToBeApplied_name:
                continue

            listOfKeys.append(s_key.name)

        # __________________________________________________

        for name in listOfKeys:
            shape_processing.set_active_shape_key(name)
            currentShapeKey = bpy.context.object.active_shape_key

            shape_processing.set_active_shape_key(shapeKeyToBeApplied_name)
            applyShapeKey = bpy.context.object.active_shape_key

            # Add new shapekey from mix
            bpy.ops.object.shape_key_clear()

            currentShapeKey.value = 1.0
            applyShapeKey.value = 1.0

            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.object.active_shape_key.name = currentShapeKey.name + "_"

        for name in listOfKeys:
            # Set index to target shapekey
            shape_processing.set_active_shape_key(name)
            # Remove
            bpy.ops.object.shape_key_remove(all=False)

        shape_processing.set_active_shape_key(shapeKeyToBeApplied_name)
        bpy.ops.object.shape_key_remove(all=False)

        # Remove the "_" at the end of each shapeKey
        for s_key in bpy.context.object.data.shape_keys.key_blocks:
            s_key.name = s_key.name[:-1]

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_UpdateBase,
]