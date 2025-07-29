bl_info = {
	"name": "ShapeUp",
	"author": "Dan Ulrich, Bogi Piroth",
	"version": (0, 2, 10),
	"blender": (3, 1, 0),
	"location": "View3D -> ShapeUp",
	"description": "Create edit and mix facial shapekeys",
	"category": "Rigging",
	"doc_url": "",
	"tracker_url": "",
}

import importlib
from bpy.utils import register_class, unregister_class


from . import ui
from . import ui_lists
from .operators import export_shapes
from .operators import shape_operators
from .operators import mesh_operators
from .operators import update_shapes
from .operators import update_base
from .operators import build_mimic
from .utils import drivers
from .utils import mesh_selection
from .utils import mesh_processing
from .utils import shape_selection
from .utils import shape_processing
from .extras import grid_align
from .extras import assign_keyline_shader
from .extras import keying_tools
from .extras import shader_facegroups
from .extras import quickset


# Each module can have register() and unregister() functions and a list of classes to register called "registry".
modules = [
	ui,
	ui_lists,
	export_shapes,
	shape_operators,
	mesh_operators,
	update_shapes,
	update_base,
	build_mimic,
	drivers,
	mesh_selection,
	mesh_processing,
	shape_selection,
	shape_processing,
	grid_align,
	assign_keyline_shader,
	keying_tools,
	shader_facegroups,
	quickset
]

def register_unregister_modules(modules: [], register: bool):
	register_func = register_class if register else unregister_class

	for m in modules:
		if register:
			importlib.reload(m)
		if hasattr(m, 'registry'):
			for c in m.registry:
				register_func(c)

		if hasattr(m, 'modules'):
			register_unregister_modules(m.modules, register)

		if register and hasattr(m, 'register'):
			m.register()
		elif hasattr(m, 'unregister'):
			m.unregister()

def register():
	register_unregister_modules(modules, register=True)

def unregister():
	register_unregister_modules(modules, register=False)