bl_info = {
    "name": "TopoSnap",
    "blender": (3, 0, 0),
    "category": "Mesh",
    "description": "Get face ID of selected face",
}
import os
import ctypes
import bpy
import bmesh
import numpy as np
import bpy_types
import gc
import time
from ctypes import wintypes

class MESH_OT_get_face_id(bpy.types.Operator):
    """Get the Face ID of the selected face in Edit Mode"""
    bl_idname = "mesh.get_face_id"
    bl_label = "Get Face ID"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        # Ensure the object is a mesh and is in Edit Mode
        if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
            # Get the BMesh data of the mesh
            bm = bmesh.from_edit_mesh(obj.data)
            os.system("cls")
            # Ensure a face is selected
            selected_faces = [f for f in bm.faces if f.select]
            if selected_faces:
                face = selected_faces[0]
                face_index = face.index
                topo_mesh = TopoMesh(obj)

                face_loops = topo_mesh.face_loops
                face_loops_start = topo_mesh.loops_start
                face_loops_total = topo_mesh.loops_total
                print("Face loop Start: {}".format(face_loops_start))
                print("Face loop Total: {}".format(face_loops_total))
                # Convert numpy arrays to ctypes pointers
                face_loops_ptr = face_loops.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                face_loops_start_ptr = face_loops_start.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                face_loops_total_ptr = face_loops_total.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                faces_count = topo_mesh.face_count
                print("Face Count: {}".format(faces_count))
                print("The lenght of face loops: {}".format(len(face_loops)))
                starting_face = face_index
                edge_offset = 0

                script_dir = os.path.dirname(os.path.realpath(__file__))
                lib_name = 'my_c_lib.dll'
                lib_name = "toposnap_lib.dll"
                test_name =  'test_openmp.dll'
                test = False
                if test:
                    test_dll_path = os.path.join(script_dir, test_name)
                    test_openmp = ctypes.CDLL(test_dll_path)
                    test_openmp.run_pthread()
                    return {'FINISHED'}
                dll_path = os.path.join(script_dir, lib_name)
                print("DLL Path: {}".format(dll_path))
                my_c_lib = ctypes.WinDLL(dll_path)
   
                # Step 5: Define the argument and return types for the sort function
                my_c_lib.reorder_topology.argtypes = [
                                                        ctypes.POINTER(ctypes.c_int),  # face_loops
                                                        ctypes.POINTER(ctypes.c_int),  # face_loops_start
                                                        ctypes.POINTER(ctypes.c_int),  # face_loops_total
                                                        ctypes.c_int,                  # face_loops_count
                                                        ctypes.c_int,                  # starting_face
                                                        ctypes.c_int                   # edge_offset
                                                    ]

                my_c_lib.reorder_topology.restype = None
                # Step 6: Call the sort_array function
                start = time.time()
                try:
                    my_c_lib.reorder_topology(
                        face_loops_ptr,
                        face_loops_start_ptr,
                        face_loops_total_ptr,
                        faces_count,
                        starting_face,
                        edge_offset
                    )
                
                except Exception as e:
                    print("Error: {}".format(e))


                end = time.time()
                print("Time: {}".format(end - start))
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)    
                kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]
                
                handle = ctypes.c_void_p(my_c_lib._handle)

                result = ctypes.windll.kernel32.FreeLibrary(handle)



                if result == 0:
                    error_code = ctypes.GetLastError()
                    print(f"FreeLibrary failed with error code: {error_code}")
                else:
                    print("FreeLibrary succeeded")
                del my_c_lib
                del face_loops_ptr
                del face_loops_start_ptr
                del face_loops_total_ptr
                del topo_mesh
                del bm
                gc.collect()



                # After sorting, the original array in Python is modified, you can print it
                # sorted_py_list = list(c_array)  # Convert ctypes array back to Python list
                # print("Sorted list:", sorted_py_list)


            else:
                self.report({'WARNING'}, "No face selected")
        else:
            self.report({'WARNING'}, "Must be in Edit Mode and select a mesh")

        return {'FINISHED'}


class VIEW3D_PT_topo_snap(bpy.types.Panel):
    """Creates a Panel in the Item tab of the 3D View"""
    bl_label = "TopoSnap"
    bl_idname = "VIEW3D_PT_topo_snap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TopSnap'

    def draw(self, context):
        layout = self.layout

        # Source Section (Placeholder for future use)
        layout.label(text="Source")
        layout.separator()

        # Target Section
        layout.label(text="Target")
        layout.operator("mesh.get_face_id", text="Get Selected Face ID")

class TopoMesh(object):
    def __init__(self, obj):
        if not isinstance(obj, bpy_types.Object):
            obj = bpy.data.objects.get(obj)
        self.obj = obj
        self.mesh = obj.data
        self.loop_count = len(self.mesh.loops)
        self.face_count = len(self.mesh.polygons)
        self.vert_count = len(self.mesh.vertices)
        self.face_loops = np.zeros(self.loop_count, dtype=np.int32)
        self.mesh.loops.foreach_get("vertex_index", self.face_loops)
        self.loops_start = np.zeros(self.face_count, dtype=np.int32)
        self.mesh.polygons.foreach_get("loop_start", self.loops_start)
        self.loops_total = np.zeros(self.face_count, dtype=np.int32)
        self.mesh.polygons.foreach_get("loop_total", self.loops_total)
        # self.face_loops_list = self.get_face_loops_list()

    def get_face_loop(self, face_id):
        start = self.loops_start[face_id]
        # print("Start: {}".format(start))
        end = start + self.loops_total[face_id]
        # print("End: {}".format(end))
        return np.array(self.face_loops[start:end])

    @staticmethod
    def offset_loop(face_loop, offset):
        offset = offset % len(face_loop)  # Handle rotation larger than the list size
        return face_loop[-offset:] + face_loop[:-offset]

    @staticmethod
    def get_connected_faces(face_loops, edge):
        faces = list()
        for loop in face_loops:
            if all(v in loop for v in edge):
                reverse_edge = edge[::-1]
                for i in range(len(loop)):
                    transposed_loop = TopoMesh.offset_loop(loop, i)
                    if reverse_edge == transposed_loop[:2]:
                        faces.append(transposed_loop)
        return faces

    @staticmethod
    def get_edges(face_loop):
        edges = list()
        for i in range(len(face_loop), 0, -1):
            edges.append(TopoMesh.offset_loop(face_loop, i)[:2])
        return edges

    @staticmethod
    def get_contiguous_loops(face_loops, face_loop, offset=0):
        edges = TopoMesh.get_edges(TopoMesh.offset_loop(face_loop, offset))
        contiguous = list()
        for edge in edges:
            connected_faces = TopoMesh.get_connected_faces(face_loops, edge)
            contiguous.extend(connected_faces)
        return contiguous

    @staticmethod
    def is_in_loops(loop, loops):
        for current_loop in loops:
            if len(loop) != len(current_loop):
                continue
            if all(x in current_loop for x in loop):
                #print("Loop {} in {}".format(loop, current_loop) )
                return True
        return False


    def sort_loops_from_face(self, face_id, edge_offset=0):
        # loops = [offset_loop(x, edge_offset) for x in loops ]
        loops = self.get_face_loops_list()
        #print(loops)
        starting_loop = TopoMesh.offset_loop(loops[face_id], edge_offset)
        # sorting out the loops for the neghbours
        loops[face_id] = starting_loop
        parsed = [loops[face_id]]
        contiguous = [starting_loop]
        while contiguous:
            connected_loops = list()
            for loop in contiguous:
                new_loops = TopoMesh.get_contiguous_loops(loops, loop)
                new_loops = [x for x in new_loops if not TopoMesh.is_in_loops(x, parsed)]
                if not TopoMesh.is_in_loops(loop, parsed):
                    parsed.append(loop)
                connected_loops.extend(new_loops)
            contiguous = connected_loops
        # for x in parsed:
        #     print("Loop: {}".format(x))
        #     for y in parsed:
        #         if x== y:
        #             continue
        #         if all(f in y for f in x):
        #             print("Found in: {}".format(y)  )
        return parsed

    def get_face_loops_list(self):
        face_loop_list = list()
        for i in range(self.face_count):
            face_id = i
            l = self.get_face_loop(face_id).tolist()
            face_loop_list.append(l)
        return face_loop_list

# Register and Unregister Classes
def register():
    bpy.utils.register_class(MESH_OT_get_face_id)
    bpy.utils.register_class(VIEW3D_PT_topo_snap)


def unregister():
    bpy.utils.unregister_class(MESH_OT_get_face_id)
    bpy.utils.unregister_class(VIEW3D_PT_topo_snap)


if __name__ == "__main__":
    register()



