# Karaoke System - Setup and Usage Guide

This guide explains how to set up a Conda environment, run `play.py` to play an audio file, use `karaoke.py` to process live microphone input and remove vocals, and finally use `playback.py` to play back the processed audio.

## 1. Cloning the Conda Environment
To ensure you have all necessary dependencies installed, clone the environment using the provided `demucs-env.yaml` file.

### **Step 1: Create a Conda Environment from YAML**
```sh
conda env create --file demucs-env.yaml
```
This will create an environment with the necessary dependencies.

### **Step 2: Activate the Environment**
```sh
conda activate demucs-env
```
Ensure that the environment is activated before running any scripts.

## 2. Running `play.py` to Play an MP3 File
The `play.py` script loads an MP3 file and plays it through a virtual audio cable. You must set up a virtual audio cable on your system and update `virtual_cable_index` in the script to the correct device index.

Alternatively you can just use a microphone input from another device if you would like to pass songs from players like spotify or apple music through.

### **Run `play.py`**
```sh
python play.py
```
This will continuously play `faster.mp3` through the virtual audio cable.

## 3. Using `karaoke.py` to Stream Live Audio and Remove Vocals
The `karaoke.py` script records live audio from your microphone, processes it using Demucs to remove vocals, and saves the processed chunks.

### **Run `karaoke.py`**
```sh
python karaoke.py
```
This will continuously record 10-second chunks of audio and process them to remove vocals. The processed files are saved in the `output` directory.

## 4. Playing Processed Audio with `playback.py`
The `playback.py` script monitors the `output` directory for new processed audio files and plays them back seamlessly while removing slight delays at the start and end of each chunk.

### **Run `playback.py`**
```sh
python playback.py
```
This will automatically detect and play the processed chunks as they become available.

## **System Requirements & Notes**
- Ensure that `demucs` is installed and configured properly inside the Conda environment.
- A Nvidia GPU is required for demucs.
- You need a virtual audio cable to reroute sound from `play.py` to be picked up by `karaoke.py`.
- Modify `virtual_cable_index` in `play.py` to match your system's audio setup.
- The system continuously processes and plays back audio, creating a near real-time karaoke effect.

This setup allows you to either play pre-recorded MP3 files or stream live audio, process it in real-time, and play back the karaoke version.