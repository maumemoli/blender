import bpy

class CreateKeylineShader:
    def __init__(self):
        pass

    def create_keyline_shader(self, context):

        self.obj = context.object
        # Create a new material
        keyline_material = bpy.data.materials.new(name="keyline_shader")
        keyline_material.use_nodes = True

        # Get the material's node tree
        node_tree = keyline_material.node_tree

        # Create a texture coordinate node
        tex_coords = node_tree.nodes.new(type='ShaderNodeTexCoord')

        # Create a mapping node and a texture image node
        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
        image_texture = node_tree.nodes.new(type='ShaderNodeTexImage')

        # Set the image texture's image and use_alpha properties
        image_texture.image = bpy.data.images.load(self.obj.keyline_path)

        # Create a principled BSDF node
        principled_bsdf = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')

        # Connect the nodes
        node_tree.links.new(tex_coords.outputs['UV'], mapping.inputs['Vector'])
        node_tree.links.new(mapping.outputs['Vector'], image_texture.inputs['Vector'])
        node_tree.links.new(image_texture.outputs['Color'], principled_bsdf.inputs['Base Color'])
        node_tree.links.new(principled_bsdf.outputs['BSDF'], node_tree.nodes['Material Output'].inputs['Surface'])

        # Set the active object's material
        bpy.context.object.active_material = keyline_material


class ShapeEditor_OT_AssignKeylineShader(bpy.types.Operator):
    """Aligns meshes in a grid"""
    bl_idname = "shapeup.keylineshader"
    bl_label = "Assign Keyline Shader"

    def execute(self, context):
        self.keyline_shader = CreateKeylineShader()

        self.keyline_shader.create_keyline_shader(context)


        return {'FINISHED'}



registry = [
    ShapeEditor_OT_AssignKeylineShader,
]