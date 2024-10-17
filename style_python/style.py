import streamlit as st
import time

def style_python():
    ###стили
    st.markdown(
        """
    <style>
        /* Основные стили */
        .css-18e3th9 {
            background-color: #ffffff;
            color: #000000;
            font-weight: 800;
        }

        /* Стили заголовков */
        h1, h2, h4, h5, h6 {
            color: #000000;
        }

        /* Стили кнопок */
        .stButton>button {
            background-color: #ffffff;
            color: #000000;
            border-radius: 8px;
            padding: 8px 20px;
            border: 1px solid  #000000;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #b5d3ec;
        }

        /* Стили текста ввода */
        .stTextInput>div>div>input {
            border-radius: 5px;
            background-color: #b5d3ec;
        }

        /* Стили select box */
        .stSelectbox>div>div>div>div>div {
            border: 1px solid  #000000;
            border-radius: 5px;
        }

        /* Стили для DataFrame */
        .dataframe {
            border: 1px solid  #000000;
            border-radius: 5px;
        }
        .dataframe th {
            background-color: #4691ce;
            color: #ffffff;
        }
        .dataframe td {
            background-color: #ffffff;
            color: #000000;
        }

        /* Стили заголовков секций */
        .css-1d391kg p {
            color: #4985c1;
            font-size: 20px;
            font-weight: bold;
        }

        /* Стили slider */
        .stSlider>div>div>div {
            color: #4691ce;
            border: 1px solid  #000000;
        }

        /* Стили checkbox */
        .stCheckbox>div>div {
            background-color: #4985c1;
            border-radius: 4px;
        }

        /* Отключение теней */
        .reportview-container .main .block-container {
            box-shadow: none;
        }

        #загрузчик
        #след строка странная конструкция, непонятно вообще почему это так работает
        [data-testid="stFileUploaderDropzoneInstructions"] div::before {color:black; font-size: 0.9em; content:"Загрузите или перетяните файлы сюда"}
        [data-testid="stFileUploaderDropzoneInstructions"] div span{display:none;}
        [data-testid="stFileUploaderDropzoneInstructions"] div::after {color:black; font-size: .8em; content:"Загрузите файлы, перетянув их сюда или щелкнув для выбора.\AЛимит 200MB на файл";white-space: pre; /* Для переноса строки */}
        [data-testid="stFileUploaderDropzoneInstructions"] div small{display:none;}
        [data-testid="stFileUploaderDropzoneInstructions"] button{display:flex;width: 30%; padding: 0px;}
        [data-testid="stFileUploaderDropzone"]{background-color:white; border-radius: 15px; /* Скругленные углы */border: 2px solid #4985c1; /* Прозрачная граница для эффекта */}
        [data-testid="stExpander"]{border-radius: 15px; border: 2px solid #4985c1;}
        [data-testid="stButton-secondary"]{border-radius: 15px; border: 2px solid #4985c1;}
        
        [data-testid="stDateInputField"]{background-color:white; border-radius: 7px; border: 1px solid #4985c1;}
        [role="presentation"] {
          background-color:white;
        }
        [aria-live="polite"] {
          background-color:white;
          border-radius: 5px;
        }
        
        [kind="secondary"] {
          border-radius: 15px; 
          border: 2px solid #4985c1;
        }

        .stButton>button{border-radius: 15px; border: 2px solid #4985c1;}

        [data-testid="stCaptionContainer"] {color:white;}
        
        [class="st-emotion-cache-m1sdux ef3psqc12"] {background-color:white; border: 2px solid white;}
        
        [class="element-container st-emotion-cache-1bnixg8 e1f1d6gn4"] {color:white}

        [data-testid="stHeaderActionElements"] {display:none;}

        h4 {
           color: white;
        }

        [class="st-ak st-al st-bd st-be st-bf st-as st-bg st-bh st-ar st-bi st-bj st-bk st-bl"] {background-color:white;}

        .st-cv {
            background-color:white;
        }
        
        .custom-success {
            background-color:#dcf3fc;
            color: blue;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #dcf3fc;
            font-size: 16px;
            margin-bottom: 15px;
        }

        .custom-alert {
            background-color:#f1fab4;
            color: #c29b3a;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #f1fab4;
            font-size: 16px;
            margin-bottom: 15px;
        }
     
    </style>
    """,
        unsafe_allow_html=True,
    )

def custom_success(text):
    # Использование кастомного стиля для успеха
    st.markdown(f'<div class="custom-success">{text}</div>', unsafe_allow_html=True)

def custom_alert(text):
    # Использование кастомного стиля для alert
    st.markdown(f'<div class="custom-alert">{text}</div>', unsafe_allow_html=True)