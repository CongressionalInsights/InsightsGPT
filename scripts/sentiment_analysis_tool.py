# Sentiment Analysis tool for Congress.gov and public uses.

import requests
import matplotlib.pyplot as plt
from textblob import TextBlob


def fetch_bill_details(keyword):
    """Search Congress.gov for bills matching the keyword and fetch their details."""
    # Replace with actual Congress.gov API call
    return {
        "bill_title": "Climate Change Act",
        "sponsor": "Senator Green",
        "cosponsors_count": 15,
        "latest_action": "Referred to the Committee on Environment and Public Works",
    }


def collect_public_sentiment_data(bill_title):
    """Collect public sentiment data for a given bill title."""
    # Replace with real data sources or API integrations
    return [
        "This bill is fantastic!",
        "I have concerns about the budget impacts.",
        "Neutral stance, but progress is good.",
        "This will harm the economy.",
        "Climate action is overdue!",
    ]


def analyze_sentiment(sentiment_data):
    """Analyze sentiment and categorize data."""
    sentiment_result = {"positive": 0, "neutral": 0, "negative": 0}

    for line in sentiment_data:
        analysis = TextBlob(line)
        if analysis.sentiment.polarity > 0:
            sentiment_result["positive"] += 1
        elif analysis.sentiment.polarity == 0:
            sentiment_result["neutral"] += 1
        else:
            sentiment_result["negative"] += 1

    return sentiment_result


def visualize_sentiment(sentiment_result):
    """Visualize sentiment data using a bar chart."""
    categories = sentiment_result.keys()
    values = sentiment_result.values()

    plt.bar(categories, values, color=["green", "blue", "red"])
    plt.title("Sentiment Analysis Results")
    plt.xlabel("Sentiment")
    plt.ylabel("Frequency")
    plt.show()


def main():
    keyword = input("Enter a keyword to search for bills: ")
    bill_details = fetch_bill_details(keyword)
    print(f"Bill Details: {bill_details}")

    sentiment_data = collect_public_sentiment_data(bill_details["bill_title"])
    sentiment_result = analyze_sentiment(sentiment_data)

    print(f"Sentiment Analysis: {sentiment_result}")
    visualize_sentiment(sentiment_result)


if __name__ == "__main__":
    main()
