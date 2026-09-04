import streamlit as st
import json
import os
import sys

# Принудительно устанавливаем UTF-8 для ввода/вывода, чтобы Windows не ругался на кириллицу
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from groq import Groq

# ... дальше ваш обычный код ...

# --- 1. НАСТРОЙКА ИИ (Groq) ---
GROQ_API_KEY = "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" 
client = Groq(api_key=GROQ_API_KEY)

# Используем 70b модель — она очень быстрая на Groq и отлично понимает грамматику
MODEL_NAME = "qwen/qwen3.8-27b"

# --- 2. ЛОГИКА ИИ (Генерация и Проверка) ---
def generate_sentences(level, count):
    """Сверхбыстрый генератор контекстных предложений через Groq."""
    prompt = f"""
    Сгенерируй {count} предложений на русском для перевода на немецкий.
    Сложность: {level}.
    Сделай фразы жизненными. Темы: покупки в EDEKA, Netto или Lidl, поездки по Deutschlandticket, бронирование на Airbnb, программирование на Python, занятия в Institut Rommel, поход в Cinecitta Multiplexkino.
    
    Верни строго JSON-объект с ключом 'sentences', который содержит список.
    Пример структуры:
    {{
      "sentences": [
        {{ "id": "1", "ru": "текст", "hint": "подсказка (макс 3 слова)" }}
      ]
    }}
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3 # Небольшая креативность для разнообразия предложений
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("sentences", []) # Возвращаем сам список из JSON-объекта
    except Exception as e:
        st.error(f"Ошибка генерации: {e}")
        return []

def check_translation(original, translation):
    """Оптимизированный чекер с минимальным промптом для Groq."""
    prompt = f"""
    Оригинал: {original}
    Перевод: {translation}
    
    Оцени перевод на немецкий. Верни строго JSON-объект:
    {{
      "perfect": boolean,
      "counts": {{"typos": 0, "wrong_word": 0, "grammar": 0, "article_gender": 0}},
      "details": {{"typos": [], "wrong_word": [], "grammar": [], "article_gender": []}}
    }}
    Пояснения в массивах 'details' пиши на русском, в 3-5 слов максимум.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1 # Минимум креативности для строгой проверки
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"perfect": False, "counts": {}, "details": {}, "error": str(e)}

# --- 3. ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
st.set_page_config(page_title="Тренажер перевода", layout="centered")
st.title("📚 Умный тренажер перевода")

# Инициализация переменных сессии
if 'sentences' not in st.session_state:
    st.session_state.sentences = []
if 'check_results' not in st.session_state:
    st.session_state.check_results = {}

# --- БОКОВАЯ ПАНЕЛЬ: НАСТРОЙКИ ГЕНЕРАЦИИ ---
with st.sidebar:
    st.header("Настройки генерации")
    # Тонкая настройка уровней, как вы и хотели
    difficulty = st.selectbox(
        "Выберите уровень:", 
        [
            "A1 (Основы)", 
            "A2 (Базовый)", 
            "B1 (Легкий - простые предложения)", 
            "B1 (Стандартный)", 
            "B1 (Сложный - придаточные предложения, сложные союзы)", 
            "B2 (Продвинутый)"
        ]
    )
    num_sentences = st.slider("Количество предложений:", min_value=1, max_value=5, value=3)
    
    if st.button("Сгенерировать новые предложения", type="primary"):
        with st.spinner("ИИ придумывает предложения..."):
            st.session_state.sentences = generate_sentences(difficulty, num_sentences)
            # Очищаем старые результаты при новой генерации
            st.session_state.check_results = {}

# --- ОСНОВНАЯ ОБЛАСТЬ: ЯЧЕЙКИ НОУТБУКА ---
if not st.session_state.sentences:
    st.info("👈 Выберите уровень в боковом меню слева и нажмите 'Сгенерировать'.")
else:
    for index, item in enumerate(st.session_state.sentences):
        with st.container(border=True):
            st.markdown(f"**Предложение {index + 1}:** {item['ru']}")
            st.caption(f"💡 {item.get('hint', '')}")
            
            input_key = f"input_{item['id']}"
            btn_key = f"btn_{item['id']}"
            
            user_text = st.text_input("Ваш перевод на немецкий:", key=input_key)
            
            if st.button("Проверить", key=btn_key):
                if user_text.strip():
                    with st.spinner("Анализирую..."):
                        result = check_translation(item['ru'], user_text)
                        st.session_state.check_results[item['id']] = result
                else:
                    st.warning("Введите текст!")
            
            # --- ВЫВОД РЕЗУЛЬТАТОВ С КАТЕГОРИЯМИ ---
            if item['id'] in st.session_state.check_results:
                res = st.session_state.check_results[item['id']]
                
                if res.get('error'):
                    st.error("Произошла ошибка при анализе.")
                elif res.get('perfect'):
                    st.success("🎉 Идеально! Ошибок нет.")
                else:
                    counts = res['counts']
                    details = res['details']
                    
                    st.error("В переводе есть недочеты.")
                    
                    # Красиво выводим количество ошибок по категориям (в одну линию)
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Опечатки", counts.get('typos', 0))
                    col2.metric("Лексика", counts.get('wrong_word', 0))
                    col3.metric("Грамматика", counts.get('grammar', 0))
                    col4.metric("Артикли/Род", counts.get('article_gender', 0))
                    
                    # Скрываемый блок (expander), который можно "клацнуть"
                    with st.expander("Посмотреть подробный разбор ошибок", expanded=False):
                        if counts.get('typos', 0) > 0:
                            st.markdown("**🔤 Опечатки:**")
                            for msg in details.get('typos', []): st.write(f"- {msg}")
                            
                        if counts.get('wrong_word', 0) > 0:
                            st.markdown("**📚 Лексика (не то слово):**")
                            for msg in details.get('wrong_word', []): st.write(f"- {msg}")
                            
                        if counts.get('grammar', 0) > 0:
                            st.markdown("**⚙️ Грамматика (структура, глаголы):**")
                            for msg in details.get('grammar', []): st.write(f"- {msg}")
                            
                        if counts.get('article_gender', 0) > 0:
                            st.markdown("**🎭 Артикли и Род:**")
                            for msg in details.get('article_gender', []): st.write(f"- {msg}")