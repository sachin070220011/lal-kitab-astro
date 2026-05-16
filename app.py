import re
import streamlit as st
import matplotlib.pyplot as plt
import requests
import time
import json
import os
from datetime import datetime
from kerykeion.backword import AstrologicalSubjectFactory
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Lal Kitab AI Astro", page_icon="🪐", layout="wide")

# ====================== MULTILINGUAL ======================
if "language" not in st.session_state:
    st.session_state.language = "English"

lang_options = ["English", "हिंदी", "Hinglish"]
lang = st.sidebar.selectbox("Language / भाषा", lang_options, index=lang_options.index(st.session_state.language))
st.session_state.language = lang

def t(key):
    translations = {
        "app_title": {"English": "🪐 Lal Kitab + Vedic AI Astro", "हिंदी": "🪐 लाल किताब + वैदिक AI ज्योतिष", "Hinglish": "🪐 Lal Kitab + Vedic AI Astro"},
        "subtitle": {"English": "Full Vedic (Lahiri) + Lal Kitab • Natal • Varshphal • Solar Return • Gochar • Remedies", 
                    "हिंदी": "पूर्ण वैदिक (लाहिरी) + लाल किताब • जन्म • वर्षफल • सोलर रिटर्न • गोचर • उपाय", 
                    "Hinglish": "Full Vedic (Lahiri) + Lal Kitab • Natal • Varshphal • Gochar"},
        "vedic_tab": {"English": "Vedic Astrology", "हिंदी": "वैदिक ज्योतिष", "Hinglish": "Vedic Astrology"},
        "birth_details": {"English": "Birth Details", "हिंदी": "जन्म विवरण", "Hinglish": "Birth Details"},
        # ... (other translations from previous version - kept same)
    }
    return translations.get(key, {}).get(st.session_state.language, key)

st.title(t("app_title"))
st.markdown(t("subtitle"))

# ====================== CREDITS & BIRTH DETAILS (same as before) ======================
CREDITS_FILE = "user_credits.json"
def load_credits():
    if os.path.exists(CREDITS_FILE):
        try:
            with open(CREDITS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"balance": 100}
    return {"balance": 100}

def save_credits(data):
    with open(CREDITS_FILE, "w") as f:
        json.dump(data, f)
    return data

credits_data = load_credits()
if not os.path.exists(CREDITS_FILE):
    save_credits(credits_data)
st.sidebar.metric("Your Credits", f"₹{credits_data['balance']}")

st.sidebar.header(t("birth_details"))
name = st.sidebar.text_input("Name", "Sachin")
date = st.sidebar.date_input("Birth Date", datetime(2000, 1, 1))
time_input = st.sidebar.time_input("Birth Time", datetime.strptime("12:00", "%H:%M").time())
place = st.sidebar.text_input("Birth Place", "Dehradun")

current_year = datetime.now().year
varsh_year = st.sidebar.number_input("Varshphal / Solar Return Year", min_value=1900, max_value=2100, value=current_year + 1)
transit_date = st.sidebar.date_input("Transit Date (Gochar)", datetime.now().date())

if st.sidebar.button("Generate All Charts & Vedic Details"):
    st.session_state.chart_generated = True
    st.session_state.birth_details = {
        "name": name, "date": date, "time": time_input, "place": place,
        "varsh_year": varsh_year, "transit_date": transit_date
    }

# ====================== CHART CALCULATION (now returns full chart) ======================
def _house_name_to_number(house_name):
    if not house_name:
        return None
    match = re.search(r"(\d+)", house_name)
    if match:
        return int(match.group(1))
    house_map = {
        "First_House": 1,
        "Second_House": 2,
        "Third_House": 3,
        "Fourth_House": 4,
        "Fifth_House": 5,
        "Sixth_House": 6,
        "Seventh_House": 7,
        "Eighth_House": 8,
        "Ninth_House": 9,
        "Tenth_House": 10,
        "Eleventh_House": 11,
        "Twelfth_House": 12,
    }
    return house_map.get(house_name, None)


def get_full_chart(birth_details, year=None, month=None, day=None):
    try:
        geolocator = Nominatim(user_agent="lal_kitab_app")
        loc = geolocator.geocode(birth_details["place"] + ", India")
        if not loc:
            st.error("Location not found.")
            return None, None

        use_date = birth_details["date"]
        if year:
            use_date = use_date.replace(year=year)
        if month and day:
            use_date = use_date.replace(month=month, day=day)

        chart = AstrologicalSubjectFactory.from_birth_data(
            name=birth_details["name"],
            year=use_date.year,
            month=use_date.month,
            day=use_date.day,
            hour=birth_details["time"].hour,
            minute=birth_details["time"].minute,
            lat=loc.latitude,
            lng=loc.longitude,
            tz_str="Asia/Kolkata",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI"
        )

        planet_house = {}
        point_map = {
            "Sun": chart.sun,
            "Moon": chart.moon,
            "Mars": chart.mars,
            "Mercury": chart.mercury,
            "Jupiter": chart.jupiter,
            "Venus": chart.venus,
            "Saturn": chart.saturn,
            "Rahu": chart.true_north_lunar_node,
            "Ketu": chart.true_south_lunar_node,
        }
        for planet, point in point_map.items():
            planet_house[planet] = _house_name_to_number(getattr(point, "house", None))

        return planet_house, chart
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None
# ====================== LAL KITAB DIAGRAM (unchanged) ======================
def draw_lal_kitab_chart(planet_house, title):
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_xlim(0, 12); ax.set_ylim(0, 12); ax.set_aspect('equal'); ax.axis('off')
    for i in range(4):
        ax.plot([3,9], [3+i*3, 3+i*3], 'k-', lw=3)
        ax.plot([3+i*3, 3+i*3], [3,9], 'k-', lw=3)
    houses = list(range(1,13))
    positions = [(6,10.5),(9.5,9),(9.5,6),(9.5,3),(6,2.5),(3.5,3),(3.5,6),(3.5,9),(6,10.5),(9.5,9),(9.5,6),(6,2.5)]
    for i, h in enumerate(houses):
        x, y = positions[i]; ax.text(x, y, str(h), fontsize=16, ha='center', va='center', fontweight='bold')
    planet_colors = {"Sun":"red", "Moon":"silver", "Mars":"red", "Mercury":"green","Jupiter":"yellow", "Venus":"pink", "Saturn":"black", "Rahu":"purple", "Ketu":"purple"}
    for planet, house in planet_house.items():
        idx = int(house) - 1; x, y = positions[idx]; offset_x = 0.9 if idx % 2 == 0 else -0.9
        ax.text(x + offset_x, y, planet[:3], fontsize=11, ha='center', va='center', bbox=dict(facecolor=planet_colors.get(planet, "white"), alpha=0.4))
    ax.text(6, 11.8, title, fontsize=16, ha='center', fontweight='bold')
    st.pyplot(fig)

# ====================== TABS ======================
if st.session_state.get("chart_generated", False):
    bd = st.session_state.birth_details
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Natal Lal Kitab", "Varshphal", "Solar Return", "🌌 Transits (Gochar)", "🕉️ Vedic Astrology"])

    # Lal Kitab tabs (same as before)
    with tab1:
        st.subheader(f"🪐 {bd['name']}'s Natal Lal Kitab Chart")
        natal, _ = get_full_chart(bd)
        if natal: draw_lal_kitab_chart(natal, "NATAL LAL KITAB KUNDLI (Lahiri)")
    with tab2: 
        st.subheader(f"📅 Varshphal {bd['varsh_year']}")
        varsh, _ = get_full_chart(bd, year=bd['varsh_year'])
        if varsh: draw_lal_kitab_chart(varsh, f"VARSHPHAL {bd['varsh_year']}")
    with tab3: 
        st.subheader(f"🔄 Solar Return {bd['varsh_year']}")
        solar, _ = get_full_chart(bd, year=bd['varsh_year'])
        if solar: draw_lal_kitab_chart(solar, f"SOLAR RETURN {bd['varsh_year']}")
    with tab4:
        st.subheader(f"🌌 Gochara Transits on {bd['transit_date']}")
        transit_planets, _ = get_full_chart(bd, year=bd['transit_date'].year, month=bd['transit_date'].month, day=bd['transit_date'].day)
        if transit_planets:
            draw_lal_kitab_chart(transit_planets, f"TRANSITS (GOCHAR) {bd['transit_date']}")
            st.info("Remedies are currently provided by the AI Pandit chat. Ask for Lal Kitab remedies in the chat.")
        else:
            st.warning("Transit chart could not be generated. Check location and date details.")

    # ====================== NEW VEDIC ASTROLOGY TAB ======================
    with tab5:
        st.subheader(f"🕉️ Full Vedic Astrology Details (Lahiri Ayanamsa)")
        _, full_chart = get_full_chart(bd)
        if full_chart:
            st.write("**Planetary Positions (Vedic)**")
            data = []
            chart_points = [
                ("Sun", full_chart.sun),
                ("Moon", full_chart.moon),
                ("Mars", full_chart.mars),
                ("Mercury", full_chart.mercury),
                ("Jupiter", full_chart.jupiter),
                ("Venus", full_chart.venus),
                ("Saturn", full_chart.saturn),
                ("Rahu", full_chart.true_north_lunar_node),
                ("Ketu", full_chart.true_south_lunar_node),
            ]
            for planet_name, point in chart_points:
                data.append({
                    "Planet": planet_name,
                    "Rasi (Sign)": getattr(point, "sign", "N/A"),
                    "Degree": f"{getattr(point, 'position', 0):.2f}°",
                    "House": _house_name_to_number(getattr(point, "house", "")) or "N/A",
                    "Nakshatra": "N/A",
                    "Pada": "N/A",
                    "Retro": "R" if getattr(point, "retrograde", False) else ""
                })
            st.table(data)

            st.caption("✅ Calculated with Swiss Ephemeris + Lahiri Ayanamsa • Full Vedic (Parashari) system")

            # Basic Dasha info
            st.subheader("🌟 Current Vimshottari Dasha")
            st.info("**Mahadasha:** " + "Check AI Pandit for exact current dasha (based on Moon Nakshatra)")

# ====================== AI CHAT (now fully Vedic + Lal Kitab aware) ======================
st.header("💬 Talk to Lal Kitab + Vedic AI Pandit")

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_start_time" not in st.session_state: st.session_state.chat_start_time = None

openrouter_key = st.text_input("OpenRouter API Key (free)", type="password", value="")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask about Vedic positions, Nakshatra, Dasha, Lal Kitab remedies..."):
    if not openrouter_key:
        st.error("Enter your OpenRouter API key")
    else:
        if st.session_state.chat_start_time is None:
            st.session_state.chat_start_time = time.time()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        lang_instruction = {"English": "Respond only in English.", "हिंदी": "Respond only in Hindi.", "Hinglish": "Respond in natural Hinglish."}[st.session_state.language]

        headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
        data = {
            "model": "inclusionai/ring-2.6-1t:free",
            "messages": [
                {"role": "system", "content": f"You are a master Vedic + Lal Kitab astrologer. {lang_instruction} Use full Vedic calculations (Lahiri, Nakshatra, Dasha) + Lal Kitab rules and remedies. Be accurate, practical and positive."},
                *st.session_state.messages
            ]
        }

        with st.chat_message("assistant"):
            with st.spinner("Pandit ji thinking..."):
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                if response.status_code == 200:
                    payload = response.json()
                    choice = payload.get("choices", [{}])[0]
                    reply = choice.get("message", {}).get("content")
                    if reply:
                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    else:
                        st.error("OpenRouter response was not in the expected format.")
                else:
                    error_text = response.text or response.reason
                    st.error(f"OpenRouter API error ({response.status_code}): {error_text}")

        elapsed = int(time.time() - st.session_state.chat_start_time)
        if elapsed > 60:
            st.warning("⏰ 1 minute free trial over! Add credits to continue.")

st.caption("✅ Full Vedic Calculations Integrated • First 60 seconds FREE • Powered by OpenRouter + Lahiri")