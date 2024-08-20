import math, os
if os.path.exists(__name__ + '.py'):
    from  asset_node import *
else:
    from .asset_node import *

# --- Common Data for importing and exporting
class CommonData():
    test_mode = False
    import_create_direction_bone_vectors = False
    import_delete_frame_objects = True
    import_frames_one_by_one = False
    export_recalculate_anim_length = False
    import_test_file = r'test\idle01.re'
    export_test_file = r'test\idle01_new.re'

    root_bone_name = 'Root'
    helper_root_bone_name = 'Root'

    default_armature_name = 'Armature'
    default_bones_name = 'Bones'

    pelvis_bone_names = ['pelvis', 'hips', 'spine3', 'neck', 'head']
    special_bone_names = ['root']
    roll_bone_names = ['roll', 'bicep2']

    unit_vector = (1, 0, 0)
    forward_vector = (0, 1, 0)
    up_vector = (0, 0, 1)
    default_bone_roll_deg = 180
    default_bone_roll_deg_y = 90
    compensation_scale = 0.01
    compensation_scale_mult = 5
    default_scene_fps = 30

    orig_skeleton = ReSkeletonNode()
    orig_animation = ReAnimationClipContainer()
    orig_edit_bones = {}
    orig_poses = {}

    parent_rotations = {}
    parent_positions = {}

    last_file_path = ''
    append_file_name = '_new'

    hdf_manager = None

# --- Mimic settings
    default_shape_key = 'default'

    placer_bone_name = 'placer'
    head_anim_obj_name = 'head_anim'
    mimic_anim_obj_name = 'mimic_anim'
    mimic_head_bones = ['torso3', 'l_shoulder']


# --- Default settings in file dialog
class ImportAnimsData:
    is_mimic_animation = False
    set_time_stretch = False
    max_anim_length = 0
    rotate_imported_object = False
    object_scale = 10
    reset_bone_roll = False
    reset_edit_bone_roll_val = -90
    try_to_find_edit_bone_rolls = False

    def read_default_data(self):
        self.filepath = CommonData.last_file_path
        self.is_mimic_animation = ImportAnimsData.is_mimic_animation
        self.set_time_stretch = ImportAnimsData.set_time_stretch
        self.max_anim_length = ImportAnimsData.max_anim_length
        self.rotate_imported_object = ImportAnimsData.rotate_imported_object
        self.object_scale = ImportAnimsData.object_scale
        self.reset_bone_roll = ImportAnimsData.reset_bone_roll
        self.reset_edit_bone_roll_val = ImportAnimsData.reset_edit_bone_roll_val
        self.try_to_find_edit_bone_rolls = ImportAnimsData.try_to_find_edit_bone_rolls

    def save_default_data(self):
        CommonData.last_file_path = self.filepath
        ImportAnimsData.is_mimic_animation = self.is_mimic_animation
        ImportAnimsData.set_time_stretch = self.set_time_stretch
        ImportAnimsData.max_anim_length = self.max_anim_length
        ImportAnimsData.rotate_imported_object = self.rotate_imported_object
        ImportAnimsData.object_scale = self.object_scale
        ImportAnimsData.reset_bone_roll = self.reset_bone_roll
        ImportAnimsData.reset_edit_bone_roll_val = self.reset_edit_bone_roll_val
        ImportAnimsData.try_to_find_edit_bone_rolls = self.try_to_find_edit_bone_rolls

# --- Default settings in file dialog
class ExportAnimsData:
    reset_bone_roll = False
    create_root_bone = False
    anim_length = 1.0

    def read_default_data(self):
        scene = bpy.context.scene
        anim_len = scene.frame_end - scene.frame_start
        frame_map_new = scene.render.frame_map_new
        frame_map_old = scene.render.frame_map_old

        self.filepath = CommonData.last_file_path
        self.reset_bone_roll = ExportAnimsData.reset_bone_roll
        self.rotate_imported_object = ImportAnimsData.rotate_imported_object
        self.anim_length = anim_len / float(CommonData.default_scene_fps) * frame_map_old / float(frame_map_new)
        self.append_file_name = CommonData.append_file_name
        self.create_root_bone = ExportAnimsData.create_root_bone
        self.root_bone_name = CommonData.helper_root_bone_name

    def save_default_data(self):
        CommonData.last_file_path = self.filepath
        ExportAnimsData.reset_bone_roll = self.reset_bone_roll
        ImportAnimsData.rotate_imported_object = self.rotate_imported_object
        ExportAnimsData.anim_length = self.anim_length
        CommonData.append_file_name = self.append_file_name
        ExportAnimsData.create_root_bone = self.create_root_bone
        CommonData.helper_root_bone_name = self.root_bone_name

class AnimHelper():
    # --- Scale skeleton back for exporting
    def rescale_skeleton(obj, scale):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.scale *= scale
        bpy.context.view_layer.update()

    # --- Rotate obj around Z axis by deg degrees
    def rotate_skeleton(obj, deg, is_mimic=False):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(True)
        obj.rotation_euler.z = math.radians(deg)
        if is_mimic:
            obj.rotation_euler.y = math.radians(CommonData.default_bone_roll_deg_y)
        obj.select_set(False)

    # --- Remove all edit bones from object
    def remove_edit_bones(obj):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        obj.animation_data_clear()
        for bone in obj.data.edit_bones:
            obj.data.edit_bones.remove(bone)

    # --- Clear bone object parent relations
    def clear_object_parent_relations(obj):
        bpy.context.view_layer.objects.active = obj
        for obj in obj.children:
            obj.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        for obj in obj.children:
            obj.select_set(False)

    # --- Reset static data
    def compare_and_reset_data(obj):
        CommonData.orig_skeleton = ReSkeletonNode()
        CommonData.orig_animation = ReAnimationClipContainer()
        CommonData.orig_edit_bones = {}
        CommonData.orig_poses = {}

        CommonData.parent_rotations = {}
        CommonData.parent_positions = {}

    # --- Unit vector getters
    def get_unit_vector(unit_vector, is_mimic=False):
        unit_vector = mathutils.Vector((unit_vector[0], unit_vector[1], unit_vector[2]))
        if is_mimic:
            unit_vector *= CommonData.compensation_scale * CommonData.compensation_scale
        else:
            unit_vector *= CommonData.compensation_scale_mult * CommonData.compensation_scale
        return unit_vector

    def get_up_unit_vec(is_mimic=False):
        return AnimHelper.get_unit_vector(CommonData.up_vector, is_mimic)

    def get_forward_unit_vec(is_mimic=False):
        return AnimHelper.get_unit_vector(CommonData.unit_vector, is_mimic)

    def get_blender_forward_unit_vec(is_mimic=False):
        return AnimHelper.get_unit_vector(CommonData.forward_vector, is_mimic)

    # --- Clear mimimc keyframe data
    def clear_mimic_keyframe_data(obj):
        key_blocks = obj.data.shape_keys.key_blocks

        for key_block in key_blocks:
            key_block.value = 0

        for key_block in key_blocks:
            data_path = f"key_blocks[\"{key_block.name}\"].value"

            animation_data = obj.data.shape_keys.animation_data
            if not animation_data.action:
                break

            curves = animation_data.action.fcurves

            for curve in curves:
                if curve.data_path == data_path:
                    curves.remove(curve)
                    break

    # --- Get selected object list
    def get_selected_obj_list(context):
        if not hasattr(context, 'selected_ids'):
            return [context.object]
        return [context.object] + context.selected_ids if len(context.selected_ids) > 1 else context.selected_ids + [context.object]
