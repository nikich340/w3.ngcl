# --- Blender plugin ---
import bpy, os
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper

from .phoneme_extractor import PhonemeExtractor
from .common_data import AnimHelper, ImportAnimsData


class LipsyncGenerator(bpy.types.Operator, ImportHelper):
    """Automated lipsync generator"""
    bl_idname = 'lipsync_generator.re'
    bl_label = 'Automated lipsync generator'

    # ImportHelper mixin class uses this
    filename_ext = '.wav'
    filter_glob: StringProperty(
        default='*.wav',
        options={'HIDDEN'},
    )

    fail_on_error: BoolProperty(
        name='Fail lipsync generation on error',
        description='If the audio file is not in a correct format, then do not generate lipsync.',
        default=True,
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

        ImportAnimsData.save_default_data(self)

        selected_obj = self.get_valid_selected_obj(context)
        if not selected_obj:
            return

        key_blocks = selected_obj.data.shape_keys.key_blocks
        drivers = selected_obj.data.shape_keys.animation_data.drivers

        phoneme_extractor = PhonemeExtractor(audio_path=self.filepath)
        seg_meta, lipsync_data, error_msg = phoneme_extractor.generate_lipsync()

        scene = bpy.context.scene
        fps = PhonemeExtractor.default_fps

        orig_anim_len = int(seg_meta.time_len * scene.render.fps)
        scene.frame_end = int(seg_meta.time_len * fps)

        scene.render.frame_map_new = round(100 * orig_anim_len / scene.frame_end)

        AnimHelper.clear_mimic_keyframe_data(selected_obj)

        if not scene.sequence_editor:
            scene.sequence_editor_create()

        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND':
                scene.sequence_editor.sequences.remove(strip)

        if error_msg:
            self.report({'ERROR'}, error_msg)
            if self.fail_on_error:
                return {'CANCELLED'}

        scene.sequence_editor.sequences.new_sound(os.path.basename(self.filepath), self.filepath, 1, 1)

        for d in drivers:
            d.mute = False

        for d in lipsync_data:
            found_key_block = self.search_for_matching_phoneme(d.phon, phoneme_extractor, key_blocks)
            if not found_key_block and len(d.phon) == 2:
                for new_phon in [d.phon[0], d.phon[1]]:
                    found_key_block = self.search_for_matching_phoneme(new_phon, phoneme_extractor, key_blocks)
                    if found_key_block:
                        break

            if found_key_block:
                blend_time = PhonemeExtractor.mimic_anim_blend_time

                frame_start = int(d.start * fps)
                frame_end   = int(d.end * fps)

                found_key_block.value = 0
                found_key_block.keyframe_insert('value', frame=0)
                found_key_block.keyframe_insert('value', frame=frame_start - blend_time)

                found_key_block.value = PhonemeExtractor.mimic_scale
                found_key_block.slider_max = PhonemeExtractor.mimic_scale
                found_key_block.keyframe_insert('value', frame=frame_start)
                found_key_block.keyframe_insert('value', frame=frame_end)

                found_key_block.value = 0
                found_key_block.keyframe_insert('value', frame=frame_end + blend_time)
            else:
                self.report({'ERROR'}, f'"{d.phon}" phoneme not found.')

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = selected_obj
        return {'FINISHED'}

    def search_for_matching_phoneme(self, phon, phoneme_extractor, key_blocks):
        phon = phoneme_extractor.simplify_phoneme(phon)
        found_key_block = None
        for key_block in key_blocks:
            if phoneme_extractor.simplify_phoneme(key_block.name) == phon:
                found_key_block = key_block
                break
        return found_key_block

# --- Standalone ---
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        PhonemeExtractor(audio_path=audio_path).generate_and_export_lipsync(hdf_in='head_anim.re', hdf_out='temp_head_anim.re')
    else:
        print(f'ERROR: Please specify an audio path!\npython {sys.argv[0]} <audio_path>')
    exit()