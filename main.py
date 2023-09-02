import requests
import smtplib


"""Constants--------------------------------------------------------------------------------------------"""


my_gmail = "your email"
gmail_connection = "smtp.gmail.com"
app_password = "your app pass"

symbols_list = [
    {"name": "USDJPY",
     "type": "forex",
     },
    {"name": "EURUSD",
     "type": "forex",
     },
    {"name": "TSLA",
     "type": "stocks",
     },
    {"name": "IBM",
     "type": "stocks",
     }
]


"""Functions--------------------------------------------------------------------------------------------"""


def email_text(change_percent, news_list):
    if change_percent > 0:

        if abs(change_percent) > 0.0099:
            change_percent = round(change_percent, ndigits=2)

        subject = f"{SYMBOL}: 🔺 {change_percent}%"
    elif change_percent < 0:

        if abs(change_percent) > 0.0099:
            change_percent = round(change_percent, ndigits=2)

        subject = f"{SYMBOL}: 🔻 {-change_percent}%"
    else:
        subject = f"{SYMBOL}: Unchanged!"

    message_text = "\n" + subject + "\n\n\n"
    for news in news_list:
        message_text += f"-Headline:\n{news['title']}\n\n-Brief: {news['description']}\n\n\n"

    return f"Subject:{subject}\n\n{message_text}"


"""Main-------------------------------------------------------------------------------------------------"""


for symbol in symbols_list:

    SYMBOL = symbol["name"]
    # either forex or stocks
    SYMBOL_TYPE = symbol["type"]

    ALPHA_URL = "https://www.alphavantage.co/query"
    ALPHA_API_KEY = "55DD7G16XMGWMIV1"
    ALPHA_PARAMETERS = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": SYMBOL,
        "apikey": ALPHA_API_KEY,
    }

    NEWS_URL = "https://newsapi.org/v2/everything"
    NEWS_API_KEY = "d3d508093232483dbfc59b0d8903f682"
    NEWS_PARAMETERS = {
        "qInTitle": f"{SYMBOL} OR {SYMBOL.capitalize()} OR {SYMBOL.lower()} OR {SYMBOL.upper()}",
        "from": "",
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }

    """Getting the responses"""

    # getting symbol data
    alpha_response = requests.get(ALPHA_URL, ALPHA_PARAMETERS)
    alpha_response.raise_for_status()
    print(alpha_response.json())
    alpha_data = alpha_response.json()["Time Series (Daily)"]

    needed_alpha_data = []
    count = 3
    for day in alpha_data:
        if count > 0:
            needed_alpha_data.append({"date": day, "close": alpha_data[day]["4. close"]})
            count -= 1

    # Fixing the difference between forex and stocks
    if SYMBOL_TYPE == "forex":
        needed_alpha_data = needed_alpha_data[1:]
    else:
        needed_alpha_data = needed_alpha_data[:-1]

    change_percentage = round((float(needed_alpha_data[0]["close"]) - float(needed_alpha_data[1]["close"])) / float(needed_alpha_data[1]["close"]) * 100, ndigits=4)
    news_date = needed_alpha_data[0]["date"]

    # update the date
    NEWS_PARAMETERS["from"] = news_date

    # getting news data
    news_response = requests.get(NEWS_URL, NEWS_PARAMETERS)
    news_data = news_response.json()["articles"][:3]
    needed_news_data = [
        {"source": news["source"]["name"],
         "title": news["title"],
         "description": news["description"],
         "content": news["content"].split(sep="[")[0],
         } for news in news_data]

    # getting the message text and fixing the encoding error
    msg = email_text(change_percentage, needed_news_data).encode("utf-8")
    with smtplib.SMTP(gmail_connection) as connection:
        connection.starttls()
        connection.login(user=my_gmail, password=app_password)
        connection.sendmail(from_addr=my_gmail, to_addrs=my_gmail, msg=msg)
