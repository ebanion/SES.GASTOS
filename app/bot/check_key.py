import os, sys
print("Python:", sys.executable)
val = os.getenv("OPENAI_API_KEY")
print("OPENAI_API_KEY:", repr(val))
print("OPENAI_API_KEY presente:", bool(val))
