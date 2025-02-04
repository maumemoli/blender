import bpy
import bmesh
import os
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from dataclasses import dataclass
import sys
# Get the directory of the current script (the add-on folder)
import os
script_dir = os.path.dirname(os.path.realpath(__file__))
import sys
sys.path.append(script_dir)
print("*****RELOADED*****")
from importlib import reload
import edgeSequence
reload(edgeSequence)


from edgeSequence import EdgeSequence

bl_info = {
    "name": "UV Transfer Tools",
    "author": "Maurizio Memoli",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "UV Editor > Sidebar > UV Tools",
    "description": "Adds a button to the UV Editor",
    "category": "UV",
}

class UVToolsPanel(bpy.types.Panel):
    """Creates a Panel in the UV Editor"""
    bl_label = "UV Tools"
    bl_idname = "UV_PT_uv_tools_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Transfer Tools"

    def draw(self, context):
        layout = self.layout
        layout.label(text="UV Tools Panel")
        layout.operator("uv.align_seams", text="Snap Seams")


class UVAlignSeams(bpy.types.Operator):
    """Align the active object's selected edges UVs to the second selected object UVs edges."""
    bl_idname = "uv.align_seams"
    bl_label = "Align Seams"

    def __init__(self):

        self.source_obj = None
        self.active_obj = None

        self.source_edge_sequence = None
        self.active_edge_sequence = None
        # draw handlers
        self._draw_handler = None

        self.start_edges_batch = None
        self.edges_batch = None
        self.inside_faces_batch = None
        self.outside_faces_batch = None

        self.edges_shader = None
        self.start_edges_shader = None
        self.inside_face_shader = None
        self.outside_face_shader = None

        # This is to draw the shaders
        self.selected_edges = []
        self.outside_face_shader_tris = []
        self.inside_face_shader_tris = []
        # colors
        edge_color = bpy.context.preferences.themes[0].view_3d.edge_mode_select
        self.selected_edge_color = (edge_color.r, edge_color.g, edge_color.b, 1.0)
        start_color = bpy.context.preferences.themes[0].view_3d.editmesh_active
        self.start_edge_color = (start_color[0], start_color[1], start_color[2], start_color[3])
        face_front = bpy.context.preferences.themes[0].view_3d.face_front
        self.inside_face_color = (face_front[0], face_front[1], face_front[2], face_front[3])
        face_back = bpy.context.preferences.themes[0].view_3d.face_back
        self.outside_face_color = (face_back[0], face_back[1], face_back[2], face_back[3])

        self.invert_inside = False

        self.x_key_short_cut = None

    @classmethod
    def poll(cls, context):
        # Enable the operator only if the object is in Edit Mode
        selected_meshes = [x for x in bpy.context.selected_objects if x.type == "MESH"]
        return context.object is not None and context.object.mode == 'EDIT' and len(selected_meshes) == 2

    def initialize_meshes(self):
        self.source_obj = None
        self.active_obj = None
        active_obj = bpy.context.active_object
        other_meshes = [x for x in bpy.context.selected_objects if x.type == "MESH" and x != active_obj]
        if len(other_meshes) == 1:
            self.source_obj = other_meshes[0]
            self.active_obj = active_obj

        if self.source_obj and self.active_obj:
            self.source_edge_sequence = EdgeSequence(self.source_obj)
            print("=======================================")
            print(self.source_edge_sequence.parametric_coordinates)
            self.active_edge_sequence = EdgeSequence(self.active_obj)
            self.active_edge_sequence.pin_outer_loops()
            self.active_edge_sequence.pin_inner_loops()

    def invoke(self, context, event):

        if context.area.type == 'VIEW_3D':
            # Get selected edges and linked faces from the active object
            self.initialize_meshes()

            if not self.source_obj or not self.active_obj:
                self.report({'WARNING'}, "Select two meshes")
                return {'CANCELLED'}

            self.inside_face_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            self.outside_face_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            self.edges_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            self.start_edges_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            self.update_selection()

            # Add a draw handler
            self.register_draw_handler(context)

            return {'RUNNING_MODAL'}

        self.report({'WARNING'}, "View3D not found or no mesh selected")
        return {'CANCELLED'}

    def modal(self, context, event):
        if event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            # Exit modal when Right Mouse is pressed
            self.unregister_draw_handler(context)
            self.report({'INFO'}, "User cancelled the operation.")
            context.area.tag_redraw()
            return {'CANCELLED'}

        if event.type in ['LEFTMOUSE', 'RET', 'NUMPAD_ENTER'] and event.value == 'PRESS':
            # Exit modal when Right Mouse is pressed
            self.report({'INFO'}, "Exiting modal operator.")
            self.unregister_draw_handler(context)
            # redraw the view
            context.area.tag_redraw()
            self.execute(context)
            return {'FINISHED'}

        # Allow navigation
        if event.type in ['MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MOUSEMOVE']:
            return {'PASS_THROUGH'}

        # Redraw if selection changes
        obj = context.active_object

        if not (obj and obj.type == 'MESH' and obj.mode == 'EDIT'):
            self.unregister_draw_handler(context)
            self.report({'INFO'}, "Exited edit mode, terminating modal operator.")
            return {'FINISHED'}

        if event.type in ["SPACE", "TAB"] and event.value == 'PRESS':
            print("PRESSING SPACE OR TAB")
            self.invert_inside = not self.invert_inside

        if obj and obj.type == 'MESH':
            self.update_selection()

        # Allow panning and rotating the viewport
        return {'RUNNING_MODAL'}

    def update_selection(self):
        # update meshes
        self.active_edge_sequence.obj.data.update()
        self.source_edge_sequence.obj.data.update()

        inner_faces_co = self.source_edge_sequence.inner_faces_batch_coords + self.active_edge_sequence.inner_faces_batch_coords
        outer_faces_co = self.source_edge_sequence.outer_faces_batch_coords + self.active_edge_sequence.outer_faces_batch_coords
        if not self.source_edge_sequence.is_border:
            if self.invert_inside != self.source_edge_sequence.inverted:
                self.source_edge_sequence.inverted = self.invert_inside
                self.source_edge_sequence.load()
        self.inside_faces_batch = self.create_face_batch(inner_faces_co, self.inside_face_shader)
        self.outside_faces_batch = self.create_face_batch(outer_faces_co, self.outside_face_shader)
        edges_co = self.source_edge_sequence.edges_batch_coords
        edges_co.extend(self.active_edge_sequence.edges_batch_coords)
        self.edges_batch = batch_for_shader(self.edges_shader, 'LINES', {"pos": edges_co})

        start_edges_co = list(self.source_edge_sequence.active_edge_batch_coords)
        start_edges_co.extend(self.active_edge_sequence.active_edge_batch_coords)

        self.start_edges_batch = batch_for_shader(self.start_edges_shader, 'LINES', {"pos": start_edges_co})

    def draw_callback(self, context):
        if self.inside_faces_batch:
            self.inside_face_shader.bind()
            self.inside_face_shader.uniform_float("color", self.inside_face_color)
            self.inside_faces_batch.draw(self.inside_face_shader)

        if self.outside_faces_batch:
            self.outside_face_shader.bind()
            self.outside_face_shader.uniform_float("color", self.outside_face_color)
            self.outside_faces_batch.draw(self.outside_face_shader)

        if self.edges_batch:
            self.edges_shader.bind()
            self.edges_shader.uniform_float("color", self.selected_edge_color)
            self.edges_batch.draw(self.edges_shader)

        if self.start_edges_batch:
            self.start_edges_shader.bind()
            self.start_edges_shader.uniform_float("color", self.start_edge_color)
            self.start_edges_batch.draw(self.start_edges_shader)

    def register_draw_handler(self, context):
        self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback, (context,), 'WINDOW', 'POST_VIEW')

        # Set the header text
        context.area.header_text_set("UV Seams: Press Right Mouse or Escape to Exit\r Enter to confirm selection. \r TAB or Space bar to invert the inside faces")

        context.window_manager.modal_handler_add(self)

    def unregister_draw_handler(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')
        context.area.header_text_set(None)  # Clear the header text
        self._draw_handler = None

    def create_face_batch(self, faces, shader):
        # Create a batch for the linked faces
        vertices = []
        indices = []
        index_offset = 0
        for face in faces:
            vertices.extend(face)
            # Create triangle indices for each face
            for i in range(1, len(face) - 1):
                indices.append((index_offset, index_offset + i, index_offset + i + 1))
            index_offset += len(face)
        return batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

    # modal end
    def execute(self, context):
        # Get the list of selected objects
        inner_uv_coords = []
        outer_uv_coords = []
        if self.source_edge_sequence.inner_uv_coords:
            inner_uv_coords = self.source_edge_sequence.inner_uv_coords
            print("Inner UV coords found")

        if self.source_edge_sequence.outer_uv_coords:
            outer_uv_coords = self.source_edge_sequence.outer_uv_coords
            print("Outer UV coords found")

        if inner_uv_coords:
            transferred_inner_uv_coords = self.active_edge_sequence.transfer_uv_coordinates(inner_uv_coords)
            print("====================================")
            print("Active  inner loops: ")
            for loop in self.active_edge_sequence.inner_loops:
                print("Loops:")
                for subloop in loop:
                    print(subloop.index)
            self.active_edge_sequence.set_inner_loops_uv_coordinates(transferred_inner_uv_coords)
            print(inner_uv_coords)
        if outer_uv_coords:
            transferred_outer_uv_coords = self.active_edge_sequence.transfer_uv_coordinates(outer_uv_coords)
            print("====================================")
            print("Active  outer loops: ")
            for loop in self.active_edge_sequence.outer_loops:
                print("Loops: ")
                for subloop in loop:
                    print(subloop.index)
            self.active_edge_sequence.set_outer_loops_uv_coordinates(transferred_outer_uv_coords)
            print(outer_uv_coords)
        else:
            print("No outer coordinates to transfer")

        return {'FINISHED'}

    @staticmethod
    def get_edges_parametric_length(edges):
        total_length = 0.0
        length_points = [0.0]
        for edge in edges:
            total_length += edge.calc_length()
            length_points.append(total_length)
        for i, point in enumerate(length_points):
            length_points[i] = point / total_length

        return length_points

    def get_inner_faces(self, edges_ids, obj, bm=None):
        """
        Get the inner faces of the object.
        :param obj: object
        :param bm: bmesh object
        :return: list of inner faces
        """
        if not edges_ids or len(edges_ids) ==0:
            return []

        free_bmesh = False
        if not bm:
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
                free_bmesh = True
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        inner_faces = list()
        edges = [bm.edges[edge_id] for edge_id in edges_ids]
        for edge in edges:
            edge.link_loops[0].face = True

    def get_selected_edges(self, obj, bm=None):
        """
        Get the selected edges from the 3d view and order the edge loops starting from the active edge.
        :param bm: bmesh object
        :return: list of ordered edge loops
        """
        free_bmesh = False
        if not bm: # create a bmesh in case it is not provided
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
                free_bmesh = True
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        # getting the active edge
        selected_edges = list()
        active_edge = bm.select_history.active if isinstance(bm.select_history.active, bmesh.types.BMEdge) else None
        if not active_edge:
            if free_bmesh:
                bm.free()
            return []
        for edge in bm.edges:
            if edge.select and edge != active_edge:
                selected_edges.append(edge)

        for edge in selected_edges:
            if len(edge.link_faces) == 0:
                if free_bmesh:
                    bm.free()
                self.report({'ERROR'}, "The selected edges are not part of a face")
                return []
            if len(edge.link_faces) > 2:
                if free_bmesh:
                    bm.free()
                self.report({'ERROR'}, "The selected edges are part of more than two faces")
                return []

        # getting the loop sequence starting from the active
        ordered_edge_loop = list()
        next_edge = active_edge
        visited = set()
        while next_edge:
            ordered_edge_loop.append(next_edge)
            visited.add(next_edge)
            linked_edges = list()
            for vert in next_edge.verts:
                for edge in vert.link_edges:
                    if edge not in visited and edge.select:
                        if edge not in linked_edges:
                            linked_edges.append(edge)

            if linked_edges:
                next_edge = linked_edges[0]
            else:
                next_edge = None
        # we are getting only the indexes
        ordered_edge_loop = [edge.index for edge in ordered_edge_loop]
        if free_bmesh:
            bm.free()
        return ordered_edge_loop

    @staticmethod
    def is_mesh_edge_loop_closed(edges):
        """
        Check if the loop is closed
        :param edges: list of edges
        :return: True if the loop is closed
        """
        if not edges:
            return False
        if edges[0].verts[0] == edges[-1].verts[1]:
            return True
        return False

    @staticmethod
    def get_vertices_sequence_from_edges(edges):
        """
        Get the vertices sequence from a list of edges
        :param edges: list of edges
        :return: list of vertices
        """
        if not edges:
            return []
        verts = list()
        verts.append(edges[0].verts[0])
        for edge in edges:
            verts.append(edge.verts[1])
        return verts

    @staticmethod
    def get_uv_coordinates_from_edges(edges_ids, obj, faces, uv_layer, bm=None):
        """
        Get the uv coordinates from a loop
        :param edges_ids: list of edges indexes
        :param obj: object
        :param faces: list of faces
        :param uv_layer: uv layer name
        :param bm: bmesh object
        :return: list of uv coordinates
        """
        if len(edges_ids) == 0 or len(faces) == 0:
            return []
        # getting the bmesh object
        free_bmesh = False
        if not bm:
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
                free_bmesh = True
            else:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # getting the UV layer
        uv_layer = bm.loops.layers.uv.get(uv_layer)

        verts =list()
        edges = [bm.edges[i] for i in edges_ids]
        # let's order the vertices
        for i in range(len(edges)):
            edge = edges[i]
            next_edge = edges[i+1] if i < len(edges)-1 else edges[0]
            edge_verts = [v for v in edge.verts]
            # reverse the vertices if the next edge is not connected to the last vertex
            if edge_verts[1] not in next_edge.verts:
                edge_verts = edge_verts[::-1]
            for v in edge_verts:
                if v not in verts:
                    verts.append(v)

        # getting the uv coordinates
        uv_coordinates = list()
        for vert in verts:
            for loop in vert.link_loops:
                if loop.face.index in faces:
                    uv = loop[uv_layer].uv
                    if uv not in uv_coordinates:
                        uv_coordinates.append(uv)
        if free_bmesh:
            bm.free()
        return uv_coordinates

    def is_edge_sequence_valid(self, edges_ids, obj):
        """
        Check if the edge sequence is valid
        :param edges: list of edges
        :param obj: The Mesh object
        :return: True if the edge sequence is valid
        """
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        if edges_ids is None or len(edges_ids) == 0:
            message = "No edges selected on Mesh: {0}".format(obj.name)
            self.report({'ERROR'}, message)
            return False

        edges = [bm.edges[i] for i in edges_ids]
        # check if the selected edges are all
        if not all(e.is_boundary for e in edges) or not all(e.is_contiguous for e in edges):
            message = "The selected edges on Mesh: {0} are not all boundary or contiguous edges".format(obj.name)
            self.report({'ERROR'}, message)
            return False

        return True




def register():
    bpy.utils.register_class(UVToolsPanel)
    bpy.utils.register_class(UVAlignSeams)


def unregister():
    bpy.utils.unregister_class(UVToolsPanel)
    bpy.utils.unregister_class(UVAlignSeams)


if __name__ == "__main__":
    register()

