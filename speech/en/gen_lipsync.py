import sys
import importlib
import os
import shutil
from blender_re_animations_plugin import phoneme_extractor
for plugin in ["pydub", "tkinter"]:
    plugin_spec = importlib.util.find_spec(plugin)
    if plugin_spec is None:
        print(f'ERROR: {plugin} module is not installed.\nDo in cmd: pip install {plugin}\nOr: python -m pip install {plugin}')
        exit()
from pydub import AudioSegment
import tkinter
from tkinter import filedialog

wav_path = str()
prepared_wav_path = str()
remove_prepared_wav = True

def prepare():
    global prepared_wav_path, wav_path
    
    tkinter.Tk().withdraw()
    while not wav_path.endswith(".wav"):
        wav_path = tkinter.filedialog.askopenfilename(initialdir= os.getcwd(), title="Select WAV audio")
    audio = AudioSegment.from_file(wav_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    prepared_wav_path = wav_path.replace(".wav", "_mono16khz.wav")
    audio.export(prepared_wav_path, format="wav")

def generate():
    global prepared_wav_path, wav_path
    os.chdir("blender_re_animations_plugin")
    phoneme_extractor.PhonemeExtractor(audio_path=prepared_wav_path).generate_and_export_lipsync()
    if not os.path.exists("temp_head_anim.re"):
        print("Something went wrong - temp_head_anim.re was not generated!")
        exit()
    re_final_path = wav_path.replace(".wav", ".re")
    shutil.move("temp_head_anim.re", re_final_path)
    if remove_prepared_wav:
        os.remove(prepared_wav_path)
    print(f"DONE! -> {re_final_path}")

prepare()
generate()
