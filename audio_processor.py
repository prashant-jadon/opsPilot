import speech_recognition as sr

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def capture_audio(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=30)
                text = self.recognizer.recognize_google(audio)
                print(f"Captured: {text}")
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None 