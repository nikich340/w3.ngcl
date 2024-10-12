import sys
import importlib
import os
import shutil
from pathlib import Path
from tqdm import tqdm
from blender_re_animations_plugin import phoneme_extractor
for plugin in ["pydub", "tkinter"]:
    plugin_spec = importlib.util.find_spec(plugin)
    if plugin_spec is None:
        print(f'ERROR: {plugin} module is not installed.\nDo in cmd: pip install {plugin}\nOr: python -m pip install {plugin}')
        exit()
from pydub import AudioSegment
import tkinter
from tkinter import filedialog

dir_path = str()
wav_path = str()
prepared_wav_path = str()
remove_prepared_wav = True


def select_dir():
    global dir_path
    while not os.path.exists(dir_path):
        dir_path = filedialog.askdirectory(title="Select wavs DIR")

def prepare(cur_wav_path):
    global prepared_wav_path, wav_path

    wav_path = cur_wav_path
    audio = AudioSegment.from_file(wav_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    prepared_wav_path = wav_path.replace(".wav", "_mono16khz.wav")
    audio.export(prepared_wav_path, format="wav")

def generate():
    global prepared_wav_path, wav_path
    phoneme_extractor.PhonemeExtractor(audio_path=prepared_wav_path).generate_and_export_lipsync()
    if not os.path.exists("temp_head_anim.re"):
        print("Something went wrong - temp_head_anim.re was not generated!")
        exit()
    re_final_path = wav_path.replace(".wav", ".re")
    shutil.move("temp_head_anim.re", re_final_path)
    if remove_prepared_wav:
        os.remove(prepared_wav_path)
    print(f"DONE! -> {re_final_path}")

select_dir()
os.chdir("blender_re_animations_plugin")
wav_paths = list( Path(dir_path).glob("*.wav") )
for p in tqdm(wav_paths):  
    prepare(str(p))
    generate()
