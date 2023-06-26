import bpy
l0 = bpy.context.user_preferences.system.solid_lights[0]
l1 = bpy.context.user_preferences.system.solid_lights[1]
l2 = bpy.context.user_preferences.system.solid_lights[2]

l0.use = True
l0.diffuse_color = (0.2734818160533905, 0.2734818160533905, 0.2734818160533905)
l0.specular_color = (0.08726591616868973, 0.08726591616868973, 0.08726591616868973)
l0.direction = (-0.1962616741657257, 0.14018690586090088, 0.9704787135124207)
l1.use = True
l1.diffuse_color = (0.034023139625787735, 0.47012192010879517, 0.7035157084465027)
l1.specular_color = (0.18021363019943237, 0.18021363019943237, 0.18021363019943237)
l1.direction = (0.3925233483314514, -0.018691588193178177, 0.9195520877838135)
l2.use = True
l2.diffuse_color = (0.06648899614810944, 0.18567109107971191, 0.30099421739578247)
l2.specular_color = (0.17069436609745026, 0.17069436609745026, 0.17069436609745026)
l2.direction = (-0.30841121077537537, 0.7102803587913513, 0.6327592730522156)