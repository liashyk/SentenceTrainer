import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. НАСТРОЙКА ИИ ---
# Вставьте сюда свой ключ из Google AI Studio
API_KEY = "AQ.Ab8RN6Lv_Vx9SEzXoQe5mVLaUHlV_pRnNKr5XFrylBKyg-HbkA" 
genai.configure(api_key=API_KEY)

# Используем JSON-режим для гарантии структуры ответа
model = genai.GenerativeModel('gemini-3.6-flash', generation_config={"response_mime_type": "application/json"})

# --- 2. ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data(filepath):
    """Загружает JSON файл. Кэшируется, чтобы не читать диск при каждом клике."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_translation_with_ai(original, translation):
    """Отправляет запрос к Gemini API."""
    prompt = f"""
    Ты строгий преподаватель немецкого языка. Пользователь переводит предложение.
    Оригинал: {original}
    Перевод студента: {translation}
    Проверь грамматику, лексику и правильность слияния предлогов с артиклями.
    Верни ответ строго в формате JSON с ключами 'error_count' (целое число) и 'explanation' (строка с пояснением на русском).
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"error_count": -1, "explanation": f"Ошибка подключения к ИИ: {e}"}

# --- 3. ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
st.set_page_config(page_title="Тренажер перевода", layout="centered")
st.title("📚 Тренажер перевода")
st.markdown("Переводите предложения ячейка за ячейкой. Ваши результаты сохраняются на странице.")

# Загружаем список предложений
try:
    sentences = load_data("sentences.json")
except FileNotFoundError:
    st.error("Файл sentences.json не найден. Пожалуйста, создайте его в той же папке.")
    st.stop()

# Инициализация хранилища сессии (чтобы результаты проверок не стирались)
if 'check_results' not in st.session_state:
    st.session_state.check_results = {}

# --- 4. ГЕНЕРАЦИЯ "ЯЧЕЕК" НОУТБУКА ---
for index, item in enumerate(sentences):
    # st.container(border=True) визуально выделяет ячейку рамкой (доступно в новых версиях Streamlit)
    with st.container(border=True):
        st.markdown(f"**Предложение {index + 1}:** {item['ru']}")
        
        # Если в JSON есть подсказка, показываем ее
        if "hint" in item:
            st.caption(f"💡 Подсказка: {item['hint']}")
        
        # Уникальные ключи (key) обязательны, чтобы Streamlit различал поля ввода
        input_key = f"input_{item['id']}"
        btn_key = f"btn_{item['id']}"
        
        user_text = st.text_input("Ваш перевод:", key=input_key)
        
        # Кнопка проверки
        if st.button("Проверить", key=btn_key):
            if user_text.strip():
                with st.spinner("Проверяю..."):
                    # Получаем ответ от ИИ и сохраняем его в session_state по ID предложения
                    result = check_translation_with_ai(item['ru'], user_text)
                    st.session_state.check_results[item['id']] = result
            else:
                st.warning("Сначала введите текст перевода!")
        
        # --- 5. ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА ---
        # Проверяем, есть ли уже сохраненный результат для этой ячейки
        if item['id'] in st.session_state.check_results:
            res = st.session_state.check_results[item['id']]
            
            # Оформляем вывод в зависимости от количества ошибок
            if res['error_count'] == 0:
                st.success("🎉 Идеально! Ошибок: 0")
                if res.get('explanation'):
                    st.info(res['explanation'])
            elif res['error_count'] > 0:
                st.error(f"❌ Ошибок найдено: {res['error_count']}")
                st.warning(res['explanation'])
            else:
                # На случай сбоя API
                st.error(res['explanation'])