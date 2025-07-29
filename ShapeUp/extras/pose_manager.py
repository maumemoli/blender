import bpy


class MyUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        pass


class MyPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "My Category"
    bl_label = "My UI"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        row = col.split(factor=0.75)

        row.template_list("MyUIList", "", context.scene, "my_list", context.scene, "my_list_index", rows=10)
        col = row.column(align=False)
        col.operator("my_operator.hello", text="Add Pose")
        col.operator("my_operator.hello", text="Set Pose")
        col.operator("my_operator.hello", text="Remove Pose")


class MyOperator(bpy.types.Operator):
    bl_idname = "my_operator.hello"
    bl_label = "Hello"

    def execute(self, context):
        print("hello")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MyUIList)
    bpy.utils.register_class(MyPanel)
    bpy.utils.register_class(MyOperator)
    bpy.types.Scene.my_list = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.Scene.my_list_index = bpy.props.IntProperty(default=-1)


def unregister():
    bpy.utils.unregister_class(MyUIList)
    bpy.utils.unregister_class(MyPanel)
    bpy.utils.unregister_class(MyOperator)
    del bpy.types.Scene.my_list
    del bpy.types.Scene.my_list_index


if __name__ == "__main__":
    register()