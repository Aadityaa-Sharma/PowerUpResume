import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

credential = AzureKeyCredential(os.getenv("AZURE_LANGUAGE_KEY"))
client = TextAnalyticsClient(
    endpoint=os.getenv("AZURE_LANGUAGE_ENDPOINT"),
    credential=credential
)

documents = ["I love this resume analyzer!"]
response = client.analyze_sentiment(documents)
print(f"Test Result: {response[0].sentiment} (Confidence: {response[0].confidence_scores.positive})")