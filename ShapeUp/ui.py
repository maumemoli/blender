import bpy
from .utils.shape_processing import ShapePrecessing
from .utils.shape_selection import ShapeSelection

owner = None
subscribe_to = (bpy.types.Object, "active_shape_key_index")
shapeselect  = ShapeSelection()
shapeprocess = ShapePrecessing()

def set_active_shape_key(*args):
    obj = bpy.context.active_object
    active_shape_key = obj.active_shape_key
    # Switch bool property (is auto refresh) to try and disable auto
    # filtering in list is shapename split len > 1

    shapes_values = shapeselect.shape_name_value_dict([active_shape_key.name])
    shapeprocess.set_shape_key_values(shapes_values)

def sub_msg_bus():
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=owner,
        args=(1, 2, 3),
        notify=set_active_shape_key
    )

def clr_msg_bus():
    bpy.msgbus.clear_by_owner(owner)

def upd_mbus_cb(self, context):
    print(f'msg_bus bool: {self.mbus}')
    if context.window_manager.mbus:
        sub_msg_bus()
    else:
        clr_msg_bus()
    return None



def register_properties():
    bpy.types.Object.shape_auto_refresh = bpy.props.BoolProperty(
        name="update flag", default=False)

    bpy.types.Object.shape_full_list = bpy.props.BoolProperty(
        name="full list flag", default=False)

    bpy.types.Object.shape_show_value = bpy.props.BoolProperty(
        name="shape value flag", default=False)

    bpy.types.Object.shape_show_frozen = bpy.props.BoolProperty(
        name="shape show frozen", default=False)


class PoseShapeKeyTarget(bpy.types.PropertyGroup):
    expression_type: bpy.props.EnumProperty(
        name="Expressions", description="expressions to choose from",
        items=[('OP1', "Linear (i.e. eyes)", ""),
               ('OP2', "Curved (i.e. no clue)", ""),
               ('OP3', "Smooth (i.e. lips)", "")],
        default='OP1'
    )
    # A*B if A>0 and B>0 is common in maya/vfx. works alright in many cases, especially eyes.
    # (A*B)**0.5 is an alternative, more suitable for mid ranges, but producing odd jumps in low ranges.
    # sin(pi/2*A)*sin(pi/2*B) works great for lip shapes, wobbles for eyes.

    keyline_path : bpy.props.StringProperty(
        name="Keyline Shader Path", default="//", subtype='FILE_PATH')

    advanced_mode : bpy.props.BoolProperty(
        name="advanced mode", default=True)

    smart_name : bpy.props.BoolProperty(
        name="smart name", default=True)

    neutralize_names : bpy.props.StringProperty(
        name="neutralize names", default="")

    neutralize_iterations : bpy.props.IntProperty(
        name="neutralize iteration", default=2)

    delete_names: bpy.props.StringProperty(
        name="delete names", default="")

    delete_iterations: bpy.props.IntProperty(
        name="delete iteration", default=2)

    mute_names: bpy.props.StringProperty(
        name="mute names", default="")

    mute_iterations: bpy.props.IntProperty(
        name="mute iteration", default=2)

    set_expression_names: bpy.props.StringProperty(
        name="set expression names", default="")

    quickset: bpy.props.BoolProperty(
        name="quickset", default=False)

    mute_inbetweens_only: bpy.props.BoolProperty(
        name="mute inbetweens only", default=False)

    mute_invert: bpy.props.BoolProperty(
        name="mute invert", default=False)




class SHAPEPANEL_PT_ShapeUpPanelTransfer(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Transfer Shapes"
    bl_category = "ShapeUp"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Transfer Panel")


class SHAPEPANEL_PT_ShapeUpPanelMain(SHAPEPANEL_PT_ShapeUpPanelTransfer, bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = "SHAPEPANEL_PT_ShapeEditor_Panel_1"
    bl_label = "ShapeUp"

    @classmethod
    def poll(cls, context):
        return context.active_object != None
        # if context.object is not None:
        #     try:
        #         z = len(context.object.data.shape_keys.key_blocks)
        #         return True
        #     except Exception:
        #         return False
        #
        # return False

    def draw(self, context):

        layout = self.layout
        obj = context.object
        wmngr = context.window_manager
        key = obj.data.shape_keys
        # kb = obj.active_shape_key
        # kb_name = kb.name

        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 2.0

        row.operator("shapeeditor.createcopy", text="Copy Mesh")

        sub = row.row(align=True)
        sub.scale_x = 2.0
        sub.operator("shapeeditor.updateshape", text="Update Shape")

        row.operator("export_test.some_data", text="Export All")

        row = box.row(align=True)
        row.scale_y = 1.1

        row.operator("shapeup.gridalign", text="Grid Align")
        row.operator("shapeeditor.createcopy", text="Live Copy")
        row.operator("shapeeditor.updateintermediate", text="Update Base")
        row.operator("export_test.build_mimic", text="Build Mimic")

        row = layout.row()

        row.prop(obj, "shape_full_list", text="Full List")
        row.prop(wmngr, "mbus", text="Quickset")
        row.prop(obj, "shape_show_value", text="Show Value")
        row.prop(obj, "smart_name", text="Smart Name")
        row.prop(obj, "advanced_mode", text="Advanced")

        box = layout.box()
        col = box.column()
        row = col.split(factor = 0.455)

        row.template_list("MESH_UL_ShapekeysList", "", key, "key_blocks", obj,
                          "active_shape_key_index", rows=20)

        row.template_list("MESH_UL_ShapekeysConnectedList", "Connected", key,
                          "key_blocks", obj, "active_shape_key_index", rows=20)
        box = layout.box()
        row = box.row(align=True)

        row.operator("shapeeditor.zeroall", text="Zero All")
        row.operator("object.shape_key_add", text="New Shape").from_mix = False
        row.operator("shapeeditor.unmuteall", text="UnMute All")
        #row.operator("object.shape_key_remove", text="UnMute All").all = False
        row.operator("shapeeditor.unmuteall", text="Freeze")
        row.operator("shapeeditor.unmuteall", text="UnFreeze All")


class SHAPEPANEL_PT_ShapeUpPanelExtras(SHAPEPANEL_PT_ShapeUpPanelTransfer, bpy.types.Panel):
    bl_parent_id = "SHAPEPANEL_PT_ShapeEditor_Panel_1"
    bl_label = "Extras"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        # Neutralize Combo


        if context.object.advanced_mode:
            box = layout.box()
            row = box.row(align=False)
            row.scale_y = 1.1

            row.operator("shapeeditor.zeroall", text="Neutralize Combo")
            row.operator("shapeeditor.zeroall", text="Neutralize <...")
            row.prop(obj, "neutralize_iterations", text="Level <")
            sub = row.row(align=True)
            sub.scale_x = 1.5
            sub.prop(obj, "neutralize_names", text="By Name")

            # Delete Shapes
            row = box.row(align=False)
            row.scale_y = 1.1

            row.operator("shapeeditor.deleteshape", text="Delete Shape")
            row.operator("shapeeditor.deletecombos", text="Delete Combos <...")
            row.prop(obj, "delete_iterations", text="Level <")
            sub = row.row(align=True)
            sub.scale_x = 1.5
            sub.prop(obj, "delete_names", text="By Name")



            # Set Expression
            row = box.row(align=False)
            row.scale_y = 1.1

            row.operator("shapeeditor.zeroall", text="Set Expression")
            row.operator("shapeeditor.zeroall", text="Set All")
            row.prop(obj, "expression_type", text="")
            sub = row.row(align=True)
            sub.scale_x = 1.5
            sub.prop(obj, "set_expression_names", text="By Name")


            # Mute Shapes
            row = box.row(align=False)
            row.scale_y = 1.1

            row.operator("shapeeditor.muteshapes", text="Mute Shapes")
            row.prop(obj, "mute_iterations", text="Level <")
            row.prop(obj, "mute_inbetweens_only", text="Inbetweens Only")
            row.prop(obj, "mute_invert", text="", icon='SELECT_SUBTRACT')

            sub = row.row(align=True)
            sub.scale_x = 1.5
            sub.prop(obj, "mute_names", text="By Name")

        box = layout.box()

        row = box.row(align=False)
        row.operator("shapeup.keylineshader", text="Keyline Shader")

        sub = row.row(align=False)
        sub.scale_x = 1.5
        sub.prop(obj, "keyline_path", text="Keyline Path")

        row = box.row(align=True)
        row.operator("shapeup.createfacegroups", text="Add Face Groups")
        row.operator("animate.qc", text="Shape Check Render")

        box = layout.box()
        row = box.row(align=True)

        row.operator("animate.shapekey10", text="Key -> 10")
        row.operator("animate.shapekey20", text="Key <-> 20")
        row.operator("animate.clearkeyframesselected", text="Delete Keys")
        row.operator("animate.clearkeyframesall", text="Delete All Keys")

        if context.object.advanced_mode:
            row = box.row(align=True)

            row.operator("shapeeditor.zeroall", text="Split Combined")
            row.operator("shapeeditor.zeroall", text="Split Selected")
            row.operator("shapeeditor.zeroall", text="Combine Splits")
            row.operator("shapeeditor.zeroall", text="Tidy Names")

            box = layout.box()
            row = box.row(align=True)

            row.operator("shapeeditor.zeroall", text="Create Meniscus")
            row.operator("shapeeditor.zeroall", text="Eye/Teeth Import")
            row.operator("shapeeditor.zeroall", text="Jaw Deltas")
            row.operator("shapeeditor.updatedecomposedshape", text="Update Composed")
            row.operator("export.decomposed_shapes", text="Export Decomposed")


class SHAPEPANEL_PT_ShapeUpPanelPose(SHAPEPANEL_PT_ShapeUpPanelTransfer, bpy.types.Panel):
    bl_parent_id = "SHAPEPANEL_PT_ShapeEditor_Panel_1"
    bl_label = "Pose Editor"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Placeholder for the transfer shapes panel.")


class SHAPEPANEL_PT_ShapeUpPanelAnimation(SHAPEPANEL_PT_ShapeUpPanelTransfer, bpy.types.Panel):
    bl_parent_id = "SHAPEPANEL_PT_ShapeEditor_Panel_1"
    bl_label = "Animation Editor"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Placeholder for the transfer shapes panel.")


registry = [
    PoseShapeKeyTarget,
    #SHAPEPANEL_PT_ShapeUpPanelTransfer,
    SHAPEPANEL_PT_ShapeUpPanelMain,
    SHAPEPANEL_PT_ShapeUpPanelExtras,
    SHAPEPANEL_PT_ShapeUpPanelPose,
    SHAPEPANEL_PT_ShapeUpPanelAnimation,
]


def register():
    bpy.types.Object.expression_type = bpy.props.EnumProperty(
        name="Expressions", description= "expressions to choose from",
        items= [('OP1', "A*B if A>0 and B>0", ""),
                ('OP2', "(A*B)**0.5", ""),
                ('OP3', "sin(pi/2*A)*sin(pi/2*B)", "")],
        default='OP1'
    )

    bpy.types.Object.keyline_path = bpy.props.StringProperty(
        name="Keyline Shader Path", default="//", subtype='FILE_PATH')

    bpy.types.Object.advanced_mode = bpy.props.BoolProperty(
        name="advanced mode", default=True)

    bpy.types.Object.smart_name = bpy.props.BoolProperty(
        name="smart name", default=True)

    bpy.types.Object.neutralize_names = bpy.props.StringProperty(
        name="neutralize names", default="")

    bpy.types.Object.neutralize_iterations = bpy.props.IntProperty(
        name="neutralize iteration", default=2)

    bpy.types.Object.delete_names = bpy.props.StringProperty(
        name="delete names", default="")

    bpy.types.Object.delete_iterations = bpy.props.IntProperty(
        name="delete iteration", default=2)

    bpy.types.Object.mute_names = bpy.props.StringProperty(
        name="mute names", default="")

    bpy.types.Object.mute_iterations = bpy.props.IntProperty(
        name="mute iteration", default=2)

    bpy.types.Object.set_expression_names = bpy.props.StringProperty(
        name="set expression names", default="")

    bpy.types.Object.quickset = bpy.props.BoolProperty(
        name="quickset", default=False)

    bpy.types.WindowManager.mbus = bpy.props.BoolProperty(
        name="mbus",
        description="Toggle message bus subscription",
        default=False,
        update=upd_mbus_cb,
    )

    bpy.types.Object.mute_inbetweens_only = bpy.props.BoolProperty(
        name="mute inbetweens only", default=False)

    bpy.types.Object.mute_invert = bpy.props.BoolProperty(
        name="mute invert", default=False)


def unregister():
    del bpy.types.Object.expression_type
    del bpy.types.Object.keyline_path
    del bpy.types.Object.advanced_mode
    del bpy.types.Object.smart_name
    del bpy.types.Object.neutralize_names
    del bpy.types.Object.neutralize_iterations
    del bpy.types.Object.delete_names
    del bpy.types.Object.delete_iterations
    del bpy.types.Object.mute_names
    del bpy.types.Object.mute_iterations
    del bpy.types.Object.set_expression_names
    del bpy.types.Object.quickset
    del bpy.types.WindowManager.mbus
    del bpy.types.Object.mute_inbetweens_only
    del bpy.types.Object.mute_invert


