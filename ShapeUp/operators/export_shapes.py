import bpy
import os
from os.path import join

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

from ..utils.drivers import Drivers
from ..utils.shape_selection import ShapeSelection
from ..utils.shape_processing import ShapePrecessing


class ExportShapes:
    def __init__(self):
        self.shape_selection = ShapeSelection()
        self.shape_processing = ShapePrecessing()
        self.drivers = Drivers()

    def exportshapes(self, filepath):
        o = bpy.context.object  # Reference the active object
        filepath = str(os.path.dirname(filepath) + '\\')
        all_shapes = []
        all_shape_names = []

        # Duplicate the object
        duplicate = o.copy()
        duplicate.data = o.data.copy()
        bpy.context.collection.objects.link(duplicate)

        # Store the original name of the object
        original_name = o.name

        # Reset all shape keys to 0 (skipping the Basis shape on index 0
        for skblock in duplicate.data.shape_keys.key_blocks[1:]:
            skblock.value = 0
            all_shapes.append(skblock)
            all_shape_names.append(skblock.name)

        combos = [shape for shape in all_shapes if self.shape_selection.check_if_combination(shape.name)]
        not_combos = [shape for shape in all_shapes if shape not in combos]

        # Deselect the original object
        o.select_set(False)

        # Remove all shape key drivers
        self.drivers.disconnect_shape_key_drivers(all_shape_names, duplicate.name)
        print("------REMOVING ALL DRIVERS--------")

        # Iterate over shape key blocks and save each as an OBJ file
        for skblock in not_combos:
            self.shape_processing.remove_shape_key_suffix(duplicate.name)
            skblock.value = 1.0  # Set shape key value to max

            # Select the duplicate object
            duplicate.select_set(True)

            # Rename the object to the shape key's name
            duplicate.name = skblock.name

            # Set OBJ file path and Export OBJ
            objFileName = skblock.name + ".obj"  # File name = shapekey name
            objPath = join(filepath, objFileName)
            bpy.ops.wm.obj_export(filepath=objPath, export_selected_objects=True)

            skblock.value = 0  # Reset shape key value to 0

        for skblock in combos:
            print(f"------SHAPE IS: {skblock.name}")
            connected_shapes = self.shape_selection.find_stream(all_shape_names, skblock.name)
            self.shape_processing.set_shape_keys(connected_shapes, duplicate.name)
            print(f"------SHAPE IS: {skblock.name}, CONNECTED SHAPES ARE: {connected_shapes}")
            # Select the duplicate object
            duplicate.select_set(True)

            # Rename the object to the shape key's name
            duplicate.name = skblock.name

            # Set OBJ file path and Export OBJ
            objFileName = skblock.name + ".obj"  # File name = shapekey name
            objPath = join(filepath, objFileName)
            bpy.ops.wm.obj_export(filepath=objPath, export_selected_objects=True)

            skblock.value = 0  # Reset shape key value to 0

        # Select the original object
        o.select_set(True)

        # Set the object's name back to its original value
        o.name = original_name

        # Delete the duplicate object
        bpy.data.objects.remove(duplicate)
        print(f"the filepath is {filepath}")

    def export_simple(self, filepath):
        o = bpy.context.active_object  # Reference the active object
        filepath = str(os.path.dirname(filepath) + '\\')
        all_shapes = self.shape_selection.shape_key_names_list(o.name)
        print(f"all shapes list is {all_shapes}")
        original_name = o.name

        for shape in all_shapes:
            key_shape_value_dict = self.shape_selection.shape_name_value_dict([shape])
            self.shape_processing.set_shape_key_values(key_shape_value_dict)
            o.name = shape
            objFileName = shape + ".obj"  # File name = shapekey name
            objPath = join(filepath, objFileName)
            bpy.ops.wm.obj_export(filepath=objPath, export_selected_objects=True)

        o.name = original_name

    def export_composed_shapes(self, filepath):
        # Reference the active object
        filepath = str(os.path.dirname(filepath) + '\\')
        o = bpy.context.active_object
        original_name = o.name
        shape_names = []

        # Reset all shape keys to 0 (skipping the Basis shape on index 0
        for skblock in o.data.shape_keys.key_blocks[1:]:
            skblock.value = 0
            shape_names.append(skblock.name)
        print(f"shape names are: {shape_names}")

        # Iterate over shape key blocks and save each as an OBJ file
        for skblock in o.data.shape_keys.key_blocks[1:]:

            current_shape = self.shape_selection.shape_name_value_dict([skblock.name])
            print(f"--------getting this from dict {current_shape}")

            for shape_key in o.data.shape_keys.key_blocks:
                shape_key.value = 0

            # Set the shape keys with matching names to the values in the dictionary
            for shape_key_name, shape_key_value in current_shape.items():
                o.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value

            downstream = (self.shape_selection.find_downstream(shape_names, skblock.name))
            downstream_no_heroes = [shape for shape in downstream if "_" in shape]

            self.shape_processing.set_additional_shape_keys(downstream_no_heroes)

            o.name = skblock.name

            # Set OBJ file path and Export OBJ
            objFileName = skblock.name + ".obj"  # File name = shapekey name
            objPath = join(filepath, objFileName)
            bpy.ops.wm.obj_export(filepath=objPath, export_selected_objects=True)

            # skblock.value = 0 # Reset shape key value to 0
        o.name = original_name

    def export_decomposed_shapes(self, filepath):
        o = bpy.context.active_object
        filepath = str(os.path.dirname(filepath) + '\\')
        original_name = o.name
        # Reset all shape keys to 0 (skipping the Basis shape on index 0
        for skblock in o.data.shape_keys.key_blocks[1:]:
            skblock.value = 0

        # Iterate over shape key blocks and save each as an OBJ file
        for skblock in o.data.shape_keys.key_blocks[1:]:
            skblock.value = 1.0  # Set shape key value to max
            o.name = skblock.name
            # Set OBJ file path and Export OBJ
            objFileName = skblock.name + ".obj"  # File name = shapekey name
            objPath = join(filepath, objFileName)
            bpy.ops.wm.obj_export(filepath=objPath, export_selected_objects=True)

            skblock.value = 0  # Reset shape key value to 0
        o.name = original_name

class ShapeEditor_OT_ExportSomeData(Operator, ExportHelper):
    """Export shape keys to named obj files, combining necessary deltas"""
    bl_idname = "export_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Shapes"
    # ExportHelper mixin class uses this
    filename_ext = ".obj"

    def execute(self, context):
        export = ExportShapes()
        export.export_simple(self.filepath)

        return {'FINISHED'}


class ShapeEditor_OT_ExportComposedShapes(Operator, ExportHelper):
    """Export composed (combined deltas) shape keys to named obj files, combining necessary deltas"""
    bl_idname = "export.composed_shapes"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Composed Shapes"
    # ExportHelper mixin class uses this
    filename_ext = ".obj"

    def execute(self, context):
        export = ExportShapes()
        export.export_composed_shapes(self.filepath)

        return {'FINISHED'}


class ShapeEditor_OT_ExportDecomposedShapes(Operator, ExportHelper):
    """Export decomposed (corrective deltas) shape keys to named obj files"""
    bl_idname = "export.decomposed_shapes"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Decomposed Shapes"
    # ExportHelper mixin class uses this
    filename_ext = ".obj"

    def execute(self, context):
        export = ExportShapes()
        export.export_decomposed_shapes(self.filepath)

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_ExportSomeData,
    ShapeEditor_OT_ExportComposedShapes,
    ShapeEditor_OT_ExportDecomposedShapes,
]