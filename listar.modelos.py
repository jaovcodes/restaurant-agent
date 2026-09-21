import os
import time
from dotenv import load_dotenv

try:
    from mistralai.client import Mistral
except ImportError:
    from mistralai import Mistral

load_dotenv()
client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

modelos = [
    "mistral-small-latest",
    "ministral-8b-2512",
    "ministral-3b-2512",
    "mistral-large-2512",
]

for modelo in modelos:
    try:
        r = client.chat.complete(
            model=modelo,
            messages=[{"role": "user", "content": "Diga olá"}],
            max_tokens=20,
        )
        print(modelo, "-> OK:", r.choices[0].message.content)
    except Exception as e:
        print(modelo, "-> ERRO:", str(e)[:150])
    time.sleep(3)