import bpy
import bgl
import blf
import gpu
import bmesh
import os
import math
import numpy as np
import traceback
from collections import deque
from mathutils import Vector
from bpy_extras.view3d_utils import (
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d,
)
from gpu_extras.batch import batch_for_shader
import mathutils
bl_info = {
    "name": "Topology Mapping Attributes",
    "author": "Maurizio Memoli",
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "Mesh",
    "description": "Create topology mapping attributes for vertex index sorting or symmetry detection",
    "category": "Mesh",
}

class MESH_OT_create_topology_mapping_attributes(bpy.types.Operator):
    """
    Create topology mapping attributes for vertex index sorting or symmetry detection
    """

    SORTED_INDICES_ATTR_NAME = "sorted_indices_from_face"
    SYMMETRY_INDICES_ATTR_NAME = "symmetry_indices"

    bl_idname = "mesh.create_topology_mapping_attributes"
    bl_label = "Create Topology Mapping Attributes"
    bl_options = {'REGISTER', 'UNDO'}
    running = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_objects = [x for x in bpy.context.selected_objects if x.type == "MESH"]
        self.hovered_face_index = None
        self.mesh_cache = None
        self.draw_handler = None
        self.hit_position = None

        self.wireframe_display_status = []
        self.highlighted_object = None
        self.highlighted_face_index = None
        self.highlighted_vertex_index = None
        self.highlighted_face_coords = None
        self.highlighted_edge_coords = None

        self.evaluated_mesh = None

        self.first_object = None
        self.second_object = None

        self.first_object_face_index = None
        self.first_object_vertex_index = None

        self.second_object_face_index = None
        self.second_object_vertex_index = None

        self.first_obj_face_coords = None
        self.second_obj_face_coords = None

        self.first_obj_edges_coords = None
        self.second_obj_edge_coords = None

        self.first_color = (0, 0, 1, 0.5)
        self.second_color =  (1, 0, 0, 0.5)

        self.current_region = None
        self.current_rv3d = None
        self.current_area = None

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    @property
    def is_first_face_selected(self):
        if all(attr is not None for attr in [
                self.first_object,
                self.first_object_face_index,
                self.first_object_vertex_index,
                self.first_obj_face_coords,
                self.first_obj_edges_coords]):
            return True
        else:
            return False

    @property
    def is_second_face_selected(self):
        if all(attr is not None for attr in [
            self.second_object,
            self.second_object_face_index,
            self.second_object_vertex_index,
            self.second_obj_face_coords,
            self.second_obj_edge_coords
        ]):
            return True
        return False

    def invoke(self, context, event):
        os.system("cls")
        if self.selected_objects:
            self.clear_highlighted()
            self.clear_first_object()
            self.clear_second_object()
            self.hovered_face_index = None
            # let's turn on wirframe display for all objects
            for obj in self.selected_objects:
                self.wireframe_display_status.append(obj.show_wire)
                obj.show_wire = True
            # Register the draw handler
            if self.draw_handler is None:
                self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                    self.draw_callback, (context,), 'WINDOW', 'POST_VIEW'
                )
            self.current_area = context.area
            context.window_manager.modal_handler_add(self)
            MESH_OT_create_topology_mapping_attributes.running = True
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No mesh object selected")
            return {'CANCELLED'}

    def refresh_window_areas(self):
        for window in bpy.context.window_manager.windows:
            for screen in window.screen.areas:
                if screen.type == 'VIEW_3D':
                    screen.tag_redraw()

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cleanup()
            self.refresh_window_areas()
            return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            self.update_hovered_face(context, event)
            self.refresh_window_areas()

        if event.type in ['MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MOUSEMOVE']:
            return {'PASS_THROUGH'}

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if self.first_object == self.highlighted_object and self.first_object_face_index == self.highlighted_face_index:
                self.clear_first_object()
                self.refresh_window_areas()
            if self.second_object == self.highlighted_object and self.second_object_face_index == self.highlighted_face_index:
                self.clear_second_object()
                self.refresh_window_areas()
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if not self.is_first_face_selected:
                if self.highlighted_object:
                    self.first_object = self.highlighted_object
                    self.first_object_face_index = self.highlighted_face_index
                    self.first_object_vertex_index = self.highlighted_vertex_index
                    self.first_obj_face_coords = self.highlighted_face_coords
                    self.first_obj_edges_coords = self.highlighted_edge_coords

                    self.refresh_window_areas()
                    return {'RUNNING_MODAL'}
            if not self.is_second_face_selected:
                if self.highlighted_object:
                    self.second_object = self.highlighted_object
                    self.second_object_face_index = self.highlighted_face_index
                    self.second_object_vertex_index = self.highlighted_vertex_index
                    self.second_obj_face_coords = self.highlighted_face_coords
                    self.second_obj_edge_coords = self.highlighted_edge_coords

                    self.refresh_window_areas()
                    return {'RUNNING_MODAL'}

        if event.type == 'RET' and event.value == 'PRESS':
            return self.execute(context)


        return {'RUNNING_MODAL'}

    def clear_highlighted(self):
        self.highlighted_object = None
        self.highlighted_face_index = None
        self.highlighted_vertex_index = None
        self.highlighted_face_coords = None
        self.highlighted_edge_coords = None

    def clear_first_object(self):
        self.first_object = None
        self.first_object_face_index = None
        self.first_object_vertex_index = None
        self.first_obj_face_coords = None
        self.first_obj_edges_coords = None

    def clear_second_object(self):
        self.second_object = None
        self.second_object_face_index = None
        self.second_object_vertex_index = None
        self.second_obj_face_coords = None
        self.second_obj_edge_coords = None

    def update_mesh_cache(self, mesh):
        """Store a BMesh instance from the object for quick lookup."""
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        if self.mesh_cache:
            if isinstance(self.mesh_cache, bmesh.types.BMesh):
                self.mesh_cache.free()
                self.mesh_cache = None
        self.mesh_cache = bm

    def update_hovered_face(self, context, event):
        coord_global = (event.mouse_x, event.mouse_y)  # Use global window coordinates
        depsgraph = context.evaluated_depsgraph_get()

        region = None
        rv3d = None
        local_coord = None

        # Detect viewport dynamically from all open Blender windows
        for window in bpy.context.window_manager.windows:
            for screen in window.screen.areas:
                if screen.type == 'VIEW_3D':
                    for region_candidate in screen.regions:
                        if region_candidate.type == 'WINDOW':
                            x, y, width, height = region_candidate.x, region_candidate.y, region_candidate.width, region_candidate.height

                            # Check if mouse is inside this viewport
                            if x <= coord_global[0] <= x + width and y <= coord_global[1] <= y + height:
                                region = region_candidate
                                rv3d = screen.spaces.active.region_3d
                                local_coord = (coord_global[0] - x, coord_global[1] - y)
                                break
                    if region:
                        if region != self.current_region:
                            print("Changing region updating draw handler.")
                            self.current_region = region
                            depsgraph = context.evaluated_depsgraph_get()
                        if screen != self.current_area:
                            self.current_area = screen
                        break

        if not region or not rv3d:
            return  # No valid viewport found

        # Perform ray casting in the detected viewport
        origin = region_2d_to_origin_3d(region, rv3d, local_coord)
        direction = region_2d_to_vector_3d(region, rv3d, local_coord)

        result, location, normal, index, obj, matrix = context.scene.ray_cast(
            depsgraph, origin, direction
        )
        if result and obj in self.selected_objects:
            evaluated_mesh = obj.evaluated_get(depsgraph).to_mesh()
            self.update_mesh_cache(evaluated_mesh)
            self.hovered_face_index = index
            self.hit_position = location
            self.highlighted_object = obj
        else:
            self.hovered_face_index = None
            self.hit_position = None
            self.highlighted_object = None

    def draw_callback(self, context):
        if self.hovered_face_index is None or not self.mesh_cache:
            self.clear_highlighted()
            self.draw_shaders(context)
            return

        bm = self.mesh_cache

        if self.hovered_face_index >= len(bm.faces):
            self.clear_highlighted()
            self.draw_shaders(context)
            return

        face = bm.faces[self.hovered_face_index]
        offset_distance = (face.calc_area() * 0.05) * -1
        # offset_distance = -0.1
        face_normal = face.normal
        # Get world-space vertex positions
        world_matrix = self.highlighted_object.matrix_world
        vertices = [world_matrix @ v.co for v in face.verts]

        # Triangulate the face for correct rendering
        triangles = []
        if len(vertices) == 3:
            triangles = vertices
        elif len(vertices) > 3:
            for i in range(1, len(vertices) - 1):
                triangles.extend([vertices[0], vertices[i], vertices[i + 1]])
        offset_vertices = offset_face_vertices(vertices, face_normal, offset_distance)
        middle_edges = []
        for i in range(len(vertices)):
            vert = vertices[i]
            next_vert = vertices[(i + 1) % len(vertices)]
            edge = (vert + next_vert) * 0.5
            middle_edges.append(edge)

        # let's find the closest vertex to the hit point
        dist = (middle_edges[0] - self.hit_position).length
        vertex_index = 0
        for i in range(1, len(middle_edges)):
            current_dist = (middle_edges[i] - self.hit_position).length
            if current_dist < dist:
                dist = current_dist
                vertex_index = i

        next_vertex_index = (vertex_index + 1) % len(vertices)

        self.highlighted_face_coords = triangles
        self.highlighted_edge_coords = [offset_vertices[vertex_index], offset_vertices[next_vertex_index]]
        self.highlighted_vertex_index = face.verts[vertex_index].index
        self.highlighted_face_index = self.hovered_face_index
        self.draw_shaders(context)

    def draw_shaders(self, context):

        if self.is_first_face_selected:
            color = self.first_color
            first_face_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            first_face_batch = batch_for_shader(first_face_shader, 'TRIS', {"pos": self.first_obj_face_coords})

            first_face_shader.bind()
            first_face_shader.uniform_float("color", color)
            first_face_batch.draw(first_face_shader)

            edges_co = self.first_obj_edges_coords
            edges_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            edges_batch = batch_for_shader(edges_shader, 'LINES', {"pos": edges_co})

            edges_shader.bind()
            edges_shader.uniform_float("color", (1, 1, 1, 0.5))
            edges_batch.draw(edges_shader)

        if self.is_second_face_selected:
            color = self.second_color
            second_face_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            second_face_batch = batch_for_shader(second_face_shader, 'TRIS', {"pos": self.second_obj_face_coords})

            second_face_shader.bind()
            second_face_shader.uniform_float("color", color)
            second_face_batch.draw(second_face_shader)

            edges_co = self.second_obj_edge_coords
            edges_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            edges_batch = batch_for_shader(edges_shader, 'LINES', {"pos": edges_co})

            edges_shader.bind()
            edges_shader.uniform_float("color", (1, 1, 1, 0.5))
            edges_batch.draw(edges_shader)

        if self.is_first_face_selected and self.is_second_face_selected:
            return
        if not self.highlighted_face_coords:
            return
        if self.highlighted_face_index == self.first_object_face_index and self.highlighted_object == self.first_object:
            # you can't select the same face
            return
        color = self.second_color
        if not self.is_first_face_selected:
            color = self.first_color

        first_face_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        first_face_batch = batch_for_shader(first_face_shader, 'TRIS', {"pos": self.highlighted_face_coords})

        first_face_shader.bind()
        first_face_shader.uniform_float("color", color)
        first_face_batch.draw(first_face_shader)

        edges_co = self.highlighted_edge_coords
        edges_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        edges_batch = batch_for_shader(edges_shader, 'LINES', {"pos": edges_co})

        edges_shader.bind()
        edges_shader.uniform_float("color", (1, 1, 1, 0.5))
        edges_batch.draw(edges_shader)

    def create_symmetry_attributes(self,
                                   obj,
                                   face_index,
                                   vertex_index,
                                   opposite_face_index,
                                   opposite_vertex_index,
                                   test=False):
        """
        Create the symmetry attributes for the object
        """
        obj_sorted_indices = self.sort_indices_from_face(obj, face_index, vertex_index)
        opposite_obj_sorted_indices = self.sort_indices_from_face(obj,
                                                                  opposite_face_index,
                                                                  opposite_vertex_index,
                                                                  True)
        obj_sorted_indices = np.array(obj_sorted_indices, dtype=np.int32)
        opposite_obj_sorted_indices = np.array(opposite_obj_sorted_indices, dtype=np.int32)

        if test:
            regular_attr = self.create_mesh_attr(obj.data, "regular_side", 'INT', 'POINT')
            opposite_attr = self.create_mesh_attr(obj.data, "opposite_side", 'INT', 'POINT')
            regular_attr.data.foreach_set("value", obj_sorted_indices)
            opposite_attr.data.foreach_set("value", opposite_obj_sorted_indices)

        # let's create the symmetry attribute
        symmetry_attr = self.create_mesh_attr(obj.data, self.SYMMETRY_INDICES_ATTR_NAME, 'INT', 'POINT')

        # Map values from `opposite` to their corresponding indices in `regular`
        symmetry_vertices = np.full_like(obj_sorted_indices, -1)  # Initialize result with -1

        # Find where regular[i] exists in opposite
        valid_regular = obj_sorted_indices >= 0
        indices_in_opposite = np.array([np.where(opposite_obj_sorted_indices == r)[0] for r in obj_sorted_indices if r >= 0], dtype=object)

        # Assign found indices in result
        symmetry_vertices[valid_regular] = [idx[0] if len(idx) > 0 else -1 for idx in indices_in_opposite]

        # Find where opposite[i] exists in regular
        valid_opposite = opposite_obj_sorted_indices >= 0
        indices_in_regular = np.array([np.where(obj_sorted_indices == o)[0] for o in opposite_obj_sorted_indices if o >= 0], dtype=object)

        # Assign found indices in result (overwrite only if necessary)
        symmetry_vertices[valid_opposite] = [idx[0] if len(idx) > 0 else -1 for idx in indices_in_regular]

        # let's get the existing values
        current_values = np.zeros(len(symmetry_attr.data), dtype=np.int32)
        symmetry_attr.data.foreach_get("value", current_values)
        # let's update the values
        # let's check if the sorted_indices valuer where is not -1 are going to replace current values with -1
        occupied_values = np.where(current_values != -1)[0]
        # if we are replacing existing values we reset all the other values to -1
        if occupied_values.size > 0 and np.max(symmetry_vertices[occupied_values]) > -1:
            # let's set all the values to -1
            current_values.fill(-1)

        add_mask = np.where(symmetry_vertices != -1)[0]
        current_values[add_mask] = symmetry_vertices[add_mask]
        symmetry_attr.data.foreach_set("value", current_values)

    def sort_meshes_indexes(self,
                            source_obj,
                            source_face_index,
                            source_vertex_index,
                            target_obj,
                            target_face_index,
                            target_vertex_index):

        source_sorted_indices = self.sort_indices_from_face(source_obj, source_face_index, source_vertex_index)
        target_sorted_indices = self.sort_indices_from_face(target_obj, target_face_index, target_vertex_index)
        source_sorted_indices = np.array(source_sorted_indices, dtype=np.int32)
        target_sorted_indices = np.array(target_sorted_indices, dtype=np.int32)

        # Initialize result array with -1
        result = np.full_like(source_sorted_indices, -1)

        # Find valid mappings
        valid_values = (source_sorted_indices != -1) & (np.isin(source_sorted_indices, target_sorted_indices))

        # Create lookup arrays
        source_indices = np.argsort(source_sorted_indices[valid_values])
        target_indices = np.argsort(target_sorted_indices[np.isin(target_sorted_indices, source_sorted_indices[valid_values])])

        # Map values
        result[np.where(valid_values)[0][source_indices]] = np.where(np.isin(target_sorted_indices, source_sorted_indices[valid_values]))[0][
            target_indices]

        return result

    def create_reorder_attributes(self,
                                  source_obj,
                                  source_face_index,
                                  source_vertex_index,
                                  target_obj,
                                  target_face_index,
                                  target_vertex_index):
        source_mesh = source_obj.data
        sorted_indices = self.sort_meshes_indexes(source_obj,
                                                  source_face_index,
                                                  source_vertex_index,
                                                  target_obj,
                                                  target_face_index,
                                                  target_vertex_index)
        # create an attribute to store the sorted indices for source_obj
        source_attr = self.create_mesh_attr(source_mesh, self.SORTED_INDICES_ATTR_NAME, 'INT', 'POINT')
        # get the existing values
        current_values = np.zeros(len(source_attr.data), dtype=np.int32)
        source_attr.data.foreach_get("value", current_values)
        # let's check if the sorted_indices valuer where is not -1 are going to replace current values with -1
        occupied_values = np.where(current_values != -1)[0]
        # if we are replacing existing values we reset all the other values to -1
        if occupied_values.size > 0 and np.max(sorted_indices[occupied_values]) > -1:
            # let's set all the values to -1
            current_values.fill(-1)
        # let's update the values
        add_mask = np.where(sorted_indices != -1)[0]
        current_values[add_mask] = sorted_indices[add_mask]
        source_attr.data.foreach_set("value", current_values)

    def cleanup(self):
        """Remove draw handler and free resources."""
        # let's restore the wireframe settings
        for i, obj in enumerate(self.selected_objects):
            obj.show_wire = self.wireframe_display_status[i]

        if self.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
            self.draw_handler = None
        if self.mesh_cache:
            self.mesh_cache.free()
        MESH_OT_create_topology_mapping_attributes.running = False

    def execute(self, context):

        if self.is_first_face_selected and self.is_second_face_selected:
            current_mode = context.object.mode
            if current_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            if self.first_object == self.second_object:
                try:
                    self.create_symmetry_attributes(self.first_object,
                                                    self.first_object_face_index,
                                                    self.first_object_vertex_index,
                                                    self.second_object_face_index,
                                                    self.second_object_vertex_index)

                    self.cleanup()
                    if context.mode != current_mode:
                        bpy.ops.object.mode_set(mode=current_mode)
                    return {'FINISHED'}
                except Exception as e:
                    error_message = traceback.format_exc()
                    print(f"There was a problem while sorting Symmetry:\n {str(error_message)}")
                    self.cleanup()
                    if context.mode != current_mode:
                        bpy.ops.object.mode_set(mode=current_mode)
                    return {'CANCELLED'}
            try:
                self.create_reorder_attributes(self.first_object,
                                               self.first_object_face_index,
                                               self.first_object_vertex_index,
                                               self.second_object,
                                               self.second_object_face_index,
                                               self.second_object_vertex_index)
                self.create_reorder_attributes(self.second_object,
                                               self.second_object_face_index,
                                               self.second_object_vertex_index,
                                               self.first_object,
                                               self.first_object_face_index,
                                               self.first_object_vertex_index)

                self.cleanup()
                if context.mode != current_mode:
                    bpy.ops.object.mode_set(mode=current_mode)
                return {'FINISHED'}
            except Exception as e:
                error_message = traceback.format_exc()
                print(f"There was a problem while sorting order:\n {str(error_message)}")
                self.cleanup()
                if context.mode != current_mode:
                    bpy.ops.object.mode_set(mode=current_mode)
                return {'CANCELLED'}

        else:
            self.report({'WARNING'}, "Select two faces to map")
            # self.cleanup()
            return {'RUNNING_MODAL'}

    @staticmethod
    def create_mesh_attr(mesh, attr_name, attr_type='INT', domain='POINT'):
        if attr_name not in mesh.attributes:
            # let's set all the the values to -1 if the attr type is INT

            mesh_attr = mesh.attributes.new(name=attr_name, type=attr_type, domain=domain)
            values = np.full(len(mesh_attr.data), -1, dtype=np.int32)
            mesh_attr.data.foreach_set("value", values)
            return mesh_attr
        else:
            return mesh.attributes[attr_name]


    @staticmethod
    def sort_indices_from_face(obj, start_face_index, face_vertex_index, flip_bmesh=False):
        """
        Sorts the indices of the vertices of the object starting from a given face and vertex index.
        Where the sorted index is -1, it means that the vertex is not connected to the island of the starting face.

        :param obj: Blender object with mesh data.
        :param start_face_index: Index of the face to start from.
        :param face_vertex_index: Index of the starting vertex in the face.
        :param flip_bmesh: If True, reverses the face orientation.
        :return: List of sorted vertex indices.
        """
        mesh = obj.data
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)
        if flip_bmesh:
            bmesh.ops.reverse_faces(bm, faces=bm.faces, flip_multires=True) # Reverse the face orientation if needed
        # Ensure lookup tables are built for faces and vertices
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        sorted_indices = [-1] * len(bm.verts)
        # Find the starting face and loop
        start_face = bm.faces[start_face_index]
        start_loop = next((loop for loop in start_face.loops if loop.vert.index == face_vertex_index), None)

        if start_loop is None:
            bm.free()
            return sorted_indices  # Early exit if no valid starting loop is found

        if flip_bmesh:
            start_loop = start_loop.link_loop_prev

        parsed_faces = set()  # Optimized lookup for processed faces
        connected_face_loops = deque([start_loop])  # Fast append/pop for traversal

        vert_id = 0
        while connected_face_loops:
            face_loop = connected_face_loops.popleft()  # Faster pop from front
            face = face_loop.face
            if face in parsed_faces:
                continue
            parsed_faces.add(face)

            # Iterate through the face loops to assign vertex indices
            end_face_loop = face_loop.link_loop_prev
            current_face_loop = face_loop
            while True:
                face_vert_id = current_face_loop.vert.index
                if sorted_indices[face_vert_id] == -1:
                    sorted_indices[face_vert_id] = vert_id
                    vert_id += 1

                # Find connected faces via radial loops
                radial_loop = current_face_loop.link_loop_radial_next
                while radial_loop != current_face_loop:
                    if radial_loop.face not in parsed_faces:
                        connected_face_loops.append(radial_loop)
                    radial_loop = radial_loop.link_loop_radial_next

                if current_face_loop == end_face_loop:
                    break
                current_face_loop = current_face_loop.link_loop_next

        bm.free()
        return sorted_indices

def offset_face_vertices(vertices,  normal , offset_distance):
    """
    Inset a sequence of vertices of a face based on the face .
    """
    offset_vertices = []
    for i in range(len(vertices)):
        previous_point = vertices[(i - 1) % len(vertices)]
        point = vertices[i]
        next_point = vertices[(i + 1) % len(vertices)]
        new_point = offset_point(point, previous_point, next_point, offset_distance, normal)
        offset_vertices.append(new_point)

    return offset_vertices

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



def order_array_by_argument(arr):
    """
    Swap two indices in an array of integers.
    """
    # Create a mask for valid values (values that are NOT -1)
    valid_mask = arr != -1

    # Get the indices of valid values
    valid_indices = np.where(valid_mask)[0]

    # Sort only the valid values
    sorted_order = np.argsort(arr[valid_mask])

    # Get ranks for valid values
    rank = np.argsort(sorted_order)

    # Create a result array filled with -1
    result = np.full_like(arr, -1)

    # Place the computed ranks in their original positions
    result[valid_indices] = rank

    return result

# Add operator to the Mesh menu in Edit Mode
def menu_func(self, context):
    self.layout.operator(MESH_OT_create_topology_mapping_attributes.bl_idname, text=MESH_OT_create_topology_mapping_attributes.bl_label)
classes = [MESH_OT_create_topology_mapping_attributes]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)

if __name__ == "__main__":
    register()
