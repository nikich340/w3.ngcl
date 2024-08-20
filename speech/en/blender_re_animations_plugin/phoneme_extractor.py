if __name__ == '__main__':
    from  install_dependecies import install_dependency
    from  hdf_manager import HdfManager
else:
    from .install_dependecies import install_dependency
    from .hdf_manager import HdfManager

try:
    import pocketsphinx
except ImportError:
    install_dependency('pocketsphinx')
try:
    import wave
except ImportError:
    install_dependency('wave')
try:
    import audioop
except ImportError:
    install_dependency('audioop')

import os, wave, audioop, re
from pocketsphinx import AudioFile, get_model_path


class Segment:
    def __init__(self, start, end, phon):
        self.start = start
        self.end = end
        self.phon = phon

class SegmentMetadata:
    def __init__(self, fps, frame_len, time_len):
        self.fps = fps
        self.frame_len = frame_len
        self.time_len = time_len

class PhonemeExtractor:
    language = 'en-us'
    sil_phoneme = 'SIL'
    noise_phonemes = ['+SPN+', '+NSN+']
    desired_samprate = 16000

    mimic_scale = 0.5
    mimic_anim_blend_time = 0.2

    default_fps = 30
    default_phonemes_filename = 'phonemes.txt'
    default_mimic_anim_filename = 'all_mimics.re'

    phonemes_data = {}
    mimic_header_list = []
    phoneme_list = []

    def __init__(self, audio_path=None, text_path=None):
        if audio_path is not None and not os.path.exists(audio_path):
            return

        self.audio_path = audio_path
        self.text_path = text_path

    def generate_lipsync(self, verbose=True) -> list:
        samprate = 16000
        time_len = 0
        fps = 100 # Default FPS for pocketsphinx
        was_audio_downsampled = False
        error_msg = ''

        samprate, _, nchannels, time_len = self.get_audio_data()

        if self.desired_samprate != samprate or nchannels != 1:
            error_msg = f'The audio file should be MONO with {self.desired_samprate}Hz sample rate. The automatic audio conversion will probably fail, please convert it manually. The lipsync generation will also probably fail.'

            # Create temp downsampled audio file
            new_audio_path = self.audio_path + '.raw'
            if not self.downsample_wav(self.audio_path, new_audio_path, inrate=samprate, outrate=self.desired_samprate, inchannels=nchannels):
                return

            was_audio_downsampled = True
            self.audio_path = new_audio_path

            samprate, _, nchannels, time_len = self.get_audio_data()

        lang = self.language

        segments = []
        seg_start_fnum = 0

        for phrase in AudioFile(
                self.audio_path,
                kws_threshold=1e-30,
                hmm=get_model_path(f'{lang}/{lang}'),
                allphone=get_model_path(f'{lang}/{lang}-phone.lm.bin'),
                dic=get_model_path(f'{lang}/cmudict-{lang}.dict'),
                #jsgf=self.create_jsfg_file(text_path),
                backtrace='yes',
                lw=1.0,
                beam=1e-80,
                wbeam=1e-60,
                pbeam=1e-80,
                samprate=samprate,
                frate=fps,
            ):
            try:
                for seg in phrase.seg():
                    if seg.word != self.sil_phoneme and seg.word not in self.noise_phonemes:
                        segments.append(
                            Segment(
                                (phrase.start_frame + seg.start_frame) / fps,
                                (phrase.start_frame + seg.end_frame) / fps,
                                seg.word,
                            )
                        )
                    seg_start_fnum = phrase.start_frame + seg.end_frame
            except:
                pass

        seg_meta = SegmentMetadata(fps=fps, frame_len=seg_start_fnum, time_len=time_len)

        if verbose:
            sep_len = 28
            print('-' * sep_len)
            print('|  %5s  |   %3s   | %4s |' % ('start', 'end', 'phon'))
            print('-' * sep_len)
            for segment in segments:
                print('| %6ss | %6ss | %4s |' % (segment.start, segment.end, segment.phon))
            print('-' * sep_len)

        # Remove temp audio
        if was_audio_downsampled:
            os.remove(self.audio_path)

        return seg_meta, segments, error_msg

    def create_jsfg_file(self) -> str:
        base_path = os.path.dirname(self.text_path)
        jsgf_path = os.path.join(base_path, 'with-word.jsgf')

        text = ''
        with open(self.text_path, 'r') as fp:
            lines = fp.readlines()
            if len(lines) > 0:
                text = lines[0].strip().lower()
                text = re.sub('[^0-9a-z]+', ' ', text).strip()

        with open(jsgf_path, 'w') as fw:
            fw.write('#JSGF V1.0;\n')
            fw.write('grammar word;\n')
            fw.write('public <wholeutt> = sil ')
            fw.write(' [ sil ] '.join(text.split(' ')))
            fw.write(' [ sil ];\n')

        return jsgf_path

    def get_audio_data(self):
        with wave.open(self.audio_path, 'r') as fp:
            samprate = fp.getframerate()
            frames = fp.getnframes()
            nchannels = fp.getnchannels()
            time_len = frames / float(samprate)
        return samprate, frames, nchannels, time_len

    def downsample_wav(self, src, dst, inrate=44100, outrate=16000, inchannels=2, outchannels=1) -> bool:
        if not os.path.exists(src):
            return False

        base_dir = os.path.dirname(dst)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        with wave.open(src, 'r') as fp:
            with wave.open(dst, 'w') as fw:
                n_frames = fp.getnframes()
                data = fp.readframes(n_frames)

                try:
                    converted = audioop.ratecv(data, 2, inchannels, inrate, outrate, None)
                    converted = converted[0]
                except:
                    return False

                try:
                    fw.setparams((outchannels, 2, outrate, 0, 'NONE', 'Uncompressed'))
                    fw.writeframes(converted)
                except:
                    return False

        return True

    def read_phoneme_weights(self, phonemes_filepath=None):
        if phonemes_filepath:
            file_path = phonemes_filepath
        else:
            file_path = os.path.join(os.path.dirname(__file__), PhonemeExtractor.default_phonemes_filename)

        self.phoneme_list = []

        with open(file_path, 'r') as fp:
            is_header_line = True
            for l in fp.readlines():
                data = l.split('\t')

                if len(data) <= 1:
                    continue

                data[-1] = data[-1].strip()

                data_head = data[0]

                self.phoneme_list.append(data_head)

                if is_header_line:
                    self.mimic_header_list = data
                    header_list = data
                    is_header_line = False
                    continue

                idx = 0
                for s in header_list:
                    if idx >= len(data):
                        break

                    try:
                        data_val = float(data[idx])
                    except:
                        data_val = data[idx]

                    if data_head not in self.phonemes_data:
                        self.phonemes_data[data_head] = {}

                    self.phonemes_data[data_head][s] = data_val

                    idx += 1


    def generate_and_export_lipsync(self, hdf_in='head_anim.re', hdf_out='temp_head_anim.re'):
        self.read_phoneme_weights()
        seg_meta, lipsync_data, error_msg = self.generate_lipsync()

        hdf_manager = HdfManager()
        hdf_manager.read_hdf_file(hdf_in)
        nodes = hdf_manager.get_nodes()

        if len(nodes) == 0:
            return

        fps = PhonemeExtractor.default_fps

        anim_node = nodes[0]

        shape_keys = []
        frame_end = 0

        default_phoneme_data = list(self.phonemes_data.values())[-1]

        for d in lipsync_data:
            found_phoneme_header = self.search_for_matching_phoneme(d.phon)
            if not found_phoneme_header and len(d.phon) == 2:
                for new_phon in [d.phon[0], d.phon[1]]:
                    found_phoneme_header = self.search_for_matching_phoneme(new_phon)
                    if found_phoneme_header:
                        break

            curr_shape_data = {}
            self.fill_mimic_data(default_phoneme_data, curr_shape_data, 0.)
            frame_start = int(d.start * fps)
            for _ in range(frame_end, frame_start):
                shape_keys.append(curr_shape_data)
            frame_end = frame_start

            if found_phoneme_header:
                phoneme_data = self.phonemes_data[found_phoneme_header]

                curr_shape_data = {}
                self.fill_mimic_data(phoneme_data, curr_shape_data, PhonemeExtractor.mimic_scale)

                frame_start = frame_end
                frame_end   = int(d.end * fps)
                for _ in range(frame_start, frame_end):
                    shape_keys.append(curr_shape_data)
            else:
                print(f'ERROR: "{d.phon}" phoneme not found.')

        curr_shape_data = {}
        anim_frame_end = int(seg_meta.time_len * fps)
        self.fill_mimic_data(default_phoneme_data, curr_shape_data, 0.)
        for _ in range(frame_end, anim_frame_end):
            shape_keys.append(curr_shape_data)

        anim_clip = anim_node.animation_container.animations[0].animation_clip
        for curve_name in anim_clip.get_curves_names():
            curve = anim_clip.get_animation_curve(curve_name)
            curve.keyframes_qts = [curve.keyframes_qts[0]]
            for _ in range(1, anim_frame_end):
                curve.keyframes_qts.append(curve.keyframes_qts[0])

        anim_node.anim_length = seg_meta.time_len
        anim_node.shape_key_container.shape_keys = shape_keys

        hdf_manager.write_hdf_file(hdf_out, anim_node)

    def fill_mimic_data(self, phoneme_data, curr_shape_data, scale):
        for mimic_data_key in phoneme_data:
            val = phoneme_data[mimic_data_key]
            if isinstance(val, float):
                val *= scale
                curr_shape_data[mimic_data_key] = val

    def simplify_phoneme(self, phon) -> str:
        phon = phon.lower()
        if len(phon) == 2 and phon[0] == phon[1]:
            phon = phon[0]
        return phon

    def search_for_matching_phoneme(self, phon):
        phon = self.simplify_phoneme(phon)
        found_phoneme_header = None
        for phoneme_header in self.phonemes_data:
            if self.simplify_phoneme(phoneme_header) == phon:
                found_phoneme_header = phoneme_header
                break
        return found_phoneme_header


# --- Standalone ---
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        PhonemeExtractor(audio_path=audio_path).generate_and_export_lipsync()
    else:
        print(f'ERROR: Please specify an audio path!\npython {os.path.basename(sys.argv[0])} <audio_path>')
