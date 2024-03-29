import bpy
l0 = bpy.context.user_preferences.system.solid_lights[0]
l1 = bpy.context.user_preferences.system.solid_lights[1]
l2 = bpy.context.user_preferences.system.solid_lights[2]

l0.use = False
l0.diffuse_color = (0.800000011920929, 0.800000011920929, 0.800000011920929)
l0.specular_color = (0.5, 0.5, 0.5)
l0.direction = (-0.8920000195503235, 0.30000001192092896, 0.8999999761581421)
l1.use = False
l1.diffuse_color = (0.43799999356269836, 0.503000020980835, 0.6000000238418579)
l1.specular_color = (0.17000000178813934, 0.18199999630451202, 0.20000000298023224)
l1.direction = (0.5879999995231628, 0.46000000834465027, 0.24799999594688416)
l2.use = True
l2.diffuse_color = (0.0, 0.0, 0.0)
l2.specular_color = (0.0, 0.0, 0.0)
l2.direction = (0.2160000056028366, -0.3919999897480011, -0.2160000056028366)
