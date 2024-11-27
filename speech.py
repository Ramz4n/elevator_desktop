import speech_recognition as sr

class Speech_recorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    def speech(self):
        with sr.Microphone() as sourse:
            self.to_say = 'Говорите!'
            audio = self.recognizer.listen(sourse)
            try:
                text = self.recognizer.recognize_google(audio, language='ru-RU')
                return text
            except sr.UnknownValueError:
                text = "Не удалось распознать речь"
                return text
            except sr.RequestError as e:
                text = f"Не удалось получить результаты от сервиса распознавания речи; {e}"
                return text