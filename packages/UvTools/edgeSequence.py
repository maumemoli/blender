import bpy
import bmesh
import numpy as np
from mathutils import Vector
import math
import os

class EdgeSequence(object):
    def __init__(self, obj: bpy.types.Object):
        '''
        Constructor
        :param obj: The object Mesh whose selected edges are to be sequenced
        '''
        self.obj = obj
        self.mesh = obj.data
        self.inverted = False
        self.bm = None
        self.edges = []
        self.inverted_edges = []
        self.corner_edges = []
        self.uv_layer = None
        self.inner_faces = []
        self.outer_faces = []
        self.active_edge_batch_coords = []
        self.edges_batch_coords = []
        self.selected_edges_batch_coords = []
        self.inner_faces_batch_coords = []
        self.outer_faces_batch_coords = []
        self.deformed_verts_postion = []
        self.outline_faces_indices = []
        self.parametric_coordinates = []
        self.inner_loops = []
        self.outer_loops = []
        self.is_border = False
        self.inner_uv_coords = []
        self.outer_uv_coords = []
        self.original_loops_uv_coords = {}
        self.uv_border_edges = []
        self.offset_uv_coordinates_array = []
        self.load()
        self.store_uv_coords()

    # def get_uv_coordinates_array(self):
    #     # Get the active UV layer data
    #     uv_layer = self.obj.data.uv_layers.active.data
    #
    #     # Create an array to store UVs (2 floats per loop)
    #     uv_data = np.empty(len(uv_layer) * 2, dtype=np.float32)
    #
    #     # Use foreach_get to quickly extract UV coordinates
    #     uv_layer.foreach_get("uv", uv_data)
    #
    #     # Reshape into (N, 2) format for easier use
    #     uv_coords = uv_data.reshape(-1, 2)
    #
    #     # Print the first few UV coordinates
    #     self.uv_coordinates_array = uv_coords


    def store_uv_coords(self):
        if self.inner_loops:
            for loop_list in self.inner_loops:
                for loop in loop_list:
                    self.original_loops_uv_coords[loop.index] = loop[self.uv_layer].uv.copy()
        if self.outer_loops:
            for loop_list in self.outer_loops:
                for loop in loop_list:
                    self.original_loops_uv_coords[loop.index] = loop[self.uv_layer].uv.copy()

    def restore_uv_coords(self):
        '''
        Restore the UV coordinates of the selected edges
        '''
        if self.original_loops_uv_coords:
            if self.inner_loops:
                for loop_list in self.inner_loops:
                    for loop in loop_list:
                        uv = self.original_loops_uv_coords[loop.index]
                        loop[self.uv_layer].uv = uv
            if self.outer_loops:
                for loop_list in self.outer_loops:
                    for loop in loop_list:
                        loop[self.uv_layer].uv = self.original_loops_uv_coords[loop.index]
            bmesh.update_edit_mesh(self.obj.data)


    def clear(self):
        '''
        Clear the object's selected edges
        '''
        if self.bm and isinstance(self.bm, bmesh.types.BMesh):
            self.bm.free()
        self.bm = None
        self.edges.clear()
        self.inverted_edges.clear()
        self.corner_edges.clear()
        self.inner_faces.clear()
        self.outer_faces.clear()
        self.active_edge_batch_coords.clear()
        self.edges_batch_coords.clear()
        self.selected_edges_batch_coords.clear()
        self.inner_faces_batch_coords.clear()
        self.outer_faces_batch_coords.clear()
        # self.deformed_verts_postion.clear()
        # self.outline_faces_indices.clear()
        self.parametric_coordinates.clear()
        self.inner_loops.clear()
        self.outer_loops.clear()
        self.is_border = False
        self.inner_uv_coords.clear()
        self.outer_uv_coords.clear()


    def load(self):
        '''
        Load the selected edges from the object
        '''

        if self.bm and isinstance(self.bm, bmesh.types.BMesh):
            self.bm.free()

        if self. obj.mode == "EDIT":
            self.get_deformed_mesh_verts_positions()
            self.bm = bmesh.from_edit_mesh(self.obj.data)
            self.bm.faces.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()
            self.bm.verts.ensure_lookup_table()
            self.uv_layer = self.bm.loops.layers.uv.active
            unselected_edges = []
            # let's store the uv coordinates for the active layer
            self.uv_border_edges = []

            for edge in self.bm.edges:
                if is_edge_uv_boundary(edge, self.uv_layer):
                    self.uv_border_edges.append(edge)
                if edge.select:
                    self.edges.append(edge)
                else:
                    unselected_edges.append(edge)
            self.is_border = any([e.is_boundary for e in self.edges])
            self.get_ordered_edges_sequence()
            self.get_inner_faces()
            self.get_outer_faces()
            if len(self.edges) > 0:
                edges = [self.edges[0]]
                self.active_edge_batch_coords = self.get_edges_batch_coords(edges)
                self.parametric_coordinates = self.get_parametric_coordinates()
            self.edges_batch_coords = self.get_edges_batch_coords(unselected_edges)
            if len(self.edges) > 1:
                edges = self.edges[1:]
                self.selected_edges_batch_coords = self.get_edges_batch_coords(edges)
            if len(self.inner_faces) > 0:
                self.inner_faces_batch_coords = self.get_faces_batch_coords(self.inner_faces)
            if len(self.outer_faces) > 0:
                self.outer_faces_batch_coords = self.get_faces_batch_coords(self.outer_faces)
            # let's store the uv coordinates for the offset
            self.offset_uv_coordinates_array = []
            for face in self.bm.faces:
                for loop in face.loops:
                    self.offset_uv_coordinates_array.append(loop[self.uv_layer].uv.copy())
            self.offset_uv_border_edges()

            if len(self.edges) > 0 and len(self.inner_faces) > 0:
                self.inner_loops = self.get_edges_faces_related_loops(self.edges, self.inner_faces)
                self.inner_uv_coords = self.get_uv_coordinates(self.edges, self.inner_faces, self.uv_layer)
            if len(self.edges) > 0 and len(self.outer_faces) > 0:
                self.outer_loops = self.get_edges_faces_related_loops(self.edges, self.outer_faces)
                self.outer_uv_coords = self.get_uv_coordinates(self.edges, self.outer_faces, self.uv_layer)



    def offset_uv_border_edges(self, offset_disance=-0.000001):
        '''
        Offset the UV border edges
        :param offset: The offset value
        '''
        uv_layer = self.uv_layer
        islands = sort_border_islands(self.uv_border_edges, uv_layer)
        for i, island in enumerate(islands):
            for i in range(len(island)):
                next_edge_id = i + 1 if i < len(island) - 1 else 0
                current_edge = island[i]
                next_edge = island[next_edge_id]
                previous_point = Vector((current_edge[0][uv_layer].uv[0], current_edge[0][uv_layer].uv[1], 0.0))
                point = Vector((current_edge[1][uv_layer].uv[0], current_edge[1][uv_layer].uv[1], 0.0))
                next_point = Vector((next_edge[1][uv_layer].uv[0], next_edge[1][uv_layer].uv[1], 0.0))
                new_point = offset_point(point, previous_point, next_point, offset_disance,
                                         normal=Vector((0.0, 0.0, 1.0)))
                # let's replace the uv coordinates in the uv_coordinates_array
                for loop in current_edge[1].vert.link_loops:
                    loop_index = loop.index
                    new_uv = Vector((new_point[0], new_point[1]))
                    if (loop[uv_layer].uv - current_edge[1][uv_layer].uv).length == 0:
                        self.offset_uv_coordinates_array[loop_index]= new_uv


    def transfer_uv_coordinates(self, uv_coords, uv_parametric_coords):
        '''
        Transfer the UV coordinates to the mesh
        :param uv_coords: The UV coordinates to transfer
        '''
        # uv_parametric_coords = convert_to_parametric_coordinates(uv_coords)
        # print("=====================================")
        # print("UV PARAMETRIC COORDS (uv_coords): ", uv_parametric_coords)
        # print("======================================")
        # print("SELF PARAMETRIC COORDS: ", self.parametric_coordinates)

        transferred_uv_coords = []
        for co in self.parametric_coordinates:
            for i in range(len(uv_parametric_coords)-1):
                current = uv_parametric_coords[i]
                next = uv_parametric_coords[i+1]
                if co >= current and co <= next:
                    # find the scale factor
                    scale_factor = (co - current) / (next - current)
                    # find the corresponding UV coordinates
                    vector = (uv_coords[i][1] - uv_coords[i][0]) * scale_factor
                    uv = uv_coords[i][0] + vector
                    transferred_uv_coords.append(uv)
                    break
        # update the UV coordinates
        return transferred_uv_coords

    def set_inner_loops_uv_coordinates(self, uv_coords):
        '''
        Set the UV coordinates of the inner loops
        :param uv_coords: The UV coordinates to set
        '''
        self.set_loops_uv_coordinates(self.inner_loops, uv_coords)

    def set_outer_loops_uv_coordinates(self, uv_coords):
        '''
        Set the UV coordinates of the outer loops
        :param uv_coords: The UV coordinates to set
        '''
        self.set_loops_uv_coordinates(self.outer_loops, uv_coords)

    def set_loops_uv_coordinates(self, loops, uv_coords):
        '''
        Set the UV coordinates of the inner loops
        :param uv_coords: The UV coordinates to set
        '''
        if len(loops) != len(uv_coords):
            print("The number of loops: {0} and UV coordinates {1} do not match".format(len(loops), len(uv_coords)))
            return
        for i in range(len(loops)):
            sub_loops = loops[i]
            for loop in sub_loops:
                loop[self.uv_layer].uv = uv_coords[i]
        # update the mesh
        bmesh.update_edit_mesh(self.obj.data)

    def pin_inner_loops(self):
        '''
        Pin the inner loops
        '''
        for loops in self.inner_loops:
            for loop in loops:
                loop[self.uv_layer].pin_uv = True
        # update the mesh
        bmesh.update_edit_mesh(self.obj.data)

    def unpin_inner_loops(self):
        '''
        Unpin the inner loops
        '''
        for loops in self.inner_loops:
            for loop in loops:
                loop[self.uv_layer].pin_uv = False
        # update the mesh
        bmesh.update_edit_mesh(self.obj.data)

    def pin_outer_loops(self):
        '''
        Pin the outer loops
        '''
        for loops in self.outer_loops:
            for loop in loops:
                loop[self.uv_layer].pin_uv = True
        # update the mesh
        bmesh.update_edit_mesh(self.obj.data)

    def unpin_outer_loops(self):
        '''
        Unpin the outer loops
        '''
        for loops in self.outer_loops:
            for loop in loops:
                loop[self.uv_layer].pin_uv = False
        # update the mesh
        bmesh.update_edit_mesh(self.obj.data)

    @property
    def is_mesh_closed_loop(self):
        '''
        Check if the edge sequence is a closed loop
        :return: True if the edge sequence is a closed loop, False otherwise
        '''
        if len(self.edges) < 2:
            return False
        if any(v in self.edges[-1].verts for v in self.edges[0].verts):
            return True
        else:
            return False

    def get_uv_coordinates(self, edges, faces, uv_layer, get_offset_coordinates = True):
        '''
        Get the UV coordinates of the edges filtered by the faces
        :return: The UV coordinates of the edges
        '''
        uv_coords = []
        for i in range(len(edges)):
            previous_edge = edges[i - 1] if i > 0 else None
            # edge_face = None
            edge = edges[i]
            # # let's get the edge face
            # for face in faces:
            #     if edge in face.edges:
            #         edge_face = face
            #         break
            next_edge = edges[i + 1] if i + 1 < len(edges) else None
            # # let's get the next edge face
            # if next_edge:
            #     for face in faces:
            #         if next_edge in face.edges:
            #             next_edge_face = face
            #             break
            verts = [edge.verts[0], edge.verts[1]]
            if next_edge:
                if verts[1] not in next_edge.verts:
                    verts = verts[::-1]
            elif previous_edge:
                if verts[0] not in previous_edge.verts:
                    verts = verts[::-1]
            verts_cords = []
            for vert in verts:
                for loop in vert.link_loops:
                    if loop.face in faces:
                        if get_offset_coordinates:
                            verts_cords.append(self.offset_uv_coordinates_array[loop.index])
                        else:
                            verts_cords.append(loop[uv_layer].uv.copy())
                        break
            uv_coords.append(verts_cords)
        return uv_coords

    def get_edges_faces_related_loops(self, edges, faces):
        '''
        Get the related loops of the edges filtered by the faces
        :return: The related loops of the edges
        '''
        loops = []
        parsed_verts = []
        for i in range(len(edges)):
            previous_edge = edges[i - 1] if i > 0 else None
            edge = edges[i]
            next_edge = edges[i + 1] if i + 1 < len(edges) else None
            verts = [edge.verts[0], edge.verts[1]]
            if next_edge:
                if verts[1] not in next_edge.verts:
                    verts = verts[::-1]
            elif previous_edge:
                if verts[0] not in previous_edge.verts:
                    verts = verts[::-1]
            for vert in verts:
                if vert in parsed_verts:
                    continue
                vert_loops = []
                for loop in vert.link_loops:
                    if loop.face in faces:
                        vert_loops.append(loop)
                parsed_verts.append(vert)
                loops.append(vert_loops)
        return loops

    def get_deformed_mesh_verts_positions(self):
        '''
        Get the deformed mesh vertices positions
        '''
        # Get the evaluated object with all deformations applied
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated_obj = self.obj.evaluated_get(depsgraph)
        # Get the final mesh data
        mesh = evaluated_obj.to_mesh()
        mesh.calc_loop_triangles()

        vp = np.zeros((len(mesh.vertices) * 3,), dtype=np.float32, )
        mesh.vertices.foreach_get('co', vp)
        vp = vp.reshape((-1, 3))

        fs = np.zeros((len(mesh.loop_triangles) * 3, ), dtype=np.int32, )
        mesh.loop_triangles.foreach_get('vertices', fs)
        fs.shape = (-1, 3, )
        self.outline_faces_indices = fs
        # multiplicate by the matrix world to get the global coordinates
        world_matrix = np.array(self.obj.matrix_world)
        self.deformed_verts_postion = transform_vertices_array(vp, world_matrix)

        evaluated_obj.to_mesh_clear()

    def get_ordered_edges_sequence(self):
        '''
        Order the edge sequence starting from the active edge
        '''
        active_edge = self.bm.select_history.active
        self.edges = [active_edge]
        next_edge = self.find_next_edge(active_edge)
        # ordering the edges in a sequence
        if next_edge:
            while next_edge:
                self.edges.append(next_edge)
                next_edge = self.find_next_edge(next_edge)
        # let's find the edges to flip and the corner edges

        self.corner_edges = [False] * len(self.edges)
        self.inverted_edges = [False] * len(self.edges)
        for i in range(len(self.edges)):
            current_edge = self.edges[i]
            next_edge = self.edges[i + 1] if i + 1 < len(self.edges) else None
            previous_edge = self.edges[i - 1] if i > 0 else None
            # print("Edge Verts: ({0}, {1})".format(current_edge.verts[0].index, current_edge.verts[1].index))
            if next_edge:
                if any(f in next_edge.link_faces for f in current_edge.link_faces):
                    self.corner_edges[i] = True
                if current_edge.verts[0] in next_edge.verts:
                    self.inverted_edges[i] = True
                    # print("This needs flipping")
            elif previous_edge:
                if current_edge.verts[1] in previous_edge.verts:
                    # print("This needs flipping")
                    self.inverted_edges[i] = True

    def is_loop_ordered(self):
        '''
        Check if the edge sequence is ordered according to the face loops
        edge[0].link_loops[1].vert == edge[1].link_loops[0].vert
        '''

        if len(self.edges) < 2:
            print("CANNOT DETERMINE IS EDGE SEQUENCE IS CLOCKWISE OR COUNTERCLOCKWISE")
            return True

        shared_vert = [v for v in self.edges[0].verts if v in self.edges[1].verts][0]
        if shared_vert == self.edges[0].link_loops[0].link_loop_next.vert:
            return True

        else:
            return False

    def get_edges_batch_coords(self, edges):
        '''
        Get the batch coordinates of the edges
        :return:
        '''
        batch_coords = []
        for edge in edges:
            for vert in edge.verts:
                deformed_vert = self.deformed_verts_postion[vert.index].tolist()
                batch_coords.append(deformed_vert)
        return batch_coords

    def get_faces_batch_coords(self, faces):
        '''
        Get the batch coordinates of the faces
        :param faces: The faces to get the coordinates from
        :return:
        '''
        faces_coords = []
        for face in faces:
            coords = []
            for vert in face.verts:
                deformed_vert = self.deformed_verts_postion[vert.index]
                coords.append(deformed_vert)
            faces_coords.append(coords)

        return faces_coords

    def get_parametric_coordinates(self):
        '''
        Get the parametric length of the edge sequence
        :return:
        '''
        verts_coords = get_edges_verts_coordinates(self.edges)
        return convert_to_parametric_coordinates(verts_coords)


    def get_inner_faces(self):
        '''
        Get the inner of the edge sequence always starting from the first faceloop
        :return:
        '''
        start_loop_idx = 0 if self.is_border else self.is_loop_ordered()
        self.inner_faces = self.get_border_faces(start_loop_idx)

    def get_outer_faces(self):
        '''
        Get the outer faces of the edge sequence
        :return:
        '''
        if self.is_border:
            return []

        self.outer_faces = self.get_border_faces(not self.is_loop_ordered())

    def get_border_faces(self, start_loop_idx=1):
        '''
        Find the faces connected to one side of the edge sequence
        '''
        paresed_faces = []
        for i in range(len(self.edges) - 1):
            next_edge = self.edges[i + 1] if i + 1 < len(self.edges) else None
            current_edge = self.edges[i]

            start_face = current_edge.link_loops[start_loop_idx].face
            if paresed_faces:
                start_face = paresed_faces[-1]
            connected_faces = get_faces_between_edges(current_edge,
                                                           next_edge,
                                                           start_face)

            for face in connected_faces:
                if face not in paresed_faces:
                    paresed_faces.append(face)
        return paresed_faces

    def find_next_edge(self, edge):
        '''
        Find the next edge in the sequence
        :param edge: The current edge
        :return:
        '''
        selected_edges = list()
        for v in edge.verts:
            for e in v.link_edges:
                # print("   Parsing edge: {0}".format(e.index))
                if e.select and e not in self.edges and e != edge:
                    selected_edges.append(e)

        if len(selected_edges) != 1:
            # print("Could not find the next edge because the length of the array is: {0}".format(len(selected_edges)))
            return None
        return selected_edges[0]


def is_edge_uv_boundary(edge, uv_layer):
    '''
    Check if the edge is a UV boundary
    :return: True if the edge is a UV boundary, False otherwise
    '''
    if edge.is_boundary:
        return True
    half_edge_1 = edge.link_loops[0]
    half_edge_2 = edge.link_loops[1]
    if half_edge_1[uv_layer].uv != half_edge_2.link_loop_next[uv_layer].uv:
        return True
    elif half_edge_2[uv_layer].uv != half_edge_1.link_loop_next[uv_layer].uv:
        return True
    else:
        return False


def get_faces_between_edges(first_edge, second_edge, start_face=None):
    '''
    Find the connected faces and orders them based on the drawing order of the faces
    '''
    # print("=====================================")
    start_face_index = start_face.index if start_face else None
    # print("EDGES: ({0}, {1} Start face: {2})".format(first_edge.index, second_edge.index, start_face_index))
    # let's find the shared vertex and the
    connected_faces = []
    is_ordered = first_edge.verts[1] in second_edge.verts
    # print("Is ordered: {0}".format(is_ordered))
    shared_vert = first_edge.verts[is_ordered]
    current_face = None
    for loop in first_edge.link_loops:

        if loop.face == start_face:
            current_face = loop.face
            break
    if current_face is None:
        return connected_faces
    if second_edge in current_face.edges:
        # print("This is a corner face {0}".format(current_face.index))
        return [current_face]

    connected_faces.append(current_face)
    shared_vert_faces = shared_vert.link_faces
    counter = 0
    while current_face:
        if counter >= 10:
            break
        counter = +1
        face_connected = []
        face_connected = get_face_connected_faces(current_face)
        # find the next face
        next_face = None
        for f in face_connected:
            if f not in connected_faces and f in shared_vert_faces and first_edge not in f.edges:
                next_face = f
                break

        if next_face:
            connected_faces.append(next_face)
            if second_edge in next_face.edges:
                # this is the last face
                current_face = None
            else:
                current_face = next_face
        else:
            current_face = None

    return connected_faces


def get_face_connected_faces(face):
    connected_faces = []
    for edge in face.edges:
        for link_face in edge.link_faces:
            if link_face in connected_faces or link_face == face:
                continue
            connected_faces.append(link_face)
    return connected_faces


def transform_vertices_array(array, mat):
    verts_co_4d = np.ones(shape=(array.shape[0] , 4) , dtype=np.float32)
    verts_co_4d[: , :-1] = array  # cos v (x,y,z,1) - point,   v(x,y,z,0)- vector
    local_transferred_position = np.einsum ('ij,aj->ai' , mat , verts_co_4d)
    return local_transferred_position[:, :3]


def offset_point(point, previous_point, next_point, offset_distance, normal=Vector((0.0, 0.0, 1.0))):
    """
    Inset a point based on previous and next coordinates.
    """

    # Compute edge vectors
    edge1 = (point - previous_point).normalized()
    edge2 = (next_point - point).normalized()

    # Compute bisector direction
    bisector = (edge1 + edge2)

    # Check if bisector is valid (avoid division by zero)
    if bisector.length < 1e-6:
        print("Warning: Bisector is nearly zero, using fallback direction")
        bisector = edge1.cross(normal).normalized()  # Fallback to normal-based direction
    else:
        bisector.normalize()

    # Compute perpendicular in plane
    perp = bisector.cross(normal).normalized()

    # Compute correct inset distance using sine rule
    angle = edge1.angle(-edge2) / 2  # Half of the inner angle

    # Prevent extreme scaling
    sin_angle = max(1e-6, math.sin(angle))  # Avoid division by zero
    scale_factor = offset_distance / sin_angle

    # Compute inset position
    inset_point = point + perp * scale_factor
    return inset_point


def find_next_uv_boder_loop(loop, border_edges, uv_layer):
    end_loop = loop.link_loop_next
    # let's find the uv border edge
    if end_loop.edge in border_edges:
        return [end_loop, end_loop.link_loop_next]
    radial_next = end_loop.link_loop_radial_next
    if radial_next == end_loop:
        # this is probably a border edge and the only possible next edge is the end_loop edge which is not in the border edges list
        return None
    next_loop = radial_next.link_loop_next
    counter = 0
    while next_loop != end_loop:
        counter += 1
        if counter > 100:
            print("Stopping the loop check vert {0} loop: {1}".format(end_loop.vert.index, end_loop.index))

            break
        if next_loop.edge not in border_edges:
            next_loop = next_loop.link_loop_radial_next.link_loop_next
            # skipping if the loop edge is not in the border edges
            continue
        if next_loop[uv_layer].uv == end_loop[uv_layer].uv:
            return [next_loop, next_loop.link_loop_next]
        next_loop = next_loop.link_loop_radial_next.link_loop_next


def sort_border_islands(uv_border_edges, uv_layer):
    islands = []
    visited = []
    for border_edge in uv_border_edges:
        island = []
        current_loop = [border_edge.link_loops[0], border_edge.link_loops[0].link_loop_next]
        if current_loop in visited:
            current_loop = [border_edge.link_loops[0].link_loop_radial_next,
                            border_edge.link_loops[0].link_loop_radial_next.link_loop_next]

        if current_loop in visited:
            continue
        while current_loop:
            island.append(current_loop)
            visited.append(current_loop)
            next_loop = find_next_uv_boder_loop(current_loop[0], uv_border_edges, uv_layer)
            if next_loop not in visited:
                current_loop = next_loop
            else:
                current_loop = None
        if island:
            islands.append(island)
    return islands


def offset_uv_border_edges(islands, uv_layer, offset_disance=-0.0003):
    for island in islands:
        deformed_points = []
        for i in range(len(island)):
            next_edge_id = (i + 1) % len(island)
            current_edge = island[i]
            next_edge = island[next_edge_id]
            previous_point = Vector((current_edge[0][uv_layer].uv[0], current_edge[0][uv_layer].uv[1], 0.0))
            point = Vector((current_edge[1][uv_layer].uv[0], current_edge[1][uv_layer].uv[1], 0.0))
            next_point = Vector((next_edge[1][uv_layer].uv[0], next_edge[1][uv_layer].uv[1], 0.0))
            new_point = offset_point(point, previous_point, next_point, offset_disance, normal=Vector((0.0, 0.0, 1.0)))
            deformed_points.append(new_point)
        for i in range(len(deformed_points)):
            current_loop = island[i][1]
            old_coord = current_loop[uv_layer].uv
            new_coord = Vector((deformed_points[i][0], deformed_points[i][1]))

            loops_to_update = []
            for link_loop in current_loop.vert.link_loops:
                if (link_loop[uv_layer].uv - old_coord).length == 0:
                    loops_to_update.append(link_loop)
            for link_loop in loops_to_update:
                link_loop[uv_layer].uv = new_coord

def get_edges_verts_coordinates(edges):
    '''
    Get the vectors of the edges
    :return:
    '''
    coordinates = []
    for i in range(len(edges)):
        verts_coords = []
        next_edge = edges[i + 1] if i + 1 < len(edges) else None
        edge = edges[i]
        previous_edge = edges[i - 1] if i > 0 else None
        verts = [edge.verts[0], edge.verts[1]]
        if next_edge:
            if verts[1] not in next_edge.verts:
                verts = verts[::-1]
        elif previous_edge:
            if verts[0] not in previous_edge.verts:
                verts = verts[::-1]
        verts_coords.append(verts[0].co.copy())
        verts_coords.append(verts[1].co.copy())
        coordinates.append(verts_coords)
    return coordinates

def convert_to_parametric_coordinates(coordinates):
    """
    Get the parametric coordinates of a list of coordinates
    :return:
    """
    paramentric_coordinates = [0.0]
    total_length = 0.0
    for i in range(len(coordinates)):
        previous_coordinates = coordinates[i][0]
        current_coordinates = coordinates[i][1]
        vector_length = (current_coordinates - previous_coordinates).length
        paramentric_coordinates.append(total_length + vector_length)
        total_length += vector_length
    return [coord / total_length for coord in paramentric_coordinates]