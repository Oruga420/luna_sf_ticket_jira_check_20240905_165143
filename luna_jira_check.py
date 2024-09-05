import time
import openai
from atlassian import Jira
import requests
import soundfile as sf
import sounddevice as sd
from pydub import AudioSegment
from pydub.playback import play
import io
import os

# Jira Setup
JIRA_URL = ""
JIRA_EMAIL = ""
JIRA_API_TOKEN = ""  # Replace with your actual JIRA API token
# ElevenLabs Setup
voice_id = ""
api_key = ""  # Replace with your actual ElevenLabs API key
model_id = "" # 11labs multilingual voice
# OpenAI Setup
openai.api_key = ""  # Replace with your actual OpenAI API key
ffmpeg_bin_path = r''

if ffmpeg_bin_path not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + ffmpeg_bin_path

# Define a function to generate audio using ElevenLabs API
def generate_elevenlabs(text, voice_id, api_key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0
        }
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("Audio generated successfully")
        response = response.content.replace(b'mp3', b'wav')
        return response
    else:
        print("No audio generated")
        return None

# Define a function to play audio
def play_audio(audio_data):
    if audio_data is None:
        print("No audio data to play.")
        return

    with io.BytesIO(audio_data) as f:
        audio_data, samplerate = sf.read(f, dtype='int16')
    print("Playing audio...")
    sd.play(audio_data, samplerate)
    sd.wait()
# Set up Jira
jira = Jira(url=JIRA_URL, username=JIRA_EMAIL, password=JIRA_API_TOKEN)


def countdown(seconds):
    for i in range(seconds, 0, -1):
        print(f"Next check in {i} seconds...", end="\r")
        time.sleep(1)

# Main Function
if __name__ == "__main__":
    jira_issue_key_input = input("Enter Jira ticket URL :")
    jira_issue_key = jira_issue_key_input.split("/")[-1]

    last_comment_count = len(jira.issue_field_value(jira_issue_key, 'comment')['comments'])

    while True:
        current_comment_count = len(jira.issue_field_value(jira_issue_key, 'comment')['comments'])
        
        if current_comment_count > last_comment_count:
            # Extract the newest comment from JIRA
            jira_comments = jira.issue_field_value(jira_issue_key, 'comment')['comments']
            new_comment = jira_comments[-1]["body"]
            print(f"\nNew comment: {new_comment}")
            last_comment_count = current_comment_count

            # Generate a summary with OpenAI
            messages = [
                {"role": "system", "content": "You are a powerful AI assistant that can summarize and analyze information from a Jira ticket. Your goal is to provide a concise and clear summary of the ticket's current status and any important details that need immediate attention."},
                {"role": "user", "content": f"the idea is for you to alert me that this: {new_comment}"},
                {"role": "user", "content": f"but I will be prob doing some cool stuff so you can say stuff like <Oruga, dude, hey boss, yo chief> and then tell what the issue is about feel free to paraphrase and remember you got my back and I trust you"},        
            ]

            response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
            summary = response["choices"][0]["message"]["content"]
            print(f"Summary: {summary}")

            # Use ElevenLabs API to say the generated comment
            audio_data = generate_elevenlabs(summary, voice_id, api_key)
            play_audio(audio_data)

        # Countdown before re-running the loop
        countdown(30)