from io import BytesIO
import numpy as np
import soundfile as sf
from kokoro import KPipeline
from flask import Flask, request, jsonify
from threading import Thread, Lock

app_kokoro = Flask("kokoro_app")

#  make sure you do this  : pip install -q kokoro>=0.8.2 soundfile

# https://huggingface.co/hexgrad/Kokoro-82M APACHE LICENCE http://www.apache.org/licenses/LICENSE-2.0 

# Initialize the Kokoro pipeline with American English ('a').
# Adjust lang_code and voice as needed.
kokoro_pipeline = KPipeline(lang_code='a')
kokoro_lock = Lock()  # Lock to serialize access to the Kokoro pipeline

def trim_and_fade(audio, sample_rate, threshold=0.01, fade_duration=0.05):
    """
    Trims leading and trailing silence from an audio signal and applies a fade-in and fade-out.
    
    Parameters:
        audio (np.array): The audio signal array.
        sample_rate (int): Sampling rate of the audio.
        threshold (float): Amplitude threshold to detect non-silent audio.
        fade_duration (float): Duration in seconds for fade-in and fade-out.
    
    Returns:
        np.array: The trimmed and smoothed audio signal.
    """
    # Find indices where the absolute amplitude is above the threshold.
    above_threshold = np.where(np.abs(audio) > threshold)[0]
    if above_threshold.size == 0:
        return audio

    start_idx = above_threshold[0]
    end_idx = above_threshold[-1] + 1  # +1 to include the last sample
    trimmed_audio = audio[start_idx:end_idx]

    # Calculate number of samples for the fade.
    fade_samples = int(fade_duration * sample_rate)
    fade_samples = min(fade_samples, len(trimmed_audio) // 2)

    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    trimmed_audio[:fade_samples] *= fade_in
    trimmed_audio[-fade_samples:] *= fade_out

    return trimmed_audio

def generate_speech_segment_kokoro(text):
    """
    Generate speech using the Kokoro TTS engine, trim silence, and apply fades.
    """
    try:
        if not text.strip():
            print("Input text is empty or whitespace.")
            return None

        with kokoro_lock:
            generator = kokoro_pipeline(
                text, 
                voice='af_bella',  # Change voice here if needed
                speed=0.8, 
                split_pattern=r'\n+'
            )
            audio_segments = []
            for i, (gs, ps, audio) in enumerate(generator):
            #    print(f"Kokoro segment {i}: graphemes: {gs}, phonemes: {ps}")
                audio_segments.append(audio)

            if not audio_segments:
                print("No audio segments generated by Kokoro pipeline.")
                return None

            full_audio = np.concatenate(audio_segments)
            # Trim silence and apply fade-in/out
            full_audio = trim_and_fade(full_audio, sample_rate=24000, threshold=0.01, fade_duration=0.05)

            # Write the full audio into a buffer as WAV
            buffer = BytesIO()
            sf.write(buffer, full_audio, 24000, format='WAV')
            buffer.seek(0)
          #  print("Kokoro speech generation successful.")
            return buffer.getvalue()

    except Exception as e:
        print(f"Error generating speech with Kokoro for text '{text}': {e}")
        raise

@app_kokoro.route('/generate_speech', methods=['POST'])
def generate_speech_kokoro_endpoint():
    """
    Endpoint for generating speech using the Kokoro TTS engine.
    """
    text = request.json.get('text', '')
    result = generate_speech_segment_kokoro(text)
    if result is None:
        print("Kokoro failed to generate audio.")
        return jsonify({"error": "Failed to generate audio with Kokoro"}), 500
    else:
        return result, 200, {'Content-Type': 'audio/wav'}

# ------------------- Run All Flask Apps -------------------
if __name__ == '__main__':
    def run_kokoro_app():
        print("Starting Kokoro App on port 8000...")
        app_kokoro.run(host='0.0.0.0', port=8000, debug=False)


    t_kokoro = Thread(target=run_kokoro_app)
    t_kokoro.start()
    t_kokoro.join()
