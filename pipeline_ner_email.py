import os
from ner.ner_extractor import extract_entities

EMAIL_DIR = "data/emails"
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(EMAIL_DIR):
    if file.endswith(".txt"):
        with open(f"{EMAIL_DIR}/{file}", "r", encoding="utf-8") as f:
            email_text = f.read()

        print(f"Processing {file}...")
        result = extract_entities(email_text)

        with open(
            f"{OUTPUT_DIR}/{file.replace('.txt', '.json')}",
            "w",
            encoding="utf-8"
        ) as out:
            out.write(result)
