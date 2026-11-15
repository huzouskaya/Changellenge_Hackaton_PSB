import zipfile
import os

files = ["solution.py", "requirements.txt", "config.py", "loader.py", "indexer.py", "assistant.py"]

with zipfile.ZipFile("submission.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    for f in files:
        if os.path.exists(f):
            zf.write(f)
            print(f"Добавлен: {f} ({os.path.getsize(f)} байт)")
        else:
            print(f"ВНИМАНИЕ: файл не найден — {f}")

print(f"\nГотово! submission.zip = {os.path.getsize('submission.zip') / 1024:.1f} KB")