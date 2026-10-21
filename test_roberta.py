from transformers import pipeline

print("Downloading and loading RoBERTa...")
# This will take a moment the first time as it downloads a ~500MB model
analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

print("Testing model...")
result = analyzer("This product is okay, but I honestly expected much better for the price.")

print(f"Result: {result}")