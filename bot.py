import os
import sys
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
sys.modules['google._upb._message'] = None
import logging
import telebot
from dotenv import load_dotenv
import google.generativeai as genai

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

if TELEGRAM_TOKEN:
    # Инициализация бота
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
else:
    bot = None

# Настройка Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
  "temperature": 0.7,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

SYSTEM_PROMPT = """
Ты — вежливый, дружелюбный и умный виртуальный ассистент образовательной академии «21 Талант». Твоя цель — консультировать родителей по программам, расписанию и ценам, опираясь строго на предоставленную ниже информацию. отвечай вежливо, с эмодзи.

ИНФОРМАЦИЯ ОБ АКАДЕМИИ:
Вас приветствует образовательная академия «21 Талант»! Помогаем детям развиваться, учиться с интересом и уверенно осваивать новые навыки.

Направления для детей от 3 лет:
- Подготовка к школе
- Комплексное развитие
- Экспресс-подготовка к школе
- Скорочтение
- Английский язык
- Казахский язык
- Китайский язык
- Творчество
- Танцы
- Спортивные направления
- Продлёнка для 1–4 классов
- Математика, физика, химия (если спрашивают про точные науки)

График работы: Пн–Сб, 09:00–20:00. После 20:00 заявки обрабатываются на следующий рабочий день.

КОМПЛЕКСНОЕ РАЗВИТИЕ (4-5 и 5-6 лет):
- 3 раза в неделю по 2 часа (пон-ср-пят 9:00-11:00, 11:15-13:15, 14:00-16:00).
- Программа: чтение, математика, логика, графомоторика, развитие речи, окружающий мир, творчество, игры на внимание/память, элементы критического мышления.
- Стоимость: 50.000 тг (12 занятий по 2 часа).
- Канцтовары бесплатно, рабочие тетради покупаются один раз.

ПРОДЛЕНКА (1-4 классы, до 8 человек в группе):
1) 2 часа в день — 50.000 тг. Время: 09:00-11:00, 14:00-16:00, 16:00-18:00. Программа: все предметы, кроме англ. и каз. языков.
2) 4 часа в день — 85.000 тг. Время: 09:00-13:00, 14:00-18:00. Программа: все предметы + 1 курс (каз. язык 2 раза в неделю), сопровождение до/после школы. Скидка 50% на доп. курс.
3) 7 часов в день — 95.000 тг. Время: 11:00-18:00. Программа: все предметы + 2 курса (каз. язык и скорочтение по 2 раза в неделю), сопровождение после школы. Скидка 50% на доп. курс.

КОНТАКТЫ И АДРЕС:
- Адрес: Казахфильм 21/8, 2 этаж, вход с торца здания.
- Телефоны: +7 705 888 2124, +7 776 270 4343, +7 707 995 6795
- Instagram: @21talant_

ПРАВИЛО ОБЩЕНИЯ: 
Если клиент пишет в первый раз, спроси: "1️⃣ Возраст ребёнка 2️⃣ Какое направление вас интересует?". Затем предложи подходящие варианты.
"""

if GEMINI_API_KEY:
    model = genai.GenerativeModel(model_name="gemini-3.5-flash", 
                                  system_instruction=SYSTEM_PROMPT,
                                  generation_config=generation_config)
else:
    model = None

# Хранение истории чатов (в памяти для простоты)
user_sessions = {}

if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        welcome_text = (
            "Здравствуйте! 🌷\n"
            "Вас приветствует образовательная академия «21 Талант»!\n\n"
            "Чтобы подобрать для вас подходящую программу, напишите, пожалуйста:\n"
            "1️⃣ Возраст ребёнка\n"
            "2️⃣ Какое направление вас интересует?"
        )
        if model:
            user_sessions[message.from_user.id] = model.start_chat(history=[])
        bot.reply_to(message, welcome_text)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        user_id = message.from_user.id
        
        if not model:
            bot.reply_to(message, "Ошибка: Не настроен Gemini API. Проверьте .env файл.")
            return

        # Если сессии нет, создаем ее
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])
            
        chat_session = user_sessions[user_id]
        
        # Показываем статус "печатает..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        try:
            # Отправляем сообщение в Gemini и получаем ответ
            response = chat_session.send_message(message.text)
            bot.reply_to(message, response.text)
        except Exception as e:
            logging.error(f"Error communicating with Gemini: {e}")
            bot.reply_to(message, "Извините, сейчас я не могу ответить. Пожалуйста, попробуйте позже или позвоните нам по номерам: +7 705 888 2124.")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logging.error("Токены не найдены! Проверьте файл .env перед запуском.")
    else:
        logging.info("Бот запущен...")
        bot.infinity_polling()
