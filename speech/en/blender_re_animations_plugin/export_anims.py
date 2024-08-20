import copy, math, os, bpy, mathutils
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import ExportHelper

from .common_data import CommonData, AnimHelper, ImportAnimsData, ExportAnimsData
from .asset_node import *
from .hdf_manager import HdfManager
from .phoneme_extractor import PhonemeExtractor


# --- Animation exporter
class ExportAnims(bpy.types.Operator, ExportHelper):
    """Exports selected object as .re animset file"""
    bl_idname = 'export_animset.re'
    bl_label = 'Export .re animset'

    # ExportHelper mixin class uses this
    filename_ext = '.re'
    filter_glob: StringProperty(
        default='*.re',
        options={'HIDDEN'},
    )

    filepath: StringProperty(
        name='File Path',
        description='Filepath used for exporting the file',
        maxlen=1024,
        subtype='FILE_PATH',
    )

    create_root_bone: BoolProperty(
        name='Create root bone if it does not exist',
        description='Create root bone if it does not exist before exporting',
        default=ExportAnimsData.create_root_bone,
    )

    root_bone_name: StringProperty(
        name='Root name',
        description='Root bone name which will be created',
        default=CommonData.helper_root_bone_name,
    )

    reset_bone_roll: BoolProperty(
        name='Reset bone rolls',
        description='For resetting and ignoring the edit bone rolls of the object',
        default=ExportAnimsData.reset_bone_roll,
    )

    rotate_imported_object: BoolProperty(
        name='Rotate by 180 deg around Z axis',
        description='Rotate object around Z axis by 180 degrees before exporting',
        default=ImportAnimsData.rotate_imported_object,
    )

    anim_length: FloatProperty(
        name='Animation time [s]',
        description='The animation length in seconds',
        min=0.0,
        default=ExportAnimsData.anim_length,
    )

    append_file_name_desc = 'Append file name if file cannot be created'
    append_file_name: StringProperty(
        name='Suffix',
        description=append_file_name_desc,
        default=CommonData.append_file_name,
    )

    context_obj_name: StringProperty()
    orig_obj_name: StringProperty()

    def draw(self, context):
        pass

    def get_valid_selected_obj(self, context):
        selected_ids = AnimHelper.get_selected_obj_list(context)
        for obj in selected_ids:
            if obj and hasattr(obj.data, 'bones'):
                return obj
        return None

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'is_exporting_mimic') or cls.get_valid_selected_obj(cls, context)

    def invoke(self, context, event):
        if CommonData.test_mode:
            self.filepath = CommonData.export_test_file

            self.execute(context)
            bpy.ops.import_animset.re('INVOKE_DEFAULT')

            return {'FINISHED'}
        else:
            ExportAnimsData.read_default_data(self)

            if hasattr(context, 'is_exporting_mimic'):
                self.rotate_imported_object = False
            else:
                export_object = self.get_valid_selected_obj(context)
                if export_object:
                    path, _ = os.path.split(self.filepath)
                    self.filepath = os.path.join(path, export_object.name)

            context.window_manager.fileselect_add(self)

            return {'RUNNING_MODAL'}

    def execute(self, context):
        export_object = self.get_valid_selected_obj(context)

        self.is_exporting_mimic = self.context_obj_name and self.context_obj_name in bpy.data.objects
        if self.is_exporting_mimic:
            export_object = bpy.data.objects[self.context_obj_name]

        if not export_object:
            return

        self.context_obj_name = ''

        export_path = self.filepath
        ExportAnimsData.save_default_data(self)

        prev_active_obj = bpy.context.view_layer.objects.active
        prev_obj_mode = prev_active_obj.mode if prev_active_obj else None
        scene = bpy.context.scene
        curr_frame = scene.frame_current

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        CommonData.import_frames_one_by_one = addon_prefs.import_frames_one_by_one

        if self.rotate_imported_object:
            AnimHelper.rotate_skeleton(export_object, CommonData.default_bone_roll_deg)
        if self.is_exporting_mimic:
            AnimHelper.rescale_skeleton(export_object, CommonData.compensation_scale**2)

        if self.create_root_bone and CommonData.helper_root_bone_name not in export_object.data.bones:
            self.create_helper_root_bone(export_object)

        if len(export_object.data.bones) > 0:
            self.search_for_root_bone_name(export_object.data.bones[0])

        AnimHelper.compare_and_reset_data(export_object)

        anim_node = self.to_ReAnimNode(export_object)

        self.fill_anim_node_data(export_object, anim_node)

        self.fill_shape_key_mimic_data(anim_node)

        if CommonData.hdf_manager is None:
            CommonData.hdf_manager = HdfManager()

        anim_node.anim_length = self.anim_length
        CommonData.hdf_manager.append_file_name = self.append_file_name
        CommonData.hdf_manager.write_hdf_file(export_path, anim_node)

        bpy.context.view_layer.objects.active = prev_active_obj
        if prev_obj_mode:
            try:
                bpy.ops.object.mode_set(mode=prev_obj_mode)
            except:
                pass
        scene.frame_set(curr_frame)

        if self.rotate_imported_object:
            AnimHelper.rotate_skeleton(export_object, -CommonData.default_bone_roll_deg)
        if self.is_exporting_mimic:
            AnimHelper.rescale_skeleton(export_object, 1./(CommonData.compensation_scale**2))

            if self.orig_obj_name in bpy.data.objects:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.context.view_layer.objects.active = bpy.data.objects[self.orig_obj_name]

        return {'FINISHED'}

    def get_keyframes_length(self, obj):
        if CommonData.export_recalculate_anim_length:
            keyframes = []
            anim = obj.animation_data
            if anim is not None and anim.action is not None:
                for fcu in anim.action.fcurves:
                    for keyframe in fcu.keyframe_points:
                        x, y = keyframe.co
                        if x not in keyframes:
                            keyframes.append((math.ceil(x)))
            max_keyframe = 0 if len(keyframes) == 0 else max(keyframes)
            return max_keyframe + 1
        else:
            return bpy.context.scene.frame_end

    def to_ReAnimNode(self, bones=None):
        asset_node = ReAssetNode()
        asset_node.asset_description.skeleton = CommonData.orig_skeleton #self.to_ReSkeletonNode()

        if not bones:
            bones = bpy.data.objects[CommonData.default_bones_name]

        self.parent_modifiers = {}
        self.parse_skeleton_for_exporting(asset_node, bones)

        bpy.context.view_layer.objects.active = bones
        bpy.ops.object.mode_set(mode='OBJECT')
        scene = bpy.context.scene

        anim_clip = CommonData.orig_animation.animation_clip

        if CommonData.import_frames_one_by_one:
            bone_obj_num = 0
            while True:
                bones_obj_name = 'Bones.' + f'{bone_obj_num + 1}'.rjust(3, '0')
                if bones_obj_name not in bpy.data.objects:
                    break
                bone_obj_num += 1
            scene.frame_start = 0
            scene.frame_end = bone_obj_num
        elif not self.is_exporting_mimic:
            scene.frame_end = self.get_keyframes_length(bones)

        if scene.frame_end - scene.frame_start == 0:
            scene.frame_start = 0
            scene.frame_end = 1

        # Validate and create missing anim node data
        if not anim_clip.get_animation_curve(CommonData.root_bone_name):
            self.add_anim_curve_root(anim_clip, scene, bones, CommonData.root_bone_name)
        if self.create_root_bone and not anim_clip.get_animation_curve(CommonData.helper_root_bone_name):
            self.add_anim_curve_root(anim_clip, scene, bones, CommonData.helper_root_bone_name)

        self.validate_anim_bone_children(anim_clip, scene, bones, asset_node.asset_description.skeleton.root)

        # Cut keyframes if animation is shorter than the original
        for curve_name in anim_clip.get_curves_names():
            curve = anim_clip.get_animation_curve(curve_name)
            curve.keyframes_qts = curve.keyframes_qts[scene.frame_start:scene.frame_end + 1 - scene.frame_start]

        # Extend keyframes if animation is longer than the original
        for curve_name in anim_clip.get_curves_names():
            curve = anim_clip.get_animation_curve(curve_name)
            if len(curve.keyframes_qts) == 0:
                continue
            keyframes_qts = []
            for f in range(scene.frame_start, scene.frame_end + 1):
                f -= scene.frame_start
                if f < len(curve.keyframes_qts):
                    keyframes_qts.append(curve.keyframes_qts[f])
                else:
                    keyframes_qts.append(copy.deepcopy(curve.keyframes_qts[-1]))
            curve.set_keyframes_qts(keyframes_qts)

        asset_node.animation_container.add_animation(CommonData.orig_animation)

        return asset_node

    def search_for_root_bone_name(self, bone):
        CommonData.root_bone_name = bone.name

    def reparent_all_root_bones(self, curr_root_bone, new_root_bone):
        for bone in curr_root_bone:
            if not bone.parent:
                bone.parent = new_root_bone
        for bone in curr_root_bone:
            bone.use_connect = False

    def create_helper_root_bone(self, export_object):
        bpy.context.view_layer.objects.active = export_object
        bpy.ops.object.mode_set(mode='EDIT')
        bone = export_object.data.edit_bones.new(CommonData.helper_root_bone_name)
        uv = CommonData.unit_vector
        uv = mathutils.Vector((uv[0], uv[1], uv[2]))
        uv *= CommonData.compensation_scale
        bone.head = (0, 0, 0)
        bone.tail = uv
        self.reparent_all_root_bones(export_object.data.edit_bones, bone)
        bone.children.append(bone)
        bpy.ops.object.mode_set(mode='OBJECT')
        export_object.location = uv
        bpy.ops.object.transform_apply()
        bpy.context.view_layer.update()

    # ----- Anim curve helpers -----
    def add_anim_curve_root(self, anim_clip, scene, root_bone, bone_name):
        self.add_anim_curve(anim_clip, scene, root_bone, bone_name)

        if self.create_root_bone:
            is_root_bone = bone_name == CommonData.helper_root_bone_name
        else:
            is_root_bone = bone_name == CommonData.root_bone_name

        if is_root_bone:
            rot = mathutils.Quaternion()
            self.parent_modifiers[bone_name] = rot
            curve = anim_clip.get_animation_curve(bone_name)
            for f in range(scene.frame_start, scene.frame_end + 1):
                f -= scene.frame_start
                if f in curve.keyframes_qts:
                    curve.keyframes_qts[f].value.rotation = rot

    def add_anim_curve(self, anim_clip, scene, root_bone, bone_name):
        if bone_name not in root_bone.data.bones:
            return

        anim_curve = anim_clip.add_curve(bone_name)
        for f in range(scene.frame_start, scene.frame_end + 1):
            f -= scene.frame_start

            bone = root_bone.data.bones[bone_name]

            transform = ReTransform()
            transform.position = bone.tail_local - bone.head_local
            transform.rotation = Quaternion(0, 0, 0, 1)
            transform.scale = Scale()
            anim_curve.add_transformation(transform)

    def validate_anim_bone_children(self, anim_clip, scene, root_bone, parent_node):
        for node in parent_node.children:
            bone_name = node.name
            child_found = False
            for curve_name in anim_clip.get_curves_names():
                if bone_name == curve_name:
                    child_found = True
                    break
            if not child_found:
                self.add_anim_curve(anim_clip, scene, root_bone, bone_name)

            self.validate_anim_bone_children(anim_clip, scene, root_bone, node)

    # ----- Anim skeleton helpers -----
    def add_skeleton_root_bone(self, asset_node, bones, bone_name):
        if bone_name not in CommonData.orig_edit_bones:
            CommonData.orig_edit_bones[bone_name] = {}
        if 'orig_transform' not in CommonData.orig_edit_bones[bone_name]:
            bone_node = self.create_bone_node(bones.data.edit_bones[bone_name])

            if self.create_root_bone:
                is_root_bone = bone_name == CommonData.helper_root_bone_name
            else:
                is_root_bone = bone_name == CommonData.root_bone_name

            if is_root_bone:
                asset_node.asset_description.skeleton.root = bone_node

            CommonData.orig_edit_bones[bone_name]['orig_transform'] = bone_node.transform

    def create_bone_node(self, bone):
        new_transform = ReTransform()
        new_transform.position = bone.tail - bone.head
        new_transform.rotation = Quaternion(0, 0, 0, 1)
        new_transform.scale = Scale()

        CommonData.orig_edit_bones[bone.name] = {
            'matrix': bone.matrix.copy(),
            'tail': bone.tail,
            'head': bone.head,
        }

        node = ReBoneNode()
        node.name = bone.name
        node.transform = new_transform
        return node

    def validate_skeleton_bone_children(self, node, parent_bone):
        for child_bone in parent_bone.children:
            bone_name = child_bone.name
            child = None
            for temp_child in node.children:
                if bone_name == temp_child.name:
                    child = temp_child
                    break
            if child == None:
                child = self.create_bone_node(child_bone)
                child.parent = node
                node.children.append(child)

            if bone_name in CommonData.orig_edit_bones:
                CommonData.orig_edit_bones[bone_name]['orig_transform'] = child.transform

            self.validate_skeleton_bone_children(child, child_bone)

    def parse_skeleton_for_exporting(self, asset_node, bones):
        bpy.context.view_layer.objects.active = bones
        bpy.ops.object.mode_set(mode='EDIT')

        if self.create_root_bone:
            root_bone_name = CommonData.helper_root_bone_name
        else:
            root_bone_name = CommonData.root_bone_name

        self.add_skeleton_root_bone(asset_node, bones, CommonData.root_bone_name)
        if self.create_root_bone:
            self.add_skeleton_root_bone(asset_node, bones, CommonData.helper_root_bone_name)

        self.validate_skeleton_bone_children(asset_node.asset_description.skeleton.root, bones.data.edit_bones[root_bone_name])

    # ----- Anim curve and skeleton exporter -----
    def get_all_parent_rots(self, parent_rotations, all_parent_rotation, parent_bone):
        if parent_bone.name not in parent_rotations:
            return
        all_parent_rotation.rotate(parent_rotations[parent_bone.name])
        if parent_bone.parent:
            self.get_all_parent_rots(parent_rotations, all_parent_rotation, parent_bone.parent)

    def reset_transformation(self, transform, clear=True):
        pos = transform.position
        rot = transform.rotation
        pos.x, pos.y, pos.z = 0, 0, 0
        rot.w, rot.x, rot.y, rot.z = 1, 0, 0, 0

    def fill_anim_node_data(self, obj, anim_node):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)

        skeleton_root = anim_node.asset_description.skeleton.root
        anim_clip = anim_node.animation_container.animations[0].animation_clip

        # Parse skeleton nodes
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        self.parent_rotations = {}
        self.reset_transformation(skeleton_root.transform)

        self.fill_anim_node_children_data(skeleton_root, obj)

        # Parse anim nodes
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='POSE')

        scene = bpy.context.scene
        for f in range(scene.frame_start, scene.frame_end + 1):
            wm.progress_update(int(100.0 * f / (scene.frame_end - scene.frame_start)))

            scene.frame_set(f)

            f -= scene.frame_start

            self.parent_rotations = {}
            curve = anim_clip.get_animation_curve(CommonData.root_bone_name)
            self.reset_transformation(curve.keyframes_qts[f].value)

            self.fill_anim_node_children_data(skeleton_root, obj, anim_clip, f)

        wm.progress_end()

    def get_bone_point(self, bone_point):
        bone_point = mathutils.Vector((bone_point.x, bone_point.y, bone_point.z))
        if not self.is_exporting_mimic:
            bone_point /= CommonData.compensation_scale
        return bone_point

    def get_bone_points(self, bones_obj, bone_name):
        if bpy.context.active_object.mode == 'EDIT':
            edit_bone = bones_obj.data.edit_bones[bone_name]
            local_bone = edit_bone

            roll = edit_bone.roll
        else:
            pose_bone = bones_obj.pose.bones[bone_name]
            local_bone = pose_bone

            forward = AnimHelper.get_forward_unit_vec()

            _, roll = pose_bone.bone.AxisRollFromMatrix(pose_bone.matrix.to_3x3(), axis=forward)

        bone_tail = self.get_bone_point(local_bone.tail)
        bone_head = self.get_bone_point(local_bone.head)

        return [bone_tail, bone_head, roll]

    def get_forward_bone_rotation(self, bone_vec, bone_roll, all_parent_rot):
        forward = AnimHelper.get_forward_unit_vec()

        rot = mathutils.Quaternion()

        if self.reset_bone_roll:
            bone_roll_deg = CommonData.default_bone_roll_deg
        else:
            bone_roll_deg = math.degrees(bone_roll)

        R = (
            mathutils.Matrix.Translation(bone_vec) @ 
            mathutils.Matrix.Rotation(math.radians(bone_roll_deg), 4, forward) @
            mathutils.Matrix.Translation(-bone_vec)
        )

        rot.rotate(R.to_quaternion())

        rot.rotate(forward.rotation_difference(bone_vec))

        rot.rotate(all_parent_rot.inverted())

        rot = rot.inverted()

        return mathutils.Quaternion((rot.w, rot.x, rot.y, rot.z))

    # Parse skeleton and anim nodes for exporting
    def fill_anim_node_children_data(self, parent_node, bones_obj, anim_clip=None, f=None):
        for skeleton_child_node in parent_node.children:
            if anim_clip is None:
                node = skeleton_child_node
                transform = node.transform
            else:
                node = ReNode()
                curve = anim_clip.get_animation_curve(skeleton_child_node.name)
                node.transform = curve.keyframes_qts[f].value
                transform = curve.keyframes_qts[f].value
                node.name = skeleton_child_node.name

                node.children = []
                for child in skeleton_child_node.children:
                    new_node = ReNode()
                    curve = anim_clip.get_animation_curve(child.name)
                    new_node.transform = curve.keyframes_qts[f].value
                    new_node.name = child.name
                    node.children.append(new_node)

            bone_tail, bone_head, bone_roll = self.get_bone_points(bones_obj, node.name)
            parent_tail, parent_head, parent_roll = self.get_bone_points(bones_obj, parent_node.name)

            child_name = skeleton_child_node.name.lower()
            parent_name = parent_node.name.lower()

            if child_name in CommonData.special_bone_names:
                self.reset_transformation(transform, False)
                self.fill_anim_node_children_data(skeleton_child_node, bones_obj, anim_clip, f)
                continue

            all_parent_rot = mathutils.Quaternion()
            self.get_all_parent_rots(self.parent_rotations, all_parent_rot, parent_node)

            bone_vec = bone_tail - bone_head
            transform.rotation = self.get_forward_bone_rotation(bone_vec, bone_roll, all_parent_rot)

            pos = transform.position
            rot = transform.rotation

            if len(node.children) > 1 and child_name in CommonData.pelvis_bone_names:
                if parent_node.parent is None:
                    bone_vec = bone_head
                else:
                    bone_vec = parent_tail - parent_head

                bone_vec.rotate(all_parent_rot.inverted())

                pos.x, pos.y, pos.z = bone_vec.x, bone_vec.y, bone_vec.z
            else:
                if len(node.children) == 1 or len(node.children) == 1 and len(parent_node.children) > 1 and child_name not in CommonData.pelvis_bone_names:
                    if len(parent_node.children) > 1:
                        tail = bone_head - parent_head

                        tail.rotate(all_parent_rot.inverted())
                        pos.x, pos.y, pos.z = tail.x, tail.y, tail.z

                    bone_vec = bone_tail - bone_head

                    all_parent_rot = mathutils.Quaternion()
                    all_parent_rot.rotate(rot.inverted())
                    self.get_all_parent_rots(self.parent_rotations, all_parent_rot, parent_node)

                    bone_vec.rotate(all_parent_rot.inverted())

                    node.children[0].transform.position = mathutils.Vector((bone_vec.x, bone_vec.y, bone_vec.z))
                    node.children[0].transform.rotation = mathutils.Quaternion((rot.w, rot.x, rot.y, rot.z))

                else:
                    tail = bone_head - parent_head
                    tail.rotate(all_parent_rot.inverted())
                    pos.x, pos.y, pos.z = tail.x, tail.y, tail.z

            self.parent_rotations[node.name] = rot.inverted()

            self.fill_anim_node_children_data(skeleton_child_node, bones_obj, anim_clip, f)


    # Fill shapekey mimic data
    def fill_shape_key_mimic_data(self, anim_node):
        if not self.is_exporting_mimic or self.orig_obj_name not in bpy.data.objects:
            return

        phoneme_extractor = PhonemeExtractor()
        phoneme_extractor.read_phoneme_weights()

        orig_obj = bpy.data.objects[self.orig_obj_name]

        scene = bpy.context.scene

        shape_keys = []
        shape_key_data = {}

        if len(orig_obj.data.shape_keys.key_blocks) > 0:
            shape_key_data = orig_obj.data.shape_keys.key_blocks

        has_mimic_header = len(phoneme_extractor.mimic_header_list) > 0

        for f in range(scene.frame_start, scene.frame_end + 1):
            f -= scene.frame_start

            scene.frame_set(f)

            curr_shape_key_data = {}

            after_default_shapekey = False

            for _, val in enumerate(shape_key_data):
                if has_mimic_header:
                    if val.name not in phoneme_extractor.mimic_header_list:
                        continue
                elif not after_default_shapekey and val.name != phoneme_extractor.default_shape_key:
                    continue

                after_default_shapekey = True

                curr_shape_key_data[val.name] = val.value

            shape_keys.append(curr_shape_key_data)

        anim_node.shape_key_container.shape_keys = shape_keys
