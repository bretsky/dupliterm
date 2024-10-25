import sys
import threading
from io import StringIO
import __main__
from pathlib import Path
from .firebase_utils import initialize_firebase, send_to_firebase, create_firebase_stream, get_valid_credentials_path

class Capture:
	def __init__(self, firebase_key_path=None):
		self.original_stdout = sys.stdout
		self.captured_output = StringIO()
		self.firebase_key_path = firebase_key_path or get_valid_credentials_path()
		self.db = initialize_firebase(self.firebase_key_path)
		self.stream = None

	def __enter__(self):
		self.stream = create_firebase_stream(self.db, Path(__main__.__file__).name)
		sys.stdout = self
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		sys.stdout = self.original_stdout
		self.stream = None

	def write(self, text):
		self.original_stdout.write(text)
		self.captured_output.write(text)
		if self.stream is not None:
			threading.Thread(target=send_to_firebase, args=(self.db, self.stream, text)).start()

	def flush(self):
		self.original_stdout.flush()

	def get_captured_output(self):
		return self.captured_output.getvalue()
	
	@classmethod
	def capture(cls, func, firebase_key_path=None):
		with cls(firebase_key_path):
			return func()
