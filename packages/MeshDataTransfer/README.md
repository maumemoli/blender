# Mesh Data Transfer

**Mesh Data Transfer** is a Blender add-on that transfers mesh data (vertex positions/shape, UV maps, shape keys, and vertex groups) from one mesh object to another using configurable sampling strategies.

It is designed for workflows where the topology of the source and target meshes differs — retopology, remeshing, projection of sculpted detail, or copying rigging data between characters. The add-on can sample the source mesh in its rest state or in a deformed state (modifiers + shape keys evaluated), in local or world space, and constrained by a vertex group or the edit-mode selection.

- **Blender minimum version:** 4.2.0
- **Extension ID:** `mesh_data_transfer`
- **Version:** 2.0.9
- **License:** GPL-3.0-or-later
- **Author / Maintainer:** Maurizio Memoli
- **Video demo:** <https://www.youtube.com/watch?v=CvMeK_IIw-Y>

---

## Table of contents

1. [Installation](#installation)
2. [Quick start](#quick-start)
3. [The UI panel](#the-ui-panel)
4. [Search methods](#search-methods)
5. [Attributes to transfer](#attributes-to-transfer)
6. [Transfer options](#transfer-options)
7. [Masking with vertex groups and selection](#masking-with-vertex-groups-and-selection)
8. [Rigging helpers (shape key drivers)](#rigging-helpers-shape-key-drivers)
9. [Operators reference](#operators-reference)
10. [Python API](#python-api)
11. [How it works](#how-it-works)
12. [Tips, limitations and troubleshooting](#tips-limitations-and-troubleshooting)
13. [File layout](#file-layout)

---

## Installation

### From the Blender extension platform

Search for **Mesh Data Transfer** in *Edit → Preferences → Get Extensions* and install it.

### From a local build (`.zip`)

1. Package the `MeshDataTransfer` folder as an extension using the Blender command line:

   ```bash
   blender --command extension build
   ```

   This produces a `.zip` archive in the add-on directory.

2. In Blender, open *Edit → Preferences → Add-ons* (or *Get Extensions → Install from Disk*) and select the generated `.zip`.
3. Enable the add-on.

### Manual (development) install

Copy the `MeshDataTransfer` directory into your Blender `scripts/addons` folder, then enable it from *Edit → Preferences → Add-ons*.

---

## Quick start

1. Select the **target** object (the one that receives the data) so it is the active object.
2. Open *Properties → Object Data Properties* and expand the **Mesh Data Transfer** panel.
3. Set **Source** to the mesh you want to sample data from.
4. Choose a **Search method** (e.g. *Closest*, *Raycast*, or *Vertex ID* for matching topology).
5. Choose the **Attribute to transfer** (Shape, UV set, Shape Keys, Vertex Groups).
6. Optionally restrict the transfer with a vertex group and/or the edit-mode selection.
7. Click **Transfer Mesh Data**.

---

## The UI panel

The panel lives in **Object Data Properties** (`bpy.types.DATA_PT_mesh_data_transfer`) and is only shown when the active object is a mesh. It is collapsed by default.

```
┌─ Mesh Data Transfer ──────────────────────────────┐
│  SEARCH METHOD                                    │
│  [Closest] [Raycast] [Vertex ID] [Active UV]      │
│                                                   │
│  ATTRIBUTE TO TRANSFER                            │
│  [Shape] [snap] [as key]   [UV set]               │
│  [Shape Keys] [snap] [muted] [Vertex Groups] [lock]│
│                                                   │
│  Source: [ Object ] [World/Local] [Deformed]      │
│  Vertex Group: [ group ] [invert]                 │
│  [selection]  [ Transfer Mesh Data ]              │
│                                                   │
│  ▸ RIGGING HELPERS                                │
│      Source Armature: [ ... ]                     │
│      Target Armature: [ ... ]                     │
│      [ Transfer Shape Keys drivers ]              │
└───────────────────────────────────────────────────┘
```

### Search method row

Four icon buttons select the sampling strategy. Depending on the method they may be **disabled** when they cannot work:

- *Vertex ID* (Topology) is only enabled when the **source** is set and both meshes have the **same vertex count**.
- *Active UV* is disabled when the attribute to transfer is *UV set*, and only enabled when the source has an active UV layer.

### Attribute row

Four mutually exclusive attribute buttons, each with associated toggles:

| Button | Toggle | Meaning |
| --- | --- | --- |
| **Shape** | Snap (closest) | Snap transferred vertices to the nearest source vertex |
| | Shape key | Store the result as a shape key instead of moving vertices |
| **Shape Keys** | Snap (closest) | Snap transferred shape-key vertices to the source shape key |
| | Exclude muted | Skip muted shape keys during transfer |
| **UV set** | — | Transfer UV coordinates |
| **Vertex Groups** | Exclude locked | Skip locked vertex groups |

### Source / space row

- **Source** — the object data is sampled from (the active object is excluded from the picker).
- **World/Local** toggle (`World` icon) — sample in world space when enabled, object-local space otherwise.
- **Deformed source** (`MOD_MESHDEFORM` icon) — sample the source mesh **after** its modifiers and shape keys are evaluated.

### Vertex group filter row

- **Vertex Group** — restrict the transfer using a vertex group on the active object.
- **Invert** (`ARROW_LEFTRIGHT` icon) — invert the group weights used as the mask.

### Transfer row

- **Edit-mode selection** (`RESTRICT_SELECT` icon) — restrict the transfer to vertices selected in edit mode.
- **Transfer Mesh Data** — runs `object.transfer_mesh_data`.

### Rigging helpers

A collapsible sub-section (collapsed by default), containing source/target armature pickers and the **Transfer Shape Keys drivers** operator. In Blender versions `<= 4.1` this uses a custom expand toggle; in `> 4.1` it uses the standard sub-panel API.

---

## Search methods

The search method determines how a point on the target mesh is mapped onto the source mesh. It is defined by the `search_method` enum:

| Identifier | UI label | Description |
| --- | --- | --- |
| `CLOSEST` | **Closest** | Finds the nearest point on the source surface for each target vertex. Good general-purpose method for arbitrary topology. |
| `RAYCAST` | **Raycast** | Bidirectional projection along the target vertex normal; if the ray misses, it is cast in the opposite direction. Best for surfaces facing each other. |
| `TOPOLOGY` | **Vertex ID** | Matches vertices by their index. Requires identical vertex counts on source and target. Transfer is a direct 1:1 copy. |
| `UVS` | **Active UV** | Samples the source in UV space. The source is reconstructed in UV coordinates (each UV loop becomes a point at `(u, v, 0)`) and the closest-point search runs in that space. When UV sampling is active the method is forced to `CLOSEST` internally. |

### Choosing a method

- **Retopology onto the same silhouette** → *Closest* or *Raycast*.
- **Same topology, different shapes** (e.g. two characters sharing a base mesh) → *Vertex ID*.
- **Transferring UV seams / matching UV layouts** → *Active UV*.
- **Raycast** is usually the most accurate when the source and target roughly face each other; **Closest** is more robust for concave/complex shapes.

---

## Attributes to transfer

The `attributes_to_transfer` enum controls which data the operator writes to the target.

| Identifier | UI label | What it does |
| --- | --- | --- |
| `SHAPE` | **Shape** | Transfers vertex positions. Can optionally be written to a shape key. |
| `UVS` | **UV set** | Transfers UV coordinates via a temporary Data Transfer modifier. |
| `SHAPE_KEYS` | **Shape Keys** | Transfers all (non-basis, optionally non-muted) shape keys as deltas. |
| `VERTEX_GROUPS` | **Vertex Groups** | Transfers vertex group weights. |

### Shape

Calls `MeshDataTransfer.transfer_vertex_position()`. Every target vertex is projected onto the source and its position replaced (respecting the active mask).

If **Transfer as shape key** is enabled, the result is stored in a shape key named `<SourceObjectName>.Transferred` and activated, leaving the base mesh untouched.

### UV set

Calls `MeshDataTransfer.transfer_uvs()`. This:

1. Temporarily marks seam islands on the source (`mark_seam_islands`).
2. Creates a **Data Transfer** modifier on the target configured for `UV` loop data and seam edge data.
3. Picks the mapping based on the search method:
   - `CLOSEST` → `POLYINTERP_NEAREST` / `NEAREST`
   - `RAYCAST` → `POLYINTERP_LNORPROJ` / `POLYINTERP_PNORPROJ`
   - `TOPOLOGY` → `TOPOLOGY`
4. Applies the modifier and restores the original source seams.

A vertex-group mask, if present, is temporarily baked into a vertex group used by the modifier and removed afterwards.

### Shape Keys

Calls `MeshDataTransfer.transfer_shape_keys()`. For each shape key on the source:

1. Sample the source shape-key positions (rest state, or deformed snapshot when *Deformed source* is on).
2. Project them onto the source surface, extract the **delta** relative to the transferred base position.
3. Blend with any existing target shape key of the same name using the inverted mask.
4. Write the resulting positions to a target shape key of the same name, preserving the source `slider_min` / `slider_max`.

The `Basis` key is created automatically if the target has no shape keys. Muted keys are skipped when *Exclude muted* is enabled. If driver transfer is enabled, shape key drivers are copied as well (see below).

### Vertex Groups

Calls `MeshDataTransfer.transfer_vertex_groups()`. Each source group's weights are expanded into a 3-component array, projected onto the target, blended with any existing target weights using the inverted mask, and then written to a target vertex group of the same name. Locked groups are skipped when *Exclude locked* is enabled.

---

## Transfer options

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `mesh_source` | Object (mesh) | `None` | Source mesh to sample. |
| `mesh_object_space` | `WORLD` / `LOCAL` | `LOCAL` | Space used for sampling and applying coordinates. |
| `search_method` | `CLOSEST` / `RAYCAST` / `TOPOLOGY` / `UVS` | `CLOSEST` | Sampling strategy. |
| `attributes_to_transfer` | `SHAPE` / `UVS` / `SHAPE_KEYS` / `VERTEX_GROUPS` | `SHAPE` | Data to transfer. |
| `vertex_group_filter` | String | `""` | Vertex group name used as a mask. |
| `invert_vertex_group_filter` | Bool | `False` | Invert mask weights. |
| `transfer_edit_selection` | Bool | `False` | Restrict to edit-mode selection. |
| `transfer_shape_as_key` | Bool | `False` | Store shape transfer as a shape key. |
| `transfer_to_new_uv` | Bool | `False` | (Reserved) transfer into a new UV map. |
| `transfer_modified_source` | Bool | `False` | Sample the deformed source (modifiers + shape keys). |
| `exclude_muted_shapekeys` | Bool | `False` | Skip muted shape keys. |
| `exclude_locked_groups` | Bool | `False` | Skip locked vertex groups. |
| `snap_to_closest_shape` | Bool | `False` | Snap transferred positions to the closest source vertex. |
| `snap_to_closest_shapekey` | Bool | `False` | Snap transferred shape-key vertices to the closest source vertex. |
| `arm_source` | Object (armature) | `None` | Source armature for driver transfer. |
| `arm_target` | Object (armature) | `None` | Target armature for driver transfer. |

> **Note on the mask:** `get_vertices_mask()` combines the vertex-group filter and the edit-mode selection multiplicatively. When inverting a group, `1 - weight` is used. Missing projections (rays that miss the source) are filled with the target's original positions, so masked-out or unmatched vertices are left unchanged.

---

## Masking with vertex groups and selection

Masking lets you transfer data to only a subset of the target.

1. Create or select an existing vertex group on the **target** object.
2. Set it in the panel's **Vertex Group** field.
3. Toggle **Invert** (`ARROW_LEFTRIGHT`) to flip which region is affected.
4. Optionally enable **Only edit mode selection** to further restrict to selected vertices.

Internally the mask is a per-vertex float array. For shape and shape-key transfers the delta is multiplied by the mask, and any pre-existing target data is preserved where the mask is `0` (via `1 - mask`). This makes masked transfers **additive/non-destructive** for existing shape keys and vertex groups.

---

## Rigging helpers (shape key drivers)

When transferring shape keys, the add-on can also copy their **drivers** so that the transferred keys respond to the same inputs (bones, properties, etc.) as the originals.

Pass the `arm_source` / `arm_target` arguments (or set them in the *Rigging Helpers* sub-panel) so that driver variable targets pointing at the source armature are re-pointed at the target armature. Likewise, references to the source shape-key datablock are re-pointed to the target's.

Supported driver variable types: `SINGLE_PROP`, `TRANSFORMS`, `ROTATION_DIFF`, `LOC_DIFF`.

The standalone **Transfer Shape Keys drivers** operator (`object.transfer_shape_key_drivers`) performs driver transfer only. It requires:

- an active object,
- a source mesh set,
- a source armature set,
- object mode.

---

## Operators reference

### `object.transfer_mesh_data`

Transfers the selected attribute from the source mesh to the active object.

- **bl_idname:** `object.transfer_mesh_data`
- **Options:** `REGISTER`, `UNDO`
- **Poll:** active object exists and is a mesh, a source mesh is set, and the combination of search method + attribute is valid (UV traversal is disallowed when transferring UVs in UV space).
- Switches to Object mode, performs the transfer, reports a warning if the source has zero-area faces, then restores the previous mode.
- Reports `INFO` "Unable to perform the operation." and returns `CANCELLED` when nothing was transferred.

### `object.transfer_shape_key_drivers`

Transfers shape-key drivers only.

- **bl_idname:** `object.transfer_shape_key_drivers`
- **Options:** `REGISTER`, `UNDO`
- **Poll:** active object exists, source mesh and source armature are set, and Blender is in Object mode.
- Warns on zero-area source faces.

### `object.map_topology`

Topology mapping helper (tooltip "Simple Object Operator").

- **bl_idname:** `object.map_topology`
- **Options:** `REGISTER`, `UNDO`

> This operator is currently commented out of the main panel and remains available programmatically. It instantiates `TopologyData` on the active object to inspect selected faces and the active edge.

---

## Python API

The add-on is importable as a module, so the transfer logic can be reused in scripts and other add-ons.

### `MeshData`

Wraps a single object's mesh and exposes helpers for reading/writing geometry.

```python
from MeshDataTransfer.mesh_data_transfer import MeshData

md = MeshData(obj, deformed=False, world_space=False, uv_space=False, triangulate=True)
md.get_mesh_data()          # builds vertex map + BVHTree
co   = md.get_verts_position()   # (n, 3) float32 array
md.set_verts_position(co)        # writes vertex positions
md.set_position_as_shape_key(shape_key_name="MyKey", co=co, activate=True)
md.free()
```

Key attributes/methods:

- `v_count`, `shape_keys`, `shape_keys_names`, `shape_keys_drivers`, `vertex_groups`
- `get_vertex_groups_weights(ignore_locked=False)`, `set_vertex_groups_weights(weights, names)`
- `get_vertex_group_weights(name)`, `set_vertex_group_weights(name, weights)`
- `get_shape_keys_vert_pos(exclude_muted=False)`
- `get_selected_verts()`, `seam_edges` (`get`/`set`)
- `generate_bmesh(deformed, world_space)`

### `MeshDataTransfer`

The main transfer engine. Construction samples the target onto the source once; the `transfer_*` methods then write data.

```python
from MeshDataTransfer.mesh_data_transfer import MeshDataTransfer

transfer = MeshDataTransfer(
    target=target_obj,
    source=source_obj,
    world_space=False,
    deformed_source=False,
    search_method="CLOSEST",   # or RAYCAST / TOPOLOGY / UVS
    vertex_group="MyMask",
    invert_vertex_group=False,
    restrict_to_selection=False,
    snap_to_closest=False,
)

if transfer.has_zero_area_faces:
    print("Warning: source has zero-area faces")

transfer.transfer_vertex_position(as_shape_key=False)
# transfer.transfer_uvs()
# transfer.transfer_shape_keys()
# transfer.transfer_vertex_groups()
# transfer.transfer_shape_keys_drivers()

transfer.free()
```

Constructor signature:

```python
MeshDataTransfer(
    source, target,
    uv_space=False,
    deformed_source=False,
    deformed_target=False,
    world_space=False,
    search_method="RAYCAST",
    topology=False,
    vertex_group=None,
    invert_vertex_group=False,
    exclude_locked_groups=False,
    exclude_muted_shapekeys=False,
    snap_to_closest=False,
    snap_to_closest_shape_key=False,
    transfer_drivers=False,
    source_arm=None,
    target_arm=None,
    restrict_to_selection=False,
)
```

Useful public state after construction:

- `has_zero_area_faces` — `True` if the source has degenerate triangles.
- `barycentric_coords` — barycentric weights of each target vertex within its hit face.
- `hit_faces`, `related_ids`, `ray_casted`, `missed_projections` — the raw projection data.

### `TopologyData`

Orders a mesh's topology starting from the selected face and active edge. Used by topology-based mapping workflows.

```python
from MeshDataTransfer.mesh_data_transfer import TopologyData

topo = TopologyData(obj)
face_verts = topo.get_face_vertices(0)
face_edges = topo.get_face_edges(0)
rolled     = topo.roll_to_edge(0, edge_index)
topo.free()
```

---

## How it works

1. **Mesh sampling.** `MeshData.get_mesh_data()` builds a triangulated `BVHTree`. If UV space is requested, a temporary mesh is created where each face loop is placed at its UV coordinate `(u, v, 0)`, and a vertex map records which original mesh vertex each UV point belongs to.
2. **Projection.** `MeshDataTransfer.cast_verts()` projects every target vertex onto the source:
   - `CLOSEST` → `BVHTree.find_nearest`
   - `RAYCAST`/`UVS` → `BVHTree.ray_cast` along the vertex normal, with a fallback in the opposite direction.
   The hit face vertices and the barycentric coordinates of the hit point are stored.
3. **Barycentric interpolation.** `get_transferred_vert_coords()` looks up the source coordinates of the hit triangle's vertices and interpolates using the precomputed barycentric weights. Missed projections fall back to the target's original positions.
4. **Zero-area handling.** `check_zero_area_triangles()` flags degenerate source triangles; `NaN` results are replaced with the target's original coordinates and a warning is reported.
5. **Masking/blending.** A per-vertex mask (vertex group and/or selection) scales the delta, preserving existing data outside the mask.
6. **Writing.** Positions are written with `foreach_set`; shape keys via `shape_key.data.foreach_set`; UVs via a temporary Data Transfer modifier; vertex groups via `VertexGroup.add`.
7. **Cleanup.** Temporary bmeshes, meshes and BVH trees are freed through `free()`.

World-space transfers transform sampled points into the target's local space using `matrix_world.inverted() @ source.matrix_world`.

---

## Tips, limitations and troubleshooting

- **Zero-area faces** in the source produce `NaN` barycentric coordinates. A warning is shown; fix the source mesh for clean results. Degenerate areas are filled with the target's original positions.
- **Vertex ID (Topology)** requires equal vertex counts. It is the only method that does not perform geometric projection, so it is exact when the two meshes are the same topology.
- **UV transfer uses a temporary modifier** and changes object/mode context internally; avoid running it while another operator relies on the current mode.
- **Raycast** can miss on thin or open meshes; the bidirectional fallback helps, but *Closest* is more robust for complex shapes.
- **Deformed source** evaluates modifiers and shape keys for sampling. This is slower for shape-key transfer because each key is snapshotted individually and the original values are restored afterwards.
- **Masks make transfers additive:** existing shape keys and vertex groups are preserved where the mask is `0`.
- **World space** matters when source and target have different transforms. Leave it off for same-space objects.
- The UI is mesh-only (`poll` checks `context.active_object.type == 'MESH'`). The GPencil branch exists but is disabled.

---

## File layout

```
MeshDataTransfer/
├── __init__.py              # UI panel, property group, registration
├── operators.py             # Blender operators (transfer, drivers, topology)
├── mesh_data_transfer.py    # Core transfer engine (MeshData, MeshDataTransfer, TopologyData)
├── blender_manifest.toml    # Blender extension manifest
└── README.md                # This documentation
```

### Registration

On enable, the add-on registers the panel and property classes and attaches two properties to `bpy.types.Object`:

- `Object.mesh_data_transfer_object` — the per-object `MeshDataSettings` property group.
- `Object.expanded` — UI toggle used by the pre-4.1 rigging-helpers section.

These are removed on disable.
