import bpy
from ..utils.shape_selection import ShapeSelection


class KeyingTools:
    def __init__(self):
        self.shape_selection = ShapeSelection()

    def clear_shape_key_keyframes(self):
        obj = bpy.context.active_object

        # get animation data
        animation_data = obj.data.shape_keys.animation_data
        # and its curves
        curves = animation_data.action.fcurves

        # loop over the curves
        for curve in curves:
            # remove it
            curves.remove(curve)

    def clear_shape_key_keyframes_selected(self):

        obj = bpy.context.active_object
        shapekeys = obj.data.shape_keys.key_blocks
        active_shapekey = shapekeys[obj.active_shape_key_index]
        active_shapekey_name = active_shapekey.name

        data_path = f"key_blocks[\"{active_shapekey_name}\"].value"

        # get animation data
        animation_data = obj.data.shape_keys.animation_data
        # and its curves
        curves = animation_data.action.fcurves

        # loop over the curves
        for curve in curves:
            # find the one that corresponds to the data path
            if curve.data_path == data_path:
                # remove it
                curves.remove(curve)
                break

    def animate_shape_key_20(self):
        # Get the active object and shape key
        obj = bpy.context.active_object
        shape_key = obj.active_shape_key
        if shape_key is None:
            print("No shape key selected")
            return

        # Clear the animation data for the object and shape keys
        self.clear_shape_key_keyframes_selected()

        # Set the start and end frames
        start_frame = 1
        end_frame = 21
        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame

        # Set all shape key values to 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0

        # Set the active shape key value to 0
        shape_key.value = 0
        shape_key.keyframe_insert(data_path="value", frame=start_frame)

        # Set the active shape key value to 1 and key it on frame 11
        shape_key.value = 1
        shape_key.keyframe_insert(data_path="value", frame=11)

        # Set the active shape key value to 0 and key it on frame 20
        shape_key.value = 0
        shape_key.keyframe_insert(data_path="value", frame=21)

    def animate_shape_key_10(self):
        # Get the active object and shape key
        obj = bpy.context.active_object
        shape_key = obj.active_shape_key
        if shape_key is None:
            print("No shape key selected")
            return
        self.clear_shape_key_keyframes_selected()
        # Clear the animation data for the object and shape keys

        # Set the start and end frames
        start_frame = 1
        end_frame = 11
        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame

        # Set all shape key values to 0
        for key in obj.data.shape_keys.key_blocks:
            key.value = 0

        # Set the active shape key value to 0
        shape_key.value = 0
        shape_key.keyframe_insert(data_path="value", frame=start_frame)

        # Set the active shape key value to 1 and key it on frame 11
        shape_key.value = 1
        shape_key.keyframe_insert(data_path="value", frame=11)

    def animate_qc(self):

        print('------------------QC Animation START--------------------')
        # Get the active object
        obj = bpy.context.object
        o = bpy.context.active_object
        scene = bpy.context.scene
        # Get the shape keys
        shape_keys = obj.data.shape_keys.key_blocks

        shape_key_list = [shape.name for shape in shape_keys if shape.name != 'Basis']
        ordered_names = self.shape_selection.order_list_combos(shape_key_list)
        print(shape_key_list)



        # Create the empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        bpy.context.active_object.name = "text_placement"
        text_empty = bpy.data.objects["text_placement"]

        for shape_key in shape_keys:
            font_curve = bpy.data.curves.new(type="FONT", name="shape_key.name" + "_text")
            font_curve.body = shape_key.name

            font_obj = bpy.data.objects.new(shape_key.name + "_text", font_curve)

            scene.collection.objects.link(font_obj)

        # Set the current frame to 1
        bpy.context.scene.frame_set(1)

        # obj.data.shape_keys.key_blocks[shape_name].value
        # Key the shape keys one by one
        for i, shape_key in enumerate(ordered_names):
            print(f"shape key is {shape_key}")
            bpy.context.scene.frame_set((i) * 20)
            # Set the value of the shape key to 0
            #for shape in obj.data.shape_keys.key_blocks:
            for shape in ordered_names:
                o.data.shape_keys.key_blocks[shape].value = 0
                o.data.shape_keys.key_blocks[shape].keyframe_insert("value")

            # Set the current frame to (i+1)*20
            bpy.context.scene.frame_set((i) * 20 + 10)

            # Set the value of the shape keys
            shape_values = self.shape_selection.shape_name_value_dict([shape_key])

            for shape_key_name, shape_key_value in shape_values.items():
                obj.data.shape_keys.key_blocks[shape_key_name].value = shape_key_value
                obj.data.shape_keys.key_blocks[shape_key_name].keyframe_insert("value")

            # Set the current frame to (i+1)*40
            bpy.context.scene.frame_set((i) * 20 + 20)

            # Set the value of the shape key to 0
            for shape in ordered_names:
                o.data.shape_keys.key_blocks[shape].value = 0
                o.data.shape_keys.key_blocks[shape].keyframe_insert("value")

            # Get the text object with the same name as the shape key
            text_object = bpy.data.objects[shape_key + '_text']
            text_object.rotation_euler[0] += 1.57
            text_object.parent = text_empty
            bpy.context.view_layer.update()

            # Animate the text object to be visible
            text_object.hide_viewport = True
            text_object.hide_render = True
            text_object.keyframe_insert("hide_viewport", frame=(i) * 20)
            text_object.keyframe_insert("hide_render", frame=(i) * 20)

            # Animate the text object to be invisible
            text_object.hide_viewport = False
            text_object.hide_render = False
            text_object.keyframe_insert("hide_viewport", frame=(i) * 20 +1)
            text_object.keyframe_insert("hide_render", frame=(i) * 20 +1)

            # Animate the text object to be visible
            text_object.hide_viewport = True
            text_object.hide_render = True
            text_object.keyframe_insert("hide_viewport", frame=(i) * 20 + 20)
            text_object.keyframe_insert("hide_render", frame=(i) * 20 + 20)

        bpy.context.scene.frame_end = len(shape_keys) * 20

        print('------------------QC Animation END--------------------')


class ShapeEditor_OT_AnimateQC(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "animate.qc"
    bl_label = "Animate Shapekey QC"
    bl_description = "Animates all shapekeys over 20 frames each and adds their name as a text object"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.keying_tools = KeyingTools()

    def execute(self, context):
        self.keying_tools.animate_qc()

        return {'FINISHED'}


class ShapeEditor_OT_AnimateShapeKey20(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "animate.shapekey20"
    bl_label = "Animate Shapekey 0-1-0"
    bl_description = "Animates the shapekey over 20 frames, going from 0 to 1 and back to 0"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.keying_tools = KeyingTools()

    def execute(self, context):
        self.keying_tools.animate_shape_key_20()

        return {'FINISHED'}


class ShapeEditor_OT_AnimateShapeKey10(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "animate.shapekey10"
    bl_label = "Animate Shapekey 0-1"
    bl_description = "Animates the shapekey over 10 frames, going from 0 to 1"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.keying_tools = KeyingTools()

    def execute(self, context):
        self.keying_tools.animate_shape_key_10()

        return {'FINISHED'}


class ShapeEditor_OT_ClearShapeKeyKeyFramesAll(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "animate.clearkeyframesall"
    bl_label = "Animate Shapekey 0-1"
    bl_description = "Removes all keyframes from all the shapekeys"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.keying_tools = KeyingTools()

    def execute(self, context):
        self.keying_tools.clear_shape_key_keyframes()

        return {'FINISHED'}


class ShapeEditor_OT_ClearShapeKeyKeyFramesSelected(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "animate.clearkeyframesselected"
    bl_label = "Animate Shapekey 0-1"
    bl_description = "Removes all keyframes from the active shapekey"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.keying_tools = KeyingTools()

    def execute(self, context):
        self.keying_tools.clear_shape_key_keyframes_selected()

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_AnimateShapeKey20,
    ShapeEditor_OT_AnimateShapeKey10,
    ShapeEditor_OT_ClearShapeKeyKeyFramesAll,
    ShapeEditor_OT_ClearShapeKeyKeyFramesSelected,
    ShapeEditor_OT_AnimateQC,
]