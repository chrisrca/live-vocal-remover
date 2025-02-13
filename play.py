from pydub import AudioSegment
import sounddevice as sd
import numpy as np

# Load MP3 file
audio = AudioSegment.from_file("song.mp3", format="mp3")

# Convert to NumPy array and normalize
samples = np.array(audio.get_array_of_samples()).astype(np.float32)
samples /= np.max(np.abs(samples))  # Normalize

# Stereo/Mono Handling
if audio.channels == 2:
    samples = samples.reshape((-1, 2))  # Reshape for stereo

# Set Virtual Cable Output Index (WASAPI recommended)
virtual_cable_index = 30  # Update to match your system

# Infinite loop for playback
while True:
    sd.play(samples, samplerate=audio.frame_rate, device=virtual_cable_index)
    sd.wait()  # Wait until playback is done before looping again
