from src.computer.browser import BrowserController
class BrowserInterface:
    def __init__(self):
        self.browser = BrowserController()

    def initialize(self):
        if not self.browser:
            self.browser = BrowserController()

    def browse(self, url: str):
        self.initialize()
        if self.browser:
            self.browser.navigate(url)
            self.current_url = url
            return True
        return False

    def close(self):
        if self.browser:
            self.browser.close()
            self.browser = None
            self.current_url = None

    def speak(self, text):
        """Speak through the browser's virtual microphone"""
        return self.browser.speak_through_mic(text)
