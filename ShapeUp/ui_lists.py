import bpy

from . import (helpers)

if "bpy" in locals():
    import importlib
    importlib.reload(helpers)
else:
    from . import (helpers)

from .utils.shape_selection import ShapeSelection
from bpy.props import EnumProperty, BoolProperty, StringProperty, IntProperty


shape_select = ShapeSelection()


def register_properties():
    bpy.types.Object.shape_auto_refresh = BoolProperty(
        name="update flag", default=False)

    bpy.types.Object.shape_full_list = BoolProperty(
        name="full list flag", default=False)

    bpy.types.Object.shape_show_value = BoolProperty(
        name="shape value flag", default=False)



class MESH_UL_ShapekeysList(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data,
                  _active_propname, index):

        obj = active_data

        key_block = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.85, align=False)
            split.prop(
                key_block, "name", text="", emboss=False)
            row = split.row(align=True)
            if key_block.mute or (obj.mode == 'EDIT'
                                  and not (obj.use_shape_key_edit_mode
                                           and obj.type == 'MESH')):
                row.active = False
            if not item.id_data.use_relative:
                row.prop(key_block, "frame", text="", emboss=False)
            elif index > 0:
                row.prop(key_block, "value", text="", emboss=False)
            else:
                row.label(text="")
            # row.prop(key_block, "mute", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def filter_items(self, context, data, propname):

        col = getattr(data, propname)
        filter_name = self.filter_name.lower()

        obj = context.object

        shapes_store = []

        if obj.shape_full_list:
            shapes_store = shape_select.shape_key_list_all()
            #helpers.filteredshapes = shapes_store
        else:
            shapes_store = shape_select.shape_key_list_hero()
            #helpers.filteredshapes = shapes_store

        flt_flags = [
            self.bitflag_filter_item if item.name in shapes_store else 0
            for i, item in enumerate(col, 1)
        ]

        if self.use_filter_sort_alpha:
            flt_neworder = [
                x[1] for x in sorted(
                    zip([
                        x[0] for x in sorted(
                            enumerate(col), key=lambda x: x[1].name)
                    ], range(len(col))))
            ]
        else:
            flt_neworder = []

        return flt_flags, flt_neworder


class MESH_UL_ShapekeysConnectedList(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, active_data,
                  _active_propname, index, flt_flag):

        key_block = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            if _context.object.shape_show_value:
                split = layout.split(factor=0.72, align=True)
                split.prop(
                    key_block, "name", text="", emboss=False, expand=True)
                row = split.row(align=False)
                row.prop(key_block, "value", text="", emboss=False)
                row.prop(key_block, "mute", text="", emboss=False, expand=True)
            else:
                split = layout.split(factor=0.925, align=True)
                split.prop(
                    key_block, "name", text="", emboss=False,  expand=True)
                row = split.row(align=False)
                row.prop(key_block, "mute", text="", emboss=False, expand=True)



        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def filter_items(self, context, data, propname):

        col = getattr(data, propname)
        filter_name = self.filter_name.lower()

        obj = context.object
        ob = bpy.context.active_object
        active_shape_key = obj.active_shape_key

        shapes_store = []

        if len(active_shape_key.name.split('_')) == 1:
            shapes_store = shape_select.shape_key_list_upstream()
            helpers.filteredshapes = shapes_store
        else:

            shapes_store = helpers.filteredshapes


        flt_flags = [
            self.bitflag_filter_item if item.name in shapes_store else 0
            for i, item in enumerate(col, 1)
        ]

        if self.use_filter_sort_alpha:
            flt_neworder = [
                x[1] for x in sorted(
                    zip([
                        x[0] for x in sorted(
                            enumerate(col), key=lambda x: x[1].name)
                    ], range(len(col))))
            ]
        else:
            flt_neworder = []


        return flt_flags, flt_neworder


class ShapeEditor_OT_UpdateFilter(bpy.types.Operator):
    """Updates the filtered shapekeys"""
    bl_idname = "shapeeditor.updatefilter"
    bl_label = "Update Shapekeys filter"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):


        helpers.filteredshapes = shape_select.shape_key_list_upstream()


        return {'FINISHED'}


registry = [
    MESH_UL_ShapekeysList,
    MESH_UL_ShapekeysConnectedList,
    ShapeEditor_OT_UpdateFilter,
]


def register():
    register_properties()


def unregister():
    pass
