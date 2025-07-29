import bpy

from ..utils.drivers import Drivers
from ..utils.shape_selection import ShapeSelection
from ..utils.shape_processing import ShapePrecessing
from ..utils.mesh_selection import MeshSelection
from ..utils.mesh_processing import MeshProcessing


class ShapeUpdate:
    def __init__(self):
        self.meshselect = MeshSelection()
        self.meshprocess = MeshProcessing()
        self.shapeselect = ShapeSelection()
        self.shapeprocess = ShapePrecessing()
        self.driverss = Drivers()

        self.selected_meshes = self.meshselect.get_selected_meshes()
        self.active_mesh = self.meshselect.get_active_mesh()
        self.active_mesh_shapes = self.shapeselect.shape_key_names_list(self.active_mesh.name)

        self.hero_shapes = []
        self.hero_shapes_existing = []

        self.negative_shapes = []
        self.negative_shapes_existing = []

        self.inbetweens = []
        self.inbetweens_existing = []
        self.inbetweens_raw = []
        self.inbetweens_homes = []
        self.inbetweens_partial = []
        self.inbetweens_missing = []
        self.inbetweens_connected = []
        self.inbetweens_to_swap = []

        self.correctives = []
        self.correctives_raw = []
        self.correctives_home = []
        self.correctives_existing = []
        self.correctives_difference = []
        self.correctives_names = []
        self.correctives_sculpt = []
        self.missing_heros = []
        self.all_shapes = self.hero_shapes + self.correctives

    def order_list(self, lst):
        # Create a set to remove duplicates
        s = set()

        # Create a new list with only the unique elements from lst, in the same order
        filtered_lst = [x for x in lst if x not in s and (s.add(x) or True)]

        # Sort the list based on the numerals in the name and the alphabetical order
        def extract_num_and_name(s):
            parts = s.split('_')
            name = parts[0]
            if len(parts) > 1:
                try:
                    num = int(parts[1])
                except ValueError:
                    num = float('inf')
            else:
                num = float('inf')
            return (name, num)

        sorted_lst = sorted(filtered_lst, key=extract_num_and_name)

        return sorted_lst

    def set_home(self, corrective_list, home):
        # Get the object with the matching name
        obj = bpy.data.objects[home]

        # Iterate over the items in the corrective list
        for item in corrective_list:

            # Set the shape key values for the object
            for shape_key in obj.data.shape_keys.key_blocks:
                shape_key.value = 0
                # Create a new shape key from mix on the new object

            # Create a duplicate of the object with the name of the item before it was split + "raw"
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            new_obj.name = item + "_clean_home"
            new_obj.shape_key_add(name="Mix")

            # Apply all the shape keys to the new object
            for shape_key in new_obj.data.shape_keys.key_blocks:
                new_obj.shape_key_remove(shape_key)

            bpy.context.collection.objects.link(new_obj)

            self.correctives_home.append(new_obj.name)
            self.correctives_names.append(item)

    def set_inbetween_home(self, corrective_list, home):
        # Get the object with the matching name
        obj = bpy.data.objects[home]

        # Iterate over the items in the corrective list
        for item in corrective_list:

            # Set the shape key values for the object
            for shape_key in obj.data.shape_keys.key_blocks:
                shape_key.value = 0
                # Create a new shape key from mix on the new object

            # Create a duplicate of the object with the name of the item before it was split + "raw"
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            new_obj.name = item + "_clean_home"
            new_obj.shape_key_add(name="Mix")

            # Apply all the shape keys to the new object
            for shape_key in new_obj.data.shape_keys.key_blocks:
                new_obj.shape_key_remove(shape_key)

            bpy.context.collection.objects.link(new_obj)

            self.inbetweens_homes.append(new_obj.name)

    def set_combo_keys_new(self, corrective, home):
        # This will get a dict of shape names and values to set, as corrective_list.
        # After setting the values it will bake the mesh, name it as name_raw and add it to a list '...raw'
        # Get the object with the matching name
        obj = bpy.data.objects[home]

        shape_values_to_set = self.shapeselect.shape_name_value_dict(corrective)
        self.shapeprocess.set_shape_key_values(shape_values_to_set)
        # Below is needed to actually get the driver values.
        bpy.context.evaluated_depsgraph_get()
        # Muting the combo in question, else the diff mesh will be empty every other time
        for shape_key in obj.data.shape_keys.key_blocks:
            if shape_key.name == str(corrective).strip("['']"):
                obj.data.shape_keys.key_blocks[str(corrective).strip("['']")].mute = True
        # Create a new shape key from mix on the new object
        # Create a duplicate of the object with the name of the item before it was split + "raw"
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        new_obj.name = str(corrective).strip("['']") + "_Raw"
        new_obj.shape_key_add(name="Mix")

        # Apply all the shape keys to the new object
        for shape_key in new_obj.data.shape_keys.key_blocks:
            new_obj.shape_key_remove(shape_key)

        bpy.context.collection.objects.link(new_obj)

        self.correctives_raw.append(new_obj)
        print(f"-------- set_combo_keys_new function: New Raw is {new_obj}")

    def set_inbetween_keys_new(self, corrective, home):
        # This will get a dict of shape names and values to set, as corrective_list.
        # After setting the values it will bake the mesh, name it as name_raw and add it to a list '...raw'
        # Get the object with the matching name
        obj = bpy.data.objects[home]
        print(f"------set_inbetween_keys_new function: These are the shape values to set{type(corrective)}")
        shape_values_to_set = self.shapeselect.shape_name_value_dict(corrective)
        print(f"------set_inbetween_keys_new function: These are the shape values to set{shape_values_to_set}")
        print(f"------set_inbetween_keys_new function: This is the name I need to add raw to {str(corrective)}")
        self.shapeprocess.set_shape_key_values(shape_values_to_set)

        # Create a new shape key from mix on the new object
        # Create a duplicate of the object with the name of the item before it was split + "raw"
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        new_obj.name = str(corrective).strip("['']") + "_Raw"
        new_obj.shape_key_add(name="Mix")

        # Apply all the shape keys to the new object
        for shape_key in new_obj.data.shape_keys.key_blocks:
            new_obj.shape_key_remove(shape_key)

        bpy.context.collection.objects.link(new_obj)

        self.inbetweens_raw.append(new_obj.name)
        print(f"------set_inbetween_keys_new function: New Raw is {new_obj.name}")

    def update_shapes(self, context, selected_meshes, active_mesh):

        self.scene = context.object

        for name in selected_meshes:
            if self.shapeselect.check_if_hero(name):
                self.hero_shapes.append(name)
            elif self.shapeselect.check_if_negative(name):
                self.negative_shapes.append(name)
            elif self.shapeselect.check_if_inbetween(name):
                self.inbetweens.append(name)
            elif self.shapeselect.check_if_combination(name):
                self.correctives.append(name)

        # ----------Hero Update Below---------------
        print("------HERO SHAPE UPDATE-------")

        for shape in self.shapeselect.shape_key_exists(self.hero_shapes, active_mesh.name):
            self.hero_shapes_existing.append(shape)

        self.shapeprocess.remove_shape_keys(self.hero_shapes_existing, active_mesh.name)

        self.shapeprocess.join_as_shapes(self.hero_shapes, active_mesh.name)

        for obj in bpy.data.objects:
            try:
                for fc in obj.data.shape_keys.animation_data.drivers:
                    fc.driver.expression = fc.driver.expression
            except:
                pass

        # ----------Negative Update Below---------------
        print("------NEGATIVE SHAPE UPDATE-------")
        for shape in self.shapeselect.shape_key_exists(self.negative_shapes, active_mesh.name):
            self.negative_shapes_existing.append(shape)
        print(f"adding these negative shapes: {self.negative_shapes}")

        self.shapeprocess.remove_shape_keys(self.negative_shapes_existing, active_mesh.name)
        print(f"removed these existing negative shapes{self.negative_shapes_existing}")

        # Insert warning here, if shapes are not being added due to missing heros
        for shape in self.negative_shapes:
            if shape.strip('N') not in self.shapeselect.shape_key_names_list(active_mesh.name):
                print(f"There's no hero shape for this negative shape to be added {shape}")
                self.negative_shapes.remove(shape)

        self.shapeprocess.join_as_shapes(self.negative_shapes, active_mesh.name)
        print(f"joined these negative shapes{self.negative_shapes}")

        self.shapeprocess.rename_negative_shapes(self.negative_shapes, '_temp')
        print(f"renamed these negative shapes{self.negative_shapes} to name_temp")

        for shape in self.negative_shapes:
            shapes_to_set = []
            shapes_to_set.append(shape + '_temp')
            shapes_to_set.append(shape[:-1])
            shapes_to_remove = []
            shapes_to_remove.append(shape + '_temp')
            self.shapeprocess.set_shape_keys(shapes_to_set, active_mesh.name)
            self.shapeprocess.create_shape_mix(active_mesh.name, shape)

            self.driverss.disconnect_shape_key_drivers(shapes_to_remove, active_mesh.name)

            self.shapeprocess.remove_shape_keys(shapes_to_remove, active_mesh.name)
            self.shapeprocess.set_shapekey_min_value(shape)

            self.driverss.disconnect_shape_key_drivers([shape], active_mesh.name)

            self.driverss.create_inbetween_driver(active_mesh, shape, shape[:-1], '-' + shape[:-1])
        # ----------Inbetween Update Below---------------
        print("------INBETWEEN SHAPE UPDATE-------")
        print(f"inbetweens to check are: {self.inbetweens}")
        for shape in self.shapeselect.shape_key_exists(self.inbetweens, active_mesh.name):
            self.inbetweens_existing.append(shape)
        print(f"these inbetweens exists: {self.inbetweens_existing}")

        self.shapeprocess.remove_shape_keys(self.inbetweens_existing, active_mesh.name)
        #  self.shapeprocess.join_as_shapes(self.inbetweens_existing, active_mesh.name)

        for shape in self.shapeselect.missing_inbetween_list(self.inbetweens, active_mesh.name):
            self.inbetweens_missing.append(shape)
        print(f"hero shapes have missing inbetweens for these shapes: {self.inbetweens_missing}")

        for shape in list(set(self.inbetweens_missing)):
            self.inbetweens_to_swap.append(shape.split("_")[0])

        for shape in list(set(self.inbetweens_to_swap)):
            self.shapeprocess.swap_shapes(shape, active_mesh.name)

        # Creating raw inbetweens
        for shape in list(set(self.inbetweens)):
            print(f"---------This need to become a raw shape - {[shape]}")
            self.set_inbetween_keys_new([shape], active_mesh.name)

        # Renaming to _sculpt
        self.inbetweens_sculpt_names = [shape + "_sculpt" for shape in self.inbetweens]
        self.meshprocess.rename_objects(self.inbetweens, self.inbetweens_sculpt_names)

        # Creating clean homes with the names if the inbetweens named _clean_home
        self.set_inbetween_home(list(set(self.inbetweens)), active_mesh.name)

        self.meshprocess.rename_objects(self.inbetweens_homes, self.inbetweens)

        for i, shape in enumerate(list(set(self.inbetweens))):
            print(f"---------passing this for inbetween delta exrtact - {self.inbetweens_raw[i]}")
            print(f"---------passing this for inbetween delta exrtact - {type(self.inbetweens_raw[i])}")
            self.meshprocess.mesh_difference(self.inbetweens_sculpt_names[i], self.inbetweens_raw[i],
                                             self.inbetweens[i])

        for shape in self.shapeselect.connected_inbetween_list(self.inbetweens, active_mesh.name):
            self.inbetweens_connected.append(shape)
        print(f"these are connected inbetweens on the mesh{list(set(self.inbetweens_connected))}")

        # Creating a list with further inbetweens to join (inbetweens which do not exist)
        # Also creating a list for all the relevant inbetweens (the ones to join as well as the ones connected upstream / downstream)
        self.inbetweens_not_existing = [shape for shape in self.inbetweens if shape not in self.inbetweens_existing]
        self.inbetweens_all = self.inbetweens + self.inbetweens_connected

        print(f"disconnecting the drivers for all inbetweens: {self.inbetweens_all}")
        self.driverss.disconnect_shape_key_drivers(self.inbetweens_all, active_mesh.name)

        # Currently deleting all drivers. Might just need to delete drivers for connected and maybe missing
        inbetween_dictionary = self.shapeselect.create_inbetween_dict(self.inbetweens_all)

        print(f"I want to join these inbnetweens {self.inbetweens_not_existing}")
        # Commenting out in an attempt to fix te inbetween issue bug
        #self.shapeprocess.join_as_shapes(self.inbetweens_not_existing, active_mesh.name)
        self.shapeprocess.join_as_shapes(self.inbetweens, active_mesh.name)

        for key, shape_list in inbetween_dictionary.items():

            print(f"for this hero shape: {key}")
            print(f"this shape list: {list(set(shape_list))}")

            sorted_shapes = self.order_list(shape_list)

            drivers = self.driverss.inbetween_expression(key, sorted(list(set(shape_list))))

            print(f"these are the drivers {drivers}")

            for i, shape in enumerate(sorted_shapes):
                last_inbetween_expression = drivers[-1]
                print(f"this is what I want to pass to the downstream function {sorted_shapes}")
                inbetweens_downstream = self.driverss.inbetweens_smaller(shape, sorted_shapes)
                inbetween_expression = drivers[i] + "- (" + " + ".join(inbetweens_downstream) + ")"
                inbetween_drivers = shape_list
                inbetween_drivers.append(key)
                inbetween_drivers.remove(shape)

                if shape.endswith("_100"):
                    self.driverss.create_inbetween_driver(active_mesh, shape, key, last_inbetween_expression)
                else:
                    self.driverss.create_shape_key_driver(active_mesh, shape, inbetween_expression,
                                                          list(set(inbetween_drivers)))

                print(f"this is the shape  - {shape} with the number {i}")
                print(f"I'm gonna create this expression {drivers[i]} for this shapekey {shape}.")

        for mesh in self.inbetweens_raw:
            print(f"----Deleting {mesh}")
            self.meshprocess.remove_mesh(mesh)

        for mesh in self.inbetweens:
            print(f"----Deleting {mesh}")
            self.meshprocess.remove_mesh(mesh)

        self.meshprocess.rename_objects([name + "_sculpt" for name in self.inbetweens], self.inbetweens)

        # ----------Corrective Update Below---------------
        print("------CORRECTIVE SHAPE UPDATE-------")
        for shape in self.shapeselect.shape_key_exists(self.correctives, active_mesh.name):
            self.correctives_existing.append(shape)

        for shape in self.shapeselect.check_combos_list(self.correctives, self.active_mesh_shapes):
            self.missing_heros.append(shape)
            self.correctives.remove(shape)
            if not self.shapeselect.check_if_inbetween_combinations(shape, self.inbetweens_existing):
                self.correctives.append(shape)
                self.missing_heros.remove(shape)
            print(f"----Missing hero shapes for combos are: {self.missing_heros}")

        # Creating a Raw combo from the hero shapes, adding raw heroes to a combined list

        print(f'-----Sending {self.correctives} to get a raw combo')
        for shape in list(set(self.correctives)):
            self.set_combo_keys_new([shape], active_mesh.name)

        # I think the next line is safe to remove but I'll keep it as a comment for now
        #self.set_combo_keys_new(list(set(self.correctives)), active_mesh.name)
        print(f'-----Got {self.correctives_raw} as a raw combo')
        print(f'-----Removing {self.correctives_existing} because it exists')
        self.shapeprocess.remove_shape_keys(self.correctives_existing, active_mesh.name)

        # Create clean homes for each shape
        print(f'-----Sending {self.correctives} to get a clean home')
        self.set_home(list(set(self.correctives)), active_mesh.name)

        for shape in list(set(self.correctives)):
            self.correctives_sculpt.append(shape)

        print(f"-----Renaming {self.correctives_sculpt} to name_sculpt")
        self.meshprocess.rename_correctives(self.correctives_sculpt, self.correctives_sculpt)
        print(f"-----Renaming {self.correctives_home} to {self.correctives_names}")
        self.meshprocess.rename_objects(self.correctives_home, self.correctives_names)

        for i, shape in enumerate(self.correctives_names):
            print("--------------DIFFERENCE EXTRACT----------------")
            print(f"sculpt is: {self.correctives_sculpt[i] + '_sculpt'}")
            print(f"raw is: {self.correctives_raw[i].name}")
            print(f"home is: {self.correctives_names[i]}")
            self.meshprocess.mesh_difference(self.correctives_sculpt[i] + '_sculpt', self.correctives_raw[i].name,
                                             self.correctives_names[i])
        print(f"correctives_names are {self.correctives_names} and correctives are {self.correctives}")
        self.shapeprocess.join_as_shapes(self.correctives, active_mesh.name)

        for mesh in self.correctives_raw:
            print(f"----Deleting {mesh.name}")
            self.meshprocess.remove_mesh(mesh.name)

        for mesh in self.correctives:
            print(f"----Deleting {mesh}")
            self.meshprocess.remove_mesh(mesh)

        self.meshprocess.rename_objects([name + "_sculpt" for name in self.correctives], self.correctives)

        self.driverss.disconnect_shape_key_drivers(self.correctives_names, active_mesh.name)

        for shape in self.correctives_names:
            #hero_drivers = shape.split("_")
            hero_drivers = self.shapeselect.get_combination_drivers(shape)
            for s in hero_drivers:
                if s.endswith('N'):
                    combo_expression = self.driverss.average_expression_N(hero_drivers)
                else:
                    if self.scene.expression_type == 'OP1':
                        combo_expression = self.driverss.average_expression_B(hero_drivers)
                    elif self.scene.expression_type == 'OP2':
                        combo_expression = self.driverss.average_expression_C(hero_drivers)
                    elif self.scene.expression_type == 'OP3':
                        combo_expression = self.driverss.average_expression(hero_drivers)

            self.driverss.create_shape_key_driver(active_mesh, shape, combo_expression, hero_drivers)

    def update_decomposed_shapes(self, context, active_mesh):

        self.all_shapes = self.shapeselect.shape_key_list_all()
        self.scene = context.object

        for name in self.all_shapes:
            print(name)
            if self.shapeselect.check_if_hero(name):
                self.hero_shapes.append(name)
            elif self.shapeselect.check_if_negative(name):
                self.negative_shapes.append(name)
            elif self.shapeselect.check_if_inbetween(name):
                self.inbetweens.append(name)
            elif self.shapeselect.check_if_combination(name):
                self.correctives.append(name)


        # ----------Negative Update Below---------------

        self.shapeprocess.rename_negative_shapes(self.negative_shapes, '_temp')
        print(f"renamed these negative shapes{self.negative_shapes} to name_temp")

        for shape in self.negative_shapes:
            shapes_to_set = []
            shapes_to_set.append(shape + '_temp')
            shapes_to_set.append(shape[:-1])
            shapes_to_remove = []
            shapes_to_remove.append(shape + '_temp')
            self.shapeprocess.set_shape_keys(shapes_to_set, active_mesh.name)
            self.shapeprocess.create_shape_mix(active_mesh.name, shape)
            self.shapeprocess.remove_shape_keys(shapes_to_remove, active_mesh.name)
            self.shapeprocess.set_shapekey_min_value(shape)

            self.driverss.disconnect_shape_key_drivers([shape], active_mesh.name)
            self.driverss.create_inbetween_driver(active_mesh, shape, shape[:-1], '-' + shape[:-1])
        # ----------Inbetween Update Below---------------
        # print(f"inbetweens to check are: {self.inbetweens}")
        #
        # for shape in list(set(self.inbetweens)):
        #     self.inbetweens_to_swap.append(shape.split("_")[0])
        # # Creating _100 shapes
        # for shape in list(set(self.inbetweens_to_swap)):
        #     self.shapeprocess.swap_shapes(shape, active_mesh.name)
        #
        # for shape in self.shapeselect.connected_inbetween_list(self.inbetweens, active_mesh.name):
        #     self.inbetweens_connected.append(shape)
        # print(f"these are connected inbetweens on the mesh{list(set(self.inbetweens_connected))}")
        #
        # # Creating a list with further inbetweens to join (inbetweens which do not exist)
        # # Also creating a list for all the relevant inbetweens (the ones to join as well as the ones connected upstream / downstream)
        #
        # self.inbetweens_all = self.inbetweens + self.inbetweens_connected
        #
        # print(f"disconnecting the drivers for all inbetweens: {self.inbetweens_all}")
        # self.driverss.disconnect_shape_key_drivers(self.inbetweens_all, active_mesh.name)
        #
        #
        # # Currently deleting all drivers. Might just need to delete drivers for connected and maybe missing
        # inbetween_dictionary = self.shapeselect.create_inbetween_dict(self.inbetweens_all)
        # print(f"--------INBETWEEN DICT: {inbetween_dictionary}")
        # for key, shape_list in inbetween_dictionary.items():
        #
        #     print(f"for this hero shape: {key}")
        #     print(f"this shape list: {list(set(shape_list))}")
        #
        #     sorted_shapes = self.order_list(shape_list)
        #
        #     drivers = self.driverss.inbetween_expression(key, sorted(list(set(shape_list))))
        #
        #     print(f"these are the drivers {drivers}")
        #
        #     for i, shape in enumerate(sorted_shapes):
        #         last_inbetween_expression = drivers[-1]
        #         print(f"this is what I want to pass to the downstream function {sorted_shapes}")
        #         inbetweens_downstream = self.driverss.inbetweens_smaller(shape, sorted_shapes)
        #         inbetween_expression = drivers[i] + "- (" + " + ".join(inbetweens_downstream) + ")"
        #         inbetween_drivers = shape_list
        #         inbetween_drivers.append(key)
        #         inbetween_drivers.remove(shape)
        #
        #         if shape.endswith("_100"):
        #             self.driverss.create_inbetween_driver(active_mesh, shape, key, last_inbetween_expression)
        #         else:
        #             self.driverss.create_shape_key_driver(active_mesh, shape, inbetween_expression,
        #                                                   list(set(inbetween_drivers)))
        #
        #         print(f"this is the shape  - {shape} with the number {i}")
        #         print(f"I'm gonna create this expression {drivers[i]} for this shapekey {shape}.")


        # ---------- Decomposed Corrective Update Below---------------


        self.driverss.disconnect_shape_key_drivers(self.correctives_names, active_mesh.name)

        for shape in self.correctives:
            hero_drivers = shape.split("_")
            #combo_expression = self.driverss.average_expression_B(hero_drivers)
            if self.scene.expression_type == 'OP1':
                combo_expression = self.driverss.average_expression_B(hero_drivers)
            elif self.scene.expression_type == 'OP2':
                combo_expression = self.driverss.average_expression_C(hero_drivers)
            elif self.scene.expression_type == 'OP3':
                combo_expression = self.driverss.average_expression(hero_drivers)

            self.driverss.create_shape_key_driver(active_mesh, shape, combo_expression, hero_drivers)

class ShapeEditor_OT_UpdateShape(bpy.types.Operator):
    """Updates the shapekey and connects drivers according to naming conventions"""
    bl_idname = "shapeeditor.updateshape"
    bl_label = "Update Shape"
    bl_description = "Update shape keys based on naming convention, to get drivers and act as either " \
                     "combination or inbetween"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.update = ShapeUpdate()
        self.meshselect = MeshSelection()
        self.selected_meshes = self.meshselect.get_selected_meshes()
        self.active_mesh = self.meshselect.get_active_mesh()

    def execute(self, context):
        self.update = ShapeUpdate()
        self.update.update_shapes(context, self.selected_meshes, self.active_mesh)

        return {'FINISHED'}

class ShapeEditor_OT_UpdateDecomposedShape(bpy.types.Operator):
    """Updates the shapekey and connects drivers according to naming conventions"""
    bl_idname = "shapeeditor.updatedecomposedshape"
    bl_label = "Update Decomposed Shapes"
    bl_description = "Update decomposed shape keys based on naming convention, to get drivers and act as either " \
                     "combination or inbetween"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def __init__(self):
        self.update = ShapeUpdate()
        self.meshselect = MeshSelection()
        self.selected_meshes = self.meshselect.get_selected_meshes()
        self.active_mesh = self.meshselect.get_active_mesh()

    def execute(self, context):
        self.update = ShapeUpdate()
        self.update.update_decomposed_shapes(context,  self.active_mesh)

        return {'FINISHED'}


registry = [
    ShapeEditor_OT_UpdateShape,
    ShapeEditor_OT_UpdateDecomposedShape,
]