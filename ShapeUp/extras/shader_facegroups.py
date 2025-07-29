import bpy

class Extras:
    def __init__(self):
        pass

    def create_face_sets_from_vertex_groups(self):
        obj = bpy.context.active_object

        # Iterate over the vertex groups
        for vg in obj.vertex_groups:
            # Enter edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            # Deselect all vertices
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_set_active(group=vg.name)
            # Select the vertices in the active vertex group
            bpy.ops.object.vertex_group_select()
            print(f"selected {vg}")
            # Exit edit mode
            bpy.ops.object.mode_set(mode='OBJECT')

            selected_vertices = [v.index for v in obj.data.vertices if v.select]
            print(f"Selected vertex IDs: {selected_vertices}")

            # Enter sculpt mode
            bpy.ops.sculpt.sculptmode_toggle()
            # Create a face set from the selected vertices
            bpy.ops.sculpt.face_sets_create(mode='SELECTION')
            # Exit sculpt mode
            bpy.ops.sculpt.sculptmode_toggle()

class ShapeEditor_OT_CreateFaceGroups(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "shapeup.createfacegroups"
    bl_label = "Create Face Groups"

    def execute(self, context):
        self.keyline_shader = Extras()

        self.keyline_shader.create_face_sets_from_vertex_groups()


        return {'FINISHED'}



registry = [
    ShapeEditor_OT_CreateFaceGroups,
]