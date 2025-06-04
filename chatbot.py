import streamlit as st
from openrouter_api import call_openrouter_chat, SYSTEM_PROMPT
from langdetect import detect
import requests
import datetime
lang_map = {
    "ab": "Abkhazian", "aa": "Afar", "af": "Afrikaans", "ak": "Akan", "sq": "Albanian",
    "am": "Amharic", "ar": "Arabic", "an": "Aragonese", "hy": "Armenian", "as": "Assamese",
    "av": "Avaric", "ae": "Avestan", "ay": "Aymara", "az": "Azerbaijani", "bm": "Bambara",
    "ba": "Bashkir", "eu": "Basque", "be": "Belarusian", "bn": "Bengali", "bh": "Bihari",
    "bi": "Bislama", "bs": "Bosnian", "br": "Breton", "bg": "Bulgarian", "my": "Burmese",
    "ca": "Catalan", "ch": "Chamorro", "ce": "Chechen", "ny": "Chichewa", "zh": "Chinese",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)", "cv": "Chuvash",
    "kw": "Cornish", "co": "Corsican", "cr": "Cree", "hr": "Croatian", "cs": "Czech",
    "da": "Danish", "dv": "Divehi", "nl": "Dutch", "dz": "Dzongkha", "en": "English",
    "eo": "Esperanto", "et": "Estonian", "ee": "Ewe", "fo": "Faroese", "fj": "Fijian",
    "fi": "Finnish", "fr": "French", "ff": "Fulah", "gl": "Galician", "ka": "Georgian",
    "de": "German", "el": "Greek", "gn": "Guarani", "gu": "Gujarati", "ht": "Haitian",
    "ha": "Hausa", "he": "Hebrew", "hz": "Herero", "hi": "Hindi", "ho": "Hiri Motu",
    "hu": "Hungarian", "ia": "Interlingua", "id": "Indonesian", "ie": "Interlingue",
    "ga": "Irish", "ig": "Igbo", "ik": "Inupiaq", "io": "Ido", "is": "Icelandic",
    "it": "Italian", "iu": "Inuktitut", "ja": "Japanese", "jv": "Javanese", "kl": "Kalaallisut",
    "kn": "Kannada", "kr": "Kanuri", "ks": "Kashmiri", "kk": "Kazakh", "km": "Central Khmer",
    "ki": "Kikuyu", "rw": "Kinyarwanda", "ky": "Kirghiz", "kv": "Komi", "kg": "Kongo",
    "ko": "Korean", "ku": "Kurdish", "kj": "Kuanyama", "la": "Latin", "lb": "Luxembourgish",
    "lg": "Ganda", "li": "Limburgan", "ln": "Lingala", "lo": "Lao", "lt": "Lithuanian",
    "lu": "Luba-Katanga", "lv": "Latvian", "gv": "Manx", "mk": "Macedonian", "mg": "Malagasy",
    "ms": "Malay", "ml": "Malayalam", "mt": "Maltese", "mi": "Maori", "mr": "Marathi",
    "mh": "Marshallese", "mn": "Mongolian", "na": "Nauru", "nv": "Navajo", "nd": "North Ndebele",
    "ne": "Nepali", "ng": "Ndonga", "nb": "Norwegian Bokmål", "nn": "Norwegian Nynorsk",
    "no": "Norwegian", "ii": "Sichuan Yi", "nr": "South Ndebele", "oc": "Occitan",
    "oj": "Ojibwa", "cu": "Church Slavic", "om": "Oromo", "or": "Odia", "os": "Ossetian",
    "pa": "Punjabi", "pi": "Pali", "fa": "Persian", "pl": "Polish", "ps": "Pashto",
    "pt": "Portuguese", "qu": "Quechua", "rm": "Romansh", "rn": "Rundi", "ro": "Romanian",
    "ru": "Russian", "sa": "Sanskrit", "sc": "Sardinian", "sd": "Sindhi", "se": "Northern Sami",
    "sm": "Samoan", "sg": "Sango", "sr": "Serbian", "gd": "Scottish Gaelic", "sn": "Shona",
    "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian", "so": "Somali", "st": "Southern Sotho",
    "es": "Spanish", "su": "Sundanese", "sw": "Swahili", "ss": "Swati", "sv": "Swedish",
    "ta": "Tamil", "te": "Telugu", "tg": "Tajik", "th": "Thai", "ti": "Tigrinya",
    "bo": "Tibetan", "tk": "Turkmen", "tl": "Tagalog", "tn": "Tswana", "to": "Tonga (Tonga Islands)",
    "tr": "Turkish", "ts": "Tsonga", "tt": "Tatar", "tw": "Twi", "ty": "Tahitian",
    "ug": "Uighur", "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek", "ve": "Venda",
    "vi": "Vietnamese", "vo": "Volapük", "wa": "Walloon", "cy": "Welsh", "wo": "Wolof",
    "fy": "Western Frisian", "xh": "Xhosa", "yi": "Yiddish", "yo": "Yoruba",
    "za": "Zhuang", "zu": "Zulu"
}
BASE_URL = "http://localhost:8000"
#Chat Interface
st.set_page_config(page_title="Healthcare Chatbot", layout="wide")
st.markdown(
    "<h1 style='display: inline; font-size: 3em;'>Sanobot</h1>"
    "<span style='font-size: 1.5em; font-weight: normal;'>Your AI-powered medical assistant</span>",
    unsafe_allow_html=True
)

# Session setup
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.email = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [SYSTEM_PROMPT]

# Sidebar authentication
st.sidebar.title("Authentication")
auth_mode = st.sidebar.selectbox("Choose", ["Login", "Signup"])

with st.sidebar.form("auth_form"):
    email = st.text_input("Email", key="email_input")
    password = st.text_input("Password", type="password", key="password_input")
    submitted = st.form_submit_button(auth_mode)

    if submitted:
        endpoint = "/login" if auth_mode == "Login" else "/signup"
        res = requests.post(f"{BASE_URL}{endpoint}", json={"email": email, "password": password})

        if res.status_code == 200:
            if auth_mode == "Login":
                token = res.json()["access_token"]
                st.session_state.token = token
                st.session_state.email = email
                st.success("✅ Logged in!")

            else:
                st.success("✅ Signup successful! Please log in.")
        else:
            st.error(f"❌ {res.json().get('detail', 'Authentication failed')}")

# Chat History Viewer (Always visible with fallback after login)
# Fetch and display full chat history after login
if st.session_state.token:
    st.sidebar.markdown("### 📜 Chat History")

    history_res = requests.get(
        f"{BASE_URL}/chat",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )

    if history_res.status_code == 200:
        data = history_res.json()
        messages = data.get("messages", [])
        if messages:
            for msg in messages[::-1]:  # Show most recent at top
                speaker = "🧑‍⚕️ Assistant" if msg["role"] == "assistant" else "🙋 You"
                st.sidebar.markdown(f"`{speaker}`: {msg['message']}")
        else:
            st.sidebar.info("ℹ️ No previous chats found.")
    else:
        st.sidebar.error("❌ Failed to retrieve chat history.")



if not st.session_state.token:
    st.stop()


# Load today's chat history
today = datetime.date.today().isoformat()
chat_res = requests.get(f"{BASE_URL}/chat", params={"user_email": st.session_state.email, "date": today})
chat_history = chat_res.json() if chat_res.status_code == 200 else []

# Chat input (only one unique key)
user_input = st.text_input("🩺 Describe your symptoms or ask a health question:", key="chat_input_main")

# Handle user message
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner(" Thinking..."):
        reply = call_openrouter_chat(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # Detect language
    try:
        detected_lang = detect(user_input)
        lang_name = lang_map.get(detected_lang, detected_lang.title())
        st.info(f"The Language you are Texting is {lang_name}")
    except Exception as e:
        st.error(f"⚠️ Error detecting language: {str(e)}")

    # Save chat
    for msg in [
        {"role": "user", "message": user_input, "date": today},
        {"role": "assistant", "message": reply, "date": today}
    ]:
        requests.post(
            f"{BASE_URL}/chat",
            params={"user_email": st.session_state.email},
            json=msg,
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )

# Display conversation history
for msg in st.session_state.chat_history[1:]:  # Skip system prompt
    speaker = "Assistant" if msg["role"] == "assistant" else "You"
    st.markdown(f"**{speaker}:** {msg['content']}")