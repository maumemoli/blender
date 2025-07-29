import bpy

from ..utils.mesh_processing import MeshProcessing

mesh_processing = MeshProcessing()


class ShapeEditor_OT_CreateCopy(bpy.types.Operator):
    """Creates a clean working mesh with all shape keys applied"""
    bl_idname = "shapeeditor.createcopy"
    bl_label = "Creates clean working mesh"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if context.object.smart_name:
            mesh_processing.duplicate_object_easy()
        else:
            mesh_processing.duplicate_object()

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_CreateCopy,
]