import bpy, os
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper

from .common_data import CommonData, AnimHelper, ImportAnimsData
from .asset_node import *
from .hdf_manager import HdfManager
from .phoneme_extractor import PhonemeExtractor


class ImportMimic(bpy.types.Operator, ImportHelper):
    """Import mimic shapekeys"""
    bl_idname = 'import_mimic.re'
    bl_label = 'Import mimic shapekeys'

    # ImportHelper mixin class uses this
    filename_ext = '.re'
    filter_glob: StringProperty(
        default='*.re',
        options={'HIDDEN'},
    )

    def get_valid_selected_obj(self, context):
        selected_ids = AnimHelper.get_selected_obj_list(context)
        for obj in selected_ids:
            if obj and obj.type == 'MESH' and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 0:
                return obj
        return None

    @classmethod
    def poll(cls, context):
        return cls.get_valid_selected_obj(cls, context)

    def invoke(self, context, event):
        ImportAnimsData.read_default_data(self)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if self.filepath is None or self.filepath == '':
            return {'CANCELLED'}

        import_path = self.filepath
        ImportAnimsData.save_default_data(self)

        CommonData.hdf_manager = HdfManager()
        CommonData.hdf_manager.read_hdf_file(import_path)

        nodes = CommonData.hdf_manager.get_nodes()

        scene = bpy.context.scene
        scene_fps = scene.render.fps

        selected_obj = self.get_valid_selected_obj(context)
        if not selected_obj:
            return

        key_blocks = selected_obj.data.shape_keys.key_blocks
        drivers = selected_obj.data.shape_keys.animation_data.drivers

        AnimHelper.clear_mimic_keyframe_data(selected_obj)

        for n in nodes:
            if isinstance(n, ReAssetNode):
                shape_keys = n.shape_key_container.shape_keys
                frame_len = len(shape_keys)

                if frame_len == 0:
                    continue

                orig_anim_len = n.anim_length
                if orig_anim_len > 0:
                    new_anim_len = frame_len / float(scene_fps)
                    scene.render.frame_map_new = round(100 * orig_anim_len / new_anim_len)

                scene.frame_start = 0
                scene.frame_end = frame_len

                for d in drivers:
                    d.mute = True

                for f, shape_key in enumerate(shape_keys):
                    scene.frame_set(f)
                    for shape_val in shape_key:
                        for key in shape_val:
                            if key in key_blocks:
                                key_blocks[key].value = shape_val[key]
                                key_blocks[key].keyframe_insert('value', frame=f)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = selected_obj
        return {'FINISHED'}


class ExportMimic(bpy.types.Operator):
    """Export mimic shapekeys"""
    bl_idname = 'export_mimic.re'
    bl_label = 'Export mimic shapekeys'

    def get_valid_selected_obj(self, context):
        selected_ids = AnimHelper.get_selected_obj_list(context)
        for obj in selected_ids:
            if obj and obj.type == 'MESH' and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 0:
                return obj
        return None

    @classmethod
    def poll(cls, context):
        return cls.get_valid_selected_obj(cls, context)

    def execute(self, context):
        context_obj_name = None
        if CommonData.head_anim_obj_name in bpy.data.objects:
            context_obj_name = CommonData.head_anim_obj_name

        selected_obj = self.get_valid_selected_obj(context)
        if not selected_obj:
            return

        override = context.copy()
        override['is_exporting_mimic'] = ''

        with context.temp_override(**override):
            bpy.ops.export_animset.re('INVOKE_DEFAULT', context_obj_name=context_obj_name, orig_obj_name=selected_obj.name)

        return {'FINISHED'}

class MimicManager(bpy.types.Operator, ImportHelper):
    """Setup mimic shapekeys"""
    bl_idname = 'shapekeys.re'
    bl_label = 'Setup mimic shapekeys'

    mimic_anim_obj_name: StringProperty(
        name='Mimic anim object name',
        description='Mimic animation object name in scene',
        default=CommonData.mimic_anim_obj_name,
    )

    import_mimic_anim: BoolProperty(
        name='Import mimic anim from file',
        description='Import mimic animation from an .re file',
        default=False,
    )

    phonemes_filepath = None
    mimic_anim_filepath = None

    def invoke(self, context, event):
        self.phonemes_filepath = None
        self.mimic_anim_filepath = None

        if self.filepath is None or not os.path.exists(self.filepath):
            self.filepath = os.path.join(os.path.dirname(__file__), PhonemeExtractor.default_phonemes_filename)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if self.filepath is None or not os.path.exists(self.filepath):
            return {'CANCELLED'}

        if self.phonemes_filepath is None:
            self.phonemes_filepath = self.filepath

            if self.import_mimic_anim:
                self.filepath = os.path.join(os.path.realpath(self.filepath), PhonemeExtractor.default_mimic_anim_filename)

                context.window_manager.fileselect_add(self)
                return {'RUNNING_MODAL'}
        else:
            self.mimic_anim_filepath = self.filepath
            self.filepath = self.phonemes_filepath

        if self.mimic_anim_obj_name not in bpy.data.objects:
            self.report({'ERROR'}, f'"{self.mimic_anim_obj_name}" object does not exist in scene! Aborting...')
            return {'FINISHED'}

        CommonData.mimic_anim_obj_name = self.mimic_anim_obj_name

        if self.import_mimic_anim:
            bpy.ops.import_animset.re(
                'INVOKE_DEFAULT',
                selected_armature=self.mimic_anim_obj_name,
                selected_file_name=self.mimic_anim_filepath,
                is_mimic_animation=True,
                reset_bone_roll=True,
                reset_edit_bone_roll_val=0,
                try_to_find_edit_bone_rolls=False,
                rotate_imported_object=True,
                remove_all_bones=True,
                rename_obj_name=False,
            )

        phoneme_extractor = PhonemeExtractor()
        phoneme_extractor.read_phoneme_weights(self.phonemes_filepath)

        mesh_objs = []
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            if not (obj.parent and obj.parent.type == 'ARMATURE'):
                has_modifier = False
                for m in obj.modifiers:
                    if m.type == 'ARMATURE':
                        has_modifier = True
                        break
                if not has_modifier:
                    continue
            mesh_objs.append(obj)

        bpy.ops.object.mode_set(mode='OBJECT')

        for obj in mesh_objs:
            bpy.context.view_layer.objects.active = obj

            selected_object = obj
            scene = bpy.context.scene

            selected_object.shape_key_clear()
            bpy.ops.object.shape_key_add()

            all_list = phoneme_extractor.phoneme_list + phoneme_extractor.mimic_header_list[1:]

            for f in range(scene.frame_start + 1, scene.frame_end + 1):
                scene.frame_set(f)

                if f >= len(all_list):
                    break

                if f >= len(phoneme_extractor.phoneme_list):
                    bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=True, modifier='Armature')
                else:
                    bpy.ops.object.shape_key_add()

            # loop through shapekeys and replace the names
            shape_keys = selected_object.data.shape_keys.key_blocks
            for index, key in enumerate(shape_keys):
                if key.name != 'Basis':
                    try: key.name = all_list[index]
                    except: pass

        ref_obj = None
        if len(mesh_objs) > 0:
            ref_obj = mesh_objs[0]

        for obj in mesh_objs:
            shape_keys = selected_object.data.shape_keys.key_blocks

            if obj == ref_obj:
                for index, s_key in enumerate(shape_keys):
                    if s_key.name not in phoneme_extractor.mimic_header_list:
                        continue

                    has_data = False
                    for phoneme_key in phoneme_extractor.phoneme_list[1:]:
                        val = phoneme_extractor.phonemes_data[phoneme_key][s_key.name]
                        if val != 0:
                            has_data = True
                    if not has_data:
                        continue

                    d = obj.data.shape_keys.driver_add( f'key_blocks["{s_key.name}"].value' ).driver

                    expression = ''
                    name = 'a'

                    for phoneme_key in phoneme_extractor.phoneme_list[1:]:
                        val = phoneme_extractor.phonemes_data[phoneme_key][s_key.name]

                        if val == 0:
                            continue

                        v = d.variables.new()
                        v.type                 = 'SINGLE_PROP'
                        v.name                 = name
                        v.targets[0].id_type   = 'KEY'
                        v.targets[0].id        = obj.data.shape_keys
                        v.targets[0].data_path = f'key_blocks["{phoneme_key}"].value'

                        expression += f'{val}*' + name + '+'

                        name = chr(ord(name) + 1)
                        if ord(name) > ord('z'):
                            name = 'A'

                    expression = expression[:-1]
                    max_var_len = 9
                    while len(expression) > 256:
                        exp = expression.split('+')

                        new_exp = []
                        for e in exp:
                            if len(e) >= max_var_len:
                                new_val = ('{:.' + str(max_var_len - 3) + 'f}').format(float(e[:-2]))
                                new_exp.append(new_val + e[-2:])
                            else:
                                new_exp.append(e)

                        new_expression = '+'.join(new_exp)

                        if len(new_expression) <= 256:
                            print('OLD -> NEW expression')
                            print('OLD : ' + expression)
                            print('NEW : ' + new_expression)
                            print()

                        expression = new_expression

                        max_var_len -= 1

                    d.expression = expression
                continue

            for s_key in shape_keys:
                d = obj.data.shape_keys.driver_add( f'key_blocks["{s_key.name}"].value' ).driver

                v = d.variables.new()
                v.type                 = 'SINGLE_PROP'
                v.name                 = 'value'
                v.targets[0].id_type   = 'KEY'
                v.targets[0].id        = ref_obj.data.shape_keys
                v.targets[0].data_path = f'key_blocks["{s_key.name}"].value'

                d.expression = 'value'

        bpy.context.view_layer.objects.active = ref_obj

        return {'FINISHED'}

