bl_info = {
    "name": "UV Transfer Tools",
    "author": "Maurizio Memoli",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "UV Editor > Sidebar > Example Panel",
    "description": "Adds a button to the UV Editor",
    "category": "UV",
}

import bpy
import bmesh
import os
from mathutils import Vector

class UVToolsPanel(bpy.types.Panel):
    """Creates a Panel in the UV Editor"""
    bl_label = "UV Tools"
    bl_idname = "UV_PT_uv_tools_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Transfer Tools"

    def draw(self, context):
        layout = self.layout
        layout.label(text="UV Tools Panel")
        layout.operator("uv.align_seams", text="Snap Seams")


class UVAlignSeams(bpy.types.Operator):
    """Aligh the seams of two meshes"""
    bl_idname = "uv.align_seams"
    bl_label = "Align Seams"

    def __init__(self):
        self.source_bmesh = None
        self.active_bmesh = None
        self.current_bmesh = None
        self.active_uv_layer = None
        self.source_uv_layer = None


    def execute(self, context):
        # Get the list of selected objects
        selected_objects = bpy.context.selected_objects
        selected_objects = [x for x in selected_objects if x.type == "MESH"]
        if len(selected_objects) != 2:
            # display an error that meshes are not selected
            self.report({'ERROR'}, "Please select two meshes")
            return {'CANCELLED'}
        active_object = bpy.context.active_object
        selected_objects.remove(active_object)
        source_object = selected_objects[0]
        self.source_bmesh = bmesh.from_edit_mesh(source_object.data)
        self.active_bmesh = bmesh.from_edit_mesh(active_object.data)

        self.active_uv_layer = self.active_bmesh.loops.layers.uv.active
        self.source_uv_layer = self.source_bmesh.loops.layers.uv.active
        # getting the active object selected edges
        active_edges = self.get_selected_uv_loops(self.active_bmesh, self.active_uv_layer)
        self.get_face_loop_sequences(active_edges, self.active_uv_layer)


        return {'FINISHED'}

    @staticmethod
    def get_selected_loops(faces):
        """
        get the selected loops from a set of faces checking if the edges are selected
        :param faces: list of faces
        :return: list of loops
        """
        loops = list()
        for face in faces:
            selected_edge = [e for e in face.edges if e.select]
            if not selected_edge:
                continue
            selected_edge_verts = selected_edge[0].verts
            selected_loops = list()
            for loop in face.loops:
                if loop.vert in selected_edge_verts:
                    selected_loops.append(loop)
            loops.append(selected_loops)
        return loops


    @staticmethod
    def get_edges_parametric_lenght(edges):
        
        complessive_length = 0.0
        length_points = [0.0]
        for edge in edges:
            complessive_length += edge.calc_length()
            length_points.append(complessive_length)
        for i, point in enumerate(length_points):
            length_points[i] = point / complessive_length

        return length_points


    @staticmethod
    def get_selected_uv_loops(bm, uv_layer):
        if not uv_layer:
            return []

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        # getting the active edge
        selected_edges = list()
        active_edge = bm.select_history.active if isinstance(bm.select_history.active, bmesh.types.BMEdge) else None

        for edge in bm.edges:
            if edge.select and edge != active_edge:
                selected_edges.append(edge)

        # getting the loop sequence starting from the active
        ordered_edge_loop = list()
        next_edge = active_edge
        visited = set()
        counter = 0
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

        return ordered_edge_loop

    @staticmethod
    def get_face_loop_sequences(edges, uv_layer):
        faces_top = list()
        faces_bottom = list()

        linked_faces = edges[0].link_faces

        previous_top = None
        previous_bottom = None

        if len(linked_faces) == 1:
            previous_top = linked_faces[0]
            faces_top.append(linked_faces[0])

        elif len(linked_faces) == 2:
            previous_top, previous_bottom = linked_faces
            faces_top.append(linked_faces[0])
            faces_bottom.append(linked_faces[1])
        else:
            return faces_top, faces_bottom

        for edge in edges[1:]:
            # getting the faces connected
            for face in edge.link_faces:
                linked_faces = list()
                for face_edge in face.edges:
                    for linked_face in face_edge.link_faces:
                        if linked_face not in edge.link_faces:
                            if linked_face not in linked_faces:
                                linked_faces.append(linked_face)

                if previous_top in linked_faces:
                    previous_top = face
                    faces_top.append(face)
                elif previous_bottom in linked_faces:
                    previous_bottom = face
                    faces_bottom.append(face)

        if faces_top:
            top_loops = UVAlignSeams.get_selected_loops(faces_top)
            for loop_edge in top_loops:
                for loop in loop_edge:
                    loop[uv_layer].select = True

        print("TOP=======")
        for face in faces_top:
            print("Face: {0}".format(face.index))

        print("Bottom=======")
        for face in faces_bottom:
            print("Face: {0}".format(face.index))

def register():
    bpy.utils.register_class(UVToolsPanel)
    bpy.utils.register_class(UVAlignSeams)


def unregister():
    bpy.utils.unregister_class(UVToolsPanel)
    bpy.utils.unregister_class(UVAlignSeams)


if __name__ == "__main__":
    register()


