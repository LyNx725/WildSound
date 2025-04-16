import os
import time
import numpy as np
import sounddevice as sd
import wave
from pydub import AudioSegment
from pydub.exceptions import PydubException
import google.generativeai as genai
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class WildlifeMonitor:
    def __init__(self):
        self.SAMPLE_RATE = 44100  # Sample rate for recording
        self.CHANNELS = 1  # Mono recording
        self.CHUNK = 1024  # Buffer size for recording
        self.RECORD_SECONDS = 15  # Length of recording in seconds
        self.THRESHOLD_MULTIPLIER = 1.5
        self.threshold = 130  # Set a threshold to trigger audio capture
        self.is_monitoring = False
        self.current_volume = 0
        self.alerts = []
        
        # Configure Gemini API
        genai.configure(api_key="your api key")

    def send_email_alert(self, recipient_email, alert):
        """Send an email alert to the registered user."""
        sender_email = "your mail@example.com"
        sender_password = "password"  # Use environment variables instead!
        import json

        subject = "Wildlife Alert Notification"

        try:
            analysis_data = json.loads(alert["analysis"])  # Convert JSON string to dictionary
            detected_sounds = analysis_data.get("detected_sounds", "Unknown sound detected")
        except (json.JSONDecodeError, TypeError):
            detected_sounds = alert["analysis"]  # Use raw text if parsing fails

        body = f"""
        ALERT: Threat detected!

        📅 Timestamp: {alert['timestamp']}
        📁 Audio File: {alert['file']}
        🔊 Detected Sounds: {detected_sounds}

        Please take appropriate action.
        """

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            print(f"Email alert sent to {recipient_email}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def start_stream(self):
        """Start the audio monitoring stream using sounddevice."""
        if not self.is_monitoring:
            self.is_monitoring = True
            print("Monitoring started...")

            # Create an InputStream for real-time audio capture
            self.stream = sd.InputStream(
                channels=self.CHANNELS,
                samplerate=self.SAMPLE_RATE,
                blocksize=self.CHUNK,
                dtype='int16',
                callback=self.audio_callback
            )
            self.stream.start()
    def stop_stream(self):
        """Stop the audio monitoring stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.is_monitoring = False
        print("Monitoring stopped.")

    def audio_callback(self, indata, frames, time, status):
        """Callback function for processing audio data in real-time."""
        if status:
            print(status)

        # Calculate the current volume in the callback
        self.current_volume = np.abs(indata).mean()

    def get_current_volume(self):
        """Get the current volume from the audio stream."""
        return self.current_volume

    def record_audio(self):
        """Record an audio clip when an alert is triggered using sounddevice."""
        filename = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        try:
            # Record audio data using sounddevice
            audio_data = sd.rec(int(self.RECORD_SECONDS * self.SAMPLE_RATE), samplerate=self.SAMPLE_RATE, channels=self.CHANNELS, dtype='int16')
            sd.wait()  # Wait for the recording to finish

            # Save the recorded data as a .wav file
            wavefile = wave.open(filename, 'wb')
            wavefile.setnchannels(self.CHANNELS)
            wavefile.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wavefile.setframerate(self.SAMPLE_RATE)
            wavefile.writeframes(audio_data.tobytes())
            wavefile.close()

            # Use pydub to handle format and sample rate conversion if needed
            audio = AudioSegment.from_wav(filename)
            audio = audio.set_frame_rate(44100)  # Ensure it's at the target sample rate
            audio = audio.set_channels(1)  # Ensure it's mono

            # Save the adjusted audio
            audio.export(filename, format="wav")

        except Exception as e:
            print(f"Error recording or processing audio: {e}")

        return filename

    def analyze_audio(self, file_path):
        """Analyze the recorded audio file using Gemini API."""
        file = genai.upload_file(file_path, mime_type="audio/wav")

        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro-exp-03-25",#"gemini-2.5-pro-exp-03-25"
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 65536,
            },
        )

        system_prompt = """You are an AI trained to analyze environmental sounds for wildlife conservation. 
        Your task is to analyze the given audio and provide a detailed report, identifying any significant 
        wildlife threats or events captured in the sound recording."""

        chat_session = model.start_chat(
            history=[{"role": "user", "parts": [file, system_prompt]}]
        )

        response = chat_session.send_message("Analyze the audio and provide a detailed report.")

        alert = {
            'timestamp': datetime.now(),
            'file': file_path,
            'analysis': response.text
        }
        self.alerts.append(alert)

        # Send alert email
        self.send_email_alert("recipientmail@example.com", alert)

        return alert

    def cleanup(self):
        """Clean up resources when stopping the monitor."""
        self.stop_stream()

        # self.audio.terminate()
