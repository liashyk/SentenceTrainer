from groq import Groq

client = Groq(api_key="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")

print("Доступные вам модели:")
for model in client.models.list().data:
    print(f"- {model.id}")