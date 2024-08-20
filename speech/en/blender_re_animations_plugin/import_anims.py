import os, bpy, mathutils, math
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper

from .common_data import CommonData, AnimHelper, ImportAnimsData
from .asset_node import *
from .hdf_manager import HdfManager


class JointData:
    jox_rot = None
    joy_rot = None
    joz_rot = None
    bone_transforms = {}

# --- Animation importer
class ImportAnims(bpy.types.Operator, ImportHelper):
    """Import selected .re animset file"""
    bl_idname = 'import_animset.re'
    bl_label = 'Import .re animset file'

    # ImportHelper mixin class uses this
    filename_ext = '.re'
    filter_glob: StringProperty(
        default='*.re',
        options={'HIDDEN'},
    )

    max_anim_length: IntProperty(
        name='Import frame num',
        description='Import maximum this many frames from animation set (loads all frames if non-positive)',
    )

    object_scale: IntProperty(
        name='Object scale',
        description='The new scale of the object',
        default=ImportAnimsData.object_scale,
    )

    ### Pose bone roll settings
    pose_bone_roll_settings = 'Pose bone roll settings'
    reset_bone_roll: BoolProperty(
        name='Reset pose bone rolls',
        description='For resetting and ignoring the pose bone rolls of the object (helpful when skinning imported fbx)',
        default=ImportAnimsData.reset_bone_roll,
    )

    add_pose_bone_roll_val: IntProperty(
        name='Add pose bone rolls',
        description='For adding the pose bone rolls of the object (helpful when skinning imported fbx, in degrees)',
        default=0,
    )

    ### Edit bone roll settings
    edit_bone_roll_settings = 'Edit bone roll settings'
    reset_edit_bone_roll_val: IntProperty(
        name='Set edit bone rolls',
        description='For setting edit bone rolls of the object (helpful when skinning imported fbx, in degrees)',
        default=ImportAnimsData.reset_edit_bone_roll_val,
    )

    add_edit_bone_roll_val: IntProperty(
        name='Add edit bone rolls',
        description='For adding edit bone rolls to the object (helpful when skinning imported fbx, in degrees)',
        default=0,
    )

    try_to_find_edit_bone_rolls: BoolProperty(
        name='Try to find edit bone rolls',
        description='If a mesh was imported with coordinate points on it, then try to rotate the edit bones with the corresponding rotations. Keeps edit bone rolls when replacing an animation',
        default=ImportAnimsData.try_to_find_edit_bone_rolls,
    )

    rotate_imported_object: BoolProperty(
        name='Rotate by 180 deg around Z axis',
        description='Rotate imported object around Z axis by 180 degrees',
        default=ImportAnimsData.rotate_imported_object,
    )

    is_mimic_animation: BoolProperty(
        name='Is mimic animation',
        description='Is mimic animation',
        default=ImportAnimsData.is_mimic_animation,
    )

    set_time_stretch: BoolProperty(
        name='Set time stretching to match 30 FPS',
        description='Set time stretching to match the Editor\'s default 30 FPS',
        default=ImportAnimsData.set_time_stretch,
    )

    imported_anim = True
    selected_armature: StringProperty()
    selected_file_name: StringProperty()
    remove_all_bones: BoolProperty()
    rename_obj_name: BoolProperty()

    def reset_values(self):
        self.selected_armature = ''
        self.selected_file_name = ''
        self.remove_all_bones = False
        self.rename_obj_name = True

    def draw(self, context):
        pass

    def invoke(self, context, event):
        if CommonData.test_mode:
            ImportAnims.imported_anim = not ImportAnims.imported_anim
            if ImportAnims.imported_anim:
                self.filepath = CommonData.export_test_file
            else:
                self.filepath = CommonData.import_test_file
                self.execute(context)
                bpy.ops.export_animset.re('INVOKE_DEFAULT')
                bpy.data.objects[CommonData.default_bones_name].select_set(True)
                bpy.data.objects[CommonData.default_bones_name + '.001'].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[CommonData.default_bones_name + '.001']
                bpy.ops.object.mode_set(mode='OBJECT')
                return {'FINISHED'}

            return self.execute(context)
        elif not os.path.exists(self.selected_file_name):
            ImportAnimsData.read_default_data(self)

            if self.selected_armature:
                path, _ = os.path.split(self.filepath)
                self.filepath = os.path.join(path, self.selected_armature + self.filename_ext)

            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.filepath = self.selected_file_name
            return self.execute(context)

    def execute(self, context):
        if self.filepath is None or self.filepath == '':
            return {'CANCELLED'}

        import_path = self.filepath
        CommonData.default_bones_name = os.path.splitext(os.path.basename(self.filepath))[0]
        if self.selected_armature and not self.rename_obj_name:
            CommonData.default_bones_name = self.selected_armature
        ImportAnimsData.save_default_data(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        CommonData.import_frames_one_by_one = addon_prefs.import_frames_one_by_one
        CommonData.import_create_direction_bone_vectors = addon_prefs.import_create_direction_bone_vectors

        AnimHelper.compare_and_reset_data(None)

        CommonData.hdf_manager = HdfManager()
        CommonData.hdf_manager.read_hdf_file(import_path)

        nodes = CommonData.hdf_manager.get_nodes()
        self.import_anims(nodes)

        return {'FINISHED'}

    def import_anims(self, nodes):
        joint_data = JointData()
        joint_data.bone_transforms = {}

        prev_active_obj = bpy.context.view_layer.objects.active
        prev_obj_mode = prev_active_obj.mode if prev_active_obj else None
        if prev_active_obj:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        for n in nodes:
            if isinstance(n, ReSkeletonNode):
                self.parse_skeleton_root(joint_data, n.root)

            if isinstance(n, ReAssetNode):
                wm = bpy.context.window_manager
                wm.progress_begin(0, 100)
                first_bone_obj = None

                if hasattr(n, 'asset_description'):
                    skeleton = n.asset_description.skeleton
                    CommonData.orig_skeleton = skeleton

                    root = skeleton.root
                    bone_object = self.parse_skeleton_root(joint_data, root)

                    bpy.context.view_layer.update()

                if hasattr(n, 'animation_container'):
                    anim_container = n.animation_container
                    for animation in anim_container.animations:
                        CommonData.orig_animation = animation
                        anim_clip = animation.animation_clip

                        for curve_name in anim_clip.get_curves_names():
                            curve = anim_clip.get_animation_curve(curve_name)
                            if curve_name in bone_object.pose.bones:
                                is_in_acceptable_range = self.max_anim_length > 0 and self.max_anim_length < len(curve.keyframes_qts)
                                keyframes_len = self.max_anim_length if is_in_acceptable_range else len(curve.keyframes_qts)
                                bpy.context.scene.frame_start = 0
                                bpy.context.scene.frame_end = keyframes_len
                                break

                        if self.set_time_stretch:
                            scene = bpy.context.scene
                            orig_anim_len = int(n.anim_length * scene.render.fps)
                            scene.render.frame_map_new = round(100 * orig_anim_len / scene.frame_end)

                        for keyframe_idx in range(keyframes_len):
                            self.report({'INFO'}, f'Importing {keyframe_idx}/{keyframes_len} frame...')

                            wm.progress_update(int(100.0 * keyframe_idx / keyframes_len))

                            # Get armature with pose
                            temp_bone_object = self.parse_skeleton_root(joint_data, root, anim_clip, keyframe_idx)

                            # Apply pose in Blender
                            bpy.context.view_layer.update()

                            if not CommonData.import_frames_one_by_one:
                                bpy.context.view_layer.objects.active = bone_object
                                bpy.ops.object.mode_set(mode='POSE')
                                self.set_rotations_for_pose(keyframe_idx, bone_object, temp_bone_object)

                            if not CommonData.import_frames_one_by_one:
                                if CommonData.import_delete_frame_objects:
                                    bpy.data.objects.remove(temp_bone_object, do_unlink = True)
                            elif '001' not in temp_bone_object.name:
                                temp_bone_object.hide_set(True)
                            else:
                                first_bone_obj = temp_bone_object

                            bpy.context.view_layer.objects.active = None

                        if self.rotate_imported_object:
                            bone_roll_deg = CommonData.default_bone_roll_deg
                            AnimHelper.rotate_skeleton(bone_object, bone_roll_deg, self.is_mimic_animation)

                        bone_object.scale = (self.object_scale, self.object_scale, self.object_scale)
                        bpy.context.view_layer.objects.active = bone_object
                        bpy.ops.object.mode_set(mode='POSE')

                wm.progress_end()

                if CommonData.import_frames_one_by_one:
                    bone_object.hide_set(True)
                    bpy.context.view_layer.objects.active = first_bone_obj

        if prev_obj_mode:
            try:
                bpy.ops.object.mode_set(mode=prev_obj_mode)
            except:
                pass


    # ----- Parse bone data -----
    def parse_skeleton_root(self, joint_data, root, anim_clip=None, keyframe_idx=None):
        is_edit_pose = anim_clip is None

        if is_edit_pose and self.try_to_find_edit_bone_rolls:
            self.edit_bone_roll_map = {}
            bone_object = None
            if self.selected_armature:
                bone_object = bpy.data.objects[self.selected_armature]
            else:
                for ob in bpy.data.objects:
                    if ob.type == 'MESH' and ob.parent and ob.parent.type == 'ARMATURE':
                        bone_object = ob.parent
                        break
            if bone_object:
                bpy.context.view_layer.objects.active = bone_object
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                for arm_bone in bone_object.data.edit_bones:
                    self.edit_bone_roll_map[arm_bone.name] = arm_bone.roll
                bpy.context.view_layer.objects.active = None

        if is_edit_pose and self.selected_armature:
            bone_object = bpy.data.objects[self.selected_armature]

            bone_object.name = CommonData.default_bones_name
            self.selected_armature = bone_object.name

            AnimHelper.clear_object_parent_relations(bone_object)

            if self.remove_all_bones:
                AnimHelper.remove_edit_bones(bone_object)

            if self.rotate_imported_object:
                bone_roll_deg = -CommonData.default_bone_roll_deg
                AnimHelper.rotate_skeleton(bone_object, bone_roll_deg, self.is_mimic_animation)
        else:
            armature = bpy.data.armatures.new(CommonData.default_armature_name)
            bone_object = bpy.data.objects.new(CommonData.default_bones_name, armature)
            bpy.context.scene.collection.objects.link(bone_object)

        bpy.context.view_layer.objects.active = bone_object
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        if root.get_attr('jointOrientX') != None:
            joint_data.jox_rot = mathutils.Matrix.Rotation(root.get_attr('jointOrientX'), 4, 'X')
        if root.get_attr('jointOrientY') != None:
            joint_data.joy_rot = mathutils.Matrix.Rotation(root.get_attr('jointOrientY'), 4, 'Y')
        if root.get_attr('jointOrientZ') != None:
            joint_data.joz_rot = mathutils.Matrix.Rotation(root.get_attr('jointOrientZ'), 4, 'Z')

        root_bone = bone_object.data.edit_bones.new(root.name)
        root_bone.head = (0, 0, 0)
        root_bone.tail = CommonData.unit_vector
        root_bone.tail *= CommonData.compensation_scale

        if is_edit_pose:
            self.edit_bone_name_map = {
                root.name: {
                    'child_name': root_bone.name,
                    'position': root_bone.tail.copy(),
                    'rotation': mathutils.Quaternion(),
                }
            }
            CommonData.root_bone_name = root_bone.name

        self.parse_bone_children(joint_data, bone_object, root, root_bone, anim_clip, keyframe_idx)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.transform_apply()

        return bone_object

    def get_bone_rotation(self, rotation_array):
        vec_rot = mathutils.Quaternion()
        for rot in rotation_array:
            vec_rot.rotate(rot)
        return vec_rot

    def get_all_parent_rots(self, all_parent_rotation, parent_bone):
        if parent_bone.name not in CommonData.parent_rotations:
            return
        all_parent_rotation.rotate(CommonData.parent_rotations[parent_bone.name])
        if parent_bone.parent:
            self.get_all_parent_rots(all_parent_rotation, parent_bone.parent)

    def create_direction_bone_vector(self, pivot_bone, parent_bone, rotation_array):
        test_bone = pivot_bone.data.edit_bones.new('dir_vector')
        vec = AnimHelper.get_forward_unit_vec()

        vec_rot = self.get_bone_rotation(rotation_array)

        vec.rotate(vec_rot)

        test_bone.head = parent_bone.tail
        test_bone.tail = test_bone.head + vec

    def set_edit_bone_roll(self, child, bone):
        if self.try_to_find_edit_bone_rolls:
            if child.name in self.edit_bone_roll_map:
                bone.roll = self.edit_bone_roll_map[child.name]
            else:
                for ob in bpy.data.objects:
                    if ob.type == 'EMPTY' and ob.name == child.name:
                        ob.empty_display_size = 5
                        ob.empty_display_type = 'ARROWS'

                        unit_x, unit_y, unit_z = mathutils.Vector((1, 0, 0)), mathutils.Vector((0, 1, 0)), mathutils.Vector((0, 0, 1))

                        rotation_diff_y = unit_y.rotation_difference(bone.tail - bone.head)

                        rotation = ob.matrix_local.to_euler()
                        unit_y.rotate(rotation)
                        unit_z.rotate(rotation)

                        unit_x.rotate(rotation_diff_y)
                        unit_x.rotate(mathutils.Matrix.Rotation(math.radians(180.0), 4, 'Z'))

                        bone.roll = unit_x.angle(unit_z)
                        if unit_y.dot(unit_x.cross(unit_z)) < 0:
                            bone.roll = 2 * math.pi - bone.roll
                        '''bone.roll -= math.pi
                        if bone.roll < 0:
                            bone.roll = math.pi + bone.roll
                        else:
                            bone.roll = bone.roll - math.pi'''

                        break
            bone.roll += math.radians(self.add_edit_bone_roll_val)
        else:
            bone.roll = math.radians(self.reset_edit_bone_roll_val)

    def parse_bone_children(self, joint_data, pivot_bone, parent_node, parent_bone=None, anim_clip=None, keyframe_idx=None):
        is_edit_pose = anim_clip is None

        children = parent_node.get_children()

        for child in children:
            if not isinstance(child, ReBoneNode):
                continue

            transform = child.transform
            if anim_clip:
                curve = anim_clip.get_animation_curve(child.name)
                if curve:
                    transform = curve.keyframes_qts[keyframe_idx].value

            # Add length to small bones
            pos = transform.position
            pos = mathutils.Vector((pos.x, pos.y, pos.z))
            if pos.length < CommonData.compensation_scale:
                pos = AnimHelper.get_forward_unit_vec(self.is_mimic_animation)
            else:
                pos *= CommonData.compensation_scale
            transform.position = pos

            bone = pivot_bone.data.edit_bones.new(child.name)

            if is_edit_pose:
                self.edit_bone_name_map[child.name] = {
                    'child_name': bone.name,
                }

            # Start with unit vector
            bone.head = (0, 0, 0)
            bone.tail = CommonData.unit_vector
            bone.parent = parent_bone

            rot = transform.rotation
            rot = mathutils.Quaternion((rot.w, rot.x, rot.y, rot.z))

            # Save current bone's rotation for later use, the rotation needs to be inverted for Blender
            CommonData.parent_rotations[bone.name] = rot.inverted()

            all_parent_rotation = mathutils.Quaternion()
            self.get_all_parent_rots(all_parent_rotation, parent_bone)

            # New bone vectors are calculated like this:
            # - The current bone's vector should be rotated with
            # - all of it's parents'rotations in respective order
            # - (the current rotation is excluded)
            pos = transform.position
            tail = mathutils.Vector((pos.x, pos.y, pos.z))
            tail.rotate(all_parent_rotation)

            child_name = child.name.lower()
            parent_name = parent_node.name

            if CommonData.import_create_direction_bone_vectors:
                self.create_direction_bone_vector(pivot_bone, parent_bone, [rot.inverted(), all_parent_rotation])

            if len(child.children) > 1 and child_name in CommonData.pelvis_bone_names:
                vec = AnimHelper.get_forward_unit_vec()

                vec_rot = self.get_bone_rotation([rot.inverted(), all_parent_rotation])

                if anim_clip is not None:
                    self.edit_bone_name_map[child.name]['position'] = vec.copy()
                    self.edit_bone_name_map[child.name]['rotation'] = vec_rot

                vec.rotate(vec_rot)

                if parent_bone.parent is None:
                    bone.head = parent_bone.head + tail
                else:
                    bone.head = parent_bone.tail.copy()
                bone.tail = bone.head + vec
            else:
                if len(parent_node.children) > 1:
                    bone.head = parent_bone.head + tail
                else:
                    bone.head = parent_bone.tail.copy()

                local_child_bone = None
                non_roll_bones_count = 0
                for local_child in child.children:
                    # First check for special bones
                    if local_child.name.lower() in CommonData.pelvis_bone_names:
                        non_roll_bones_count = 1
                        local_child_bone = local_child
                        break
                if not local_child_bone:
                    for local_child in child.children:
                        is_local_child_roll_bone = False
                        for roll_bone_name in CommonData.roll_bone_names:
                            if roll_bone_name in local_child.name.lower():
                                is_local_child_roll_bone = True
                                break
                        if not is_local_child_roll_bone:
                            non_roll_bones_count += 1
                            local_child_bone = local_child

                if non_roll_bones_count == 1 and local_child_bone:
                    child_transform = local_child_bone.transform

                    if anim_clip is not None:
                        curve = anim_clip.get_animation_curve(local_child_bone.name)
                        if curve is not None:
                            child_transform = curve.keyframes_qts[keyframe_idx].value

                    vec = child_transform.position
                    vec = mathutils.Vector((vec.x, vec.y, vec.z))
                    if vec.length < CommonData.compensation_scale:
                        vec = AnimHelper.get_forward_unit_vec(self.is_mimic_animation)
                    else:
                        vec *= CommonData.compensation_scale

                    all_parent_rotation = mathutils.Quaternion()
                    self.get_all_parent_rots(all_parent_rotation, bone)

                    if anim_clip is not None:
                        self.edit_bone_name_map[child.name]['position'] = vec.copy()
                        self.edit_bone_name_map[child.name]['rotation'] = all_parent_rotation

                    vec.rotate(all_parent_rotation)

                    bone.tail = bone.head + vec
                else:
                    vec = AnimHelper.get_forward_unit_vec(self.is_mimic_animation)

                    vec_rot = self.get_bone_rotation([rot.inverted(), all_parent_rotation])

                    if anim_clip is not None:
                        self.edit_bone_name_map[child.name]['position'] = vec.copy()
                        self.edit_bone_name_map[child.name]['rotation'] = vec_rot

                    vec.rotate(vec_rot)

                    bone.tail = bone.head + vec

            if is_edit_pose:
                self.set_edit_bone_roll(child, bone)

            self.parse_bone_children(joint_data, pivot_bone, child, bone, anim_clip, keyframe_idx)

    # ----- Setting pose rotations -----
    def set_pose_bone_rotation(self, pb, target_data):
        if 'head_pos' not in target_data or 'position' not in target_data or 'rotation' not in target_data:
            return

        pos = target_data['position']
        rot = target_data['rotation']
        head_pos = target_data['head_pos']

        forward = AnimHelper.get_blender_forward_unit_vec()
        rot_diff = forward.rotation_difference(pos)

        if self.reset_bone_roll:
            pos.rotate(rot)
            rot = forward.rotation_difference(pos)

            M = (
                mathutils.Matrix.Translation(head_pos) @
                rot.to_matrix().to_4x4()
                )
        else:
            M = (
                mathutils.Matrix.Translation(head_pos) @
                rot.to_matrix().to_4x4() @
                rot_diff.to_matrix().to_4x4()
                )

        self.matrix_map[pb.name] = M

    def set_rotations_for_pose(self, frame_idx, pose_ob, target_ob):
        scene = bpy.context.scene
        scene.frame_current = frame_idx

        self.matrix_map = {}

        for bone in target_ob.pose.bones:
            if bone.name in self.edit_bone_name_map:
                self.edit_bone_name_map[bone.name]['head_pos'] = bone.head

        def get_target_data(child_name):
            for bone_name in self.edit_bone_name_map:
                if child_name == self.edit_bone_name_map[bone_name]['child_name']:
                    return self.edit_bone_name_map[bone_name]
            return None

        def parse_children(bone):
            for child in bone.children:
                pose_bone = pose_ob.pose.bones[child.name]
                target_data = get_target_data(child.name)

                if not target_data:
                    break

                self.set_pose_bone_rotation(pose_bone, target_data)

                parse_children(child)

        root_bone = pose_ob.pose.bones[CommonData.root_bone_name]
        parse_children(root_bone)

        self.set_pose_matrices(pose_ob, self.matrix_map)

        for pose_bone in pose_ob.pose.bones:
            pose_bone.keyframe_insert('rotation_quaternion', frame=frame_idx)
            pose_bone.keyframe_insert('location', frame=frame_idx)

    def set_pose_matrices(self, obj, matrix_map):
        "Assign pose space matrices of all bones at once, ignoring constraints."

        def rec(pbone, parent_matrix):
            if pbone.name in matrix_map:
                matrix = matrix_map[pbone.name]

                # # Instead of:
                # pbone.matrix = matrix
                # bpy.context.view_layer.update()

                # Compute and assign local matrix, using the new parent matrix
                if pbone.parent:
                    pbone.matrix_basis = pbone.bone.convert_local_to_pose(
                        matrix,
                        pbone.bone.matrix_local,
                        parent_matrix=parent_matrix,
                        parent_matrix_local=pbone.parent.bone.matrix_local,
                        invert=True
                    )
                else:
                    pbone.matrix_basis = pbone.bone.convert_local_to_pose(
                        matrix,
                        pbone.bone.matrix_local,
                        invert=True
                    )
            else:
                # Compute the updated pose matrix from local and new parent matrix
                if pbone.parent:
                    matrix = pbone.bone.convert_local_to_pose(
                        pbone.matrix_basis,
                        pbone.bone.matrix_local,
                        parent_matrix=parent_matrix,
                        parent_matrix_local=pbone.parent.bone.matrix_local,
                    )
                else:
                    matrix = pbone.bone.convert_local_to_pose(
                        pbone.matrix_basis,
                        pbone.bone.matrix_local,
                    )

            # Recursively process children, passing the new matrix through
            for child in pbone.children:
                rec(child, matrix)

        # Scan all bone trees from their roots
        for pbone in obj.pose.bones:
            if not pbone.parent:
                rec(pbone, None)


class ReplaceAnims(bpy.types.Operator):
    """Replace selected object with .re animset file"""
    bl_idname = 'replace_animset.re'
    bl_label = 'Replace object with .re animset file'

    remove_all_bones: BoolProperty()

    def get_valid_selected_obj(self, context):
        selected_ids = AnimHelper.get_selected_obj_list(context)
        for obj in selected_ids:
            if obj and hasattr(obj.data, 'edit_bones') and obj.name in bpy.data.objects:
                return obj
        return None

    @classmethod
    def poll(cls, context):
        return cls.get_valid_selected_obj(cls, context)

    def execute(self, context):
        selected_obj = self.get_valid_selected_obj(context)
        if not selected_obj:
            return

        selected_armature = selected_obj.name

        ImportAnimsData.try_to_find_edit_bone_rolls = True

        bpy.ops.import_animset.re(
            'INVOKE_DEFAULT',
            selected_armature=selected_armature,
            remove_all_bones=self.remove_all_bones,
            rename_obj_name=True,
        )

        return {'FINISHED'}

