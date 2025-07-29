import bpy

from ..utils.shape_processing import ShapePrecessing
from ..utils.shape_selection import ShapeSelection
from ..utils.drivers import Drivers




class ShapeEditor_OT_DeleteShape(bpy.types.Operator):
    """Unmute all shapes"""
    bl_idname = "shapeeditor.deleteshape"
    bl_label = "Export Selected Shape"


    def __init__(self):
        self.shape_processing = ShapePrecessing()
        self.shape_selection = ShapeSelection()
        self.driverss = Drivers()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = bpy.context.active_object
        hero_upstream = []
        active_shapekey = self.shape_selection.get_active_shape_key_name()
        if self.shape_selection.check_if_hero(active_shapekey):
            self.shape_processing.remove_shape_keys(self.shape_selection.shape_key_list_upstream(), obj.name)
            print(f"Delete Shape OP - Deleting hero and upstream shapes: {self.shape_selection.shape_key_list_upstream()}")
        elif self.shape_selection.check_if_inbetween(active_shapekey):
            print("Delete Shape OP - Removing inbetween")
            self.driverss.disconnect_active_shape_key_driver()

            print(f"Delete Shape OP - sending these to inb function {[active_shapekey]} {obj.name}")
            inb_list = self.shape_selection.connected_inbetween_list([active_shapekey], obj.name)
            ordered_inb_list = self.shape_selection.order_list(inb_list)
            driver_shape = ordered_inb_list[0].split('_')[0]
            drivers = self.driverss.inbetween_expression(driver_shape, ordered_inb_list)
            print(f"Delete Shape OP - inb list is {inb_list}")
            print(f"Delete Shape OP - ordered inb list is {ordered_inb_list}")
            print(f"Delete Shape OP - driver is {ordered_inb_list[0].split('_')[0]}")
            for i, shape in enumerate(ordered_inb_list):
                last_inbetween_expression = drivers[-1]

                inbetween_expression = drivers[i] + "- (" + " + ".join(ordered_inb_list) + ")"
                print(f"Delete Shape OP - expression for {shape} is {inbetween_expression}")

                #ordered_inb_list.append(driver_shape)
                ordered_inb_list.remove(shape)

                if shape.endswith("_100"):
                    self.driverss.create_inbetween_driver(obj, shape, driver_shape, last_inbetween_expression)
                else:
                    self.driverss.create_shape_key_driver(obj, shape, inbetween_expression,
                                                          ordered_inb_list)





            bpy.ops.object.shape_key_remove(all=False)
        elif self.shape_selection.check_if_combination(active_shapekey):
            self.driverss.disconnect_active_shape_key_driver()
            bpy.ops.object.shape_key_remove(all=False)
            print("Delete Shape OP - Removing combination")



        return {'FINISHED'}


class ShapeEditor_OT_DeleteCombos(bpy.types.Operator):
    """Unmute all shapes"""
    bl_idname = "shapeeditor.deletecombos"
    bl_label = "Export Selected Shape"


    def __init__(self):
        self.shape_processing = ShapePrecessing()
        self.shape_selection = ShapeSelection()
        self.driverss = Drivers()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        c = context.object
        obj = bpy.context.active_object
        all_shapes = []
        to_delete = []
        for shape_key in obj.data.shape_keys.key_blocks:
            if not self.shape_selection.check_if_hero(shape_key.name) and not self.shape_selection.check_if_inbetween(shape_key.name):
                all_shapes.append(shape_key.name)

        for shape in all_shapes:
            if len(shape.split('_')) > c.delete_iterations:
                if c.delete_names == "":
                    self.shape_processing.set_active_shape_key(shape)
                    self.shape_processing.remove_shape_keys(self.shape_selection.shape_key_list_upstream(), obj.name)
                    print(f"Delete Combo OP - Deleting combo shapes: {self.shape_selection.shape_key_list_upstream()}")
                elif c.delete_names in shape:
                    to_delete.append(shape)
            else:
                print("Delete Combo OP - There are no matching combos")

        for shape in to_delete:
            if len(shape.split('_')) > c.delete_iterations:
                self.shape_processing.set_active_shape_key(shape)
                self.shape_processing.remove_shape_keys(self.shape_selection.shape_key_list_upstream(), obj.name)
                print(f"Delete Combo OP - Deleting combo shapes: {self.shape_selection.shape_key_list_upstream()}")
            else:
                print("Delete Combo OP - There are no matching combos")



        return {'FINISHED'}


class ShapeEditor_OT_MuteShapes(bpy.types.Operator):
    """Unmute all shapes"""
    bl_idname = "shapeeditor.muteshapes"
    bl_label = "Export Selected Shape"


    def __init__(self):
        self.shape_processing = ShapePrecessing()
        self.shape_selection = ShapeSelection()
        self.driverss = Drivers()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        c = context.object
        obj = bpy.context.active_object

        all_shapes = []
        inbetweens = []
        for shape_key in obj.data.shape_keys.key_blocks:
            if not self.shape_selection.check_if_hero(shape_key.name):
                all_shapes.append(shape_key.name)

        for shape_key in obj.data.shape_keys.key_blocks:
            if not self.shape_selection.check_if_inbetween(shape_key.name):
                inbetweens.append(shape_key.name)

        for shape in obj.data.shape_keys.key_blocks:
            if (len(shape.name.split('_')) > c.mute_iterations and
                    shape.name in all_shapes and
                    c.mute_names == "" and not
                    c.mute_invert and not
                    c.mute_inbetweens_only):
                shape.mute = True
            elif (shape.name in inbetweens and
                    c.mute_names == "" and not
                    c.mute_invert and
                    c.mute_inbetweens_only):
                shape.mute = True
            elif (len(shape.name.split('_')) > c.mute_iterations and
                    shape.name in all_shapes and
                    c.mute_names in shape.name and not
                    c.mute_invert and not
                    c.mute_inbetweens_only):
                shape.mute = True
            elif (len(shape.name.split('_')) > c.mute_iterations and
                    shape.name not in all_shapes and
                    c.mute_names in shape.name and
                    c.mute_invert and not
                    c.mute_inbetweens_only):
                shape.mute = True
            elif (len(shape.name.split('_')) > c.mute_iterations and
                    shape.name in inbetweens and
                    c.mute_names in shape.name and not
                    c.mute_invert and
                    c.mute_inbetweens_only):
                shape.mute = True
            elif (len(shape.name.split('_')) > c.mute_iterations and
                    shape.name in inbetweens and
                    c.mute_names in shape.name and
                    c.mute_invert and
                    c.mute_inbetweens_only):
                shape.mute = True


            print("Mute Shapes OP - There are no matching shapes")



        return {'FINISHED'}


class ShapeEditor_OT_UnmuteAll(bpy.types.Operator):
    """Unmute all shapes"""
    bl_idname = "shapeeditor.unmuteall"
    bl_label = "Export Selected Shape"

    def __init__(self):
        self.shape_processing = ShapePrecessing()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        self.shape_processing.unmute_all_shapes()
        return {'FINISHED'}


class ShapeEditor_OT_ZeroAll(bpy.types.Operator):
    """Zero out all shapes"""
    bl_idname = "shapeeditor.zeroall"
    bl_label = "Zero Out Shapes"

    def __init__(self):
        self.shape_processing = ShapePrecessing()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        self.shape_processing.set_shape_key_values_to_zero()

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_UnmuteAll,
    ShapeEditor_OT_ZeroAll,
    ShapeEditor_OT_DeleteShape,
    ShapeEditor_OT_DeleteCombos,
    ShapeEditor_OT_MuteShapes,
]