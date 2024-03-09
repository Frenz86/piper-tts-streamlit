#sudo apt-get update
#sudo apt-get install ffmpeg

import streamlit as st
import os
import uuid
import re
import subprocess
import json
import docx

# Function to format the text
def format_name(text):
    if text.endswith("."):
        text = text[:-1]
    text = text.lower()
    text = text.strip()
    # Replace non-alphabetic characters with a single underscore
    text = re.sub('[^a-z]+', '_', text)
    return text

# Function to generate the file name for TTS
def tts_file_name(text):
    text = format_name(text)
    truncated_text = text[:25] if len(text) > 25 else text if len(text) > 0 else "empty"
    random_string = uuid.uuid4().hex[:8].upper()
    file_name = f"audio/{truncated_text}_{random_string}.wav"

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    return file_name

# Modify the TTS function to return the converted MP3 file path
def piper_tts(text, model_name, speed):
    output_file = tts_file_name(text)
    command = f'echo "{text}" | piper --model {model_name} --length-scale {1/speed} --output_file {output_file}'
    result = subprocess.run(command, shell=True)
    if result.returncode == 0:
        st.write("TTS Generated Successfully!")
        return convert_to_mp3(output_file)
    else:
        st.write(f"Command failed with return code {result.returncode}")
        return None

from pydub import AudioSegment

def convert_to_mp3(wav_file):
    audio = AudioSegment.from_wav(wav_file)
    mp3_file = wav_file.replace(".wav", ".mp3")
    audio.export(mp3_file, format="mp3")
    return mp3_file

# Function to extract text from docx
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    full_text = ""
    for paragraph in doc.paragraphs:
        full_text += paragraph.text + "\n"
    return full_text

def clean_audio_folder():
    audio_folder = "audio"
    for file in os.listdir(audio_folder):
        if file.endswith(".wav") or file.endswith(".mp3"):
            file_path = os.path.join(audio_folder, file)
            os.remove(file_path)
    st.write("All audio files cleaned successfully!")

# Main function to run the Streamlit app
def main():
    st.title("TTS Streamlit App")
    with open("best_quality.json", 'r', encoding='utf-8') as f:
        read_data = json.load(f)

    # Extracting language names, voice names, and model names
    languages = list(read_data.keys())
    voice_info = {lang: list(read_data[lang].keys()) for lang in languages}
    model_info = {lang: {voice: read_data[lang][voice]["model_name"] for voice in voice_info[lang]} for lang in languages}

    # Create language dropdown
    sorted_language_list = sorted(languages, key=lambda x: x.split(' ')[0])
    default_language_index = sorted_language_list.index('Italian (Italian, Italy)')
    language_name = st.selectbox("Select Language", sorted_language_list, index=default_language_index)

    # Create voice dropdown
    selected_language = voice_info.get(language_name, [])
    voice_names = st.selectbox("Select Voice", selected_language)

    # Get model name based on language and voice
    model_name = model_info.get(language_name, {}).get(voice_names, "")

    # File uploader for docx files
    docx_file = st.file_uploader("Upload a .docx file", type=["docx"])

    if docx_file is not None:
        text = extract_text_from_docx(docx_file)
        st.text_area("Text from Document", value=text)

        # Speed slider
        speed = st.slider("Select Speed", min_value=0.1, max_value=2.0, value=1.1, step=0.1)

        if "button1" not in st.session_state:
            st.session_state["button1"] = False

        if "button2" not in st.session_state:
            st.session_state["button2"] = False

        if st.button("Generate TTS"):
            st.session_state["button1"] = not st.session_state["button1"]
            if text:
                mp3_file_path = piper_tts(text, model_name, speed)
                st.audio(mp3_file_path)
                with open(mp3_file_path, 'rb') as f:
                    mp3_content = f.read()
                    st.session_state["button2"] = not st.session_state["button2"]
                    st.download_button(label="Download MP3", data=mp3_content, file_name="trascrizione.mp3", mime="audio/mp3")
        
        if st.button("Clean Audio Folder"):
            clean_audio_folder()

if __name__ == "__main__":
    main()
