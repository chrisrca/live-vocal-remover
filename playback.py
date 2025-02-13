import os
import time
import queue
import threading
import torchaudio
import sounddevice as sd
import numpy as np

# Directory where processed no-vocals files are stored
OUTPUT_DIR = "output"
playback_queue = queue.Queue()

def monitor_processed_files():
    """
    Continuously checks for new 'chunk_#_no_vocals.wav' files in OUTPUT_DIR
    and adds them (if not already added) to the playback_queue in numerical order.
    """
    print("Monitoring for processed audio files...")
    while True:
        # Get all files matching the naming pattern.
        files = [f for f in os.listdir(OUTPUT_DIR)
                 if f.startswith("chunk_") and f.endswith("_no_vocals.wav")]
        # Sort the files based on the chunk number.
        files.sort(key=lambda x: int(x.split("_")[1]))
        
        for filename in files:
            file_path = os.path.join(OUTPUT_DIR, filename)
            # Only add if it isn't already in the queue.
            if file_path not in playback_queue.queue:
                print(f"New file detected: {file_path}")
                playback_queue.put(file_path)
        time.sleep(1)

def play_audio():
    """
    Plays audio files from the playback_queue.
    For each file, it removes 0.5 seconds from the beginning and 0.5 seconds from the end,
    then plays the remaining audio seamlessly.
    """
    print("Starting seamless playback...")

    # Open an output stream with the desired parameters.
    with sd.OutputStream(samplerate=44100, channels=2, dtype='float32', blocksize=4096) as stream:
        while True:
            # Wait for the next processed file.
            current_file = playback_queue.get()
            print(f"Playing file (trimmed): {current_file}")
            current_wave, sr = torchaudio.load(current_file)
            # Convert from shape (channels, samples) to (samples, channels) and ensure float32.
            current_np = current_wave.numpy().T.astype(np.float32)
            try:
                os.remove(current_file)
                print(f"Deleted: {current_file}")
            except Exception as e:
                print(f"Error deleting {current_file}: {e}")

            # Determine the number of samples corresponding to 0.5 seconds.
            trim_samples = int(sr * 0.5)
            if current_np.shape[0] > 2 * trim_samples:
                trimmed_np = current_np[trim_samples:-trim_samples]
            else:
                # If the chunk is too short, play it in full.
                print(f"Warning: {current_file} is too short to trim; playing entire file.")
                trimmed_np = current_np

            # Play the trimmed chunk.
            stream.write(trimmed_np)

if __name__ == "__main__":
    # Start the file monitoring thread.
    monitor_thread = threading.Thread(target=monitor_processed_files, daemon=True)
    monitor_thread.start()

    # Start playback.
    play_audio()
