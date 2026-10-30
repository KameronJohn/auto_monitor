import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================

URL = "https://linktr.ee/torontohkyouth"

# Save state file in the same folder as this script
STATE_FILE = Path(__file__).resolve().parent / "volleyball_state.json"

TARGET_PREFIX = "排球 🏐"
TARGET_PREFIX = "GAKI"
TARGET_DAY = "Wed"
TARGET_TIME = "6-8 pm"


import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DISCORD_WEBHOOK_URL_1 = os.getenv("DISCORD_WEBHOOK_URL_1")
DISCORD_WEBHOOK_URL_2 = os.getenv("DISCORD_WEBHOOK_URL_2")


def send_discord_message(channel, message):
    """
    Send a message to Discord using a webhook.

    Args:
        message (str): Message content to send.

    Returns:
        bool: True if successful, False otherwise.
    """

    if not DISCORD_WEBHOOK_URL_1 and not DISCORD_WEBHOOK_URL_2:
        print("Error: Discord webhook URL not configured.")
        return False

    payload = {
        "content": message
    }

    if channel == 1:
        DISCORD_WEBHOOK_URL = DISCORD_WEBHOOK_URL_1
    elif channel == 2:
        DISCORD_WEBHOOK_URL = DISCORD_WEBHOOK_URL_2

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=15
        )

        if response.status_code == 204:
            print("Discord notification sent successfully.")
            return True

        print(
            f"Discord error: {response.status_code} "
            f"- {response.text}"
        )
        return False

    except requests.RequestException as error:
        print(f"Discord connection error: {error}")
        return False

# ==========================================
# FETCH TARGET EVENT
# ==========================================

def fetch_volleyball_event():

    response = requests.get(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            )
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select(
        '[data-testid="NewLinkContainer"] '
        'a[data-testid="LinkClickTriggerLink"]'
    )

    for link in links:

        label = link.select_one('[data-link-label="true"]')

        if label is None:
            continue

        title = label.get_text(" ", strip=True)
        # print("Found event:", repr(title))

        # Normalize spaces and capitalization
        normalized_title = " ".join(title.lower().split())

        # Match Wednesday 6-8 PM only
        if (
            title.startswith(TARGET_PREFIX)
            and TARGET_DAY.lower() in normalized_title
            and TARGET_TIME.lower().replace(" ", "")
                in normalized_title.replace(" ", "")
        ):
            send_discord_message(1, "new event found")
            return {
                "title": title,
                "url": link.get("href", "")
            }
        else:
            send_discord_message(2, "no updates found")

    # Event not found: send Discord notification
    send_discord_message(2,
        "🚨 **VOLLEYBALL EVENT NOT FOUND**\n\n"
        "The Wednesday 6–8 PM volleyball event could not be found.\n\n"
        "Possible reasons:\n"
        "• Event title has changed\n"
        "• Event has been removed\n"
        "• Linktree page structure has changed\n\n"
        "Check the page:\n"
        "https://linktr.ee/torontohkyouth"
    )

    raise RuntimeError(
        "Wednesday 6-8 PM volleyball event not found. "
        "The title may have changed or the event may have been removed."
    )


# ==========================================
# LOAD PREVIOUS STATE
# ==========================================

def load_previous_state():

    if not STATE_FILE.exists():
        return None

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


# ==========================================
# SAVE CURRENT STATE
# ==========================================

def save_state(event):

    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            event,
            file,
            ensure_ascii=False,
            indent=2
        )


# ==========================================
# MAIN MONITORING FUNCTION
# ==========================================

def main():

    current = fetch_volleyball_event()
    previous = load_previous_state()

    print("================================")
    print("VOLLEYBALL EVENT MONITOR")
    print("================================")

    print("Current event:", current["title"])
    print("Registration:", current["url"])

    print("State file:", STATE_FILE)

    # First run: establish baseline
    if previous is None:

        save_state(current)

        print("\nInitial baseline saved.")
        print("Monitoring started.")

        return

    # Check for changes
    if current != previous:

        print("\n🚨 VOLLEYBALL EVENT UPDATED!")

        if current["title"] != previous["title"]:

            print("Previous title:", previous["title"])
            print("Current title: ", current["title"])

        if current["url"] != previous["url"]:

            print("Previous URL:", previous["url"])
            print("Current URL: ", current["url"])

        save_state(current)

    else:

        print("\nNo changes detected.")


# ==========================================
# RUN SCRIPT
# ==========================================

if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print("Monitoring error:", error)
        raise