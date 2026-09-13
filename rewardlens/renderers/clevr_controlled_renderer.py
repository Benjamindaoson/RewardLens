from __future__ import print_function

import argparse
import json
import math
import os
import sys


def _insert_clevr_path(clevr_image_generation):
    clevr_image_generation = os.path.abspath(clevr_image_generation)
    if clevr_image_generation not in sys.path:
        sys.path.insert(0, clevr_image_generation)


INSIDE_BLENDER = True
try:
    import bpy
    from mathutils import Vector
except ImportError:
    INSIDE_BLENDER = False
    bpy = None
    Vector = None


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def write_json(path, payload):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def vec_to_list(value):
    return [float(value[0]), float(value[1]), float(value[2])]


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def configure_render(run_config, output_image, render_seed):
    render_args = bpy.context.scene.render
    render_args.engine = "CYCLES"
    render_args.filepath = output_image
    render_args.resolution_x = int(run_config["width"])
    render_args.resolution_y = int(run_config["height"])
    render_args.resolution_percentage = 100
    render_args.tile_x = int(run_config["tile_size"])
    render_args.tile_y = int(run_config["tile_size"])

    bpy.data.worlds["World"].cycles.sample_as_light = True
    bpy.context.scene.cycles.blur_glossy = 2.0
    bpy.context.scene.cycles.samples = int(run_config["samples"])
    bpy.context.scene.cycles.transparent_min_bounces = 8
    bpy.context.scene.cycles.transparent_max_bounces = 8

    if hasattr(bpy.context.scene.cycles, "use_animated_seed"):
        bpy.context.scene.cycles.use_animated_seed = False
    bpy.context.scene.cycles.seed = int(render_seed)


def snapshot_render_contract(run_config, render_seed):
    camera = bpy.data.objects["Camera"]
    return {
        "cycles_seed": int(render_seed),
        "use_animated_seed": False,
        "samples": int(run_config["samples"]),
        "width": int(run_config["width"]),
        "height": int(run_config["height"]),
        "camera_jitter": 0.0,
        "key_light_jitter": 0.0,
        "fill_light_jitter": 0.0,
        "back_light_jitter": 0.0,
        "camera_location": vec_to_list(camera.location),
        "camera_rotation_euler": vec_to_list(camera.rotation_euler),
        "lamp_key_location": vec_to_list(bpy.data.objects["Lamp_Key"].location),
        "lamp_fill_location": vec_to_list(bpy.data.objects["Lamp_Fill"].location),
        "lamp_back_location": vec_to_list(bpy.data.objects["Lamp_Back"].location),
    }


def compute_directions():
    bpy.ops.mesh.primitive_plane_add(radius=5)
    plane = bpy.context.object
    camera = bpy.data.objects["Camera"]
    plane_normal = plane.data.vertices[0].normal
    cam_behind = camera.matrix_world.to_quaternion() * Vector((0, 0, -1))
    cam_left = camera.matrix_world.to_quaternion() * Vector((-1, 0, 0))
    cam_up = camera.matrix_world.to_quaternion() * Vector((0, 1, 0))
    plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
    plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
    plane_up = cam_up.project(plane_normal).normalized()
    utils.delete_object(plane)
    return {
        "behind": tuple(plane_behind),
        "front": tuple(-plane_behind),
        "left": tuple(plane_left),
        "right": tuple(-plane_left),
        "above": tuple(plane_up),
        "below": tuple(-plane_up),
    }


def compute_relationships(scene_struct, eps=0.2):
    all_relationships = {}
    for name, direction_vec in scene_struct["directions"].items():
        if name in ("above", "below"):
            continue
        all_relationships[name] = []
        for i, obj1 in enumerate(scene_struct["objects"]):
            coords1 = obj1["3d_coords"]
            related = set()
            for j, obj2 in enumerate(scene_struct["objects"]):
                if i == j:
                    continue
                coords2 = obj2["3d_coords"]
                diff = [coords2[k] - coords1[k] for k in (0, 1, 2)]
                dot = sum(diff[k] * direction_vec[k] for k in (0, 1, 2))
                if dot > eps:
                    related.add(j)
            all_relationships[name].append(sorted(list(related)))
    return all_relationships


def add_controlled_object(obj_spec, properties, shape_dir, camera):
    shape_name = obj_spec["shape"]
    color_name = obj_spec["color"]
    material_name = obj_spec["material"]
    size_name = obj_spec["size"]
    blender_shape_name = properties["shapes"][shape_name]
    blender_material_name = properties["materials"][material_name]
    rgb = properties["colors"][color_name]
    rgba = [float(c) / 255.0 for c in rgb] + [1.0]
    scale = float(properties["sizes"][size_name])
    if blender_shape_name == "SmoothCube_v2":
        scale /= math.sqrt(2)
    x = float(obj_spec["x"])
    y = float(obj_spec["y"])
    theta = float(obj_spec.get("rotation", 0.0))
    utils.add_object(shape_dir, blender_shape_name, scale, (x, y), theta=theta)
    blender_obj = bpy.context.object
    utils.add_material(blender_material_name, Color=rgba)
    pixel_coords = utils.get_camera_coords(camera, blender_obj.location)
    return {
        "role": obj_spec.get("role", "base"),
        "object_id": obj_spec.get("object_id"),
        "shape": shape_name,
        "size": size_name,
        "material": material_name,
        "color": color_name,
        "rotation": theta,
        "x": x,
        "y": y,
        "3d_coords": vec_to_list(blender_obj.location),
        "pixel_coords": list(pixel_coords),
    }


def variant_paths(output_dir, triplet_id, variant_name):
    image_path = os.path.join(output_dir, "images", "%s_%s.png" % (triplet_id, variant_name))
    scene_path = os.path.join(output_dir, "scenes", "%s_%s.json" % (triplet_id, variant_name))
    return image_path, scene_path


def files_exist(paths):
    for path in paths:
        if not os.path.isfile(path):
            return False
    return True


def render_variant(run_config, spec, variant_name, properties):
    output_dir = run_config["output_dir"]
    triplet_id = spec["triplet_id"]
    render_seed = int(spec["render_seed"])
    output_image, output_scene = variant_paths(output_dir, triplet_id, variant_name)

    if run_config.get("skip_existing") and files_exist([output_image, output_scene]):
        print("SKIP EXISTING:", output_image)
        sys.stdout.flush()
        return

    bpy.ops.wm.open_mainfile(filepath=run_config["base_scene_blendfile"])
    utils.load_materials(run_config["material_dir"])
    configure_render(run_config, output_image, render_seed)

    directions = compute_directions()
    camera = bpy.data.objects["Camera"]
    render_contract = snapshot_render_contract(run_config, render_seed)

    objects = []
    for obj_spec in spec["variants"][variant_name]["objects"]:
        objects.append(add_controlled_object(obj_spec, properties, run_config["shape_dir"], camera))

    scene_struct = {
        "triplet_id": triplet_id,
        "factor": spec.get("factor"),
        "variant": variant_name,
        "image_filename": os.path.basename(output_image),
        "question": spec["question"],
        "candidate_a": spec["candidate_a"],
        "candidate_b": spec["candidate_b"],
        "preferred": spec["preferred"][variant_name],
        "answers": spec.get("answers"),
        "query": spec.get("query"),
        "uniqueness": spec.get("uniqueness"),
        "magnitude": spec.get("magnitude"),
        "render_seed": render_seed,
        "render_contract": render_contract,
        "directions": directions,
        "objects": objects,
        "intervention": spec.get("intervention"),
    }
    scene_struct["relationships"] = compute_relationships(scene_struct)
    bpy.ops.render.render(write_still=True)
    write_json(output_scene, scene_struct)
    print("WROTE IMAGE:", output_image)
    print("WROTE SCENE:", output_scene)
    sys.stdout.flush()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_config", required=True)
    parser.add_argument("--specs_file", required=True)
    args = parser.parse_args(argv)

    run_config = load_json(args.run_config)
    specs_payload = load_json(args.specs_file)
    specs = specs_payload["triplets"]

    clevr_dir = os.path.abspath(run_config["clevr_image_generation"])
    _insert_clevr_path(clevr_dir)
    os.chdir(clevr_dir)

    global utils
    import utils

    ensure_dir(os.path.join(run_config["output_dir"], "images"))
    ensure_dir(os.path.join(run_config["output_dir"], "scenes"))
    properties = load_json(run_config["properties_json"])

    for spec in specs:
        print("RENDER TRIPLET:", spec["triplet_id"])
        sys.stdout.flush()
        for variant_name in ("base", "relevant", "irrelevant"):
            render_variant(run_config, spec, variant_name, properties)

    print("CONTROLLED_RENDER_OK")
    sys.stdout.flush()


if __name__ == "__main__":
    if not INSIDE_BLENDER:
        print("This script must be launched from Blender.")
        sys.exit(1)
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    main(argv)
