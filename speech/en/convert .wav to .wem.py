# script written by nikich340
from pathlib import Path
from tqdm import tqdm
from tkinter import Tk, filedialog, messagebox
from shutil import move
import os
import subprocess

# setup these paths, then double-click on py file to select folder
redkit_r4data = "D:/SteamLibrary/steamapps/common/The Witcher 3 REDkit/r4data"
wwise_cli = "C:/Program Files (x86)/Audiokinetic/Wwise 2021.1.11.7933/Authoring/x64/Release/bin/WwiseCLI.exe"

def main():
    global redkit_r4data, wwise_cli
    wav_dir = ""
    
    Tk().withdraw()
    while not os.path.exists(wwise_cli):
        wwise_cli = filedialog.askopenfilename(title="Select WwiseCLI.exe")

    while not os.path.exists(redkit_r4data):
        redkit_r4data = filedialog.askdirectory(title="Select Redkit r4data DIR")

    while not os.path.exists(wav_dir):
        wav_dir = filedialog.askdirectory(title="Select wavs DIR")

    # cleanup old wem files
    for p in Path(f"{redkit_r4data}/speech").glob("*.wem"):
        if p.is_file():
            os.remove(p)

    wav_list = list( x for x in Path(wav_dir).glob("*.wav") if x.is_file() )
    print(f"Wav files: {len(wav_list)}")
    
    with open(f"{redkit_r4data}/speech/wwise/ExtSourceListGenerated.wsources", mode="w", encoding="utf-8") as f_xml:
        f_xml.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f_xml.write('<ExternalSourcesList SchemaVersion="1" Root="myExternalSources">\n')
        for w in wav_list:
            f_xml.write(f'	<Source Path="{str(w)}" />\n')
        f_xml.write('</ExternalSourcesList>\n')
    
    print(f"Converting, please wait...")
    p = subprocess.Popen([wwise_cli, f"{redkit_r4data}/speech/wwise/wwise.wproj", "-ConvertExternalSources"])
    p.wait()
    
    os.makedirs(f"{wav_dir}.wems", exist_ok=True)
    wem_cnt = 0
    for p in Path(f"{redkit_r4data}/speech").glob("*.wem"):
        if p.is_file():
            wem_cnt += 1
            move(str(p), f"{wav_dir}.wems/{p.name}")

    messagebox.showinfo('INFO', f'READY: {wem_cnt} wem files in: {wav_dir}.wems')
    Tk().destroy()
    exit()
    
main()
