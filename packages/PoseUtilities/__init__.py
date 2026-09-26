import bpy
import bmesh
from mathutils import Vector, Euler, Matrix
import re
bl_info = {
    "name": "Pose Mirroring Utilities",
    "author": "Maurizio Memoli",
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Pose Mode > Sidebar > Pose Tools",
    "description": "A set of utilities to mirror pose transforms in armatures",
    "category": "Animation",
}


def get_mirror_bone_name(bone_name):
    """Get the mirrored bone name by swapping L/R suffixes"""
    # Check for .L/.R pattern
    print(bone_name)
    bone_name_tokens = bone_name.split(".")
    if "L" in bone_name_tokens:
        i = bone_name_tokens.index("L")
        bone_name_tokens[i] = "R"
        other_side_name = ".".join(bone_name_tokens)
        print(other_side_name)
        return other_side_name

    if "R" in bone_name_tokens:
        i = bone_name_tokens.index("R")
        bone_name_tokens[i] = "L"
        other_side_name = ".".join(bone_name_tokens)
        print(other_side_name)
        return other_side_name

    return None


def is_side_bone(bone_name):
    """Check if bone_name is a side bone"""
    bone_name_tokens = bone_name.split(".")
    if "L" in bone_name_tokens or "R" in bone_name_tokens:
        return True
    else:
        return False


def mirror_pose_bone_matrix(matrix):
    """Mirror a pose bone matrix on the X-axis"""
    mirrored = matrix.copy()

    # Mirror translation
    mirrored.translation.x *= -1

    # Mirror rotation - extract euler angles and flip X and Z rotations
    euler = mirrored.to_euler('XYZ')
    euler.x *= -1  # Flip X rotation
    euler.z *= -1  # Flip Z rotation
    # Y rotation stays the same

    # Reconstruct matrix with mirrored rotation
    mirrored = Matrix.Translation(mirrored.translation) @ euler.to_matrix().to_4x4()

    return mirrored


def is_center_bone(pose_bone):
    """Check if a bone is at the center (X position close to 0)"""
    bone_head_world = pose_bone.bone.head_local
    return abs(bone_head_world.x) < 0.001  # Tolerance for floating point precision


def get_relative_matrix(pose_bone):
    """Get the bone relative matrix """
    # Get both matrices
    print(pose_bone.name)
    rest_matrix = pose_bone.bone.matrix_local  # Original/rest position
    print("Rest matrix:")
    print(rest_matrix)
    print("Basis matrix:")
    print(pose_bone.matrix_basis)
    print("Matrix:")
    print(pose_bone.matrix)
    current_matrix = pose_bone.matrix  # Current pose

    # Calculate the transformation from rest to current pose
    relative_transform = rest_matrix.inverted() @ current_matrix
    print("Relative transform:")
    print(relative_transform)
    return relative_transform


def combine_transformations(matrix_a, matrix_b, invert_a=False, invert_b=False):
    """
    Combine the current bone matrix with the opposite bone matrix
    to create a new transformation that mirrors the pose.
    """
    # Combine the transformations
    matrix_a_trans, matrix_a_rot, matrix_a_scale = matrix_a.decompose()
    matrix_b_trans, matrix_b_rot, matrix_b_scale = matrix_b.decompose()

    if invert_a:
        matrix_a_trans.x = matrix_a_trans.x * -1
    if invert_b:
        matrix_b_trans.x = matrix_b_trans.x * -1

    combined_transform = matrix_a_trans + matrix_b_trans

    matrix_a_euler = matrix_a_rot.to_euler()
    matrix_b_euler = matrix_b_rot.to_euler()
    if invert_a:
        matrix_a_euler.y = matrix_a_euler.y * -1
        matrix_a_euler.z = matrix_a_euler.z * -1
    if invert_b:
        matrix_b_euler.y = matrix_b_euler.y * -1
        matrix_b_euler.z = matrix_b_euler.z * -1

    combined_euler = Euler((
                                    matrix_a_euler.x + matrix_b_euler.x,
                                    matrix_a_euler.y + matrix_b_euler.y,
                                    matrix_a_euler.z + matrix_b_euler.z
                                    ), 'XYZ')
    combined_scale = Vector((
        matrix_a_scale.x * matrix_b_scale.x,
        matrix_a_scale.y * matrix_b_scale.y,
        matrix_a_scale.z * matrix_b_scale.z
    ))


    return Matrix.LocRotScale(combined_transform, combined_euler, combined_scale)


def mirror_pose_transforms():
    """
    Mirror pose transforms from source side to target side
    source_side: 'L' or 'R' - which side to copy from
    target_side: 'L' or 'R' - which side to copy to
    """

    # Get active object (should be armature)
    obj = bpy.context.active_object
    if not obj or obj.type != 'ARMATURE':
        print("Error: Please select an armature object")
        return

    # Make sure we're in pose mode
    if bpy.context.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')

    selected_bones = bpy.context.selected_pose_bones
    if not selected_bones:
        print("Error: No pose bones selected")
        return
    bones_info = list()
    bones_count = 0
    processed_bones = []

    for pose_bone in selected_bones:
        if pose_bone in processed_bones:
            continue
        bone_name = pose_bone.name

        # get mirror bone
        if is_side_bone(bone_name):
            # Find the mirror bone
            mirror_name = get_mirror_bone_name(bone_name)
            if mirror_name and mirror_name in obj.pose.bones:
                mirror_bone = obj.pose.bones[mirror_name]
                pose_bone_matrix_basis = combine_transformations(pose_bone.matrix_basis,
                                                           mirror_bone.matrix_basis,
                                                           False,
                                                           True)
                mirror_bone_matrix_basis = combine_transformations(pose_bone.matrix_basis,
                                                           mirror_bone.matrix_basis,
                                                           True,
                                                           False)
                pose_bone.matrix_basis = pose_bone_matrix_basis
                mirror_bone.matrix_basis = mirror_bone_matrix_basis
                bones_info.append("Mirrored: {0} → {1} \r Mirrored: {1} → {0}".format(bone_name, mirror_name))
                processed_bones.extend([pose_bone, mirror_bone])
                bones_count += 2
                continue

        # Check if this is a center bone
        elif is_center_bone(pose_bone):


            pose_bone.matrix_basis = combine_transformations(pose_bone.matrix_basis,
                                                             pose_bone.matrix_basis,
                                                             False,
                                                             True)
            bones_info.append("Zeroed center bone: {0}".format(bone_name))
            bones_count += 1


    # Update the viewport
    bpy.context.view_layer.update()

    print(f"Processed {bones_count} bones:")
    for bone_info in bones_info:
        print(f"  {bone_info}")


# UI Panel
class POSE_PT_MirrorPanel(bpy.types.Panel):
    bl_label = "Pose Mirror"
    bl_idname = "POSE_PT_mirror_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_context = "posemode"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Mirror Selected Pose Bones:")

        row = col.row(align=True)
        op1 = row.operator("pose.mirror_selected", text="L → R")
        op1.source_side = 'L'
        op1.target_side = 'R'

        op2 = row.operator("pose.mirror_selected", text="R → L")
        op2.source_side = 'R'
        op2.target_side = 'L'

        col.separator()
        col.label(text="Center bones (X≈0) will be")
        col.label(text="zeroed on X-axis")


# Operator
class POSE_OT_MirrorSelected(bpy.types.Operator):
    bl_idname = "pose.mirror_selected"
    bl_label = "Mirror Selected Pose Bones"
    bl_description = "Mirror pose transforms from one side to another"
    bl_options = {'REGISTER', 'UNDO'}

    source_side: bpy.props.StringProperty(default='L')
    target_side: bpy.props.StringProperty(default='R')

    def execute(self, context):
        mirror_pose_transforms()
        return {'FINISHED'}


# Register classes
def register():
    bpy.utils.register_class(POSE_OT_MirrorSelected)
    bpy.utils.register_class(POSE_PT_MirrorPanel)


def unregister():
    bpy.utils.unregister_class(POSE_PT_MirrorPanel)
    bpy.utils.unregister_class(POSE_OT_MirrorSelected)


if __name__ == "__main__":
    register()

    # For testing, you can also call the function directly:
    # mirror_pose_transforms('L', 'R')  # Mirror from Left to Right
    # mirror_pose_transforms('R', 'L')  # Mirror from Right to Left