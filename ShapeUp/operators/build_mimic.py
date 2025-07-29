import bpy
import os
from os.path import join

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

from ..utils.drivers import Drivers
from ..utils.shape_selection import ShapeSelection
from ..utils.shape_processing import ShapePrecessing


class ExportShapes:
    def __init__(self):
        self.shape_selection = ShapeSelection()
        self.shape_processing = ShapePrecessing()
        self.drivers = Drivers()

    def build_mimic(self, folder_path):
        folder_path = str(os.path.dirname(folder_path) + '\\')

        shapes_collection = bpy.data.collections.new("Shapes")
        bpy.context.scene.collection.children.link(shapes_collection)
        layer_collection = bpy.context.view_layer.layer_collection.children[shapes_collection.name]
        bpy.context.view_layer.active_layer_collection = layer_collection

        for file in os.listdir(folder_path):
            if file.endswith(".obj"):
                file_path = os.path.join(folder_path, file)
                bpy.ops.wm.obj_import(filepath=file_path)


class ShapeEditor_OT_BuildMimic(Operator, ImportHelper):
    """Export shape keys to named obj files, combining necessary deltas"""
    bl_idname = "export_test.build_mimic"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Build Mimic"
    # ExportHelper mixin class uses this
    filename_ext = ".obj"

    def execute(self, context):
        export = ExportShapes()
        export.build_mimic(self.filepath)

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_BuildMimic,

]