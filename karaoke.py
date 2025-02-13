import sounddevice as sd
import torchaudio
import torch
import os
import time
import threading
import queue
import subprocess
import shutil  # For moving & deleting directories
import numpy as np  # For concatenating numpy arrays

# Settings
SAMPLE_RATE = 44100           # Standard sample rate for audio
CHANNELS = 2                  # Stereo recording
BUFFER_SIZE = 10              # Seconds per chunk (total length after adding overlap)
OVERLAP = 1                   # Seconds from previous chunk to include
TMP_DIR = "recorded_chunks"   # Directory to store audio files
OUTPUT_DIR = "demucs_output"  # Where Demucs outputs processed files
FINAL_OUTPUT_DIR = "output"   # Where final no_vocals.wav files will be moved
MODEL_NAME = "htdemucs"       # Demucs model
DEVICE = "cuda"               # Change to "cpu" if no GPU

# Queue to handle processing
processing_queue = queue.Queue()

# Ensure directories exist
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

def record_audio():
    """
    Records BUFFER_SIZE-second chunks from the microphone.
    Each chunk (after the first) has the last OVERLAP seconds of the previous chunk prepended.
    """
    chunk_counter = 1
    prev_tail = None  # Will hold the last OVERLAP seconds of the previous recording
    print("Recording live microphone input... Press Ctrl+C to stop.")

    try:
        while True:
            if chunk_counter == 1:
                # For the first chunk, record full BUFFER_SIZE seconds.
                print(f"Recording chunk {chunk_counter} (full {BUFFER_SIZE} seconds)...")
                recording = sd.rec(int(SAMPLE_RATE * BUFFER_SIZE),
                                   samplerate=SAMPLE_RATE,
                                   channels=CHANNELS,
                                   dtype='float32')
                sd.wait()  # Wait for recording to finish

                # Save the last OVERLAP seconds for the next chunk.
                prev_tail = recording[-int(SAMPLE_RATE * OVERLAP):, :]
                audio_chunk = recording

            else:
                # For subsequent chunks, record only (BUFFER_SIZE - OVERLAP) seconds.
                record_duration = BUFFER_SIZE - OVERLAP
                print(f"Recording chunk {chunk_counter} (will prepend previous {OVERLAP} second)...")
                new_audio = sd.rec(int(SAMPLE_RATE * record_duration),
                                   samplerate=SAMPLE_RATE,
                                   channels=CHANNELS,
                                   dtype='float32')
                sd.wait()

                # Prepend the previous tail to the new recording.
                audio_chunk = np.concatenate((prev_tail, new_audio), axis=0)

                # Update prev_tail for the next chunk from the current audio_chunk.
                prev_tail = audio_chunk[-int(SAMPLE_RATE * OVERLAP):, :]

            # Convert to Torch tensor with shape (channels, samples)
            audio_tensor = torch.tensor(audio_chunk.T, dtype=torch.float32)

            # Save chunk as WAV file.
            chunk_path = os.path.join(TMP_DIR, f"chunk_{chunk_counter}.wav")
            torchaudio.save(chunk_path, audio_tensor, SAMPLE_RATE)
            print(f"Saved: {chunk_path}")

            # Add the chunk to the processing queue.
            processing_queue.put((chunk_counter, chunk_path))

            chunk_counter += 1  # Increment for next chunk

    except KeyboardInterrupt:
        print("\nRecording stopped.")

def run_demucs():
    """
    Processes audio chunks using Demucs, moves the result, deletes the temp output folder,
    and then deletes the original chunk file from the recorded_chunks directory.
    """
    while True:
        chunk_counter, chunk_path = processing_queue.get()
        output_chunk_dir = os.path.join(OUTPUT_DIR, f"output_{chunk_counter}")

        print(f"Processing chunk {chunk_counter} with Demucs...")

        # Start timing
        start_time = time.time()

        # Run Demucs (adjust command line arguments as needed)
        subprocess.run(
            [
                "demucs", "-n", MODEL_NAME,
                "--two-stems=vocals",
                "-d", DEVICE,
                "--overlap", "0",
                "--out", output_chunk_dir,
                chunk_path
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # End timing
        elapsed_time = time.time() - start_time
        print(f"Chunk {chunk_counter} processed in {elapsed_time:.2f} seconds.")

        # Locate output instrumental track
        model_output_dir = os.path.join(output_chunk_dir, MODEL_NAME)
        possible_folders = [f for f in os.listdir(model_output_dir)
                            if os.path.isdir(os.path.join(model_output_dir, f))]

        if not possible_folders:
            print(f"Error: No extracted folders found in {model_output_dir}!")
        else:
            instrumental_folder = os.path.join(model_output_dir, possible_folders[0])
            instrumental_file = os.path.join(instrumental_folder, "no_vocals.wav")

            if os.path.exists(instrumental_file):
                # Define new location in FINAL_OUTPUT_DIR
                final_file_path = os.path.join(FINAL_OUTPUT_DIR, f"chunk_{chunk_counter}_no_vocals.wav")

                # Move the file
                shutil.move(instrumental_file, final_file_path)
                print(f"Moved: {instrumental_file} -> {final_file_path}")

                # Delete the entire output_X folder
                shutil.rmtree(output_chunk_dir, ignore_errors=True)
                print(f"Deleted: {output_chunk_dir}")
            else:
                print(f"Error: No vocals file found for chunk {chunk_counter}!")

        # Delete the original recorded chunk after processing.
        try:
            os.remove(chunk_path)
            print(f"Deleted original chunk file: {chunk_path}")
        except Exception as e:
            print(f"Error deleting chunk file {chunk_path}: {e}")

# Start the processing thread
processing_thread = threading.Thread(target=run_demucs, daemon=True)
processing_thread.start()

# Start recording
record_audio()
