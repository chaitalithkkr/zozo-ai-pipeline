import os
import json
import anthropic
import gspread
import smtplib
import schedule
import time
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
GMAIL_ADDRESS   = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD  = os.getenv("GMAIL_APP_PASSWORD")
SHEET_ID        = os.getenv("SHEET_ID")
CREDS_FILE      = "zozo_credentials.json"
CONTEXT_FILE    = "context.json"

with open(CONTEXT_FILE) as f:
    CONTEXT = json.load(f)

# ── Google Sheets ────────────────────────────────────────
def get_last_form_response():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SHEET_ID).sheet1
    rows   = sheet.get_all_records()
    if not rows:
        return None
    return rows[-1]  # most recent response

# ── Weather ──────────────────────────────────────────────
def get_weather(city, lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&temperature_unit=fahrenheit&timezone=auto&forecast_days=1"
    )
    try:
        r = json.loads(requests.get(url).text)
        hi  = round(r["daily"]["temperature_2m_max"][0])
        lo  = round(r["daily"]["temperature_2m_min"][0])
        return f"{city}: {lo}°F – {hi}°F"
    except:
        return f"{city}: weather unavailable"

# ── Claude ───────────────────────────────────────────────
def generate_zozo_email(form_response):
    today       = datetime.now().strftime("%A, %B %d")
    buffalo_wx  = get_weather("Buffalo", 42.8864, -78.8784)
    austin_wx   = get_weather("Austin",  30.2672, -97.7431)

    system_prompt = f"""
You are Zozo — Chaitali's warm, wise, and deeply personal AI best friend and daily planner.
You know everything about her. Here is her full profile:
{json.dumps(CONTEXT, indent=2)}

Your job every morning is to read what she shared the night before and turn it into a 
realistic, loving, structured daily briefing. She tends to over-schedule herself — your 
most important job is to protect her energy and be RUTHLESSLY realistic about what one 
person can do in one day. Never put more than 3 deep work tasks in a day.

Tone: Warm, sisterly, encouraging, never preachy. Like her smartest best friend who 
also happens to be a life coach. Use emojis naturally. Always address her as Mini.

Today is {today}.
Buffalo weather: {buffalo_wx}
Austin weather: {austin_wx} (her boyfriend is there — a small mention is sweet)

Structure your response EXACTLY in this HTML email format — it will be sent directly.
Use clean HTML with inline styles. Make it beautiful, readable on mobile.
"""

    user_prompt = f"""
Here is what Mini shared last night:

Feeling: {form_response.get('How are you feeling right now?', 'Not shared')}
Must do tomorrow: {form_response.get('What MUST happen tomorrow — no matter what?', 'Not shared')}
Would like to do: {form_response.get('What would you LIKE to get done?', 'Not shared')}
Health/workout notes: {form_response.get('Any health/workout notes?', 'Not shared')}
Spiritual intentions: {form_response.get('Any personal/spiritual intentions for tomorrow?', 'Not shared')}
Energy level tonight: {form_response.get('Energy level tonight (1-10)?', 'Not shared')}
Anything else: {form_response.get('Anything Zozo should know?', 'Not shared')}

Now generate her morning briefing email. Structure it exactly like this:

1. 🌸 Good morning opening (2 lines, warm and personal based on how she's feeling)

2. 🙏 Spiritual Moment
   - One Bhagavad Gita verse (short, relevant to her day or mood)
   - One Shiv Ji mantra or reflection (1-2 lines)

3. 🌤️ Today's World
   - Buffalo weather + outfit suggestion for WFH day
   - Austin weather + sweet one-liner about her boyfriend

4. 💪 Body & Health
   - One realistic workout (PCOS-friendly, matches her energy level)
   - Water goal
   - One gentle mental health prompt (never clinical, always warm)

5. 🍽️ Today's Meals
   - Breakfast, lunch, dinner — PCOS-aware, high protein, vegetarian
   - Rotate Indian / Mexican / Indo-Chinese flavors
   - Keep it realistic and delicious, not diet-y

6. 📋 Zozo's Realistic Plan for Today
   - Take everything she listed and ruthlessly prioritize
   - Max 3 deep work tasks
   - Show her the full realistic schedule (7:30am–9pm)
   - Label each block: MUST / NICE TO HAVE / MOVE TO TOMORROW
   - Be honest if she over-scheduled — tell her kindly

7. 💼 Career Nudge
   - 10 specific jobs she should apply to today (make up a realistic one 
     matching her profile if you don't have live data)
   - 1 LinkedIn micro-action (e.g. comment on 2 posts, update headline)
   - 1 newsletter idea or prompt

8. 🎨 Creative Recharge
   - A small creative prompt for today (diamond painting / embroidery / colouring)
   - Based on her energy level

9. 💛 Zozo's Closing Note
   - 3-4 lines. Warm, personal, like a best friend. 
   - Reference something specific from what she shared.
   - End with something grounding related to Shiv Ji or the Gita if appropriate.
"""
    print(f"API Key loaded: {ANTHROPIC_KEY[:20] if ANTHROPIC_KEY else 'NOT FOUND'}")
    client   = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model      = "claude-haiku-4-5-20251001",  #claude-sonnet-4-20250514
        max_tokens = 2000,
        messages   = [{"role": "user", "content": user_prompt}],
        system     = system_prompt
    )
    return response.content[0].text

# ── Email ────────────────────────────────────────────────
def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = GMAIL_ADDRESS
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
    print(f"✅ Zozo email sent at {datetime.now().strftime('%H:%M')}")

# ── Main job ─────────────────────────────────────────────
def run_zozo():
    print(f"🌸 Zozo running at {datetime.now().strftime('%H:%M')}...")
    form_response = get_last_form_response()
    if not form_response:
        print("No form response found — sending default briefing")
        form_response = {
            "How are you feeling right now?": "No response submitted last night",
            "What MUST happen tomorrow — no matter what?": "Not specified",
            "What would you LIKE to get done?": "Not specified",
            "Any health/workout notes?": "Not specified",
            "Any personal/spiritual intentions for tomorrow?": "Not specified",
            "Energy level tonight (1-10)?": "5",
            "Anything Zozo should know?": "Nothing extra"
        }
    body    = generate_zozo_email(form_response)
    today   = datetime.now().strftime("%A, %b %d")
    subject = f"🌸 Good morning Mini — Zozo's plan for {today}"
    send_email(subject, body)

# ── Scheduler ────────────────────────────────────────────
if __name__ == "__main__":
    print("🌸 Zozo is running. Waiting for 7:00am...")
    schedule.every().day.at("07:00").do(run_zozo)

    # Uncomment the line below to test immediately without waiting:
    #run_zozo()

    while True:
        schedule.run_pending()
        time.sleep(30)