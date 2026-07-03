from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import g4f
import json
import os
import re
import time
from datetime import datetime, timedelta
import logging
import copy
import asyncio
import psutil
import platform
import threading
import atexit
import sys

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not os.path.exists("token.json"):
    print("token.json not found. Please create token.json, set your token inside, and try again.")
    input("Press Enter to exit...")
    sys.exit(1)

with open("token.json", "r") as f:
    try:
        TELEGRAM_TOKEN = json.load(f).get("token", "").strip()
    except:
        TELEGRAM_TOKEN = ""

if not TELEGRAM_TOKEN:
    print("No token found in token.json. Please set your token and try again.")
    input("Press Enter to exit...")
    sys.exit(1)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "sp": "Español",
    "fr": "Français",
    "ru": "Русский",
    "ar": "العربية",
    "bn": "বাংলা",
    "hi": "हिन्दी"
}
DEFAULT_LANGUAGE = "en"

def get_default_persona(language):
    personas = {
        "en": "You are a helpful assistant who speaks English. Be friendly and helpful in your responses.",
        "sp": "Eres un asistente útil que habla español. Sé amable y servicial en tus respuestas.",
        "fr": "Vous êtes un assistant utile qui parle français. Soyez amical et serviable dans vos réponses.",
        "ru": "Вы полезный помощник, который говорит на русском языке. Будьте дружелюбны и полезны в своих ответах.",
        "ar": "أنت مساعد مفيد يتحدث اللغة العربية. كن لطيفًا ومفيدًا في ردودك.",
        "bn": "আপনি একজন সহায়ক সহকারী যিনি বাংলায় কথা বলেন। আপনার উত্তরে বন্ধুত্বপূর্ণ এবং সহায়ক হন।",
        "hi": "आप एक सहायक सहायक हैं जो हिंदी बोलते हैं। अपने उत्तरों में मित्रवत और सहायक रहें।"
    }
    return personas.get(language, personas["en"])

LANGUAGE_STRINGS = {
    "start_message": {
        "en": """🎯 **Available Bot Commands:**
/start - Start conversation
/help - Show all commands
/clear - Clear conversation memory
/think - Deep thinking on specific text
/think_full - Analyze last 10 messages
/customize - Customize bot personality
/mystats - Show your statistics
/web - Internet search
/users_info - User statistics
/feedback - Send your opinion about the bot
/credits - Developer information
/server_info - Server information
🌐 **Language Settings:**
/en - Set language to English
/sp - Set language to Spanish
/fr - Set language to French
/ru - Set language to Russian
/ar - Set language to Arabic
/bn - Set language to Bengali
/hi - Set language to Hindi
💡 **Bot Features:**
- Remembers your previous conversation (for 2 days)
- Saves up to 100 messages in conversation
- Excellent language support
- Deep thinking mode for accurate responses
- Customize bot personality as you wish
- Advanced processing system (10 analysis stages)
- Preset system for saving custom personalities
- Advanced internet search
- Permanent data storage system
- Rating and feedback system
- Server monitoring and automatic downtime detection""",
        "bn": """🎯 **উপলব্ধ বট কমান্ডসমূহ:**
/start - কথোপকথন শুরু করুন
/help - সব কমান্ড দেখুন
/clear - কথোপকথনের মেমোরি মুছুন
/think - নির্দিষ্ট টেক্সটে গভীর চিন্তা করুন
/think_full - শেষ ১০টি মেসেজ বিশ্লেষণ করুন
/customize - বটের ব্যক্তিত্ব কাস্টমাইজ করুন
/mystats - আপনার পরিসংখ্যান দেখুন
/web - ইন্টারনেট অনুসন্ধান
/users_info - ব্যবহারকারীদের পরিসংখ্যান
/feedback - বট সম্পর্কে আপনার মতামত দিন
/credits - ডেভেলপারের তথ্য
/server_info - সার্ভারের তথ্য
🌐 **ভাষা সেটিংস:**
/en - ইংরেজিতে সেট করুন
/sp - স্প্যানিশে সেট করুন
/fr - ফ্রেঞ্চে সেট করুন
/ru - রুশ ভাষায় সেট করুন
/ar - আরবিতে সেট করুন
/bn - বাংলায় সেট করুন
/hi - হিন্দিতে সেট করুন
💡 **বটের বৈশিষ্ট্য:**
- আপনার আগের কথোপকথন মনে রাখে (২ দিন পর্যন্ত)
- ১০০টি মেসেজ পর্যন্ত সংরক্ষণ করে
- চমৎকার ভাষা সমর্থন
- নির্ভুল উত্তরের জন্য গভীর চিন্তা মোড
- ইচ্ছেমতো বটের ব্যক্তিত্ব কাস্টমাইজ করুন
- অ্যাডভান্সড প্রসেসিং সিস্টেম (১০টি বিশ্লেষণ স্তর)
- কাস্টম পার্সোনালিটি সংরক্ষণের প্রিসেট সিস্টেম
- অ্যাডভান্সড ইন্টারনেট সার্চ
- স্থায়ী ডেটা সংরক্ষণ ব্যবস্থা
- রেটিং ও ফিডব্যাক সিস্টেম
- সার্ভার মনিটরিং ও স্বয়ংক্রিয় ডাউনটাইম সনাক্তকরণ""",
        "hi": """🎯 **उपलब्ध बॉट कमांड्स:**
/start - बातचीत शुरू करें
/help - सभी कमांड देखें
/clear - बातचीत मेमोरी साफ़ करें
/think - विशिष्ट टेक्स्ट पर गहन विचार करें
/think_full - अंतिम 10 संदेशों का विश्लेषण करें
/customize - बॉट की व्यक्तित्व कस्टमाइज़ करें
/mystats - अपने आंकड़े देखें
/web - इंटरनेट खोज
/users_info - उपयोगकर्ता आंकड़े
/feedback - बॉट के बारे में अपनी राय दें
/credits - डेवलपर जानकारी
/server_info - सर्वर जानकारी
🌐 **भाषा सेटिंग्स:**
/en - अंग्रेज़ी में सेट करें
/sp - स्पेनिश में सेट करें
/fr - फ्रेंच में सेट करें
/ru - रूसी में सेट करें
/ar - अरबी में सेट करें
/bn - बांग्ला में सेट करें
/hi - हिंदी में सेट करें
💡 **बॉट की विशेषताएं:**
- आपकी पिछली बातचीत याद रखता है (2 दिन तक)
- 100 संदेशों तक सहेजता है
- उत्कृष्ट भाषा समर्थन
- सटीक उत्तर के लिए गहन चिंतन मोड
- अपनी इच्छानुसार बॉट व्यक्तित्व कस्टमाइज़ करें
- उन्नत प्रोसेसिंग सिस्टम (10 विश्लेषण चरण)
- कस्टम व्यक्तित्व सहेजने के लिए प्रीसैट सिस्टम
- उन्नत इंटरनेट खोज
- स्थायी डेटा भंडारण प्रणाली
- रेटिंग और फीडबैक सिस्टम
- सर्वर निगरानी और स्वचालित डाउनटाइम पहचान"""
    },
    "help_message": {
        "en": """🎯 **Available Bot Commands:**
/start - Start conversation
/help - Show all commands
/clear - Clear conversation memory
🤔 **Advanced Thinking Features:**
/think [text] - Deep thinking on specific text (generates 10 responses and merges them)
/think_full - Analyze last 10 messages and respond point by point
🎭 **Personality Customization:**
/customize - Customize bot personality and save as preset
/customize /s - Save current customization as preset
/customize /t [title] - Add title to preset
/customize /list - Show all saved presets
🔍 **Internet Search:**
/web [query] - Search in more than 20 reliable sources
🌐 **Language Settings:**
/en - Set language to English
/sp - Set language to Spanish
/fr - Set language to French
/ru - Set language to Russian
/ar - Set language to Arabic
/bn - Set language to Bengali
/hi - Set language to Hindi
📊 **Statistics:**
/mystats - Show your statistics
/users_info - General user statistics
/server_info - Server and performance information
⭐ **Rating and Feedback:**
/feedback [your opinion] - Send your opinion about the bot (once every 5 days)
/credits - Developer information
💾 **Memory Features:**
- Remembers 100 complete messages
- Saves conversation for 2 days
- Learns from your preferences
- Saves up to 10 custom personalities
- Permanent data storage system""",
        "bn": """🎯 **উপলব্ধ বট কমান্ডসমূহ:**
/start - কথোপকথন শুরু করুন
/help - সব কমান্ড দেখুন
/clear - কথোপকথনের মেমোরি মুছুন
🤔 **উন্নত চিন্তা বৈশিষ্ট্য:**
/think [টেক্সট] - নির্দিষ্ট টেক্সটে গভীর চিন্তা (১০টি উত্তর তৈরি ও মার্জ করে)
/think_full - শেষ ১০টি মেসেজ বিশ্লেষণ ও পয়েন্ট বাই পয়েন্ট উত্তর
🎭 **ব্যক্তিত্ব কাস্টমাইজেশন:**
/customize - বটের ব্যক্তিত্ব কাস্টমাইজ ও প্রিসেট হিসেবে সেভ
/customize /s - বর্তমান কাস্টমাইজেশন প্রিসেট হিসেবে সেভ
/customize /t [শিরোনাম] - প্রিসেটে শিরোনাম যোগ
/customize /list - সব সংরক্ষিত প্রিসেট দেখান
🔍 **ইন্টারনেট অনুসন্ধান:**
/web [কুয়েরি] - ২০+টি নির্ভরযোগ্য সোর্সে অনুসন্ধান
🌐 **ভাষা সেটিংস:**
/en - ইংরেজিতে সেট করুন
/sp - স্প্যানিশে সেট করুন
/fr - ফ্রেঞ্চে সেট করুন
/ru - রুশ ভাষায় সেট করুন
/ar - আরবিতে সেট করুন
/bn - বাংলায় সেট করুন
/hi - হিন্দিতে সেট করুন
📊 **পরিসংখ্যান:**
/mystats - আপনার পরিসংখ্যান দেখুন
/users_info - সাধারণ ব্যবহারকারী পরিসংখ্যান
/server_info - সার্ভার ও পারফরম্যান্স তথ্য
⭐ **রেটিং ও ফিডব্যাক:**
/feedback [আপনার মতামত] - বট সম্পর্কে আপনার মতামত দিন (প্রতি ৫ দিনে একবার)
/credits - ডেভেলপারের তথ্য
💾 **মেমোরি বৈশিষ্ট্য:**
- ১০০টি সম্পূর্ণ মেসেজ মনে রাখে
- ২ দিন পর্যন্ত কথোপকথন সংরক্ষণ করে
- আপনার পছন্দ থেকে শেখে
- ১০টি কাস্টম ব্যক্তিত্ব সংরক্ষণ করে
- স্থায়ী ডেটা সংরক্ষণ ব্যবস্থা""",
        "hi": """🎯 **उपलब्ध बॉट कमांड्स:**
/start - बातचीत शुरू करें
/help - सभी कमांड देखें
/clear - बातचीत मेमोरी साफ़ करें
🤔 **उन्नत विचार सुविधाएँ:**
/think [टेक्स्ट] - विशिष्ट टेक्स्ट पर गहन विचार (10 उत्तर उत्पन्न करता है और उन्हें मर्ज करता है)
/think_full - अंतिम 10 संदेशों का विश्लेषण करें और बिंदुवार उत्तर दें
🎭 **व्यक्तित्व कस्टमाइज़ेशन:**
/customize - बॉट व्यक्तित्व कस्टमाइज़ करें और प्रीसैट के रूप में सहेजें
/customize /s - वर्तमान कस्टमाइज़ेशन को प्रीसैट के रूप में सहेजें
/customize /t [शीर्षक] - प्रीसैट में शीर्षक जोड़ें
/customize /list - सभी सहेजे गए प्रीसैट दिखाएं
🔍 **इंटरनेट खोज:**
/web [क्वेरी] - 20 से अधिक विश्वसनीय स्रोतों में खोजें
🌐 **भाषा सेटिंग्स:**
/en - अंग्रेज़ी में सेट करें
/sp - स्पेनिश में सेट करें
/fr - फ्रेंच में सेट करें
/ru - रूसी में सेट करें
/ar - अरबी में सेट करें
/bn - बांग्ला में सेट करें
/hi - हिंदी में सेट करें
📊 **आंकड़े:**
/mystats - अपने आंकड़े देखें
/users_info - सामान्य उपयोगकर्ता आंकड़े
/server_info - सर्वर और प्रदर्शन जानकारी
⭐ **रेटिंग और फीडबैक:**
/feedback [आपकी राय] - बॉट के बारे में अपनी राय दें (हर 5 दिन में एक बार)
/credits - डेवलपर जानकारी
💾 **मेमोरी सुविधाएँ:**
- 100 पूर्ण संदेश याद रखता है
- 2 दिनों तक बातचीत सहेजता है
- आपकी प्राथमिकताओं से सीखता है
- 10 कस्टम व्यक्तित्व सहेजता है
- स्थायी डेटा भंडारण प्रणाली"""
    },
    "clear_message": {
        "en": "✅ **Conversation memory cleared!** We started a new conversation.",
        "bn": "✅ **কথোপকথনের মেমোরি মুছে ফেলা হয়েছে!** আমরা নতুন কথোপকথন শুরু করলাম।",
        "hi": "✅ **बातचीत मेमोरी साफ़ हो गई!** हमने नई बातचीत शुरू की।"
    },
    "cleanup_message": {
        "en": "🧹 **Conversation cleaned**\n🗑️ Deleted {count} old messages\n💾 Your settings and presets were preserved",
        "bn": "🧹 **কথোপকথন পরিষ্কার করা হয়েছে**\n🗑️ {count}টি পুরোনো মেসেজ মুছে ফেলা হয়েছে\n💾 আপনার সেটিংস ও প্রিসেট সংরক্ষণ করা হয়েছে",
        "hi": "🧹 **बातचीत साफ़ की गई**\n🗑️ {count} पुराने संदेश हटाए गए\n💾 आपकी सेटिंग्स और प्रीसैट सहेजे गए"
    },
    "downtime_message": {
        "en": "🤖 **Bot is currently offline**\n⏰ **Downtime:** {duration}\n📨 All your messages will be answered when the bot returns\n🔔 You will be notified when the bot is back online",
        "bn": "🤖 **বট বর্তমানে অফলাইন**\n⏰ **ডাউনটাইম:** {duration}\n📨 বট ফিরে এলে আপনার সব মেসেজের উত্তর দেওয়া হবে\n🔔 বট অনলাইনে ফিরলে আপনাকে জানানো হবে",
        "hi": "🤖 **बॉट वर्तमान में ऑफलाइन है**\n⏰ **डाउनटाइम:** {duration}\n📨 बॉट वापस आने पर आपके सभी संदेशों का उत्तर दिया जाएगा\n🔔 बॉट वापस ऑनलाइन आने पर आपको सूचित किया जाएगा"
    },
    "back_online_message": {
        "en": "🤖 Bot is back online!\n⏰ Downtime: {duration}\n📨 All your messages will be processed now",
        "bn": "🤖 বট আবার অনলাইনে ফিরেছে!\n⏰ ডাউনটাইম: {duration}\n📨 আপনার সব মেসেজ এখন প্রসেস করা হবে",
        "hi": "🤖 बॉट वापस ऑनलाइन है!\n⏰ डाउनटाइम: {duration}\n📨 आपके सभी संदेश अब प्रोसेस किए जाएंगे"
    },
    "think_full_analysis": {
        "en": "📊 **Deep analysis of last {count} messages:**\n{response}",
        "bn": "📊 **শেষ {count}টি মেসেজের গভীর বিশ্লেষণ:**\n{response}",
        "hi": "📊 **अंतिम {count} संदेशों का गहन विश्लेषण:**\n{response}"
    },
    "no_messages_to_analyze": {
        "en": "❌ No recent messages to analyze.",
        "bn": "❌ বিশ্লেষণ করার মতো কোনো সাম্প্রতিক মেসেজ নেই।",
        "hi": "❌ विश्लेषण करने के लिए कोई हालिया संदेश नहीं।"
    },
    "deep_thinking": {
        "en": "🤔 **Deep thinking... {progress}%** (This may take up to 2 minutes)",
        "bn": "🤔 **গভীর চিন্তা করছি... {progress}%** (এতে ২ মিনিট পর্যন্ত সময় লাগতে পারে)",
        "hi": "🤔 **गहन विचार कर रहा हूँ... {progress}%** (इसमें 2 मिनट तक लग सकते हैं)"
    },
    "deep_thinking_result": {
        "en": "💭 **Deep thinking result (10 perspectives):**\n{response}",
        "bn": "💭 **গভীর চিন্তার ফলাফল (১০টি দৃষ্টিকোণ থেকে):**\n{response}",
        "hi": "💭 **गहन विचार का परिणाम (10 परिप्रेक्ष्य):**\n{response}"
    },
    "web_searching": {
        "en": "🔍 **Searching the internet...**",
        "bn": "🔍 **ইন্টারনেটে অনুসন্ধান করছি...**",
        "hi": "🔍 **इंटरनेट पर खोज रहा हूँ...**"
    },
    "web_results": {
        "en": "🌐 **Search results for: '{query}'**\n{response}",
        "bn": "🌐 **'{query}' এর জন্য অনুসন্ধান ফলাফল:**\n{response}",
        "hi": "🌐 **'{query}' के लिए खोज परिणाम:**\n{response}"
    },
    "customization_start": {
        "en": "🎭 **Bot Personality Customization**\nSend /customize followed by the new personality description.\nExample: /customize You are a chemistry doctor specialized in medical analysis\nOr choose from the options below:",
        "bn": "🎭 **বটের ব্যক্তিত্ব কাস্টমাইজেশন**\n/customize এর পরে নতুন ব্যক্তিত্বের বিবরণ পাঠান।\nউদাহরণ: /customize আপনি একজন রসায়ন ডাক্তার যিনি চিকিৎসা বিশ্লেষণে বিশেষজ্ঞ\nঅথবা নিচের অপশন থেকে বেছে নিন:",
        "hi": "🎭 **बॉट व्यक्तित्व कस्टमाइज़ेशन**\n/customize के बाद नया व्यक्तित्व विवरण भेजें।\nउदाहरण: /customize आप एक रसायन विज्ञान डॉक्टर हैं जो चिकित्सा विश्लेषण में विशेषज्ञ हैं\nया नीचे दिए गए विकल्पों में से चुनें:"
    },
    "customization_saved": {
        "en": "✅ **Current customization saved as new preset!**\n**Title:** {title}\nYou can change the title using /customize /t [new title]",
        "bn": "✅ **বর্তমান কাস্টমাইজেশন নতুন প্রিসেট হিসেবে সংরক্ষণ করা হয়েছে!**\n**শিরোনাম:** {title}\nআপনি /customize /t [নতুন শিরোনাম] ব্যবহার করে শিরোনাম পরিবর্তন করতে পারেন",
        "hi": "✅ **वर्तमान कस्टमाइज़ेशन नए प्रीसैट के रूप में सहेजा गया!**\n**शीर्षक:** {title}\nआप /customize /t [नया शीर्षक] का उपयोग करके शीर्षक बदल सकते हैं"
    },
    "no_customization_to_save": {
        "en": "❌ No current customization to save.",
        "bn": "❌ সংরক্ষণ করার মতো কোনো বর্তমান কাস্টমাইজেশন নেই।",
        "hi": "❌ सहेजने के लिए कोई वर्तमान कस्टमाइज़ेशन नहीं।"
    },
    "max_presets_reached": {
        "en": "❌ Maximum presets reached (10). Please delete one first.",
        "bn": "❌ সর্বোচ্চ প্রিসেট পৌঁছেছে (১০টি)। প্রথমে একটি মুছুন।",
        "hi": "❌ अधिकतम प्रीसैट पहुँच गया (10)। कृपया पहले एक हटाएँ।"
    },
    "preset_title_updated": {
        "en": "✅ **Preset title updated to:** {title}",
        "bn": "✅ **প্রিসেটের শিরোনাম আপডেট করা হয়েছে:** {title}",
        "hi": "✅ **प्रीसैट शीर्षक अपडेट किया गया:** {title}"
    },
    "no_presets": {
        "en": "❌ No saved presets.",
        "bn": "❌ কোনো সংরক্ষিত প্রিসেট নেই।",
        "hi": "❌ कोई सहेजा गया प्रीसैट नहीं।"
    },
    "saved_presets": {
        "en": "📋 **Saved presets:**\n{list}\n\n💡 Use /customize /use [number] to activate a specific preset.",
        "bn": "📋 **সংরক্ষিত প্রিসেট:**\n{list}\n\n💡 একটি নির্দিষ্ট প্রিসেট সক্রিয় করতে /customize /use [নম্বর] ব্যবহার করুন।",
        "hi": "📋 **सहेजे गए प्रीसैट:**\n{list}\n\n💡 किसी विशिष्ट प्रीसैट को सक्रिय करने के लिए /customize /use [नंबर] का उपयोग करें।"
    },
    "preset_activated": {
        "en": "✅ **Preset activated:** {title}",
        "bn": "✅ **প্রিসেট সক্রিয় করা হয়েছে:** {title}",
        "hi": "✅ **प्रीसैट सक्रिय किया गया:** {title}"
    },
    "invalid_preset_number": {
        "en": "❌ Invalid preset number.",
        "bn": "❌ ভুল প্রিসেট নম্বর।",
        "hi": "❌ अमान्य प्रीसैट नंबर।"
    },
    "preset_deleted": {
        "en": "✅ **Preset deleted:** {title}",
        "bn": "✅ **প্রিসেট মুছে ফেলা হয়েছে:** {title}",
        "hi": "✅ **प्रीसैट हटाया गया:** {title}"
    },
    "personality_customized": {
        "en": "✅ **Bot personality customized successfully!**\n**New personality:** {personality}\nWould you like to save this customization as a preset for later use?",
        "bn": "✅ **বটের ব্যক্তিত্ব সফলভাবে কাস্টমাইজ করা হয়েছে!**\n**নতুন ব্যক্তিত্ব:** {personality}\nআপনি কি এই কাস্টমাইজেশনটি পরবর্তী ব্যবহারের জন্য প্রিসেট হিসেবে সংরক্ষণ করতে চান?",
        "hi": "✅ **बॉट का व्यक्तित्व सफलतापूर्वक कस्टमाइज़ किया गया!**\n**नया व्यक्तित्व:** {personality}\nक्या आप इस कस्टमाइज़ेशन को बाद में उपयोग के लिए प्रीसैट के रूप में सहेजना चाहेंगे?"
    },
    "reset_to_default": {
        "en": "✅ **Bot personality reset to default settings.**",
        "bn": "✅ **বটের ব্যক্তিত্ব ডিফল্ট সেটিংসে রিসেট করা হয়েছে।**",
        "hi": "✅ **बॉट का व्यक्तित्व डिफ़ॉल्ट सेटिंग्स पर रीसेट किया गया।**"
    },
    "preset_save_skipped": {
        "en": "✅ **Preset save skipped.**",
        "bn": "✅ **প্রিসেট সংরক্ষণ এড়িয়ে গেছে।**",
        "hi": "✅ **प्रीसैट सहेजना छोड़ दिया गया।**"
    },
    "customization_cancelled": {
        "en": "✅ **Customization cancelled.**",
        "bn": "✅ **কাস্টমাইজেশন বাতিল করা হয়েছে।**",
        "hi": "✅ **कस्टमाइज़ेशन रद्द कर दिया गया।**"
    },
    "customization_options_closed": {
        "en": "Customization options closed.",
        "bn": "কাস্টমাইজেশন অপশন বন্ধ করা হয়েছে।",
        "hi": "कस्टमाइज़ेशन विकल्प बंद कर दिए गए।"
    },
    "enter_search_query": {
        "en": "⚠️ Please send search query after the command. Example: /web Gold price today in Egypt",
        "bn": "⚠️ অনুগ্রহ করে কমান্ডের পরে সার্চ কুয়েরি পাঠান। উদাহরণ: /web আজ মিশরে সোনার দাম",
        "hi": "⚠️ कृपया कमांड के बाद खोज क्वेरी भेजें। उदाहरण: /web आज मिस्र में सोने की कीमत"
    },
    "enter_think_query": {
        "en": "⚠️ Please send text to think about after the command. Example: /think What is the meaning of life?",
        "bn": "⚠️ অনুগ্রহ করে কমান্ডের পরে চিন্তা করার টেক্সট পাঠান। উদাহরণ: /think জীবনের অর্থ কী?",
        "hi": "⚠️ कृपया कमांड के बाद विचार करने के लिए टेक्स्ट भेजें। उदाहरण: /think जीवन का अर्थ क्या है?"
    },
    "error_analysis": {
        "en": "❌ Error during analysis. Please try again later.",
        "bn": "❌ বিশ্লেষণের সময় ত্রুটি হয়েছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
        "hi": "❌ विश्लेषण के दौरान त्रुटि। कृपया बाद में पुनः प्रयास करें।"
    },
    "error_search": {
        "en": "❌ Error during search. Please try again later.",
        "bn": "❌ সার্চের সময় ত্রুটি হয়েছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
        "hi": "❌ खोज के दौरान त्रुटि। कृपया बाद में पुनः प्रयास करें।"
    },
    "error_thinking": {
        "en": "❌ Error during deep thinking. Please try again later.",
        "bn": "❌ গভীর চিন্তার সময় ত্রুটি হয়েছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
        "hi": "❌ गहन विचार के दौरान त्रुटि। कृपया बाद में पुनः प्रयास करें।"
    },
    "error_merging": {
        "en": "⚠️ Could not merge all perspectives due to content length. Showing first 3 perspectives only.",
        "bn": "⚠️ কন্টেন্টের দৈর্ঘ্যের কারণে সব দৃষ্টিকোণ মার্জ করা সম্ভব হয়নি। শুধু প্রথম ৩টি দৃষ্টিকোণ দেখানো হচ্ছে।",
        "hi": "⚠️ सामग्री की लंबाई के कारण सभी परिप्रेक्ष्यों को मर्ज नहीं किया जा सका। केवल पहले 3 परिप्रेक्ष्य दिखा रहा हूँ।"
    },
    "error_processing": {
        "en": "Sorry, an error occurred during processing. Please try later.",
        "bn": "দুঃখিত, প্রসেসিংয়ের সময় একটি ত্রুটি হয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।",
        "hi": "क्षमा करें, प्रोसेसिंग के दौरान एक त्रुटि हुई। कृपया बाद में प्रयास करें।"
    },
    "error_command": {
        "en": "Sorry, an error occurred processing the command. Please try later.",
        "bn": "দুঃখিত, কমান্ড প্রসেসিংয়ের সময় একটি ত্রুটি হয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।",
        "hi": "क्षमा करें, कमांड प्रोसेसिंग के दौरान एक त्रुटि हुई। कृपया बाद में प्रयास करें।"
    },
    "error_showing_stats": {
        "en": "Sorry, an error occurred showing statistics. Please try later.",
        "bn": "দুঃখিত, পরিসংখ্যান দেখানোর সময় একটি ত্রুটি হয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।",
        "hi": "क्षमा करें, आंकड़े दिखाने के दौरान एक त्रुटि हुई। कृपया बाद में प्रयास करें।"
    },
    "error_sending_feedback": {
        "en": "Sorry, an error occurred sending feedback. Please try later.",
        "bn": "দুঃখিত, ফিডব্যাক পাঠানোর সময় একটি ত্রুটি হয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।",
        "hi": "क्षमा करें, फीडबैक भेजने के दौरान एक त्रुटि हुई। कृपया बाद में प्रयास करें।"
    },
    "error_showing_credits": {
        "en": "Sorry, an error occurred showing credits. Please try later.",
        "bn": "দুঃখিত, ক্রেডিট দেখানোর সময় একটি ত্রুটি হয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।",
        "hi": "क्षमा करें, क्रेडिट दिखाने के दौरान एक त्रुटि हुई। कृपया बाद में प्रयास करें।"
    },
    "error_showing_server_info": {
        "en": "Sorry, an error occurred showing server information. Please try later.",
        "bn": "দুঃখিত, সার্ভারের তথ্য দেখানোর সময় একটি ত্রুটি হয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।",
        "hi": "क्षमा करें, सर्वर जानकारी दिखाने के दौरान एक त्रुटि हुई। कृपया बाद में प्रयास करें।"
    },
    "language_changed": {
        "en": "✅ Language changed to {language}!",
        "bn": "✅ ভাষা {language} এ পরিবর্তন করা হয়েছে!",
        "hi": "✅ भाषा {language} में बदल दी गई!"
    },
    "unsupported_language": {
        "en": "❌ Unsupported language code. Supported codes: {codes}",
        "bn": "❌ অসমর্থিত ভাষা কোড। সমর্থিত কোড: {codes}",
        "hi": "❌ असमर्थित भाषा कोड। समर्थित कोड: {codes}"
    },
    "bot_status_online": {
        "en": "✅ Bot operating normally",
        "bn": "✅ বট স্বাভাবিকভাবে কাজ করছে",
        "hi": "✅ बॉट सामान्य रूप से काम कर रहा है"
    },
    "bot_status_offline": {
        "en": "⏸️ Bot offline since: {duration}",
        "bn": "⏸️ বট অফলাইন: {duration}",
        "hi": "⏸️ बॉट ऑफलाइन: {duration}"
    },
    "feedback_sent": {
        "en": """⭐ **Thank you for your feedback!**
We greatly appreciate user opinions to improve and develop the bot.
Your feedback will be read carefully and your notes will be taken into consideration.
You can send new feedback {days_left} days from now.""",
        "bn": """⭐ **আপনার ফিডব্যাকের জন্য ধন্যবাদ!**
আমরা বট উন্নয়নের জন্য ব্যবহারকারীদের মতামতকে অত্যন্ত গুরুত্ব দিই।
আপনার ফিডব্যাক মনোযোগ সহকারে পড়া হবে এবং আপনার নোটগুলি বিবেচনায় নেওয়া হবে।
আপনি {days_left} দিন পর নতুন ফিডব্যাক পাঠাতে পারবেন।""",
        "hi": """⭐ **आपके फीडबैक के लिए धन्यवाद!**
हम बॉट को बेहतर बनाने के लिए उपयोगकर्ताओं की राय को अत्यधिक महत्व देते हैं।
आपका फीडबैक ध्यान से पढ़ा जाएगा और आपके नोट्स पर विचार किया जाएगा।
आप {days_left} दिन बाद नया फीडबैक भेज सकते हैं।"""
    },
    "feedback_waiting": {
        "en": "⏳ You can send new feedback after {days} day/s. Thank you for your interest!",
        "bn": "⏳ আপনি {days} দিন পর নতুন ফিডব্যাক পাঠাতে পারবেন। আপনার আগ্রহের জন্য ধন্যবাদ!",
        "hi": "⏳ आप {days} दिन बाद नया फीडबैक भेज सकते हैं। आपकी रुचि के लिए धन्यवाद!"
    },
    "developer_info": {
        "en": """👨‍💻 **Developer Information:**
**Bot Developer:** HAKORA
**Twitter:** https://x.com/HAKORAdev/""",
        "bn": """👨‍💻 **ডেভেলপারের তথ্য:**
**বট ডেভেলপার:** HAKORA
**টুইটার:** https://x.com/HAKORAdev/""",
        "hi": """👨‍💻 **डेवलपर जानकारी:**
**बॉट डेवलपर:** HAKORA
**ट्विटर:** https://x.com/HAKORAdev/"""
    },
    "no_recent_feedbacks": {
        "en": "\nNo recent feedbacks.",
        "bn": "\nকোনো সাম্প্রতিক ফিডব্যাক নেই।",
        "hi": "\nकोई हालिया फीडबैक नहीं।"
    },
    "enter_feedback_query": {
        "en": "⚠️ Please send your opinion after the command. Example: /feedback The bot is great!",
        "bn": "⚠️ অনুগ্রহ করে কমান্ডের পরে আপনার মতামত পাঠান। উদাহরণ: /feedback বটটি খুব ভালো!",
        "hi": "⚠️ कृपया कमांड के बाद अपनी राय भेजें। उदाहरण: /feedback बॉट बहुत अच्छा है!"
    }
}

DEFAULT_USER_STATS = {
    "messages_sent": 0,
    "messages_received": 0,
    "deep_thoughts": 0,
    "customizations": 0,
    "think_full": 0,
    "think": 0,
    "presets_created": 0,
    "presets_used": 0,
    "web_searches": 0,
    "feedbacks_submitted": 0
}

user_conversations = {}
user_stats = {}
user_feedbacks = {}
bot_stats = {
    "start_time": datetime.now().isoformat(),
    "total_messages_processed": 0,
    "messages_today": 0,
    "messages_week": 0,
    "messages_month": 0,
    "last_message_time": None,
    "downtime_start": None,
    "downtime_periods": [],
    "users_today": set(),
    "users_week": set(),
    "users_month": set()
}
last_save_time = 0
save_lock = threading.Lock()

def get_translation(user_id, key, **kwargs):
    try:
        user_memory = get_user_memory(user_id)
        language = user_memory.get("language", DEFAULT_LANGUAGE)
        # যদি ভাষা না থাকে তাহলে ডিফল্ট ইংরেজি
        if language not in LANGUAGE_STRINGS[key]:
            language = "en"
        text = LANGUAGE_STRINGS[key][language]
        return text.format(**kwargs)
    except Exception as e:
        logger.error(f"Error in get_translation: {e}")
        try:
            return LANGUAGE_STRINGS[key]["en"].format(**kwargs)
        except:
            return "Translation error"

def load_data():
    global user_conversations, user_stats, user_feedbacks, bot_stats
    try:
        if os.path.exists('conversations.json'):
            with open('conversations.json', 'r', encoding='utf-8') as f:
                user_conversations = json.load(f)
            for user_id, data in user_conversations.items():
                if "messages" not in data:
                    data["messages"] = []
                if "last_active" not in data:
                    data["last_active"] = datetime.now().isoformat()
                if "custom_persona" not in data:
                    language = data.get("language", DEFAULT_LANGUAGE)
                    data["custom_persona"] = get_default_persona(language)
                if "presets" not in data:
                    data["presets"] = []
                if "active_preset" not in data:
                    data["active_preset"] = None
                if "last_feedback" not in data:
                    data["last_feedback"] = None
                if "language" not in data:
                    data["language"] = DEFAULT_LANGUAGE
                for msg in data["messages"]:
                    if "timestamp" not in msg:
                        msg["timestamp"] = datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Error loading conversations: {e}")
        user_conversations = {}
    try:
        if os.path.exists('user_stats.json'):
            with open('user_stats.json', 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            for user_id, stats in user_stats.items():
                for key, value in DEFAULT_USER_STATS.items():
                    if key not in stats:
                        stats[key] = value
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
        user_stats = {}
    try:
        if os.path.exists('user_feedbacks.json'):
            with open('user_feedbacks.json', 'r', encoding='utf-8') as f:
                user_feedbacks = json.load(f)
    except Exception as e:
        logger.error(f"Error loading feedbacks: {e}")
        user_feedbacks = {}
    try:
        if os.path.exists('bot_stats.json'):
            with open('bot_stats.json', 'r', encoding='utf-8') as f:
                saved_bot_stats = json.load(f)
                for key, value in saved_bot_stats.items():
                    if key in bot_stats:
                        if key in ["users_today", "users_week", "users_month"]:
                            bot_stats[key] = set(value)
                        else:
                            bot_stats[key] = value
    except Exception as e:
        logger.error(f"Error loading bot statistics: {e}")
    load_permanent_data()
    update_users_info()

def load_permanent_data():
    try:
        if os.path.exists('conversations_save.json'):
            with open('conversations_save.json', 'r', encoding='utf-8') as f:
                conversations_save = json.load(f)
            for user_id, data in conversations_save.items():
                if user_id not in user_conversations:
                    user_conversations[user_id] = data
                else:
                    if "language" not in user_conversations[user_id]:
                        user_conversations[user_id]["language"] = DEFAULT_LANGUAGE
        if os.path.exists('user_stats_save.json'):
            with open('user_stats_save.json', 'r', encoding='utf-8') as f:
                user_stats_save = json.load(f)
            for user_id, stats in user_stats_save.items():
                if user_id not in user_stats:
                    user_stats[user_id] = stats
        if os.path.exists('user_feedbacks_save.json'):
            with open('user_feedbacks_save.json', 'r', encoding='utf-8') as f:
                user_feedbacks_save = json.load(f)
            for user_id, feedback in user_feedbacks_save.items():
                if user_id not in user_feedbacks:
                    user_feedbacks[user_id] = feedback
    except Exception as e:
        logger.error(f"Error loading permanent data: {e}")

def save_data():
    global last_save_time
    current_time = time.time()
    if current_time - last_save_time < 5:
        return
    with save_lock:
        try:
            with open('conversations.json', 'w', encoding='utf-8') as f:
                json.dump(user_conversations, f, ensure_ascii=False, indent=2)
            with open('user_stats.json', 'w', encoding='utf-8') as f:
                json.dump(user_stats, f, ensure_ascii=False, indent=2)
            with open('user_feedbacks.json', 'w', encoding='utf-8') as f:
                json.dump(user_feedbacks, f, ensure_ascii=False, indent=2)
            bot_stats_to_save = bot_stats.copy()
            for key in ["users_today", "users_week", "users_month"]:
                if key in bot_stats_to_save:
                    bot_stats_to_save[key] = list(bot_stats_to_save[key])
            with open('bot_stats.json', 'w', encoding='utf-8') as f:
                json.dump(bot_stats_to_save, f, ensure_ascii=False, indent=2)
            save_permanent_data()
            last_save_time = current_time
        except Exception as e:
            logger.error(f"Error saving data: {e}")

def save_permanent_data():
    try:
        with open('conversations_save.json', 'w', encoding='utf-8') as f:
            json.dump(user_conversations, f, ensure_ascii=False, indent=2)
        with open('user_stats_save.json', 'w', encoding='utf-8') as f:
            json.dump(user_stats, f, ensure_ascii=False, indent=2)
        with open('user_feedbacks_save.json', 'w', encoding='utf-8') as f:
            json.dump(user_feedbacks, f, ensure_ascii=False, indent=2)
        update_users_info()
    except Exception as e:
        logger.error(f"Error saving permanent data: {e}")

def update_bot_stats(message_count=0, user_id=None):
    try:
        current_time = datetime.now()
        bot_stats["last_message_time"] = current_time.isoformat()
        if message_count > 0:
            bot_stats["total_messages_processed"] += message_count
            if is_today(current_time):
                bot_stats["messages_today"] += message_count
            if is_this_week(current_time):
                bot_stats["messages_week"] += message_count
            if is_this_month(current_time):
                bot_stats["messages_month"] += message_count
            if user_id:
                if is_today(current_time):
                    bot_stats["users_today"].add(user_id)
                if is_this_week(current_time):
                    bot_stats["users_week"].add(user_id)
                if is_this_month(current_time):
                    bot_stats["users_month"].add(user_id)
        if bot_stats["total_messages_processed"] % 10 == 0:
            save_data()
    except Exception as e:
        logger.error(f"Error updating bot statistics: {e}")

def is_today(timestamp):
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return timestamp.date() == datetime.now().date()
    except:
        return False

def is_this_week(timestamp):
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        return timestamp.date() >= start_of_week.date()
    except:
        return False

def is_this_month(timestamp):
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        now = datetime.now()
        return timestamp.month == now.month and timestamp.year == now.year
    except:
        return False

def get_uptime():
    try:
        start_time = datetime.fromisoformat(bot_stats["start_time"])
        uptime = datetime.now() - start_time
        return uptime
    except:
        return timedelta(0)

def format_uptime(uptime):
    try:
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes, {seconds} seconds"
        else:
            return f"{minutes} minutes, {seconds} seconds"
    except:
        return "Not available"

def get_server_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else "N/A"
        cpu_freq_max = cpu_freq.max if cpu_freq else "N/A"
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 ** 3)
        memory_used = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)
        disk_used = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        system_info = platform.platform()
        processor = platform.processor()
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "freq_current": cpu_freq_current,
                "freq_max": cpu_freq_max
            },
            "memory": {
                "total": memory_total,
                "used": memory_used,
                "percent": memory_percent
            },
            "disk": {
                "total": disk_total,
                "used": disk_used,
                "percent": disk_percent
            },
            "system": {
                "platform": system_info,
                "processor": processor
            }
        }
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return None

async def check_bot_status(application):
    while True:
        try:
            current_time = datetime.now()
            last_message_time = bot_stats.get("last_message_time")
            if last_message_time:
                last_time = datetime.fromisoformat(last_message_time)
                downtime = current_time - last_time
                if downtime.total_seconds() > 300 and not bot_stats.get("downtime_start"):
                    bot_stats["downtime_start"] = last_time.isoformat()
                    logger.warning(f"Bot stopped since: {last_time}")
                elif bot_stats.get("downtime_start") and downtime.total_seconds() <= 300:
                    downtime_start = datetime.fromisoformat(bot_stats["downtime_start"])
                    downtime_period = current_time - downtime_start
                    bot_stats["downtime_periods"].append({
                        "start": downtime_start.isoformat(),
                        "end": current_time.isoformat(),
                        "duration_seconds": downtime_period.total_seconds()
                    })
                    bot_stats["downtime_start"] = None
                    active_users = get_active_users(24)
                    for user_id in active_users:
                        try:
                            user_memory = get_user_memory(user_id)
                            language = user_memory.get("language", DEFAULT_LANGUAGE)
                            duration_text = format_downtime(downtime_period)
                            message = LANGUAGE_STRINGS["back_online_message"][language].format(duration=duration_text)
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=message
                            )
                        except Exception as e:
                            logger.error(f"Error sending notification to user {user_id}: {e}")
                    logger.info(f"Bot back online after: {format_downtime(downtime_period)}")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error checking bot status: {e}")
            await asyncio.sleep(60)

def format_downtime(downtime):
    try:
        days = downtime.days
        hours, remainder = divmod(downtime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes, {seconds} seconds"
        else:
            return f"{minutes} minutes, {seconds} seconds"
    except:
        return "Unknown period"

def get_active_users(hours=24):
    try:
        active_users = set()
        threshold = datetime.now() - timedelta(hours=hours)
        for user_id, data in user_conversations.items():
            if "last_active" in data:
                last_active = datetime.fromisoformat(data["last_active"])
                if last_active >= threshold:
                    active_users.add(user_id)
        return active_users
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        return set()

def update_users_info():
    try:
        awake_users = 0
        sleeping_users = 0
        dead_users = 0
        total_feedbacks = len(user_feedbacks)
        current_time = datetime.now()
        for user_id, data in user_conversations.items():
            if "last_active" in data:
                last_active = datetime.fromisoformat(data["last_active"])
                days_inactive = (current_time - last_active).days
                if days_inactive <= 1:
                    awake_users += 1
                elif 2 <= days_inactive <= 6:
                    sleeping_users += 1
                else:
                    dead_users += 1
        users_info = {
            "awake_users": awake_users,
            "sleeping_users": sleeping_users,
            "dead_users": dead_users,
            "total_feedbacks": total_feedbacks,
            "last_updated": current_time.isoformat(),
            "total_users": len(user_conversations),
            "recent_feedbacks": get_recent_feedbacks(5)
        }
        with open('users_info.json', 'w', encoding='utf-8') as f:
            json.dump(users_info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error updating user info: {e}")

def get_recent_feedbacks(limit=5):
    try:
        recent_feedbacks = []
        for user_id, feedback_data in user_feedbacks.items():
            if len(recent_feedbacks) >= limit:
                break
            recent_feedbacks.append({
                "user_id": user_id,
                "feedback": feedback_data.get("feedback", ""),
                "timestamp": feedback_data.get("timestamp", ""),
                "rating": feedback_data.get("rating", "Not specified")
            })
        return recent_feedbacks
    except Exception as e:
        logger.error(f"Error getting recent feedbacks: {e}")
        return []

def cleanup_old_conversations():
    try:
        current_time = datetime.now()
        two_days_ago = current_time - timedelta(days=2)
        deleted_count = 0
        for user_id, data in user_conversations.items():
            if "last_active" in data:
                last_active = datetime.fromisoformat(data["last_active"])
                if last_active < two_days_ago:
                    old_msg_count = len(data.get("messages", []))
                    custom_persona = data.get("custom_persona", get_default_persona(data.get("language", DEFAULT_LANGUAGE)))
                    presets = data.get("presets", [])
                    active_preset = data.get("active_preset", None)
                    last_feedback = data.get("last_feedback", None)
                    user_conversations[user_id] = {
                        "messages": [
                            {
                                "role": "system", 
                                "content": custom_persona,
                                "timestamp": datetime.now().isoformat()
                            }
                        ],
                        "last_active": datetime.now().isoformat(),
                        "custom_persona": custom_persona,
                        "presets": presets,
                        "active_preset": active_preset,
                        "last_feedback": last_feedback,
                        "language": data.get("language", DEFAULT_LANGUAGE),
                        "last_cleanup_notification": datetime.now().isoformat()
                    }
                    deleted_count += 1
                    user_conversations[user_id]["show_cleanup_message"] = True
                    user_conversations[user_id]["deleted_messages_count"] = old_msg_count - 1
        if deleted_count > 0:
            logger.info(f"Cleaned conversations for {deleted_count} users due to inactivity")
        save_permanent_data()
    except Exception as e:
        logger.error(f"Error cleaning old conversations: {e}")

def update_user_stats(user_id, stat_type):
    try:
        if user_id not in user_stats:
            user_stats[user_id] = copy.deepcopy(DEFAULT_USER_STATS)
        if stat_type not in user_stats[user_id]:
            user_stats[user_id][stat_type] = 0
        user_stats[user_id][stat_type] += 1
        save_data()
    except Exception as e:
        logger.error(f"Error updating statistics: {e}")

def get_user_memory(user_id):
    try:
        if user_id not in user_conversations:
            default_persona = get_default_persona(DEFAULT_LANGUAGE)
            user_conversations[user_id] = {
                "messages": [
                    {
                        "role": "system", 
                        "content": default_persona,
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "last_active": datetime.now().isoformat(),
                "custom_persona": default_persona,
                "presets": [],
                "active_preset": None,
                "last_feedback": None,
                "language": DEFAULT_LANGUAGE
            }
        else:
            user_data = user_conversations[user_id]
            if "presets" not in user_data:
                user_data["presets"] = []
            if "active_preset" not in user_data:
                user_data["active_preset"] = None
            if "custom_persona" not in user_data:
                language = user_data.get("language", DEFAULT_LANGUAGE)
                user_data["custom_persona"] = get_default_persona(language)
            if "last_feedback" not in user_data:
                user_data["last_feedback"] = None
            if "language" not in user_data:
                user_data["language"] = DEFAULT_LANGUAGE
            if user_data["messages"] and user_data["messages"][0]["role"] == "system":
                user_data["messages"][0]["content"] = user_data["custom_persona"]
        return user_conversations[user_id]
    except Exception as e:
        logger.error(f"Error getting user memory: {e}")
        default_persona = get_default_persona(DEFAULT_LANGUAGE)
        return {
            "messages": [
                {
                    "role": "system", 
                    "content": default_persona,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "last_active": datetime.now().isoformat(),
            "custom_persona": default_persona,
            "presets": [],
            "active_preset": None,
            "last_feedback": None,
            "language": DEFAULT_LANGUAGE
        }

def clean_response(response):
    try:
        if not response:
            return "Sorry, I couldn't generate a response. Please try again."
        response = re.sub(r'\?\?+$', '', response)
        response = re.sub(r'[^\w\s\u0600-\u06FF\.\,\!\"\'\-\؟]$', '', response)
        return response.strip()
    except Exception as e:
        logger.error(f"Error cleaning response: {e}")
        return "Sorry, an error occurred while processing the response."

def advanced_processing(messages, custom_persona=None):
    try:
        processed_messages = copy.deepcopy(messages)
        system_message = custom_persona if custom_persona else "You are a helpful assistant who speaks English. Be friendly and helpful in your responses."
        context = extract_conversation_context(processed_messages)
        intent = analyze_user_intent(processed_messages[-1]["content"] if processed_messages else "")
        sentiment = analyze_sentiment(processed_messages)
        keywords = extract_keywords(processed_messages)
        detail_level = determine_detail_level(processed_messages)
        direct_questions = identify_direct_questions(processed_messages)
        timeline = analyze_conversation_timeline(processed_messages)
        priorities = determine_response_priorities(processed_messages)
        patterns = analyze_conversation_patterns(processed_messages)
        enhanced_system_message = build_enhanced_system_message(
            system_message, context, intent, sentiment, keywords,
            detail_level, direct_questions, timeline, priorities, patterns
        )
        if processed_messages and processed_messages[0]["role"] == "system":
            processed_messages[0]["content"] = enhanced_system_message
        else:
            processed_messages.insert(0, {"role": "system", "content": enhanced_system_message})
        return processed_messages
    except Exception as e:
        logger.error(f"Error in advanced processing: {e}")
        return messages

def extract_conversation_context(messages):
    try:
        if len(messages) <= 2:
            return "New conversation, not much context"
        recent_messages = messages[-5:]
        context = "Recent conversation context: "
        for msg in recent_messages:
            if msg["role"] == "user":
                context += f"User: {msg['content'][:50]}... "
            elif msg["role"] == "assistant":
                context += f"Assistant: {msg['content'][:30]}... "
        return context
    except:
        return "Cannot extract context due to error"

def analyze_user_intent(user_message):
    try:
        user_message = user_message.lower()
        if any(word in user_message for word in ["how", "method", "steps"]):
            return "User requests explanation or instructions"
        elif any(word in user_message for word in ["why", "reason", "cause"]):
            return "User requests explanation or reasons"
        elif any(word in user_message for word in ["what is", "definition"]):
            return "User requests definition or concept explanation"
        elif any(word in user_message for word in ["want", "need", "search for"]):
            return "User requests help finding something"
        else:
            return "General intent - normal conversation or inquiry"
    except:
        return "Undefined intent"

def analyze_sentiment(messages):
    try:
        if not messages:
            return "Neutral"
        last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        last_user_message = last_user_message.lower()
        positive_words = ["thanks", "excellent", "great", "beautiful", "well done"]
        negative_words = ["angry", "bad", "annoying", "wrong", "why"]
        if any(word in last_user_message for word in positive_words):
            return "Positive"
        elif any(word in last_user_message for word in negative_words):
            return "Negative"
        else:
            return "Neutral"
    except:
        return "Neutral"

def extract_keywords(messages):
    try:
        if not messages:
            return "No keywords"
        all_text = " ".join([msg["content"] for msg in messages if "content" in msg])
        stop_words = ["in", "from", "on", "to", "that", "he", "she", "is", "what", "not"]
        words = re.findall(r'\b[\u0600-\u06FF]{3,}\b', all_text)
        keywords = [word for word in words if word not in stop_words]
        return ", ".join(list(set(keywords))[:5])
    except:
        return "No keywords"

def determine_detail_level(messages):
    try:
        if not messages:
            return "Medium"
        last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        if any(word in last_user_message for word in ["briefly", "quickly", "summarize"]):
            return "Low"
        elif any(word in last_user_message for word in ["in detail", "detailed explanation", "detailed"]):
            return "High"
        else:
            return "Medium"
    except:
        return "Medium"

def identify_direct_questions(messages):
    try:
        if not messages:
            return "No direct questions"
        questions = []
        for msg in messages[-3:]:
            if msg["role"] == "user" and any(mark in msg["content"] for mark in ["؟", "?", "what is", "how"]):
                questions.append(msg["content"][:50] + "...")
        return ", ".join(questions) if questions else "No recent direct questions"
    except:
        return "No direct questions"

def analyze_conversation_timeline(messages):
    try:
        if len(messages) < 3:
            return "New conversation, no long timeline"
        user_msg_count = sum(1 for msg in messages if msg["role"] == "user")
        assistant_msg_count = sum(1 for msg in messages if msg["role"] == "assistant")
        return f"Conversation has {user_msg_count} user messages and {assistant_msg_count} responses"
    except:
        return "Cannot analyze timeline"

def determine_response_priorities(messages):
    try:
        if not messages:
            return "Respond to current message only"
        last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        if any(word in last_user_message for word in ["important", "urgent", "critical"]):
            return "High priority - respond urgently and directly"
        elif any(word in last_user_message for word in ["curiosity", "know", "understand"]):
            return "Medium priority - detailed explanation"
        else:
            return "Normal priority - usual response"
    except:
        return "Normal priority - usual response"

def analyze_conversation_patterns(messages):
    try:
        if len(messages) < 5:
            return "No clear patterns yet (short conversation)"
        roles = [msg["role"] for msg in messages]
        user_streak = 0
        max_user_streak = 0
        for role in roles:
            if role == "user":
                user_streak += 1
                max_user_streak = max(max_user_streak, user_streak)
            else:
                user_streak = 0
        if max_user_streak >= 2:
            return "Pattern: User sends multiple consecutive messages (may be excited or need urgent help)"
        else:
            return "Pattern: Normal alternation between user and assistant"
    except:
        return "Cannot analyze patterns"

def build_enhanced_system_message(base_message, context, intent, sentiment, keywords,
                                 detail_level, direct_questions, timeline, priorities, patterns):
    try:
        enhanced_message = f"""
{base_message}
**Advanced Conversation Analysis:**
- **Context:** {context}
- **Intent:** {intent}
- **Sentiment:** {sentiment}
- **Keywords:** {keywords}
- **Detail Level:** {detail_level}
- **Direct Questions:** {direct_questions}
- **Timeline:** {timeline}
- **Priorities:** {priorities}
- **Patterns:** {patterns}
**Response Guidelines:**
- Focus on answering direct questions first
- Adapt detail level according to request
- Notice user sentiment state
- Use keywords in your response
- Follow the specified priorities
"""
        return enhanced_message
    except:
        return base_message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_memory = get_user_memory(user_id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        if bot_stats.get("downtime_start"):
            downtime_start = datetime.fromisoformat(bot_stats["downtime_start"])
            downtime = datetime.now() - downtime_start
            duration_text = format_downtime(downtime)
            downtime_message = get_translation(user_id, "downtime_message", duration=duration_text)
            await update.message.reply_text(downtime_message)
            return
        
        if user_memory.get("show_cleanup_message"):
            deleted_count = user_memory.get("deleted_messages_count", 0)
            if deleted_count > 0:
                cleanup_message = get_translation(user_id, "cleanup_message", count=deleted_count)
                await update.message.reply_text(cleanup_message)
            user_memory["show_cleanup_message"] = False
            save_data()
        
        help_text = get_translation(user_id, "start_message")
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        error_message = get_translation(user_id, "error_command")
        await update.message.reply_text(error_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        help_text = get_translation(user_id, "help_message")
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        error_message = get_translation(user_id, "error_command")
        await update.message.reply_text(error_message)

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_memory = get_user_memory(user_id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        custom_persona = user_memory.get("custom_persona", get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE)))
        presets = user_memory.get("presets", [])
        active_preset = user_memory.get("active_preset", None)
        last_feedback = user_memory.get("last_feedback", None)
        user_memory["messages"] = [
            {
                "role": "system", 
                "content": custom_persona,
                "timestamp": datetime.now().isoformat()
            }
        ]
        user_memory["last_active"] = datetime.now().isoformat()
        user_memory["presets"] = presets
        user_memory["active_preset"] = active_preset
        user_memory["last_feedback"] = last_feedback
        save_data()
        clear_message = get_translation(user_id, "clear_message")
        await update.message.reply_text(clear_message)
    except Exception as e:
        logger.error(f"Error in clear command: {e}")
        error_message = get_translation(user_id, "error_command")
        await update.message.reply_text(error_message)

async def think_full_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_memory = get_user_memory(user_id)
        update_user_stats(user_id, "think_full")
        update_bot_stats(1, user_id)
        thinking_msg = await update.message.reply_text(get_translation(user_id, "deep_thinking", progress=0))
        last_10_messages = user_memory["messages"][-10:] if len(user_memory["messages"]) > 10 else user_memory["messages"]
        if not last_10_messages:
            no_messages = get_translation(user_id, "no_messages_to_analyze")
            await thinking_msg.edit_text(no_messages)
            return
        
        analysis_messages = [
            {
                "role": "system",
                "content": "You are an expert conversation analyst. Comprehensively analyze the last 10 messages in the conversation."
            }
        ]
        for i, msg in enumerate(last_10_messages):
            if msg["role"] == "user":
                analysis_messages.append({"role": "user", "content": f"Message {i+1} from user: {msg['content']}"})
            elif msg["role"] == "assistant":
                analysis_messages.append({"role": "user", "content": f"Response {i+1} from assistant: {msg['content']}"})
        
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            provider=g4f.Provider.MetaAI,
            messages=analysis_messages,
            stream=False,
        )
        cleaned_response = clean_response(response)
        analysis_text = get_translation(user_id, "think_full_analysis", count=len(last_10_messages), response=cleaned_response)
        await thinking_msg.edit_text(analysis_text)
    except Exception as e:
        logger.error(f"Error in think_full command: {e}")
        try:
            error_message = get_translation(user_id, "error_analysis")
            await thinking_msg.edit_text(error_message)
        except:
            error_message = get_translation(user_id, "error_analysis")
            await update.message.reply_text(error_message)

async def update_progress(thinking_msg, progress, user_id):
    try:
        progress_text = get_translation(user_id, "deep_thinking", progress=progress)
        await thinking_msg.edit_text(progress_text)
    except:
        pass

async def think_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_memory = get_user_memory(user_id)
    update_user_stats(user_id, "think")
    update_bot_stats(1, user_id)
    if not context.args:
        no_query = get_translation(user_id, "enter_think_query")
        await update.message.reply_text(no_query)
        return
    
    query = " ".join(context.args)
    thinking_msg = await update.message.reply_text(get_translation(user_id, "deep_thinking", progress=0))
    try:
        responses = []
        perspectives = [
            "Deep philosophical analysis",
            "Accurate scientific analysis",
            "Practical application perspective",
            "Psychological and emotional analysis",
            "Historical perspective",
            "Future vision and prediction",
            "Economic analysis",
            "Social and cultural perspective",
            "Creative innovative analysis",
            "Comprehensive integrated vision"
        ]
        for i, perspective in enumerate(perspectives):
            try:
                progress = (i + 1) * 10
                await update_progress(thinking_msg, progress, user_id)
                response = g4f.ChatCompletion.create(
                    model="gpt-4o",
                    provider=g4f.Provider.MetaAI,
                    messages=[
                        {"role": "system", "content": f"Provide a deep and comprehensive analysis from perspective: {perspective}. Be accurate and detailed."},
                        {"role": "user", "content": query}
                    ],
                    stream=False,
                )
                cleaned_response = clean_response(response)
                if len(cleaned_response.split('\n')) > 25:
                    lines = cleaned_response.split('\n')
                    cleaned_response = '\n'.join(lines[:25]) + "\n... (Analysis shortened for focus)"
                responses.append(f"## Perspective {i+1}: {perspective}\n{cleaned_response}\n")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error generating response from perspective {i+1}: {e}")
                continue
        
        if not responses:
            error_message = get_translation(user_id, "error_thinking")
            await thinking_msg.edit_text(error_message)
            return
        
        await update_progress(thinking_msg, 95, user_id)
        try:
            all_responses_text = "\n".join(responses)
            if len(all_responses_text) > 4000:
                shortened_responses = []
                for response in responses:
                    lines = response.split('\n')
                    if len(lines) > 10:
                        shortened = '\n'.join(lines[:10]) + "\n... (Analysis shortened)"
                        shortened_responses.append(shortened)
                    else:
                        shortened_responses.append(response)
                all_responses_text = "\n".join(shortened_responses)
            
            merge_prompt = f"""
            Merge the following analyses from ten different perspectives into one integrated, comprehensive, and organized response:
            {all_responses_text}
            Merge instructions:
            1. Provide a final response that integrates all these insights coherently
            2. Organize content in a logical and organized manner
            3. Add subheadings for each main section
            4. Ensure comprehensive and accurate response
            5. Delete any unnecessary repetition
            6. Arrange ideas in logical sequential order
            7. Write in clear language of the user
            8. Add conclusion summarizing main points
            9. Do not exceed 100-150 lines
            The final response should be a comprehensive analysis covering all aspects presented.
            """
            merged_response = g4f.ChatCompletion.create(
                model="gpt-4o",
                provider=g4f.Provider.MetaAI,
                messages=[
                    {"role": "system", "content": "You are an expert in merging multiple analyses. Provide a final response that integrates all perspectives coherently and organized while maintaining depth and accuracy."},
                    {"role": "user", "content": merge_prompt}
                ],
                stream=False,
            )
            cleaned_response = clean_response(merged_response)
            if len(cleaned_response.split('\n')) > 150:
                lines = cleaned_response.split('\n')
                cleaned_response = '\n'.join(lines[:150]) + "\n... (Final analysis shortened for focus)"
            
            user_memory["messages"].extend([
                {"role": "user", "content": f"/think {query}", "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": cleaned_response, "timestamp": datetime.now().isoformat()}
            ])
            save_data()
            result_text = get_translation(user_id, "deep_thinking_result", response=cleaned_response)
            await thinking_msg.edit_text(result_text)
        except Exception as merge_error:
            logger.error(f"Error merging responses: {merge_error}")
            fallback_response = get_translation(user_id, "deep_thinking_result", response="")
            for i, response in enumerate(responses[:3]):
                fallback_response += f"\n{response}\n{'='*50}\n"
            fallback_response += "\n" + get_translation(user_id, "error_merging")
            user_memory["messages"].extend([
                {"role": "user", "content": f"/think {query}", "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": fallback_response, "timestamp": datetime.now().isoformat()}
            ])
            save_data()
            await thinking_msg.edit_text(fallback_response)
    except Exception as e:
        logger.error(f"Error in think command: {e}")
        try:
            error_message = get_translation(user_id, "error_thinking")
            await thinking_msg.edit_text(error_message)
        except:
            error_message = get_translation(user_id, "error_thinking")
            await update.message.reply_text(error_message)

async def web_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_memory = get_user_memory(user_id)
    update_user_stats(user_id, "web_searches")
    update_bot_stats(1, user_id)
    if not context.args:
        no_query = get_translation(user_id, "enter_search_query")
        await update.message.reply_text(no_query)
        return
    
    query = " ".join(context.args)
    search_msg = await update.message.reply_text(get_translation(user_id, "web_searching"))
    try:
        search_prompt = f"""
        You are an advanced search assistant. Search for the following information through the internet focusing on reliable and recent sources.
        Search query: {query}
        Search instructions:
        1. Search in more than 20 different reliable sources
        2. Focus on recent sources (last 6 months)
        3. Verify information accuracy from multiple sources
        4. Compare between different sources
        5. Exclude unreliable or old information
        6. Provide comprehensive answer covering all aspects of the query
        7. Add information sources if possible
        8. Organize response in clear and logical manner
        The answer should be accurate, comprehensive and reliable, focusing on the latest available information.
        """
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            provider=g4f.Provider.MetaAI,
            messages=[
                {"role": "system", "content": "You are a specialized search assistant. Your task is to search for information through the internet from reliable and multiple sources. Provide accurate and comprehensive answers focusing on recent and reliable sources."},
                {"role": "user", "content": search_prompt}
            ],
            stream=False,
        )
        cleaned_response = clean_response(response)
        user_memory["messages"].extend([
            {"role": "user", "content": f"/web {query}", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": cleaned_response, "timestamp": datetime.now().isoformat()}
        ])
        save_data()
        results_text = get_translation(user_id, "web_results", query=query, response=cleaned_response)
        await search_msg.edit_text(results_text)
    except Exception as e:
        logger.error(f"Error in web command: {e}")
        try:
            error_message = get_translation(user_id, "error_search")
            await search_msg.edit_text(error_message)
        except:
            error_message = get_translation(user_id, "error_search")
            await update.message.reply_text(error_message)

async def customize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_memory = get_user_memory(user_id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        if context.args and context.args[0] == "/s":
            if not user_memory["custom_persona"] or user_memory["custom_persona"] == get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE)):
                no_customization = get_translation(user_id, "no_customization_to_save")
                await update.message.reply_text(no_customization)
                return
            if len(user_memory["presets"]) >= 10:
                max_presets = get_translation(user_id, "max_presets_reached")
                await update.message.reply_text(max_presets)
                return
            new_preset = {
                "id": len(user_memory["presets"]),
                "persona": user_memory["custom_persona"],
                "title": get_translation(user_id, "preset_title_default", number=len(user_memory['presets']) + 1),
                "created_at": datetime.now().isoformat()
            }
            user_memory["presets"].append(new_preset)
            update_user_stats(user_id, "presets_created")
            save_data()
            saved_message = get_translation(user_id, "customization_saved", title=new_preset['title'])
            await update.message.reply_text(saved_message)
            return
        elif context.args and context.args[0] == "/t" and len(context.args) > 1:
            if not user_memory["presets"]:
                no_presets = get_translation(user_id, "no_presets")
                await update.message.reply_text(no_presets)
                return
            new_title = " ".join(context.args[1:])
            user_memory["presets"][-1]["title"] = new_title
            save_data()
            updated_message = get_translation(user_id, "preset_title_updated", title=new_title)
            await update.message.reply_text(updated_message)
            return
        elif context.args and context.args[0] == "/list":
            if not user_memory["presets"]:
                no_presets = get_translation(user_id, "no_presets")
                await update.message.reply_text(no_presets)
                return
            presets_list = ""
            for i, preset in enumerate(user_memory["presets"]):
                active_indicator = " ✅" if user_memory.get("active_preset") == preset["id"] else ""
                presets_list += f"{i+1}. {preset['title']}{active_indicator}\n"
            presets_text = get_translation(user_id, "saved_presets", list=presets_list)
            await update.message.reply_text(presets_text)
            return
        elif context.args and context.args[0] == "/use" and len(context.args) > 1:
            try:
                preset_id = int(context.args[1]) - 1
                if preset_id < 0 or preset_id >= len(user_memory["presets"]):
                    invalid_number = get_translation(user_id, "invalid_preset_number")
                    await update.message.reply_text(invalid_number)
                    return
                preset = user_memory["presets"][preset_id]
                user_memory["custom_persona"] = preset["persona"]
                user_memory["active_preset"] = preset["id"]
                if user_memory["messages"] and user_memory["messages"][0]["role"] == "system":
                    user_memory["messages"][0]["content"] = preset["persona"]
                update_user_stats(user_id, "presets_used")
                save_data()
                activated_message = get_translation(user_id, "preset_activated", title=preset['title'])
                await update.message.reply_text(activated_message)
                return
            except ValueError:
                invalid_number = get_translation(user_id, "invalid_preset_number")
                await update.message.reply_text(invalid_number)
                return
        elif context.args and context.args[0] == "/delete" and len(context.args) > 1:
            try:
                preset_id = int(context.args[1]) - 1
                if preset_id < 0 or preset_id >= len(user_memory["presets"]):
                    invalid_number = get_translation(user_id, "invalid_preset_number")
                    await update.message.reply_text(invalid_number)
                    return
                deleted_preset = user_memory["presets"].pop(preset_id)
                for i, preset in enumerate(user_memory["presets"]):
                    preset["id"] = i
                if user_memory.get("active_preset") == preset_id:
                    user_memory["active_preset"] = None
                    user_memory["custom_persona"] = get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE))
                    if user_memory["messages"] and user_memory["messages"][0]["role"] == "system":
                        user_memory["messages"][0]["content"] = get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE))
                save_data()
                deleted_message = get_translation(user_id, "preset_deleted", title=deleted_preset['title'])
                await update.message.reply_text(deleted_message)
                return
            except ValueError:
                invalid_number = get_translation(user_id, "invalid_preset_number")
                await update.message.reply_text(invalid_number)
                return
        if not context.args:
            keyboard_options = [
                [get_translation(user_id, "reset_to_default")],
                [get_translation(user_id, "save_as_preset"), get_translation(user_id, "show_presets")],
                [get_translation(user_id, "cancel")]
            ]
            reply_markup = {
                "keyboard": keyboard_options,
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
            customization_text = get_translation(user_id, "customization_start")
            await update.message.reply_text(
                customization_text,
                reply_markup=reply_markup
            )
            return
        new_persona = " ".join(context.args)
        user_memory["custom_persona"] = new_persona
        user_memory["active_preset"] = None
        if user_memory["messages"] and user_memory["messages"][0]["role"] == "system":
            user_memory["messages"][0]["content"] = new_persona
        update_user_stats(user_id, "customizations")
        save_data()
        keyboard_options = [
            [get_translation(user_id, "save_as_preset")],
            [get_translation(user_id, "skip")]
        ]
        reply_markup = {
            "keyboard": keyboard_options,
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
        personality_text = get_translation(user_id, "personality_customized", personality=new_persona)
        await update.message.reply_text(
            personality_text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in customize command: {e}")
        error_message = get_translation(user_id, "error_command")
        await update.message.reply_text(error_message)

async def handle_customization_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        user_memory = get_user_memory(user_id)
        
        reset_text = get_translation(user_id, "reset_to_default")
        save_preset_text = get_translation(user_id, "save_as_preset")
        show_presets_text = get_translation(user_id, "show_presets")
        skip_text = get_translation(user_id, "skip")
        cancel_text = get_translation(user_id, "cancel")
        
        if user_message == reset_text:
            default_persona = get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE))
            user_memory["custom_persona"] = default_persona
            user_memory["active_preset"] = None
            if user_memory["messages"] and user_memory["messages"][0]["role"] == "system":
                user_memory["messages"][0]["content"] = default_persona
            save_data()
            reset_message = get_translation(user_id, "reset_to_default")
            await update.message.reply_text(reset_message)
        elif user_message == save_preset_text:
            if not user_memory["custom_persona"] or user_memory["custom_persona"] == get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE)):
                no_customization = get_translation(user_id, "no_customization_to_save")
                await update.message.reply_text(no_customization)
                return
            if len(user_memory["presets"]) >= 10:
                max_presets = get_translation(user_id, "max_presets_reached")
                await update.message.reply_text(max_presets)
                return
            new_preset = {
                "id": len(user_memory["presets"]),
                "persona": user_memory["custom_persona"],
                "title": get_translation(user_id, "preset_title_default", number=len(user_memory['presets']) + 1),
                "created_at": datetime.now().isoformat()
            }
            user_memory["presets"].append(new_preset)
            update_user_stats(user_id, "presets_created")
            save_data()
            saved_message = get_translation(user_id, "customization_saved", title=new_preset['title'])
            await update.message.reply_text(saved_message)
        elif user_message == show_presets_text:
            if not user_memory["presets"]:
                no_presets = get_translation(user_id, "no_presets")
                await update.message.reply_text(no_presets)
                return
            presets_list = ""
            for i, preset in enumerate(user_memory["presets"]):
                active_indicator = " ✅" if user_memory.get("active_preset") == preset["id"] else ""
                presets_list += f"{i+1}. {preset['title']}{active_indicator}\n"
            presets_text = get_translation(user_id, "saved_presets", list=presets_list)
            await update.message.reply_text(presets_text)
        elif user_message == skip_text:
            skip_message = get_translation(user_id, "preset_save_skipped")
            await update.message.reply_text(skip_message)
        elif user_message == cancel_text:
            cancel_message = get_translation(user_id, "customization_cancelled")
            await update.message.reply_text(cancel_message)
        
        remove_keyboard = {"remove_keyboard": True}
        options_closed = get_translation(user_id, "customization_options_closed")
        await update.message.reply_text(options_closed, reply_markup=remove_keyboard)
    except Exception as e:
        logger.error(f"Error in handle_customization_choice: {e}")
        error_message = get_translation(user_id, "error_command")
        await update.message.reply_text(error_message)

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        if user_id not in user_stats:
            no_stats = get_translation(user_id, "no_stats")
            await update.message.reply_text(no_stats)
            return
        
        stats = user_stats[user_id]
        user_memory = get_user_memory(user_id)
        oldest_msg_days = 0
        if user_memory["messages"] and len(user_memory["messages"]) > 1:
            try:
                oldest_msg_time = min(
                    datetime.fromisoformat(msg["timestamp"]) 
                    for msg in user_memory["messages"] 
                    if "timestamp" in msg
                )
                oldest_msg_days = (datetime.now() - oldest_msg_time).days
            except:
                oldest_msg_days = 0
        
        custom_personality = "✅" if user_memory.get('custom_persona') != get_default_persona(user_memory.get("language", DEFAULT_LANGUAGE)) else "❌"
        
        stats_text = get_translation(user_id, "user_stats", 
            messages_sent=stats.get('messages_sent', 0),
            messages_received=stats.get('messages_received', 0),
            think=stats.get('think', 0),
            think_full=stats.get('think_full', 0),
            customizations=stats.get('customizations', 0),
            presets_created=stats.get('presets_created', 0),
            presets_used=stats.get('presets_used', 0),
            web_searches=stats.get('web_searches', 0),
            feedbacks_submitted=stats.get('feedbacks_submitted', 0),
            messages_saved=len(user_memory['messages']),
            oldest_days=max(1, oldest_msg_days),
            custom_personality=custom_personality,
            presets_count=len(user_memory.get('presets', []))
        )
        await update.message.reply_text(stats_text)
    except Exception as e:
        logger.error(f"Error in mystats command: {e}")
        error_message = get_translation(user_id, "error_showing_stats")
        await update.message.reply_text(error_message)

async def users_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        update_users_info()
        try:
            with open('users_info.json', 'r', encoding='utf-8') as f:
                users_info = json.load(f)
        except:
            users_info = {
                "awake_users": 0,
                "sleeping_users": 0,
                "dead_users": 0,
                "total_users": 0,
                "total_feedbacks": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        feedbacks_text = ""
        recent_feedbacks = users_info.get('recent_feedbacks', [])
        if recent_feedbacks:
            for i, feedback in enumerate(recent_feedbacks[:3]):
                user_id_short = feedback.get('user_id', '')[:8] + '...' if feedback.get('user_id') else 'Unknown'
                feedback_text = feedback.get('feedback', '')[:50] + '...' if len(feedback.get('feedback', '')) > 50 else feedback.get('feedback', '')
                feedbacks_text += f"\n{i+1}. User {user_id_short}: {feedback_text}"
        else:
            feedbacks_text = get_translation(user_id, "no_recent_feedbacks")
        
        last_updated = datetime.fromisoformat(users_info.get('last_updated', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M:%S')
        
        info_text = get_translation(user_id, "general_user_stats", 
            total_users=users_info.get('total_users', 0),
            awake_users=users_info.get('awake_users', 0),
            sleeping_users=users_info.get('sleeping_users', 0),
            dead_users=users_info.get('dead_users', 0),
            total_feedbacks=users_info.get('total_feedbacks', 0),
            last_updated=last_updated,
            feedbacks=feedbacks_text
        )
        await update.message.reply_text(info_text)
    except Exception as e:
        logger.error(f"Error in users_info command: {e}")
        error_message = get_translation(user_id, "error_showing_stats")
        await update.message.reply_text(error_message)

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_memory = get_user_memory(user_id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        if not context.args:
            await update.message.reply_text(get_translation(user_id, "enter_feedback_query"))
            return
        
        if user_memory.get("last_feedback"):
            last_feedback_time = datetime.fromisoformat(user_memory["last_feedback"])
            time_since_last = datetime.now() - last_feedback_time
            if time_since_last.days < 5:
                days_left = 5 - time_since_last.days
                waiting_message = get_translation(user_id, "feedback_waiting", days=days_left)
                await update.message.reply_text(waiting_message)
                return
        
        feedback_text = " ".join(context.args)
        user_feedbacks[user_id] = {
            "feedback": feedback_text,
            "timestamp": datetime.now().isoformat(),
            "username": update.effective_user.username or "Unknown",
            "first_name": update.effective_user.first_name or "Unknown"
        }
        user_memory["last_feedback"] = datetime.now().isoformat()
        update_user_stats(user_id, "feedbacks_submitted")
        save_data()
        feedback_sent = get_translation(user_id, "feedback_sent", days_left=5)
        await update.message.reply_text(feedback_sent)
    except Exception as e:
        logger.error(f"Error in feedback command: {e}")
        error_message = get_translation(user_id, "error_sending_feedback")
        await update.message.reply_text(error_message)

async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        credits_text = get_translation(user_id, "developer_info")
        await update.message.reply_text(credits_text)
    except Exception as e:
        logger.error(f"Error in credits command: {e}")
        error_message = get_translation(user_id, "error_showing_credits")
        await update.message.reply_text(error_message)

async def server_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        server_info = get_server_info()
        if not server_info:
            error_message = get_translation(user_id, "error_showing_server_info")
            await update.message.reply_text(error_message)
            return
        
        uptime = get_uptime()
        formatted_uptime = format_uptime(uptime)
        
        if bot_stats.get("downtime_start"):
            downtime_start = datetime.fromisoformat(bot_stats["downtime_start"])
            downtime = datetime.now() - downtime_start
            bot_status = get_translation(user_id, "bot_status_offline", duration=format_downtime(downtime))
        else:
            bot_status = get_translation(user_id, "bot_status_online")
        
        info_text = get_translation(user_id, "server_info",
            uptime=formatted_uptime,
            cpu_percent=server_info['cpu']['percent'],
            cpu_count=server_info['cpu']['count'],
            cpu_freq_current=server_info['cpu']['freq_current'],
            cpu_freq_max=server_info['cpu']['freq_max'],
            memory_total=server_info['memory']['total'],
            memory_used=server_info['memory']['used'],
            memory_percent=server_info['memory']['percent'],
            disk_total=server_info['disk']['total'],
            disk_used=server_info['disk']['used'],
            disk_percent=server_info['disk']['percent'],
            total_messages=bot_stats['total_messages_processed'],
            messages_today=bot_stats['messages_today'],
            messages_week=bot_stats['messages_week'],
            messages_month=bot_stats['messages_month'],
            users_today=len(bot_stats['users_today']),
            users_week=len(bot_stats['users_week']),
            users_month=len(bot_stats['users_month']),
            bot_status=bot_status
        )
        await update.message.reply_text(info_text)
    except Exception as e:
        logger.error(f"Error in server_info command: {e}")
        error_message = get_translation(user_id, "error_showing_server_info")
        await update.message.reply_text(error_message)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code):
    user_id = str(update.effective_user.id)
    user_memory = get_user_memory(user_id)
    
    if lang_code not in SUPPORTED_LANGUAGES:
        supported_codes = ", ".join(SUPPORTED_LANGUAGES.keys())
        error_message = get_translation(user_id, "unsupported_language", codes=supported_codes)
        await update.message.reply_text(error_message)
        return
    
    user_memory["language"] = lang_code
    default_persona = get_default_persona(lang_code)
    user_memory["custom_persona"] = default_persona
    if user_memory["messages"] and user_memory["messages"][0]["role"] == "system":
        user_memory["messages"][0]["content"] = default_persona
    
    save_data()
    
    language_name = SUPPORTED_LANGUAGES[lang_code]
    success_message = get_translation(user_id, "language_changed", language=language_name)
    await update.message.reply_text(success_message)

async def set_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "en")

async def set_spanish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "sp")

async def set_french(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "fr")

async def set_russian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "ru")

async def set_arabic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "ar")

async def set_bengali(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "bn")

async def set_hindi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "hi")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        user_memory = get_user_memory(user_id)
        if bot_stats.get("downtime_start"):
            downtime_start = datetime.fromisoformat(bot_stats["downtime_start"])
            downtime = datetime.now() - downtime_start
            duration_text = format_downtime(downtime)
            downtime_message = get_translation(user_id, "downtime_message", duration=duration_text)
            await update.message.reply_text(downtime_message)
            return
        
        if user_memory.get("show_cleanup_message"):
            deleted_count = user_memory.get("deleted_messages_count", 0)
            if deleted_count > 0:
                cleanup_message = get_translation(user_id, "cleanup_message", count=deleted_count)
                await update.message.reply_text(cleanup_message)
            user_memory["show_cleanup_message"] = False
            save_data()
        
        update_user_stats(user_id, "messages_received")
        update_bot_stats(1, user_id)
        
        reset_text = get_translation(user_id, "reset_to_default")
        save_preset_text = get_translation(user_id, "save_as_preset")
        show_presets_text = get_translation(user_id, "show_presets")
        skip_text = get_translation(user_id, "skip")
        cancel_text = get_translation(user_id, "cancel")
        
        if user_message in [reset_text, save_preset_text, show_presets_text, skip_text, cancel_text]:
            await handle_customization_choice(update, context)
            return
        
        user_memory["messages"].append({
            "role": "user", 
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        user_memory["last_active"] = datetime.now().isoformat()
        
        if len(user_memory["messages"]) > 100:
            system_message = user_memory["messages"][0]
            other_messages = user_memory["messages"][1:]
            user_memory["messages"] = [system_message] + other_messages[-99:]
        
        processed_messages = advanced_processing(
            [{k: v for k, v in msg.items() if k != "timestamp"} for msg in user_memory["messages"]],
            user_memory.get("custom_persona")
        )
        
        response = g4f.ChatCompletion.create(
            model="gpt-4o",
            provider=g4f.Provider.MetaAI,
            messages=processed_messages,
            stream=False,
        )
        cleaned_response = clean_response(response)
        
        user_memory["messages"].append({
            "role": "assistant", 
            "content": cleaned_response,
            "timestamp": datetime.now().isoformat()
        })
        
        await update.message.reply_text(cleaned_response)
        update_user_stats(user_id, "messages_sent")
        save_data()
        
        if len(user_memory["messages"]) % 10 == 0:
            cleanup_old_conversations()
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        user_id = str(update.effective_user.id)
        error_message = get_translation(user_id, "error_processing")
        await update.message.reply_text(error_message)

def cleanup_resources():
    try:
        import aiohttp
        if 'session' in globals():
            asyncio.get_event_loop().run_until_complete(session.close())
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def check_memory_usage():
    try:
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        if memory_usage > 500:
            logger.warning(f"High memory usage: {memory_usage:.2f}MB")
            import gc
            gc.collect()
            return True
    except Exception as e:
        logger.error(f"Memory check error: {e}")
    return False

async def main():
    atexit.register(cleanup_resources)
    load_data()
    try:
        cleanup_old_conversations()
    except Exception as e:
        logger.error(f"Error cleaning old conversations: {e}")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_memory))
    application.add_handler(CommandHandler("think", think_command))
    application.add_handler(CommandHandler("think_full", think_full_command))
    application.add_handler(CommandHandler("customize", customize_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("web", web_search_command))
    application.add_handler(CommandHandler("users_info", users_info_command))
    application.add_handler(CommandHandler("feedback", feedback_command))
    application.add_handler(CommandHandler("credits", credits_command))
    application.add_handler(CommandHandler("server_info", server_info_command))
    
    application.add_handler(CommandHandler("en", set_english))
    application.add_handler(CommandHandler("sp", set_spanish))
    application.add_handler(CommandHandler("fr", set_french))
    application.add_handler(CommandHandler("ru", set_russian))
    application.add_handler(CommandHandler("ar", set_arabic))
    application.add_handler(CommandHandler("bn", set_bengali))
    application.add_handler(CommandHandler("hi", set_hindi))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await application.initialize()
    
    asyncio.create_task(check_bot_status(application))
    
    await application.start()
    await application.updater.start_polling()
    
    print("Bot started successfully")
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        if sys.version_info < (3, 7):
            raise RuntimeError("This bot requires Python 3.7 or higher")
        
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Critical error starting bot: {e}", exc_info=True)
        print(f"Failed to start bot: {e}")
        sys.exit(1)
