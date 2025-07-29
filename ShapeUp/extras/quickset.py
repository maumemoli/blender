import bpy

from ..utils.shape_selection import ShapeSelection
from ..utils.shape_processing import ShapePrecessing

class Quickset(bpy.types.PropertyGroup):
    def __init__(self):
        self.shapeselect  = ShapeSelection()
        self.shapeprocess = ShapePrecessing()

    def set_active_shape_key(self):
        obj = bpy.context.active_object
        active_shape_key = obj.active_shape_key

        shapes_values = self.shapeselect.shape_name_value_dict([active_shape_key.name])
        self.shapeprocess.set_shape_key_values(shapes_values)


    def update_quickset(self, context):
        obj = context.object
        if obj.quickset:
            bpy.msgbus.subscribe_rna(
                key=bpy.context.object.path_resolve("active_shape_key_index", False),
                owner=None,
                args=(bpy.context.scene,),
                notify=self.set_active_shape_key
            )
        else:
            bpy.msgbus.clear_by_owner(None)



registry = [
    Quickset,
]