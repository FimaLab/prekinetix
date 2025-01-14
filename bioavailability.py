###### Подключение пакетов
import streamlit as st

#предварительный просмотр общего доступа
st.set_page_config(page_title="Доклинические исследования", page_icon="favicon.png", layout="centered", initial_sidebar_state="auto", menu_items=None)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import math
import statistics  
import seaborn as sns
import statsmodels.api as sm
import streamlit.components as stc
from pyxlsb import open_workbook as open_xlsb
import os
from cycler import cycler
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components 
import codecs
from utils.functions import *
from utils.radio_unit import *
from style_python.style import *


with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#применение стилей python
style_python()

####### Главное меню

st.sidebar.image("logo-new.png", width=110)

####### Левое боковое меню

st.sidebar.markdown('<h3 style="color:white; padding-bottom: 0; padding-left: 5px;">Выберите вид исследования</h3>', unsafe_allow_html=True)

option = st.sidebar.selectbox('',
    ('Фармакокинетика','Биодоступность', 'Распределение по органам', 'Линейность дозирования','Экскреция препарата'),disabled = False, key = "Вид исследования")

############### файл пример

df_example_file = pd.read_excel("server_example_file.xlsx")
df_example_file_xlsx = to_excel(df_example_file)
st.sidebar.download_button(label='Примеры файлов 🗂️', data=df_example_file_xlsx , file_name= 'example_file.xlsx')

############ памятка

text_contents = '''1)Оглавлять колонку с номерами животных должно слово «Номер» (в верхнем регистре).
2)Знак «№» обязательно должен присутствовать при указании номера животного, иначе приложение выдаст ошибку. 
3) Не ставить в ячейки знак «-» в случае нулевого значения. Ставить число «0» для корректной работы приложения.
4)Ни в каком исследовании загружаемые файлы не должны называться одинаково.
'''
st.sidebar.download_button('Инструкция по заполнению 📝', text_contents)

#Инизиализация состояния фреймов с результатами исследований
if "df_total_PK_pk" not in st.session_state:
    st.session_state["df_total_PK_pk"] = None

if 'df_total_PK_org' not in st.session_state:
    st.session_state['df_total_PK_org'] = None

if 'df_total_PK_lin' not in st.session_state:
    st.session_state['df_total_PK_lin'] = None

if 'df_total_PK_iv' not in st.session_state:
    st.session_state["df_total_PK_iv"] = None

if 'df_total_PK_po_sub' not in st.session_state:
    st.session_state['df_total_PK_po_sub'] = None

if 'df_total_PK_po_rdf' not in st.session_state:
    st.session_state['df_total_PK_po_rdf'] = None

if 'df1_model_lin' not in st.session_state:
    st.session_state['df1_model_lin'] = 1

if 'df2_model_lin' not in st.session_state:
    st.session_state['df2_model_lin'] = 1

################################
if option == 'Фармакокинетика':

    st.header('Расчет фармакокинетических параметров')

    col1, col2 = st.columns([0.66, 0.34])
   
    ####### основной экран
    with col1:
        
        panel = st.radio(
            "⚙️Панель управления",
            ("Загрузка файлов", "Таблицы","Графики"),
            horizontal=True, key= "Загрузка файлов - Расчет фармакокинетических параметров"
        )
      
        if "dose_pk" not in st.session_state:
           st.session_state["dose_pk"] = ""
        
        #cписки для word-отчета
        list_heading_word=[]
        list_table_word=[]
        list_graphics_word=[]
        list_heading_graphics_word=[]

        if panel == "Загрузка файлов":
           
           ######### боковое меню справа
           with col2:
                
                selected = option_menu(None, ["Настройка дополнительных параметров"], 
                   icons=['menu-button'], 
                   menu_icon="cast", default_index=0, orientation="vertical",
                   styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                   })

                if selected == "Настройка дополнительных параметров":
                   type_parameter = st.selectbox('Выберите параметр',
                   ("Вид введения",'Двойные пики'),disabled = False, key = "Вид параметра - фк")
                   
                if "agree_cmax2 - фк" not in st.session_state:
                      st.session_state["agree_cmax2 - фк"] = False

                if type_parameter == 'Двойные пики':

                   st.session_state["agree_cmax2 - фк"] = st.checkbox('В зависимости "Концентрация-Время" отчетливо наблюдаются двойные пики', key = "Возможность добавления Cmax2 - фк", value = st.session_state["agree_cmax2 - фк"])
                   
                   if st.session_state["agree_cmax2 - фк"] == True:
                      custom_success('Параметр добавлен!')

                if "agree_injection - фк" not in st.session_state:
                      st.session_state["agree_injection - фк"] = False

                if type_parameter == "Вид введения":

                   # Проверка наличия значения в сессии, если его нет, устанавливаем значение по умолчанию
                   if "injection_choice - фк" not in st.session_state:
                       st.session_state["injection_choice - фк"] = 0  # Значение по умолчанию

                   # Радиокнопка для выбора типа введения
                   injection_type = st.radio(
                       "Выберите тип введения:",
                       options=["Внутривенное введение", "Внесосудистое введение"],
                       index=st.session_state["injection_choice - фк"],
                       key="injection_choice_фк",  # Ключ для сохранения выбора в сессии
                   )

                   # Логика для обновления состояния сессии
                   if injection_type == "Внутривенное введение":
                       st.session_state["agree_injection - фк"] = True
                       st.session_state["injection_choice - фк"] = 0
                   else:
                       st.session_state["agree_injection - фк"] = False
                       st.session_state["injection_choice - фк"] = 1

                   # Сообщение в зависимости от выбора
                   if st.session_state["agree_injection - фк"]:
                       custom_success("Выбрано: Внутривенное введение!")
                   else:
                       custom_success("Выбрано: Внесосудистое введение!")

           measure_unit_pk_time  = select_time_unit("фк")
           measure_unit_pk_concentration  = select_concentration_unit("фк")
           measure_unit_pk_dose  = select_dose_unit("фк")


           #cостояние радио-кнопки "method_auc"
           if "index_method_auc - фк" not in st.session_state:
               st.session_state["index_method_auc - фк"] = 0

           method_auc = st.radio("📈 Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = "Метод подсчёта AUC и AUMC - фк", index = st.session_state["index_method_auc - фк"])
           
           if st.session_state["Метод подсчёта AUC и AUMC - фк"] == 'linear':
              st.session_state["index_method_auc - фк"] = 0
           if st.session_state["Метод подсчёта AUC и AUMC - фк"] == "linear-up/log-down":
              st.session_state["index_method_auc - фк"] = 1
                        
           uploaded_file_pk = st.file_uploader("Выбрать файл концентраций ЛС (формат XLSX)", key='Файл введения ЛС при расчете фк')
           
           #сохранение файла
           if uploaded_file_pk is not None:
              save_uploadedfile(uploaded_file_pk)
              st.session_state["uploaded_file_pk"] = uploaded_file_pk.name

           if 'uploaded_file_pk' in st.session_state:
              custom_success(f"Файл загружен: {st.session_state['uploaded_file_pk']}")
              

           dose_pk = st.text_input("Доза при введении ЛС", key='Доза при введении ЛС при при расчете фк', value = st.session_state["dose_pk"])
           
           st.session_state["dose_pk"] = dose_pk
           
           if "uploaded_file_pk" in st.session_state and dose_pk and measure_unit_pk_concentration:

              df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_pk"]))
              st.subheader('Индивидуальные значения концентраций в крови после введения ЛС')
              
              ###интерактивная таблица
              df = edit_frame(df,st.session_state["uploaded_file_pk"])

              ###количество животных 
              count_rows_number_pk= len(df.axes[0])
        
              table_heading='Индивидуальные и усредненные значения концентраций в крови после введения ЛС'
              list_heading_word.append(table_heading)

              ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
              df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']
              
              list_table_word.append(df_concat_round_str_transpose)
              
           ########### графики    

           ######индивидуальные    

              # в линейных координатах
              col_mapping = df.columns.tolist()
              col_mapping.remove('Номер')

              count_row_df = len(df.axes[0])

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)
              
              #if st.session_state["agree_injection - фк"] == True: 
                 #list_time.remove(0)

              for r in range(0,count_row_df):

                  list_concentration=df.iloc[r].tolist()

                  numer_animal=list_concentration[0]

                  list_concentration.pop(0) #удаление номера животного

                  list_concentration = [float(v) for v in list_concentration]

                  #if st.session_state["agree_injection - фк"] == True:
                     #list_concentration.remove(0)


                  fig, ax = plt.subplots()
                  plt.plot(list_time,list_concentration,marker='o',markersize=4.0, color = "black", markeredgecolor="black",markerfacecolor="black")
                  plt.xlabel(f"Время, {measure_unit_pk_time}")
                  plt.ylabel("Концентрация, "+measure_unit_pk_concentration)
                 
                  list_graphics_word.append(fig)  

                  graphic='График индивидуального фармакокинетического профиля в крови (в линейных координатах) после введения ЛС,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

               #в полулогарифмических координатах методом удаления точек
                  count_for_0_1=len(list_concentration)
                  list_range_for_0_1=range(0,count_for_0_1)

                  list_time_0=[]
                  list_for_log_1=[]
                  for i in list_range_for_0_1:
                      if list_concentration[i] !=0:
                         list_for_log_1.append(list_concentration[i])
                         list_time_0.append(list_time[i]) 

                  fig, ax = plt.subplots()
                  plt.plot(list_time_0,list_for_log_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  ax.set_yscale("log")
                  plt.xlabel(f"Время, {measure_unit_pk_time}")
                  plt.ylabel("Концентрация, "+measure_unit_pk_concentration)

                  list_graphics_word.append(fig) 

                  graphic='График индивидуального фармакокинетического профиля в крови (в полулогарифмических координатах) после введения ЛС,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

           # объединенные индивидуальные в линейных координатах

              df_for_plot_conc=df.drop(['Номер'], axis=1)
              df_for_plot_conc_1 = df_for_plot_conc.transpose()

              if st.session_state["agree_injection - фк"] == True:
                 df_for_plot_conc_1=df_for_plot_conc_1.replace(0, None) ###т.к. внутривенное

              list_numer_animal_for_plot=df['Номер'].tolist()
              count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

              list_color = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]

              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_pk_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_pk_concentration)
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))

              list_graphics_word.append(fig) 

              graphic="Сравнение индивидуальных фармакокинетических профилей (в линейных координатах) после введения ЛС"
              list_heading_graphics_word.append(graphic)    
           # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
              df_for_plot_conc_1_log=df_for_plot_conc_1.replace(0, None)

              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1_log,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_pk_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_pk_concentration)
              ax.set_yscale("log")
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))

              list_graphics_word.append(fig) 
       
              graphic="Сравнение индивидуальных фармакокинетических профилей (в полулогарифмических координатах) после введения ЛС"
              list_heading_graphics_word.append(graphic) 

           ### усреденные    
           #в линейных    

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              df_averaged_concentrations=df.describe()
              list_concentration=df_averaged_concentrations.loc['mean'].tolist()
              err_y_pk=df_averaged_concentrations.loc['std'].tolist()
              
              #if st.session_state["agree_injection - фк"] == True:
                 #list_time.remove(0) ###т.к. внутривенное
                 #list_concentration.remove(0)
                 #err_y_pk.remove(0)

              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_pk, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              plt.xlabel(f"Время, {measure_unit_pk_time}")
              plt.ylabel("Концентрация, "+measure_unit_pk_concentration)

              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в линейных координатах) после введения ЛС'
              list_heading_graphics_word.append(graphic)  

           #в полулогарифмических координатах
              #if st.session_state["agree_injection - фк"] == False:
                 #list_time.remove(0) ###т.к. внутривенное
                 #list_concentration.remove(0)
                 #err_y_pk.remove(0) 


              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_pk, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              ax.set_yscale("log")
              plt.xlabel(f"Время, {measure_unit_pk_time}")
              plt.ylabel("Концентрация, "+measure_unit_pk_concentration)

              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в полулогарифмических координатах) после введения ЛС'
              list_heading_graphics_word.append(graphic)

              ############ Параметры ФК
              if st.session_state["agree_injection - фк"] == False:
                  result_PK = pk_parametrs_total_extravascular(df,"фк",method_auc,dose_pk,measure_unit_pk_concentration,measure_unit_pk_time,measure_unit_pk_dose)
              else:
                  result_PK = pk_parametrs_total_intravenously(df,"фк",method_auc,dose_pk,measure_unit_pk_concentration,measure_unit_pk_time,measure_unit_pk_dose)
              
              
              if result_PK is not None:
                  if st.session_state["agree_cmax2 - фк"] == False:
                     df_total_PK_pk = result_PK["df_total_PK"]
                  if st.session_state["agree_cmax2 - фк"] == True:
                     df_total_PK_pk = result_PK["df_total_PK"]
                     df_total_PK_additional_double_peaks_pk = result_PK["df_total_PK_additional_double_peaks"]
                  
                  st.session_state["df_total_PK_pk"] = df_total_PK_pk

                  table_heading='Фармакокинетические показатели в крови после введения ЛС'
                  list_heading_word.append(table_heading)
                  
                  list_table_word.append(df_total_PK_pk)

                  if st.session_state["agree_cmax2 - фк"] == True:
                     table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле'
                     list_heading_word.append(table_heading)
                     
                     list_table_word.append(df_total_PK_additional_double_peaks_pk)
              else:
                  st.session_state["df_total_PK_pk"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                  st.error("Выберете необходимое количество значений Cmax и Cmax(2)")

           else:
               st.write("")
           ###сохранение состояния 
           st.session_state["list_heading_word"] = list_heading_word
           st.session_state["list_table_word"] = list_table_word
           st.session_state["list_graphics_word"] = list_graphics_word
           st.session_state["list_heading_graphics_word"] = list_heading_graphics_word
          
    #отдельная панель, чтобы уменьшить размер вывода результатов

    col1, col2 = st.columns([0.66,0.34])
    
    with col1:
     
       #####Создание word отчета
       if panel == "Таблицы":
          if st.session_state["df_total_PK_pk"] is not None:
             
             list_heading_word = st.session_state["list_heading_word"]
             list_table_word = st.session_state["list_table_word"]

             ###вызов функции визуализации таблиц
             visualize_table(list_heading_word,list_table_word)


             with col2:
                  
                  selected = option_menu(None, ["Cформированный отчeт"], 
                  icons=['file-earmark-arrow-down-fill'], 
                  menu_icon="cast", default_index=0, orientation="vertical",
                  styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                  })

                  if selected == "Cформированный отчeт":

                     ###вызов функции создания Word-отчета таблиц
                         create_table(list_heading_word,list_table_word)
          else:
             st.error("Введите и загрузите все необходимые данные!")

       if panel == "Графики":
          if st.session_state["df_total_PK_pk"] is not None:
             list_graphics_word = st.session_state["list_graphics_word"]
             list_heading_graphics_word = st.session_state["list_heading_graphics_word"]
             
             #######визуализация

             #классификация графиков по кнопкам
             type_graphics = st.selectbox('Выберите вид графиков',
       ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля'),disabled = False, key = "Вид графика - фк" )

             count_graphics_for_visual = len(list_heading_graphics_word)
             list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)
             
             for i in list_range_count_graphics_for_visual:
                 if list_heading_graphics_word[i].__contains__("индивидуального"): 
                    if type_graphics == 'Индивидуальные фармакокинетические профили':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])
                 if list_heading_graphics_word[i].__contains__("Сравнение индивидуальных"):   
                    if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])
                 if list_heading_graphics_word[i].__contains__("усредненного"):
                    if type_graphics == 'Графики усредненного фармакокинетического профиля':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])

             with col2:
                  
                  selected = option_menu(None, ["Cформированный отчeт"], 
                  icons=['file-earmark-arrow-down-fill'], 
                  menu_icon="cast", default_index=0, orientation="vertical",
                  styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                  })
                   
                  if selected == "Cформированный отчeт":
                     ###вызов функции создания Word-отчета графиков
                     create_graphic(list_graphics_word,list_heading_graphics_word) 
          else:
              st.error("Введите и загрузите все необходимые данные!")
######################################################################################################################################

if option == 'Биодоступность':
    
    st.header('Изучение абсолютной и относительной биодоступности препарата')

    col1, col2 = st.columns([0.66, 0.34])
    
    ####### основной экран
    with col1:
        
        panel = st.radio(
            "⚙️Панель управления",
            ("Загрузка файлов", "Таблицы","Графики"),
            horizontal=True, key= "Загрузка файлов - Изучение абсолютной и относительной биодоступности препарата"
        )

        ###создание состояния
        if "dose_iv" not in st.session_state:
           st.session_state["dose_iv"] = ""
        if "dose_po_sub" not in st.session_state:   
           st.session_state["dose_po_sub"] = ""
        if "dose_po_rdf" not in st.session_state:   
           st.session_state["dose_po_rdf"] = ""
           
        #cписки для word-отчета
        list_heading_word=[]
        list_table_word=[]
        list_graphics_word=[]
        list_heading_graphics_word=[]

        if panel == "Загрузка файлов":
           
           ######### боковое меню справа
           with col2:
                 
                 selected = option_menu(None, ["Настройка дополнительных параметров"], 
                    icons=['menu-button'], 
                    menu_icon="cast", default_index=0, orientation="vertical",
                    styles={
                      "container": {"padding": "0!important", "background-color": "#1f3b57"},
                      "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                      "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                      "nav-link-selected": {"background-color": "#73b5f2"},
                    })

                 if selected == "Настройка дополнительных параметров":
                    type_parameter = st.selectbox('Выберите параметр',
                    (['Двойные пики']),disabled = False, key = "Вид параметра - ИБ")
                    
                 
                 if "agree_cmax2 - ИБ" not in st.session_state:
                       st.session_state["agree_cmax2 - ИБ"] = False
                 
                 if "agree_cmax2 - ИБ_iv" not in st.session_state:
                       st.session_state["agree_cmax2 - ИБ_iv"] = False

                 if "agree_cmax2 - ИБ_po_sub" not in st.session_state:
                       st.session_state["agree_cmax2 - ИБ_po_sub"] = False

                 if "agree_cmax2 - ИБ_po_rdf" not in st.session_state:
                       st.session_state["agree_cmax2 - ИБ_po_rdf"] = False

                 if type_parameter == 'Двойные пики':
                    
                    st.session_state["agree_cmax2 - ИБ"] = st.checkbox('В зависимости "Концентрация-Время" отчетливо наблюдаются двойные пики', key = "Возможность добавления Cmax2 - ИБ", value = st.session_state["agree_cmax2 - ИБ"])
                    
                    if st.session_state["agree_cmax2 - ИБ"] == True:
                       st.session_state["agree_cmax2 - ИБ_iv"] = True
                       st.session_state["agree_cmax2 - ИБ_po_sub"] = True
                       st.session_state["agree_cmax2 - ИБ_po_rdf"] = True
                       custom_success('Параметр добавлен!')

           measure_unit_rb_time  = select_time_unit("ИБ")
           measure_unit_rb_concentration = select_concentration_unit("ИБ")
           measure_unit_rb_dose  = select_dose_unit("ИБ")
           
           #cостояние радио-кнопки "method_auc"
           if "index_method_auc - ИБ" not in st.session_state:
               st.session_state["index_method_auc - ИБ"] = 0

           method_auc = st.radio("📈 Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = "Метод подсчёта AUC и AUMC - ИБ", index = st.session_state["index_method_auc - ИБ"])
           
           if st.session_state["Метод подсчёта AUC и AUMC - ИБ"] == 'linear':
              st.session_state["index_method_auc - ИБ"] = 0
           if st.session_state["Метод подсчёта AUC и AUMC - ИБ"] == "linear-up/log-down":
              st.session_state["index_method_auc - ИБ"] = 1

           st.subheader('Внутривенное введение субстанции')
           
           uploaded_file_1 = st.file_uploader("Выбрать файл внутривенного введения субстанции (формат XLSX)", key='Файл внутривенного введения при изучении абсолютной и относительной биодоступности препарата')
           
           #сохранение файла
           if uploaded_file_1 is not None:
              save_uploadedfile(uploaded_file_1)
              st.session_state["uploaded_file_1"] = uploaded_file_1.name
           
           if 'uploaded_file_1' in st.session_state: 
              custom_success(f"Файл загружен: {st.session_state['uploaded_file_1']}")
              
           dose_iv = st.text_input("Доза при внутривенном введении", key='Доза при внутривенном введении при изучении абсолютной и относительной биодоступности препарата', value = st.session_state["dose_iv"])
           
           st.session_state["dose_iv"] = dose_iv

           if "uploaded_file_1" in st.session_state and dose_iv and measure_unit_rb_concentration:
              df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_1"]))
              st.subheader('Индивидуальные значения концентраций в крови после внутривенного введения субстанции')
              
              ###интерактивная таблица
              df = edit_frame(df,st.session_state["uploaded_file_1"])

              ###количество животных 
              count_rows_number_iv= len(df.axes[0])
             
              ################

              table_heading='Индивидуальные и усредненные значения концентраций в крови после внутривенного введения субстанции'
              list_heading_word.append(table_heading)

              ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
              df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']

              list_table_word.append(df_concat_round_str_transpose)
           ########### графики    

           ######индивидуальные    

              # в линейных координатах
              col_mapping = df.columns.tolist()
              col_mapping.remove('Номер')

              count_row_df = len(df.axes[0])

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              #list_time.remove(0) ###т.к. внутривенное

              for r in range(0,count_row_df):

                  list_concentration=df.iloc[r].tolist()

                  numer_animal=list_concentration[0]

                  list_concentration.pop(0) #удаление номера животного

                  list_concentration = [float(v) for v in list_concentration]

                  #list_concentration.remove(0) ###т.к. внутривенное

                  fig, ax = plt.subplots()
                  plt.plot(list_time,list_concentration,marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  plt.xlabel(f"Время, {measure_unit_rb_time}")
                  plt.ylabel("Концентрация, "+ measure_unit_rb_concentration)
                  
                  list_graphics_word.append(fig) 
                  
                  #переобъявляем переменную названия графика
                  graphic='График индивидуального фармакокинетического профиля в крови (в линейных координатах) после внутривенного введения субстанции,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

               #в полулогарифмических координатах методом удаления точек
                  count_for_0_1=len(list_concentration)
                  list_range_for_0_1=range(0,count_for_0_1)

                  list_time_0=[]
                  list_for_log_1=[]
                  for i in list_range_for_0_1:
                      if list_concentration[i] !=0:
                         list_for_log_1.append(list_concentration[i])
                         list_time_0.append(list_time[i]) 

                  fig, ax = plt.subplots()
                  plt.plot(list_time_0,list_for_log_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  ax.set_yscale("log")
                  plt.xlabel(f"Время, {measure_unit_rb_time}")
                  plt.ylabel("Концентрация, "+measure_unit_rb_concentration)
                  
                  
                  list_graphics_word.append(fig)
                  
                  graphic='График индивидуального фармакокинетического профиля в крови (в полулогарифмических координатах) после внутривенного введения субстанции,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

           # объединенные индивидуальные в линейных координатах

              df_for_plot_conc=df.drop(['Номер'], axis=1)
              df_for_plot_conc_1 = df_for_plot_conc.transpose()

              df_for_plot_conc_1=df_for_plot_conc_1.replace(0, None) ###т.к. внутривенное

              list_numer_animal_for_plot=df['Номер'].tolist()
              count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

              list_color = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]
              
              fig, ax = plt.subplots()
             
              ax.set_prop_cycle(cycler(color=list_color))
             
              plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)
              
              ax.set_xlabel(f"Время, {measure_unit_rb_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))
                 
              list_graphics_word.append(fig)

              graphic="Сравнение индивидуальных фармакокинетических профилей (в линейных координатах) после внутривенного введения субстанции"
              list_heading_graphics_word.append(graphic)    
           # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
              df_for_plot_conc_1_log=df_for_plot_conc_1.replace(0, None)
              

              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1_log,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_rb_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
              ax.set_yscale("log")
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))
              
              list_graphics_word.append(fig)

              graphic="Сравнение индивидуальных фармакокинетических профилей (в полулогарифмических координатах) после внутривенного введения субстанции"
              list_heading_graphics_word.append(graphic)
               ###усредненные    
           # в линейных координатах
              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              df_averaged_concentrations=df.describe()
              list_concentration=df_averaged_concentrations.loc['mean'].tolist()
              err_y_1=df_averaged_concentrations.loc['std'].tolist()
              
              #list_time.remove(0) ###т.к. внутривенное
              #list_concentration.remove(0)
              #err_y_1.remove(0) 
              
              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              plt.xlabel(f"Время, {measure_unit_rb_time}")
              plt.ylabel("Концентрация, "+measure_unit_rb_concentration)
              
              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в линейных координатах) после внутривенного введения субстанции'
              list_heading_graphics_word.append(graphic)



           #в полулогарифмических координатах
              #для полулогарифм. построим без нуля (ноль уже удален)


              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              ax.set_yscale("log")
              plt.xlabel(f"Время, {measure_unit_rb_time}")
              plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

              
              list_graphics_word.append(fig)

              graphic='График усредненного фармакокинетического профиля в крови (в полулогарифмических координатах) после внутривенного введения субстанции'
              list_heading_graphics_word.append(graphic)


              ############ Параметры ФК

              result_PK = pk_parametrs_total_intravenously(df,"ИБ_iv",method_auc,dose_iv,measure_unit_rb_concentration,measure_unit_rb_time, measure_unit_rb_dose)

              if result_PK is not None:
                  if st.session_state["agree_cmax2 - ИБ"] == False:
                     df_total_PK_iv = result_PK["df_total_PK"]
                     df_PK = result_PK["df_PK"]
                     df_concat_PK_iv = result_PK["df_concat_PK"]
                     list_cmax_1_iv = result_PK["list_cmax_1"]
                  if st.session_state["agree_cmax2 - ИБ"] == True:
                     df_total_PK_iv = result_PK["df_total_PK"]
                     df_PK = result_PK["df_PK"]
                     df_concat_PK_iv = result_PK["df_concat_PK"]
                     df_total_PK_additional_double_peaks_iv = result_PK["df_total_PK_additional_double_peaks"]
                     list_cmax_1_iv = result_PK["list_cmax_1"]
                     list_cmax_2_iv = result_PK["list_cmax_2"]
                  
                  st.session_state["df_total_PK_iv"] = df_total_PK_iv

                  table_heading='Фармакокинетические показатели в крови после введения ЛС'
                  list_heading_word.append(table_heading)
                  
                  list_table_word.append(df_total_PK_iv)

                  if st.session_state["agree_cmax2 - ИБ"] == True:
                     table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле'
                     list_heading_word.append(table_heading)
                     
                     list_table_word.append(df_total_PK_additional_double_peaks_iv)

                  ####получение интервала для средних ФК параметров
                  list_PK_Cmax_1_not_round = df_PK['Cmax'].tolist()
                  list_PK_Tmax_1_not_round = df_PK['Tmax'].tolist() 
                  list_PK_MRT0_inf_not_round = df_PK['MRT0→∞'].tolist() 
                  list_PK_half_live_not_round = df_PK['T1/2'].tolist() 
                  list_PK_AUC0_t_not_round = df_PK['AUC0-t'].tolist()
                  list_PK_AUC0_inf_not_round = df_PK['AUC0→∞'].tolist()
                  list_PK_AUMC0_inf_not_round = df_PK['AUMC0-∞'].tolist()
                  list_PK_Сmax_dev_AUC0_t_not_round = df_PK['Сmax/AUC0-t'].tolist()
                  list_PK_Kel_not_round = df_PK['Kel'].tolist()

                  list_list_PK_parametr_iv=[list_PK_Cmax_1_not_round,list_PK_AUC0_t_not_round,list_PK_Kel_not_round,list_PK_AUC0_inf_not_round,list_PK_half_live_not_round,list_PK_AUMC0_inf_not_round,list_PK_MRT0_inf_not_round,list_PK_Сmax_dev_AUC0_t_not_round]
                  list_parametr_mean_h_iv=[]
                  for i in list_list_PK_parametr_iv:
                       n=len(i)

                       def confidential_interval(i):
                           if n < 30:
                              h = statistics.stdev(i)
                              mean = np.mean(i)
                           else:
                              h = statistics.stdev(i)  ### прояснить момент с n-1
                              mean = np.mean(i)
                           return ([mean,h]) 
                       func_mean_h = confidential_interval(i)

                       list_parametr_mean_h_iv.append(func_mean_h)

                  list_mean_h_iv_Cmax_round=[v for v in list_parametr_mean_h_iv[0]]
                  parametr_round_mean_h_Cmax=str(list_mean_h_iv_Cmax_round[0]) +"±"+str(list_mean_h_iv_Cmax_round[1])

                  list_mean_h_iv_AUC0_t_round=[v for v in list_parametr_mean_h_iv[1]] 
                  parametr_round_mean_h_AUC0_t=str(list_mean_h_iv_AUC0_t_round[0]) +"±"+str(list_mean_h_iv_AUC0_t_round[1]) 

                  list_mean_h_iv_Kel_round=[v for v in list_parametr_mean_h_iv[2]]
                  parametr_round_mean_h_Kel=str(list_mean_h_iv_Kel_round[0]) +"±"+str(list_mean_h_iv_Kel_round[1])

                  list_mean_h_iv_AUC0_inf_round= [v for v in list_parametr_mean_h_iv[3]]
                  parametr_round_mean_h_AUC0_inf=str(list_mean_h_iv_AUC0_inf_round[0]) +"±"+str(list_mean_h_iv_AUC0_inf_round[1]) 

                  list_mean_h_iv_half_live_round=[v for v in list_parametr_mean_h_iv[4]]
                  parametr_round_mean_h_half_live=str(list_mean_h_iv_half_live_round[0]) +"±"+str(list_mean_h_iv_half_live_round[1])

                  list_mean_h_iv_AUMC0_inf_round=[v for v in list_parametr_mean_h_iv[5]] 
                  parametr_round_mean_h_AUMC0_inf=str(list_mean_h_iv_AUMC0_inf_round[0]) +"±"+str(list_mean_h_iv_AUMC0_inf_round[1]) 

                  list_mean_h_iv_MRT0_inf_round=[v for v in list_parametr_mean_h_iv[6]]
                  parametr_round_mean_h_MRT0_inf=str(list_mean_h_iv_MRT0_inf_round[0]) +"±"+str(list_mean_h_iv_MRT0_inf_round[1])

                  list_mean_h_iv_Сmax_dev_AUC0_t_round=[v for v in list_parametr_mean_h_iv[7]]
                  parametr_round_mean_h_Сmax_dev_AUC0_t=str(list_mean_h_iv_Сmax_dev_AUC0_t_round[0]) +"±"+str(list_mean_h_iv_Сmax_dev_AUC0_t_round[1])

                  list_parametr_round_mean_h_iv= [parametr_round_mean_h_Cmax,parametr_round_mean_h_AUC0_t,parametr_round_mean_h_Kel,parametr_round_mean_h_AUC0_inf,parametr_round_mean_h_half_live,parametr_round_mean_h_AUMC0_inf,parametr_round_mean_h_MRT0_inf,parametr_round_mean_h_Сmax_dev_AUC0_t]

                  t_mean_iv = str(round_to_significant_figures(np.mean(list_PK_Tmax_1_not_round), 4))     
                  list_parametr_round_mean_h_iv.insert(1,t_mean_iv)

              else:
                  st.session_state["df_total_PK_iv"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                  st.error("Выберете необходимое количество значений Cmax и Cmax(2)")

           ############################################################################################################### 
           st.subheader('Пероральное введение субстанции')
           
           uploaded_file_2 = st.file_uploader("Выбрать файл перорального введения субстанции (формат XLSX)", key='Файл перорального введения субстанции при изучении абсолютной и относительной биодоступности препарата')
           
           #сохранение файла
           if uploaded_file_2 is not None:
              save_uploadedfile(uploaded_file_2)
              st.session_state["uploaded_file_2"] = uploaded_file_2.name
           
           if 'uploaded_file_2' in st.session_state: 
              custom_success(f"Файл загружен: {st.session_state['uploaded_file_2']}")

           dose_po_sub = st.text_input("Доза при пероральном введении субстанции", key='Доза при пероральном введении субстанции при изучении абсолютной и относительной биодоступности препарата', value = st.session_state["dose_po_sub"])
           
           st.session_state["dose_po_sub"] = dose_po_sub

           if "uploaded_file_2" in st.session_state and dose_po_sub and measure_unit_rb_concentration:

              df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_2"]))
              st.subheader('Индивидуальные значения концентраций в крови после перорального введения субстанции')
              
              ###интерактивная таблица
              df = edit_frame(df,st.session_state["uploaded_file_2"])

              ###количество животных 
              count_rows_number_sub= len(df.axes[0])
        
              table_heading='Индивидуальные и усредненные значения концентраций в крови после перорального введения субстанции'
              list_heading_word.append(table_heading)

              ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
              df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']
              
              list_table_word.append(df_concat_round_str_transpose)

           ########### графики    

           ######индивидуальные    

              # в линейных координатах
              col_mapping = df.columns.tolist()
              col_mapping.remove('Номер')

              count_row_df = len(df.axes[0])

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              for r in range(0,count_row_df):

                  list_concentration=df.iloc[r].tolist()

                  numer_animal=list_concentration[0]

                  list_concentration.pop(0) #удаление номера животного

                  list_concentration = [float(v) for v in list_concentration]


                  fig, ax = plt.subplots()
                  plt.plot(list_time,list_concentration,marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  plt.xlabel(f"Время, {measure_unit_rb_time}")
                  plt.ylabel("Концентрация, "+measure_unit_rb_concentration)
                 
                  list_graphics_word.append(fig)  

                  graphic='График индивидуального фармакокинетического профиля в крови (в линейных координатах) после перорального введения субстанции,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

               #в полулогарифмических координатах методом удаления точек
                  count_for_0_1=len(list_concentration)
                  list_range_for_0_1=range(0,count_for_0_1)

                  list_time_0=[]
                  list_for_log_1=[]
                  for i in list_range_for_0_1:
                      if list_concentration[i] !=0:
                         list_for_log_1.append(list_concentration[i])
                         list_time_0.append(list_time[i]) 

                  fig, ax = plt.subplots()
                  plt.plot(list_time_0,list_for_log_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  ax.set_yscale("log")
                  plt.xlabel(f"Время, {measure_unit_rb_time}")
                  plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

                  list_graphics_word.append(fig) 

                  graphic='График индивидуального фармакокинетического профиля в крови (в полулогарифмических координатах) после перорального введения субстанции,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

           # объединенные индивидуальные в линейных координатах

              df_for_plot_conc=df.drop(['Номер'], axis=1)
              df_for_plot_conc_1 = df_for_plot_conc.transpose()
              list_numer_animal_for_plot=df['Номер'].tolist()
              count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

              list_color = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]

              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_rb_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))

              list_graphics_word.append(fig) 

              graphic="Сравнение индивидуальных фармакокинетических профилей (в линейных координатах) после перорального введения субстанции"
              list_heading_graphics_word.append(graphic)    
           # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
              df_for_plot_conc_1_log=df_for_plot_conc_1.replace(0, None)


              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1_log,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_rb_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
              ax.set_yscale("log")
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))

              list_graphics_word.append(fig) 
       
              graphic="Сравнение индивидуальных фармакокинетических профилей (в полулогарифмических координатах) после перорального введения субстанции"
              list_heading_graphics_word.append(graphic) 

           ### усреденные    
           #в линейных    

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              df_averaged_concentrations=df.describe()
              list_concentration=df_averaged_concentrations.loc['mean'].tolist()
              err_y_2=df_averaged_concentrations.loc['std'].tolist()


              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_2, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              plt.xlabel(f"Время, {measure_unit_rb_time}")
              plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в линейных координатах) после перорального введения субстанции'
              list_heading_graphics_word.append(graphic)  

           #в полулогарифмических координатах
              list_time.remove(0)
              list_concentration.remove(0)
              err_y_2.remove(0) 


              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_2, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              ax.set_yscale("log")
              plt.xlabel(f"Время, {measure_unit_rb_time}")
              plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в полулогарифмических координатах) после перорального введения субстанции'
              list_heading_graphics_word.append(graphic) 

              ############ Параметры ФК

              result_PK = pk_parametrs_total_extravascular(df,"ИБ_po_sub",method_auc,dose_po_sub,measure_unit_rb_concentration,measure_unit_rb_time, measure_unit_rb_dose)

              if result_PK is not None:
                  if st.session_state["agree_cmax2 - ИБ"] == False:
                     df_total_PK_po_sub = result_PK["df_total_PK"]
                     df_PK = result_PK["df_PK"]
                     df_concat_PK_po_sub = result_PK["df_concat_PK"]
                     list_cmax_1_sub = result_PK["list_cmax_1"]
                  if st.session_state["agree_cmax2 - ИБ"] == True:
                     df_total_PK_po_sub = result_PK["df_total_PK"]
                     df_PK = result_PK["df_PK"]
                     df_concat_PK_po_sub = result_PK["df_concat_PK"]
                     df_total_PK_additional_double_peaks_po_sub = result_PK["df_total_PK_additional_double_peaks"]
                     list_cmax_1_sub = result_PK["list_cmax_1"]
                     list_cmax_2_sub = result_PK["list_cmax_2"]
                  
                  st.session_state["df_total_PK_po_sub"] = df_total_PK_po_sub

                  table_heading='Фармакокинетические показатели в крови после введения ЛС'
                  list_heading_word.append(table_heading)
                  
                  list_table_word.append(df_total_PK_po_sub)

                  if st.session_state["agree_cmax2 - ИБ"] == True:
                     table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле'
                     list_heading_word.append(table_heading)
                     
                     list_table_word.append(df_total_PK_additional_double_peaks_po_sub)

                  ####получение интервала для средних ФК параметров
                  list_PK_Cmax_1_not_round = df_PK['Cmax'].tolist()
                  list_PK_Tmax_1_not_round = df_PK['Tmax'].tolist() 
                  list_PK_MRT0_inf_not_round = df_PK['MRT0→∞'].tolist() 
                  list_PK_half_live_not_round = df_PK['T1/2'].tolist() 
                  list_PK_AUC0_t_not_round = df_PK['AUC0-t'].tolist()
                  list_PK_AUC0_inf_not_round = df_PK['AUC0→∞'].tolist()
                  list_PK_AUMC0_inf_not_round = df_PK['AUMC0-∞'].tolist()
                  list_PK_Сmax_dev_AUC0_t_not_round = df_PK['Сmax/AUC0-t'].tolist()
                  list_PK_Kel_not_round = df_PK['Kel'].tolist()

                  list_list_PK_parametr_po_sub=[list_PK_Cmax_1_not_round,list_PK_AUC0_t_not_round,list_PK_Kel_not_round,list_PK_AUC0_inf_not_round,list_PK_half_live_not_round,list_PK_AUMC0_inf_not_round,list_PK_MRT0_inf_not_round,list_PK_Сmax_dev_AUC0_t_not_round]
                  list_parametr_mean_h_po_sub=[]
                  for i in list_list_PK_parametr_po_sub:
                       n=len(i)

                       def confidential_interval(i):
                           if n < 30:
                              h = statistics.stdev(i)
                              mean = np.mean(i)
                           else:
                              h = statistics.stdev(i)  ### прояснить момент с n-1
                              mean = np.mean(i)
                           return ([mean,h]) 
                       func_mean_h = confidential_interval(i)

                       list_parametr_mean_h_po_sub.append(func_mean_h)

                  list_mean_h_po_sub_Cmax_round=[v for v in list_parametr_mean_h_po_sub[0]]
                  parametr_round_mean_h_Cmax=str(list_mean_h_po_sub_Cmax_round[0]) +"±"+str(list_mean_h_po_sub_Cmax_round[1])

                  list_mean_h_po_sub_AUC0_t_round=[v for v in list_parametr_mean_h_po_sub[1]] 
                  parametr_round_mean_h_AUC0_t=str(list_mean_h_po_sub_AUC0_t_round[0]) +"±"+str(list_mean_h_po_sub_AUC0_t_round[1]) 

                  list_mean_h_po_sub_Kel_round=[v for v in list_parametr_mean_h_po_sub[2]]
                  parametr_round_mean_h_Kel=str(list_mean_h_po_sub_Kel_round[0]) +"±"+str(list_mean_h_po_sub_Kel_round[1])

                  list_mean_h_po_sub_AUC0_inf_round= [v for v in list_parametr_mean_h_po_sub[3]]
                  parametr_round_mean_h_AUC0_inf=str(list_mean_h_po_sub_AUC0_inf_round[0]) +"±"+str(list_mean_h_po_sub_AUC0_inf_round[1]) 

                  list_mean_h_po_sub_half_live_round=[v for v in list_parametr_mean_h_po_sub[4]]
                  parametr_round_mean_h_half_live=str(list_mean_h_po_sub_half_live_round[0]) +"±"+str(list_mean_h_po_sub_half_live_round[1])

                  list_mean_h_po_sub_AUMC0_inf_round=[v for v in list_parametr_mean_h_po_sub[5]] 
                  parametr_round_mean_h_AUMC0_inf=str(list_mean_h_po_sub_AUMC0_inf_round[0]) +"±"+str(list_mean_h_po_sub_AUMC0_inf_round[1]) 

                  list_mean_h_po_sub_MRT0_inf_round=[v for v in list_parametr_mean_h_po_sub[6]]
                  parametr_round_mean_h_MRT0_inf=str(list_mean_h_po_sub_MRT0_inf_round[0]) +"±"+str(list_mean_h_po_sub_MRT0_inf_round[1])

                  list_mean_h_po_sub_Сmax_dev_AUC0_t_round=[v for v in list_parametr_mean_h_po_sub[7]]
                  parametr_round_mean_h_Сmax_dev_AUC0_t=str(list_mean_h_po_sub_Сmax_dev_AUC0_t_round[0]) +"±"+str(list_mean_h_po_sub_Сmax_dev_AUC0_t_round[1])

                  list_parametr_round_mean_h_po_sub= [parametr_round_mean_h_Cmax,parametr_round_mean_h_AUC0_t,parametr_round_mean_h_Kel,parametr_round_mean_h_AUC0_inf,parametr_round_mean_h_half_live,parametr_round_mean_h_AUMC0_inf,parametr_round_mean_h_MRT0_inf,parametr_round_mean_h_Сmax_dev_AUC0_t]

                  t_mean_po_sub = str("%.2f" % round(np.mean(list_PK_Tmax_1_not_round),2))     
                  list_parametr_round_mean_h_po_sub.insert(1,t_mean_po_sub)
              else:
                  st.session_state["df_total_PK_po_sub"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                  st.error("Выберете необходимое количество значений Cmax и Cmax(2)")

           ##############################################################################################################

           st.subheader('Пероральное введение ГЛФ')
           
           uploaded_file_3 = st.file_uploader("Выбрать файл перорального введения ГЛФ (формат XLSX)", key='Файл перорального введения ГЛФ при изучении абсолютной и относительной биодоступности препарата')
           
           #сохранение файла
           if uploaded_file_3 is not None:
              save_uploadedfile(uploaded_file_3)
              st.session_state["uploaded_file_3"] = uploaded_file_3.name
           
           if 'uploaded_file_3' in st.session_state: 
              custom_success(f"Файл загружен: {st.session_state['uploaded_file_3']}")
              

           dose_po_rdf = st.text_input("Доза при пероральном введении ГЛФ", key='Доза при пероральном введении ГЛФ при изучении абсолютной и относительной биодоступности препарата', value = st.session_state["dose_po_rdf"])
           
           st.session_state["dose_po_rdf"] = dose_po_rdf

           if "uploaded_file_3" in st.session_state and dose_po_rdf and measure_unit_rb_concentration:

              df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_3"]))
              st.subheader('Индивидуальные значения концентраций в крови после перорального введения ГЛФ')
              
              ###интерактивная таблица
              df = edit_frame(df,st.session_state["uploaded_file_3"])

              ###количество животных 
              count_rows_number_rdf= len(df.axes[0])
        
              table_heading='Индивидуальные и усредненные значения концентраций в крови после перорального введения ГЛФ'
              list_heading_word.append(table_heading)

              ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
              df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']
              
              list_table_word.append(df_concat_round_str_transpose)

           ########### графики    

           ######индивидуальные    

              # в линейных координатах
              col_mapping = df.columns.tolist()
              col_mapping.remove('Номер')

              count_row_df = len(df.axes[0])

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              for r in range(0,count_row_df):

                  list_concentration=df.iloc[r].tolist()

                  numer_animal=list_concentration[0]

                  list_concentration.pop(0) #удаление номера животного

                  list_concentration = [float(v) for v in list_concentration]


                  fig, ax = plt.subplots()
                  plt.plot(list_time,list_concentration,marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  plt.xlabel(f"Время, {measure_unit_rb_time}")
                  plt.ylabel("Концентрация, "+measure_unit_rb_concentration)
                 
                  list_graphics_word.append(fig)  

                  graphic='График индивидуального фармакокинетического профиля в крови (в линейных координатах) после перорального введения ГЛФ,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

               #в полулогарифмических координатах методом удаления точек
                  count_for_0_1=len(list_concentration)
                  list_range_for_0_1=range(0,count_for_0_1)

                  list_time_0=[]
                  list_for_log_1=[]
                  for i in list_range_for_0_1:
                      if list_concentration[i] !=0:
                         list_for_log_1.append(list_concentration[i])
                         list_time_0.append(list_time[i]) 

                  fig, ax = plt.subplots()
                  plt.plot(list_time_0,list_for_log_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                  ax.set_yscale("log")
                  plt.xlabel(f"Время, {measure_unit_rb_time}")
                  plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

                  list_graphics_word.append(fig) 

                  graphic='График индивидуального фармакокинетического профиля в крови (в полулогарифмических координатах) после перорального введения ГЛФ,  '+numer_animal
                  list_heading_graphics_word.append(graphic)

           # объединенные индивидуальные в линейных координатах

              df_for_plot_conc=df.drop(['Номер'], axis=1)
              df_for_plot_conc_1 = df_for_plot_conc.transpose()
              list_numer_animal_for_plot=df['Номер'].tolist()
              count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

              list_color = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]

              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_rb_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))

              list_graphics_word.append(fig) 

              graphic="Сравнение индивидуальных фармакокинетических профилей (в линейных координатах) после перорального введения ГЛФ"
              list_heading_graphics_word.append(graphic)    
           # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
              df_for_plot_conc_1_log=df_for_plot_conc_1.replace(0, None)


              fig, ax = plt.subplots()
              
              ax.set_prop_cycle(cycler(color=list_color))

              plt.plot(df_for_plot_conc_1_log,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

              ax.set_xlabel(f"Время, {measure_unit_rb_time}")
              ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
              ax.set_yscale("log")
              if count_numer_animal > 20:
                 ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
              else:
                 ax.legend(bbox_to_anchor=(1, 1))

              list_graphics_word.append(fig) 
       
              graphic="Сравнение индивидуальных фармакокинетических профилей (в полулогарифмических координатах) после перорального введения ГЛФ"
              list_heading_graphics_word.append(graphic) 

           ### усреденные    
           #в линейных    

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)

              df_averaged_concentrations=df.describe()
              list_concentration=df_averaged_concentrations.loc['mean'].tolist()
              err_y_2=df_averaged_concentrations.loc['std'].tolist()


              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_2, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              plt.xlabel(f"Время, {measure_unit_rb_time}")
              plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в линейных координатах) после перорального введения ГЛФ'
              list_heading_graphics_word.append(graphic)  

           #в полулогарифмических координатах
              list_time.remove(0)
              list_concentration.remove(0)
              err_y_2.remove(0) 


              fig, ax = plt.subplots()
              plt.errorbar(list_time,list_concentration,yerr=err_y_2, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
              ax.set_yscale("log")
              plt.xlabel(f"Время, {measure_unit_rb_time}")
              plt.ylabel("Концентрация, "+measure_unit_rb_concentration)

              list_graphics_word.append(fig) 

              graphic='График усредненного фармакокинетического профиля в крови (в полулогарифмических координатах) после перорального введения ГЛФ'
              list_heading_graphics_word.append(graphic) 

              ############### Параметры ФК

              result_PK = pk_parametrs_total_extravascular(df,"ИБ_po_rdf",method_auc,dose_po_rdf,measure_unit_rb_concentration,measure_unit_rb_time, measure_unit_rb_dose)

              if result_PK is not None:
                  if st.session_state["agree_cmax2 - ИБ"] == False:
                     df_total_PK_po_rdf = result_PK["df_total_PK"]
                     df_PK = result_PK["df_PK"]
                     df_concat_PK_po_rdf = result_PK["df_concat_PK"]
                     list_cmax_1_rdf = result_PK["list_cmax_1"]
                  if st.session_state["agree_cmax2 - ИБ"] == True:
                     df_total_PK_po_rdf = result_PK["df_total_PK"]
                     df_PK = result_PK["df_PK"]
                     df_concat_PK_po_rdf = result_PK["df_concat_PK"]
                     df_total_PK_additional_double_peaks_po_rdf = result_PK["df_total_PK_additional_double_peaks"]
                     list_cmax_1_rdf = result_PK["list_cmax_1"]
                     list_cmax_2_rdf = result_PK["list_cmax_2"]
                  
                  st.session_state["df_total_PK_po_rdf"] = df_total_PK_po_rdf

                  table_heading='Фармакокинетические показатели в крови после введения ЛС'
                  list_heading_word.append(table_heading)
                  
                  list_table_word.append(df_total_PK_po_rdf)

                  if st.session_state["agree_cmax2 - ИБ"] == True:
                     table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле'
                     list_heading_word.append(table_heading)
                     
                     list_table_word.append(df_total_PK_additional_double_peaks_po_rdf)
                  
                  ####получение интервала для средних ФК параметров
                  list_PK_Cmax_1_not_round = df_PK['Cmax'].tolist()
                  list_PK_Tmax_1_not_round = df_PK['Tmax'].tolist() 
                  list_PK_MRT0_inf_not_round = df_PK['MRT0→∞'].tolist() 
                  list_PK_half_live_not_round = df_PK['T1/2'].tolist() 
                  list_PK_AUC0_t_not_round = df_PK['AUC0-t'].tolist()
                  list_PK_AUC0_inf_not_round = df_PK['AUC0→∞'].tolist()
                  list_PK_AUMC0_inf_not_round = df_PK['AUMC0-∞'].tolist()
                  list_PK_Сmax_dev_AUC0_t_not_round = df_PK['Сmax/AUC0-t'].tolist()
                  list_PK_Kel_not_round = df_PK['Kel'].tolist()

                  list_list_PK_parametr_po_rdf=[list_PK_Cmax_1_not_round,list_PK_AUC0_t_not_round,list_PK_Kel_not_round,list_PK_AUC0_inf_not_round,list_PK_half_live_not_round,list_PK_AUMC0_inf_not_round,list_PK_MRT0_inf_not_round,list_PK_Сmax_dev_AUC0_t_not_round]
                  list_parametr_mean_h_po_rdf=[]
                  for i in list_list_PK_parametr_po_rdf:
                       n=len(i)

                       def confidential_interval(i):
                           if n < 30:
                              h = statistics.stdev(i)
                              mean = np.mean(i)
                           else:
                              h = statistics.stdev(i)  ### прояснить момент с n-1
                              mean = np.mean(i)
                           return ([mean,h]) 
                       func_mean_h = confidential_interval(i)

                       list_parametr_mean_h_po_rdf.append(func_mean_h)


                  list_mean_h_po_rdf_Cmax_round=[v for v in list_parametr_mean_h_po_rdf[0]]
                  parametr_round_mean_h_Cmax=str(list_mean_h_po_rdf_Cmax_round[0]) +"±"+str(list_mean_h_po_rdf_Cmax_round[1])

                  list_mean_h_po_rdf_AUC0_t_round=[v for v in list_parametr_mean_h_po_rdf[1]] 
                  parametr_round_mean_h_AUC0_t=str(list_mean_h_po_rdf_AUC0_t_round[0]) +"±"+str(list_mean_h_po_rdf_AUC0_t_round[1]) 

                  list_mean_h_po_rdf_Kel_round=[v for v in list_parametr_mean_h_po_rdf[2]]
                  parametr_round_mean_h_Kel=str(list_mean_h_po_rdf_Kel_round[0]) +"±"+str(list_mean_h_po_rdf_Kel_round[1])

                  list_mean_h_po_rdf_AUC0_inf_round= [v for v in list_parametr_mean_h_po_rdf[3]]
                  parametr_round_mean_h_AUC0_inf=str(list_mean_h_po_rdf_AUC0_inf_round[0]) +"±"+str(list_mean_h_po_rdf_AUC0_inf_round[1]) 

                  list_mean_h_po_rdf_half_live_round=[v for v in list_parametr_mean_h_po_rdf[4]]
                  parametr_round_mean_h_half_live=str(list_mean_h_po_rdf_half_live_round[0]) +"±"+str(list_mean_h_po_rdf_half_live_round[1])

                  list_mean_h_po_rdf_AUMC0_inf_round=[v for v in list_parametr_mean_h_po_rdf[5]] 
                  parametr_round_mean_h_AUMC0_inf=str(list_mean_h_po_rdf_AUMC0_inf_round[0]) +"±"+str(list_mean_h_po_rdf_AUMC0_inf_round[1]) 

                  list_mean_h_po_rdf_MRT0_inf_round=[v for v in list_parametr_mean_h_po_rdf[6]]
                  parametr_round_mean_h_MRT0_inf=str(list_mean_h_po_rdf_MRT0_inf_round[0]) +"±"+str(list_mean_h_po_rdf_MRT0_inf_round[1])

                  list_mean_h_po_rdf_Сmax_dev_AUC0_t_round=[v for v in list_parametr_mean_h_po_rdf[7]]
                  parametr_round_mean_h_Сmax_dev_AUC0_t=str(list_mean_h_po_rdf_Сmax_dev_AUC0_t_round[0]) +"±"+str(list_mean_h_po_rdf_Сmax_dev_AUC0_t_round[1])

                  list_parametr_round_mean_h_po_rdf= [parametr_round_mean_h_Cmax,parametr_round_mean_h_AUC0_t,parametr_round_mean_h_Kel,parametr_round_mean_h_AUC0_inf,parametr_round_mean_h_half_live,parametr_round_mean_h_AUMC0_inf,parametr_round_mean_h_MRT0_inf,parametr_round_mean_h_Сmax_dev_AUC0_t]

                  t_mean_po_rdf = str("%.2f" % round(np.mean(list_PK_Tmax_1_not_round),2))     
                  list_parametr_round_mean_h_po_rdf.insert(1,t_mean_po_rdf)
                 
              else:
                  st.session_state["df_total_PK_po_rdf"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                  st.error("Выберете необходимое количество значений Cmax и Cmax(2)")

           ###Биодоступность
           button_calculation_bioavailability = False
           
           if ("uploaded_file_1" in st.session_state) and ("uploaded_file_2" in st.session_state) and ("uploaded_file_3" in st.session_state) and measure_unit_rb_concentration and dose_iv and dose_po_sub and dose_po_rdf and st.session_state["df_total_PK_iv"] is not None and st.session_state["df_total_PK_po_sub"] is not None and st.session_state["df_total_PK_po_rdf"] is not None:
              
              condition_iv_cmax1 =  len(list_cmax_1_iv) == count_rows_number_iv
              condition_sub_cmax1 = len(list_cmax_1_sub) == count_rows_number_sub
              condition_rdf_cmax1 = len(list_cmax_1_rdf) == count_rows_number_rdf
              
              if st.session_state["agree_cmax2 - ИБ"] == True:
                 condition_iv_cmax2 =  len(list_cmax_2_iv) == count_rows_number_iv
                 condition_sub_cmax2 = len(list_cmax_2_sub) == count_rows_number_sub
                 condition_rdf_cmax2 = len(list_cmax_2_rdf) == count_rows_number_rdf
              
              if st.session_state["agree_cmax2 - ИБ"] == True:
                 if (condition_iv_cmax2 and condition_sub_cmax2 and condition_rdf_cmax2):
                    button_calculation_bioavailability = True
              if st.session_state["agree_cmax2 - ИБ"] == False:
                 if (condition_iv_cmax1 and condition_sub_cmax1 and condition_rdf_cmax1):
                    button_calculation_bioavailability = True

              if button_calculation_bioavailability == True:
                 custom_success('Расчеты произведены!')
              else:   
                 st.error('Заполните все поля ввода и загрузите файлы!')

           if ("uploaded_file_1" in st.session_state) and ("uploaded_file_2" in st.session_state) and ("uploaded_file_3" in st.session_state) and measure_unit_rb_concentration and dose_iv and dose_po_sub and dose_po_rdf and button_calculation_bioavailability:
               
               table_heading='Усредненные фармакокинетические параметры в крови после внутривенного введения субстанции, перорального введения субстанции и перорального введения ГЛФ, а также абсолютная и относительная биодоступность'
               list_heading_word.append(table_heading)

               AUCT_inf_mean_iv = df_concat_PK_iv["AUC0-t"].loc["mean"]
               AUCT_inf_mean_po_sub = df_concat_PK_po_sub["AUC0-t"].loc["mean"]
               AUCT_inf_mean_po_rdf = df_concat_PK_po_rdf["AUC0-t"].loc["mean"]

               #абсолютная биодоступность

               F_po_sub_iv=round((AUCT_inf_mean_po_sub * float(dose_iv))/(AUCT_inf_mean_iv*float(dose_po_sub))*100,2)
               F_po_rdf_iv=round((AUCT_inf_mean_po_rdf * float(dose_iv))/(AUCT_inf_mean_iv*float(dose_po_rdf))*100,2)

               #относительная биодоступность
               RF_po_sub_rdf=round((AUCT_inf_mean_po_rdf*float(dose_po_sub))/(AUCT_inf_mean_po_sub*float(dose_po_rdf))*100,2)

               df_intravenous_substance = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_1"]))
               df_oral_substance = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_2"]))
               df_oral_rdf = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_3"]))

               df_averaged_concentrations_intravenous_substance=df_intravenous_substance.describe()
               list_concentration__intravenous_substance=df_averaged_concentrations_intravenous_substance.loc['mean'].tolist()

               df_averaged_concentrations_oral_substance=df_oral_substance.describe()
               list_concentration__oral_substance=df_averaged_concentrations_oral_substance.loc['mean'].tolist()

               df_averaged_concentrations_oral_rdf=df_oral_rdf.describe()
               list_concentration__oral_rdf=df_averaged_concentrations_oral_rdf.loc['mean'].tolist()

           ### итоговый фрейм по PK параметрам

               list_index_for_df_total_PK_mean = ['Cmax ' +"("+measure_unit_rb_concentration+")",'Tmax ' +"("+f"{measure_unit_rb_time}"+")",'AUC0-t '+"("+measure_unit_rb_concentration+f"×{measure_unit_rb_time}" +")",'Kel '+"("+f"{measure_unit_rb_time}\u207B\u00B9"+")",'AUC0→∞ '+"("+measure_unit_rb_concentration+f"×{measure_unit_rb_time}" +")",'T1/2 '+"("+f"{measure_unit_rb_time}"+")",'AUMC0-∞ '+"("+measure_unit_rb_concentration+f"×{measure_unit_rb_time}\u00B2"+")",'MRT0→∞ '+"("+f"{measure_unit_rb_time}"+")",'Сmax/AUC0-t '+"("+f"{measure_unit_rb_time}\u207B\u00B9"+")","F(абсолютная биодоступность),%","Относительная биодоступность,% (по сравнению с пероральным введением субстанции)"]
               
               #добавление значений биодоступности
               list_parametr_round_mean_h_iv.append("-")
               list_parametr_round_mean_h_iv.append("-")

               list_parametr_round_mean_h_po_sub.append(F_po_sub_iv)
               list_parametr_round_mean_h_po_sub.append("-")

               list_parametr_round_mean_h_po_rdf.append(F_po_rdf_iv)
               list_parametr_round_mean_h_po_rdf.append(RF_po_sub_rdf)


               df_total_PK_mean = pd.DataFrame(list(zip(list_parametr_round_mean_h_iv,list_parametr_round_mean_h_po_sub,list_parametr_round_mean_h_po_rdf)),columns=['Внутривенное введение субстанции','Пероральное введение субстанции','Пероральное введение ГЛФ'],index=list_index_for_df_total_PK_mean)
               df_total_PK_mean.index.name = 'Параметры, размерность'
               
               list_table_word.append(df_total_PK_mean)

           #####объединенные графики

           ### в линейных координатах
               col_mapping = df_intravenous_substance.columns.tolist() ### можно указать любой фрейм
               col_mapping.remove('Номер')
               list_time = []
               for i in col_mapping:
                   numer=float(i)
                   list_time.append(numer)

               err_y_1=df_averaged_concentrations_intravenous_substance.loc['std'].tolist()
               err_y_2=df_averaged_concentrations_oral_substance.loc['std'].tolist()
               err_y_3=df_averaged_concentrations_oral_rdf.loc['std'].tolist()
               
               df_total_injection = pd.DataFrame(list(zip(list_concentration__intravenous_substance, list_concentration__oral_substance, list_concentration__oral_rdf)),columns =['внутривенное введение','пероральное введение субстанции','пероральное введение ГЛФ'])
               df_total_injection.loc[df_total_injection["внутривенное введение"] == 0, "внутривенное введение"] = np.nan #т.к. внутривенное введение
               
               df_total_error = pd.DataFrame(list(zip(err_y_1, err_y_2, err_y_3)),columns =['внутривенное введение','пероральное введение субстанции','пероральное введение ГЛФ'])
               df_total_error.loc[df_total_injection["внутривенное введение"] == 0, "внутривенное введение"] = np.nan #т.к. внутривенное введение
               list_name_injection = ['внутривенное введение','пероральное введение субстанции','пероральное введение ГЛФ']
               list_name_colors = ["black","red","blue"]
               zip_injection_colors_error = zip(list_name_injection,list_name_colors)


               fig, ax = plt.subplots()
               
               for injection,color in zip_injection_colors_error:
                   plt.errorbar(list_time,df_total_injection[injection],yerr=df_total_error[injection],color= color, marker='o',markersize=4.0,markeredgecolor=color,markerfacecolor=color,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = injection)
                   ax.set_xlabel(f"Время, {measure_unit_rb_time}")
                   ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
                   ax.legend()

               list_graphics_word.append(fig) 

               graphic="Сравнение фармакокинетических профилей (в линейных координатах) после внутривенного введения субстанции, перорального введения субстанции и перорального введения ГЛФ"
               list_heading_graphics_word.append(graphic) 
           ### в полулогарифмических координатах
               if 0 in list_time:
                  list_time.remove(0)
               
               list_concentration__oral_substance.remove(0)
               list_concentration__oral_rdf.remove(0)
               
               err_y_2.remove(0) 
               err_y_3.remove(0) 

               fig, ax = plt.subplots()    

               plt.errorbar(list_time,list_concentration__intravenous_substance,yerr=err_y_1,color="black", marker='o',markersize=4.0,markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = 'внутривенное введение')
               plt.errorbar(list_time,list_concentration__oral_substance,yerr=err_y_2,color= "red", marker='o',markersize=4.0,markeredgecolor="red",markerfacecolor="red",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = 'пероральное введение субстанции')
               plt.errorbar(list_time,list_concentration__oral_rdf,yerr=err_y_3,color= "blue", marker='o',markersize=4.0,markeredgecolor="blue",markerfacecolor="blue",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = 'пероральное введение ГЛФ')

               ax.set_yscale("log")
               ax.set_xlabel(f"Время, {measure_unit_rb_time}")
               ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
               ax.legend()

               list_graphics_word.append(fig) 

               graphic="Сравнение фармакокинетических профилей (в полулогарифмических координатах) после внутривенного введения субстанции, перорального введения субстанции и перорального введения ГЛФ"
               list_heading_graphics_word.append(graphic)
           else:
               st.write("")

           ##############################################################################################################

           ###сохранение состояния 
           st.session_state["list_heading_word"] = list_heading_word
           st.session_state["list_table_word"] = list_table_word
           st.session_state["list_graphics_word"] = list_graphics_word
           st.session_state["list_heading_graphics_word"] = list_heading_graphics_word
    
    #отдельная панель, чтобы уменьшить размер вывода результатов

    col1, col2 = st.columns([0.66,0.34])
    
    with col1:
     
       #####Создание word отчета
       if panel == "Таблицы":
          
          if st.session_state["df_total_PK_iv"] is not None and st.session_state["df_total_PK_po_sub"] is not None and st.session_state["df_total_PK_po_rdf"] is not None:

             list_heading_word = st.session_state["list_heading_word"]
             list_table_word = st.session_state["list_table_word"]
             
             ###вызов функции визуализации таблиц
             visualize_table(list_heading_word,list_table_word)

             with col2:
                  
                  selected = option_menu(None, ["Cформированный отчeт"], 
                  icons=['file-earmark-arrow-down-fill'], 
                  menu_icon="cast", default_index=0, orientation="vertical",
                  styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                  })

                  if selected == "Cформированный отчeт":

                     ###вызов функции создания Word-отчета таблиц
                     create_table(list_heading_word,list_table_word)
          else:
             st.error("Введите и загрузите все необходимые данные!")

       if panel == "Графики":
             
          if st.session_state["df_total_PK_iv"] is not None and st.session_state["df_total_PK_po_sub"] is not None and st.session_state["df_total_PK_po_rdf"] is not None:
             
             list_graphics_word = st.session_state["list_graphics_word"]
             list_heading_graphics_word = st.session_state["list_heading_graphics_word"]
             
             #######визуализация

             #классификация графиков по кнопкам
             type_graphics = st.selectbox('Выберите вид графиков',
             ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля', "Сравнение фармакокинетических профилей при разных видах введения"),disabled = False, key = "Вид графика - ИБ" )

             count_graphics_for_visual = len(list_heading_graphics_word)
             list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)
             
             for i in list_range_count_graphics_for_visual:
                 if list_heading_graphics_word[i].__contains__("индивидуального"): 
                    if type_graphics == 'Индивидуальные фармакокинетические профили':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])
                 if list_heading_graphics_word[i].__contains__("Сравнение индивидуальных"):   
                    if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])
                 if list_heading_graphics_word[i].__contains__("усредненного"):
                    if type_graphics == 'Графики усредненного фармакокинетического профиля':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])
                 if list_heading_graphics_word[i].__contains__("Сравнение фармакокинетических"):
                    if type_graphics == 'Сравнение фармакокинетических профилей при разных видах введения':
                       st.pyplot(list_graphics_word[i])
                       st.subheader(list_heading_graphics_word[i])

             with col2:
                  
                  selected = option_menu(None, ["Cформированный отчeт"], 
                  icons=['file-earmark-arrow-down-fill'], 
                  menu_icon="cast", default_index=0, orientation="vertical",
                  styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                  })
                   
                  if selected == "Cформированный отчeт":
                     ###вызов функции создания Word-отчета графиков
                     create_graphic(list_graphics_word,list_heading_graphics_word)

          else:
             st.error("Введите и загрузите все необходимые данные!")          
#####################################################################        
if option == 'Распределение по органам':
   
   st.header('Исследование ФК параметров для органов животных')
   
   col1, col2 = st.columns([0.66, 0.34])
   
   with col1:
       
      panel = st.radio(
           "⚙️Панель управления",
           ("Загрузка файлов", "Таблицы","Графики"),
           horizontal=True, key= "Загрузка файлов - Исследование ФК параметров для органов животных"
       )

      ###создание состояния
      if "dose_org" not in st.session_state:
         st.session_state["dose_org"] = ""

      #cписки для word-отчета
      list_heading_word=[]
      list_table_word=[]
      list_graphics_word=[]
      list_heading_graphics_word=[]
       
      if panel == "Загрузка файлов":
         
         ######### боковое меню справа
         with col2:
              
              selected = option_menu(None, ["Настройка дополнительных параметров"], 
                    icons=['menu-button'], 
                    menu_icon="cast", default_index=0, orientation="vertical",
                    styles={
                      "container": {"padding": "0!important", "background-color": "#1f3b57"},
                      "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                      "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                      "nav-link-selected": {"background-color": "#73b5f2"},
                    })

              if selected == "Настройка дополнительных параметров":
                    type_parameter = st.selectbox('Выберите параметр',
                    ("Вид введения",'Двойные пики'),disabled = False, key = "Вид параметра - органы")
                 
              if "agree_cmax2 - органы" not in st.session_state:
                    st.session_state["agree_cmax2 - органы"] = False

              if type_parameter == 'Двойные пики':

                 st.session_state["agree_cmax2 - органы"] = st.checkbox('В зависимости "Концентрация-Время" отчетливо наблюдаются двойные пики', key = "Возможность добавления Cmax2 - органы", value = st.session_state["agree_cmax2 - органы"])
                 
                 if st.session_state["agree_cmax2 - органы"] == True:
                    custom_success('Параметр добавлен!')

              if "agree_injection - органы" not in st.session_state:
                    st.session_state["agree_injection - органы"] = False

              if type_parameter == "Вид введения":

               # Проверка наличия значения в сессии, если его нет, устанавливаем значение по умолчанию
                 if "injection_choice - органы" not in st.session_state:
                     st.session_state["injection_choice - органы"] = 0  # Значение по умолчанию

                 # Радиокнопка для выбора типа введения
                 injection_type = st.radio(
                     "Выберите тип введения:",
                     options=["Внутривенное введение", "Внесосудистое введение"],
                     index=st.session_state["injection_choice - органы"],
                     key="injection_choice_органы",  # Ключ для сохранения выбора в сессии
                 )

                 # Логика для обновления состояния сессии
                 if injection_type == "Внутривенное введение":
                     st.session_state["agree_injection - органы"] = True
                     st.session_state["injection_choice - органы"] = 0
                 else:
                     st.session_state["agree_injection - органы"] = False
                     st.session_state["injection_choice - органы"] = 1

                 # Сообщение в зависимости от выбора
                 if st.session_state["agree_injection - органы"]:
                   custom_success("Выбрано: Внутривенное введение!")
                 else:
                   custom_success("Выбрано: Внесосудистое введение!")

         measure_unit_org_time = select_time_unit("органы")
         measure_unit_org_blood = select_concentration_unit("органы")
         measure_unit_org_organs = select_organ_concentration_unit("органы")
         measure_unit_org_dose = select_dose_unit("органы")
         
         dose = st.text_input("Доза препарата", key='Доза препарата при изучении фармакокинетики в органах животных', value = st.session_state["dose_org"])
         
         st.session_state["dose_org"] = dose

         #cостояние радио-кнопки "method_auc"
         if "index_method_auc - ИО" not in st.session_state:
             st.session_state["index_method_auc - ИО"] = 0

         method_auc = st.radio("📈 Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = "Метод подсчёта AUC и AUMC - ИО", index = st.session_state["index_method_auc - ИО"])
         
         if st.session_state["Метод подсчёта AUC и AUMC - ИО"] == 'linear':
            st.session_state["index_method_auc - ИО"] = 0
         if st.session_state["Метод подсчёта AUC и AUMC - ИО"] == "linear-up/log-down":
            st.session_state["index_method_auc - ИО"] = 1
         
         custom_alert("Выберите нужное количество файлов соответственно количеству исследуемых органов; файл должен быть назван соотвественно органу; исходный файл крови должен быть назван 'Кровь'")
         file_uploader = st.file_uploader("",accept_multiple_files=True, key='Файлы при изучении фармакокинетики в органах животных')

         if 'list_files_name_organs' not in st.session_state:
             st.session_state['list_files_name_organs'] = []

         ###сохранение файла
         list_files_name_organs = []
         if file_uploader is not None:
            for i in file_uploader:
                save_uploadedfile(i)
                st.session_state[str(i.name)] = i.name
                list_files_name_organs.append(i.name)
         
         st.session_state['list_files_name_organs'] = list_files_name_organs
         
         if st.session_state['list_files_name_organs'] != []:
              custom_success(f"Файлы загружены: {', '.join(st.session_state['list_files_name_organs'])}") 
              
         
         list_keys_file_org = []
         for i in st.session_state.keys():
             if i.__contains__("xlsx") and (not i.__contains__("Дозировка")) and (not i.__contains__("edited_df")):### чтобы не перекрывалось с lin; #обрезаем фразу ненужного добавления названия "edited_df"
                list_keys_file_org.append(i)


         if (list_keys_file_org != []) and dose and measure_unit_org_blood and measure_unit_org_organs:

             list_name_organs=[]
             list_df_unrounded=[]
             list_df_for_mean_unround_for_graphics=[]
             list_t_graph=[]
             

             # Значение, которое нужно переместить
             blood_file_name = 'Кровь.xlsx'

             # Проверка, существует ли значение в списке
             if blood_file_name in list_keys_file_org:
                 # Удаляем значение из списка и добавляем его в начало
                 list_keys_file_org.remove(blood_file_name)
                 list_keys_file_org.insert(0, blood_file_name)


             for i in list_keys_file_org:
                 df = pd.read_excel(os.path.join("Папка для сохранения файлов",i))

                 file_name=st.session_state[i][:-5]

                 st.subheader('Индивидуальные значения концентраций ' + "("+file_name+")")
                 
                 ###интерактивная таблица
                 df = edit_frame(df,i)

                 ###количество животных 
                 count_rows_number_org = len(df.axes[0])

                 table_heading='Индивидуальные и усредненные значения концентраций ' + "("+file_name+")"
                 list_heading_word.append(table_heading)

                 ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                 df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']

                 list_table_word.append(df_concat_round_str_transpose)

                 if file_name == "Кровь":
                    measure_unit_org = measure_unit_org_blood
                 else:
                    measure_unit_org = measure_unit_org_organs
                 ########### графики    

                 ######индивидуальные    

                 # в линейных координатах 
                 col_mapping = df.columns.tolist()
                 col_mapping.remove('Номер')

                 count_row_df = len(df.axes[0])

                 list_time = []
                 for i in col_mapping:
                     numer=float(i)
                     list_time.append(numer)
                 list_t_graph.append(list_time)

                 #if st.session_state["agree_injection - органы"] == True: 
                    #list_time.remove(0)

                 for r in range(0,count_row_df):

                     list_concentration=df.iloc[r].tolist()

                     numer_animal=list_concentration[0]

                     list_concentration.pop(0) #удаление номера животного

                     list_concentration = [float(v) for v in list_concentration]

                     #if st.session_state["agree_injection - органы"] == True:
                        #list_concentration.remove(0)

                     fig, ax = plt.subplots()
                     plt.plot(list_time,list_concentration,marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                     plt.xlabel(f"Время, {measure_unit_org_time}")
                     plt.ylabel("Концентрация, "+measure_unit_org)
      
                     list_graphics_word.append(fig)

                     graphic='График индивидуального фармакокинетического профиля в линейных координатах '  + "("+file_name+")"',  '+numer_animal
                     list_heading_graphics_word.append(graphic)  
                     

                  #в полулогарифмических координатах методом удаления точек
                     count_for_0_1=len(list_concentration)
                     list_range_for_0_1=range(0,count_for_0_1)

                     list_time_0=[]
                     list_for_log_1=[]
                     for i in list_range_for_0_1:
                         if list_concentration[i] !=0:
                            list_for_log_1.append(list_concentration[i])
                            list_time_0.append(list_time[i]) 

                     fig, ax = plt.subplots()
                     plt.plot(list_time_0,list_for_log_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                     ax.set_yscale("log")
                     plt.xlabel(f"Время, {measure_unit_org_time}")
                     plt.ylabel("Концентрация, "+measure_unit_org)

                     
                     list_graphics_word.append(fig)

                     graphic='График индивидуального фармакокинетического профиля в полулогарифмических координатах ' + "("+file_name+")"',  '+numer_animal
                     list_heading_graphics_word.append(graphic) 
       
              # объединенные индивидуальные в линейных координатах

                 df_for_plot_conc=df.drop(['Номер'], axis=1)
                 df_for_plot_conc_1 = df_for_plot_conc.transpose()
                 
                 #if st.session_state["agree_injection - органы"] == True:
                    #df_for_plot_conc_1=df_for_plot_conc_1.replace(0, None) ###т.к. внутривенное

                 list_numer_animal_for_plot=df['Номер'].tolist()
                 count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

                 list_color = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]

                 fig, ax = plt.subplots()
                 
                 ax.set_prop_cycle(cycler(color=list_color))

                 plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

                 ax.set_xlabel(f"Время, {measure_unit_org_time}")
                 ax.set_ylabel("Концентрация, "+measure_unit_org)
                 if count_numer_animal > 20:
                    ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
                 else:
                    ax.legend(bbox_to_anchor=(1, 1))
                 
                 list_graphics_word.append(fig)

                 graphic="Сравнение индивидуальных фармакокинетических профилей в линейных координатах " + "("+file_name+")"
                 list_heading_graphics_word.append(graphic)     
              # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
                 df_for_plot_conc_1_log=df_for_plot_conc_1.replace(0, None)


                 fig, ax = plt.subplots()

                 ax.set_prop_cycle(cycler(color=list_color))

                 plt.plot(df_for_plot_conc_1_log,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

                 ax.set_xlabel(f"Время, {measure_unit_org_time}")
                 ax.set_ylabel("Концентрация, "+measure_unit_org)
                 ax.set_yscale("log")
                 if count_numer_animal > 20:
                    ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
                 else:
                    ax.legend(bbox_to_anchor=(1, 1))
                 
                 list_graphics_word.append(fig)

                 graphic="Сравнение индивидуальных фармакокинетических профилей в полулогарифмических координатах " + "("+file_name+")"
                 list_heading_graphics_word.append(graphic)
                  ###усредненные    
              # в линейных координатах
                 list_time = []
                 for i in col_mapping:
                     numer=float(i)
                     list_time.append(numer)

                 df_averaged_concentrations=df.describe()
                 list_concentration=df_averaged_concentrations.loc['mean'].tolist()
                 err_y_1=df_averaged_concentrations.loc['std'].tolist()
                 
                 #if st.session_state["agree_injection - органы"] == True:
                    #list_time.remove(0) ###т.к. внутривенное
                    #list_concentration.remove(0)
                    #err_y_1.remove(0)

                 fig, ax = plt.subplots()
                 plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
                 plt.xlabel(f"Время, {measure_unit_org_time}")
                 plt.ylabel("Концентрация, "+measure_unit_org)
                 
                 list_graphics_word.append(fig)

                 graphic='График усредненного фармакокинетического профиля в линейных координатах ' + "("+file_name+")"
                 list_heading_graphics_word.append(graphic)

              #в полулогарифмических координатах
                 #для полулогарифм. посторим без нуля
                 if st.session_state["agree_injection - органы"] == False:
                    list_time.remove(0)
                    list_concentration.remove(0)
                    err_y_1.remove(0) 

                 fig, ax = plt.subplots()
                 plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
                 ax.set_yscale("log")
                 plt.xlabel(f"Время, {measure_unit_org_time}")
                 plt.ylabel("Концентрация, "+measure_unit_org)

                 list_graphics_word.append(fig)

                 graphic='График усредненного фармакокинетического профиля в полулогарифмических координатах ' + "("+file_name+")"
                 list_heading_graphics_word.append(graphic)

                 ############ Параметры ФК
                 
                 if f"agree_cmax2 - органы {file_name}" not in st.session_state:
                    st.session_state[f"agree_cmax2 - органы {file_name}"] = False
                 
                 if st.session_state["agree_cmax2 - органы"] == True:
                    st.session_state[f"agree_cmax2 - органы {file_name}"] = True


                 if st.session_state["agree_injection - органы"] == False:
                     result_PK = pk_parametrs_total_extravascular(df,f"органы {file_name}",method_auc,dose,measure_unit_org,measure_unit_org_time,measure_unit_org_dose)
                 else:
                     result_PK = pk_parametrs_total_intravenously(df,f"органы {file_name}",method_auc,dose,measure_unit_org,measure_unit_org_time,measure_unit_org_dose)

                 if result_PK is not None:
                     if st.session_state["agree_cmax2 - органы"] == False:
                        df_total_PK_org = result_PK["df_total_PK"]
                        df_concat_PK_org = result_PK["df_concat_PK"]
                        list_cmax_1_org = result_PK["list_cmax_1"]
                     if st.session_state["agree_cmax2 - органы"] == True:
                        df_total_PK_org = result_PK["df_total_PK"]
                        df_concat_PK_org = result_PK["df_concat_PK"]
                        list_cmax_1_org = result_PK["list_cmax_1"]
                        list_cmax_2_org = result_PK["list_cmax_2"]
                        df_total_PK_additional_double_peaks_org = result_PK["df_total_PK_additional_double_peaks"]
                         
                     st.session_state["df_total_PK_org"] = df_total_PK_org

                     table_heading='Фармакокинетические показатели ' + "("+file_name+")"
                     list_heading_word.append(table_heading)
                     
                     list_table_word.append(df_total_PK_org)
                     
                     if st.session_state["agree_cmax2 - органы"] == True:
                        table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле '  + "("+file_name+")"
                        list_heading_word.append(table_heading)
                        
                        list_table_word.append(df_total_PK_additional_double_peaks_org)

                     #создание списков фреймов, названий органов и т.д.

                     ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                     df_concat = create_table_descriptive_statistics(df)['df_concat']

                     list_name_organs.append(file_name)
                     list_df_unrounded.append(df_concat_PK_org)
                     list_df_for_mean_unround_for_graphics.append(df_concat)
                 else:
                     st.session_state["df_total_PK_org"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                     st.error("Выберете необходимое количество значений Cmax и Cmax(2)")

             ###Кнопка активации дальнейших действий
             button_calculation = False
             
             if (list_keys_file_org != []) and dose and measure_unit_org_blood and measure_unit_org_organs and result_PK is not None:
              
                condition_cmax1 =  len(list_cmax_1_org) == count_rows_number_org
                
                if st.session_state["agree_cmax2 - органы"] == True:
                   condition_cmax2 =  len(list_cmax_2_org) == count_rows_number_org
                
                if st.session_state["agree_cmax2 - органы"] == True:
                   if (condition_cmax2):
                      button_calculation = True
                if st.session_state["agree_cmax2 - органы"] == False:
                   if (condition_cmax1):
                      button_calculation = True

                if button_calculation == True:
                   custom_success('Расчеты произведены!')
                else:   
                   st.error('Заполните все поля ввода и загрузите файлы!')
             
             if (list_keys_file_org != []) and dose and measure_unit_org_blood and measure_unit_org_organs and button_calculation:
                
                list_list_PK_par_mean=[]
                for i in list_df_unrounded: 
                    mean_сmax=i['Cmax'].loc['mean']
                    mean_tmax=i['Tmax'].loc['mean']
                    mean_mrt0inf=i['MRT0→∞'].loc['mean']
                    mean_thalf=i['T1/2'].loc['mean']
                    mean_auc0t=i['AUC0-t'].loc['mean']
                    mean_auc0inf=i['AUC0→∞'].loc['mean']
                    mean_aumc0inf=i['AUMC0-∞'].loc['mean']
                    mean_kel=i['Kel'].loc['mean']
                    list_list_PK_par_mean.append([mean_сmax,mean_tmax,mean_mrt0inf,mean_thalf,mean_auc0t,mean_auc0inf,mean_aumc0inf,mean_kel])

                ### получение итогового фрейма ФК параметров органов
                
                df_PK_organs_total = pd.DataFrame(list_list_PK_par_mean, columns =['Cmax','Tmax','MRT0→∞','T1/2','AUC0-t','AUC0→∞','AUMC0-∞','Kel'],index=list_name_organs) 
                
                df_PK_organs_total_transpose=df_PK_organs_total.transpose()

                index_blood = list_name_organs.index("Кровь")
                ###ft
                list_aucot_for_ft=[]
                list_columns_df_PK_organs_total_transpose=df_PK_organs_total_transpose.columns.tolist()
                list_columns_df_PK_organs_total_transpose.remove('Кровь') #исходный файл крови должен быть назван так "Кровь"
                for i in list_columns_df_PK_organs_total_transpose:
                    aucot=df_PK_organs_total_transpose[i].loc['AUC0-t']
                    list_aucot_for_ft.append(aucot)

                list_ft=[] ## для диаграммы
                list_ft_round=[]
                for i in list_aucot_for_ft:
                    ft=i/df_PK_organs_total_transpose["Кровь"].loc['AUC0-t']
                    list_ft.append(ft)
                    list_ft_round.append("%.2f" % round(ft,2))
                list_ft_round.insert(index_blood, "-")

                df_PK_organs_total_transpose.loc[ len(df_PK_organs_total_transpose.index )] = list_ft_round


                df_PK_organs_total_transpose.index=['Cmax ' +"("+measure_unit_org_blood+")",'Tmax ' +"("+f"{measure_unit_org_time}"+")",'MRT0→∞ '+"("+f"{measure_unit_org_time}"+")",'T1/2 '+"("+f"{measure_unit_org_time}"+")",'AUC0-t '+"("+measure_unit_org_blood+f"×{measure_unit_org_time}" +")",'AUC0→∞ '+"("+measure_unit_org_blood+f"×{measure_unit_org_time}" +")",'AUMC0-∞ '+"("+measure_unit_org_blood+f"×{measure_unit_org_time}\u00B2" +")",'Kel '+"("+f"{measure_unit_org_time}\u207B\u00B9"+")",'fт']
                
                #округление фрейма df_PK_organs_total_transpose

                df_organs_trans_trans=df_PK_organs_total_transpose.transpose()


                series_Cmax=df_organs_trans_trans['Cmax ' +"("+measure_unit_org_blood+")"].tolist() 
                series_Cmax=pd.Series([v for v in series_Cmax])

                series_Tmax=df_organs_trans_trans['Tmax ' +"("+f"{measure_unit_org_time}"+")"].tolist()       
                series_Tmax=pd.Series([v for v in series_Tmax]) 
                
                series_MRT0_inf= df_organs_trans_trans['MRT0→∞ '+"("+f"{measure_unit_org_time}"+")"].tolist()   
                series_MRT0_inf=pd.Series([v for v in series_MRT0_inf])

                series_half_live= df_organs_trans_trans['T1/2 '+"("+f"{measure_unit_org_time}"+")"].tolist()   
                series_half_live=pd.Series([v for v in series_half_live]) 

                series_AUC0_t= df_organs_trans_trans['AUC0-t '+"("+measure_unit_org_blood+f"×{measure_unit_org_time}" +")"].tolist()   
                series_AUC0_t=pd.Series([v for v in series_AUC0_t])

                series_AUC0_inf= df_organs_trans_trans['AUC0→∞ '+"("+measure_unit_org_blood+f"×{measure_unit_org_time}" +")"].tolist()  
                series_AUC0_inf=pd.Series([v for v in series_AUC0_inf]) 

                series_AUMC0_inf= df_organs_trans_trans['AUMC0-∞ '+"("+measure_unit_org_blood+f"×{measure_unit_org_time}\u00B2" +")"].tolist()   
                series_AUMC0_inf=pd.Series([v for v in series_AUMC0_inf])
          
                series_Kel= df_organs_trans_trans['Kel '+"("+f"{measure_unit_org_time}\u207B\u00B9"+")"].tolist()   
                series_Kel=pd.Series([v for v in series_Kel])

                series_ft= df_organs_trans_trans['fт'].tolist() ##уже округлен
                series_ft=pd.Series(series_ft)
                
                df_total_total_organs = pd.concat([series_Cmax,series_Tmax,series_MRT0_inf,series_half_live,series_AUC0_t,series_AUC0_inf,series_AUMC0_inf,series_Kel,series_ft], axis= 1)

                df_total_total_organs.index=df_PK_organs_total_transpose.columns.tolist()
                df_total_total_organs.columns=df_PK_organs_total_transpose.index.tolist() 

                df_total_total_organs_total= df_total_total_organs.transpose()
                df_total_total_organs_total.index.name = 'Параметры, размерность'

                table_heading='Фармакокинетические параметры в различных тканях'
                list_heading_word.append(table_heading) 

                list_table_word.append(df_total_total_organs_total) 

                ###построение графика "Фармакокинетический профиль в органах"

                ### в линейных координатах

                list_list_mean_conc=[]
                list_list_std_conc=[]
                for i in list_df_for_mean_unround_for_graphics: 
                    mean_conc_list=i.loc['mean'].tolist()
                    std_conc_list=i.loc['std'].tolist()
                    list_list_mean_conc.append(mean_conc_list)
                    list_list_std_conc.append(std_conc_list)

                list_name_organs_std=[]
                for i in list_name_organs:
                 j= i + " std"
                 list_name_organs_std.append(j)
                
                list_time_new_df = list_t_graph[0]

                #if st.session_state["agree_injection - органы"] == True:
                   #list_time_new_df.insert(0,0)

                df_mean_conc_graph = pd.DataFrame(list_list_mean_conc, columns =list_time_new_df,index=list_name_organs)
                df_mean_conc_graph_1=df_mean_conc_graph.transpose()
                df_std_conc_graph = pd.DataFrame(list_list_std_conc, columns =list_time_new_df,index=list_name_organs_std)
                df_std_conc_graph_1=df_std_conc_graph.transpose()
                df_concat_mean_std= pd.concat([df_mean_conc_graph_1,df_std_conc_graph_1],sort=False,axis=1)

                list_colors = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]
                
                list_t_organs=list(df_concat_mean_std.index)

                #if st.session_state["agree_injection - органы"] == True:
                   #list_t_organs.remove(0)
                   #df_concat_mean_std=df_concat_mean_std.drop([0])

                list_zip_mean_std_colors=zip(list_name_organs,list_name_organs_std,list_colors)    

                fig, ax = plt.subplots()
                for i,j,c in list_zip_mean_std_colors:
                     plt.errorbar(list_t_organs,df_concat_mean_std[i],yerr=df_concat_mean_std[j],color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,label=i)
                     plt.xlabel(f"Время, {measure_unit_org_time}")
                     plt.ylabel("Концентрация, "+ measure_unit_org_blood)
                     ax.legend(fontsize = 5)
                
                list_graphics_word.append(fig)

                graphic='Сравнение фармакокинетических профилей (в линейных координатах) в органах'
                list_heading_graphics_word.append(graphic)

                ### в полулог. координатах

                list_t_organs=list(df_concat_mean_std.index)

                if st.session_state["agree_injection - органы"] == False:
                   list_t_organs.remove(0)
                   df_concat_mean_std=df_concat_mean_std.drop([0])

                list_zip_mean_std_colors=zip(list_name_organs,list_name_organs_std,list_colors)

                fig, ax = plt.subplots()
                for i,j,c in list_zip_mean_std_colors:
                     plt.errorbar(list_t_organs,df_concat_mean_std[i],yerr=df_concat_mean_std[j],color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,label=i)
                     ax.set_yscale("log")
                     plt.xlabel(f"Время, {measure_unit_org_time}")
                     plt.ylabel("Концентрация, "+ measure_unit_org_blood)
                     ax.legend(fontsize = 5)
                
                list_graphics_word.append(fig)

                graphic='Сравнение фармакокинетических профилей (в полулогарифмических координатах) в органах'
                list_heading_graphics_word.append(graphic)

                ###построение диаграммы для тканевой доступности

                #list_zip_list_ft_list_name_organs=zip(list_ft,list_name_organs)
                list_name_organs.remove("Кровь")

                fig, ax = plt.subplots()

                sns.barplot(x=list_name_organs, y=list_ft,color='blue',width=0.3)

                plt.ylabel("Тканевая доступность")

                ax.set_xticklabels(list_name_organs,fontdict={'fontsize': 6.0})

                list_graphics_word.append(fig)
                
                graphic='Тканевая доступность в органах'
                list_heading_graphics_word.append(graphic) 
                

         ###сохранение состояния 
         st.session_state["list_heading_word"] = list_heading_word
         st.session_state["list_table_word"] = list_table_word
         st.session_state["list_graphics_word"] = list_graphics_word
         st.session_state["list_heading_graphics_word"] = list_heading_graphics_word
   
   #отдельная панель, чтобы уменьшить размер вывода результатов

   col1, col2 = st.columns([0.66,0.34])
   
   with col1:

      #####Создание word отчета
      if panel == "Таблицы": 
         if st.session_state["df_total_PK_org"] is not None:
            list_heading_word = st.session_state["list_heading_word"]
            list_table_word = st.session_state["list_table_word"]

            ###вызов функции визуализации таблиц
            visualize_table(list_heading_word,list_table_word)

            with col2:
                 
                 selected = option_menu(None, ["Cформированный отчeт"], 
                 icons=['file-earmark-arrow-down-fill'], 
                 menu_icon="cast", default_index=0, orientation="vertical",
                 styles={
                        "container": {"padding": "0!important", "background-color": "#1f3b57"},
                        "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                        "nav-link-selected": {"background-color": "#73b5f2"},
                 })

                 if selected == "Cформированный отчeт":

                    ###вызов функции создания Word-отчета таблиц
                    create_table(list_heading_word,list_table_word)
         else:
             st.error("Введите и загрузите все необходимые данные!")

      if panel == "Графики":
         if st.session_state["df_total_PK_org"] is not None:

            list_graphics_word = st.session_state["list_graphics_word"]
            list_heading_graphics_word = st.session_state["list_heading_graphics_word"]
            
            #######визуализация

            #классификация графиков по кнопкам
            type_graphics = st.selectbox('Выберите вид графиков',
      ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля', "Сравнение фармакокинетических профилей в различных органах", "Тканевая доступность в органах"),disabled = False, key = "Вид графика - ИО" )

            count_graphics_for_visual = len(list_heading_graphics_word)
            list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)
            
            for i in list_range_count_graphics_for_visual:
                if list_heading_graphics_word[i].__contains__("индивидуального"): 
                   if type_graphics == 'Индивидуальные фармакокинетические профили':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Сравнение индивидуальных"):   
                   if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("усредненного"):
                   if type_graphics == 'Графики усредненного фармакокинетического профиля':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Сравнение фармакокинетических"):
                   if type_graphics == 'Сравнение фармакокинетических профилей в различных органах':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Тканевая"):
                   if type_graphics == 'Тканевая доступность в органах':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
            
            with col2:
                     
                 selected = option_menu(None, ["Cформированный отчeт"], 
                 icons=['file-earmark-arrow-down-fill'], 
                 menu_icon="cast", default_index=0, orientation="vertical",
                 styles={
                        "container": {"padding": "0!important", "background-color": "#1f3b57"},
                        "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                        "nav-link-selected": {"background-color": "#73b5f2"},
                 })
                  
                 if selected == "Cформированный отчeт":
                    ###вызов функции создания Word-отчета графиков
                    create_graphic(list_graphics_word,list_heading_graphics_word)
         else:
             st.error("Введите и загрузите все необходимые данные!")
################################################################################################

if option == 'Линейность дозирования':
   
   st.header('Исследование линейности дозирования')
   
   col1, col2 = st.columns([0.66, 0.34])

   with col1:

      panel = st.radio(
           "⚙️Панель управления",
           ("Загрузка файлов", "Таблицы","Графики"),
           horizontal=True, key= "Загрузка файлов - Исследование ФК параметров для линейности дозирования"
       )

      #cписки для word-отчета
      list_heading_word=[]
      list_table_word=[]
      list_graphics_word=[]
      list_heading_graphics_word=[]

      if panel == "Загрузка файлов":
         
         ######### боковое меню справа
         with col2:
              
              selected = option_menu(None, ["Настройка дополнительных параметров"], 
                    icons=['menu-button'], 
                    menu_icon="cast", default_index=0, orientation="vertical",
                    styles={
                      "container": {"padding": "0!important", "background-color": "#1f3b57"},
                      "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                      "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                      "nav-link-selected": {"background-color": "#73b5f2"},
                    })

              if selected == "Настройка дополнительных параметров":
                 type_parameter = st.selectbox('Выберите параметр',
                 ("Вид введения",'Двойные пики'),disabled = False, key = "Вид параметра - линейность")
                 
              if "agree_cmax2 - линейность" not in st.session_state:
                    st.session_state["agree_cmax2 - линейность"] = False

              if type_parameter == 'Двойные пики':

                 st.session_state["agree_cmax2 - линейность"] = st.checkbox('В зависимости "Концентрация-Время" отчетливо наблюдаются двойные пики', key = "Возможность добавления Cmax2 - линейность", value = st.session_state["agree_cmax2 - линейность"])
                 
                 if st.session_state["agree_cmax2 - линейность"] == True:
                    custom_success('Параметр добавлен!')

              if "agree_injection - линейность" not in st.session_state:
                    st.session_state["agree_injection - линейность"] = False

              if type_parameter == "Вид введения":

                 # Проверка наличия значения в сессии, если его нет, устанавливаем значение по умолчанию
                 if "injection_choice - линейность" not in st.session_state:
                     st.session_state["injection_choice - линейность"] = 0  # Значение по умолчанию

                 # Радиокнопка для выбора типа введения
                 injection_type = st.radio(
                     "Выберите тип введения:",
                     options=["Внутривенное введение", "Внесосудистое введение"],
                     index=st.session_state["injection_choice - линейность"],
                     key="injection_choice_линейность",  # Ключ для сохранения выбора в сессии
                 )

                 # Логика для обновления состояния сессии
                 if injection_type == "Внутривенное введение":
                     st.session_state["agree_injection - линейность"] = True
                     st.session_state["injection_choice - линейность"] = 0
                 else:
                     st.session_state["agree_injection - линейность"] = False
                     st.session_state["injection_choice - линейность"] = 1

                 # Сообщение в зависимости от выбора
                 if st.session_state["agree_injection - линейность"]:
                   custom_success("Выбрано: Внутривенное введение!")
                 else:
                   custom_success("Выбрано: Внесосудистое введение!")
         
         measure_unit_lin_time = select_time_unit("линейность")
         measure_unit_lin_concentration = select_concentration_unit("линейность")
         measure_unit_dose_lin = select_dose_unit("линейность")

         #cостояние радио-кнопки "method_auc"
         if "index_method_auc - ЛД" not in st.session_state:
             st.session_state["index_method_auc - ЛД"] = 0

         method_auc = st.radio("📈 Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = "Метод подсчёта AUC и AUMC - ЛД", index = st.session_state["index_method_auc - ЛД"])
         
         if st.session_state["Метод подсчёта AUC и AUMC - ЛД"] == 'linear':
            st.session_state["index_method_auc - ЛД"] = 0
         if st.session_state["Метод подсчёта AUC и AUMC - ЛД"] == "linear-up/log-down":
            st.session_state["index_method_auc - ЛД"] = 1
            
         custom_alert("Выберите нужное количество файлов соответственно количеству исследуемых дозировок (не менее 3-х файлов); файл должен быть назван соотвественно своей дозировке, например: 'Дозировка 50'. Если дозировка предcтавляет из себя дробное число, дробь писать через точку. Слово 'Дозировка' обязательно в верхнем регистре!")
         file_uploader = st.file_uploader("",accept_multiple_files=True, key='Файлы при исследовании линейности дозирования')
         
         if 'list_files_name_doses' not in st.session_state:
             st.session_state['list_files_name_doses'] = []

         ###сохранение файла
         list_files_name_doses = []
         if file_uploader is not None:
            for i in file_uploader:
                save_uploadedfile(i)
                st.session_state[str(i.name)] = i.name
                list_files_name_doses.append(i.name)
         
         st.session_state['list_files_name_doses'] = list_files_name_doses
         
         if st.session_state['list_files_name_doses'] != []: 
              custom_success(f"Файлы загружены: {', '.join(st.session_state['list_files_name_doses'])}")
         
         list_keys_file_lin = []
         for i in st.session_state.keys():
             if i.__contains__("xlsx") and i.__contains__("Дозировка") and (not i.__contains__("edited_df")): ###слово дозировка нужно, чтобы отличать файлы от других xlsx органов, т.к там тоже ключи имя файла; #обрезаем фразу ненужного добавления названия "edited_df"
                list_keys_file_lin.append(i)

         if (list_keys_file_lin != []) and measure_unit_lin_concentration and measure_unit_dose_lin:

             list_name_doses=[]
             list_df_unrounded=[]
             list_df_for_mean_unround_for_graphics=[]
             list_t_graph=[]
             
             list_keys_file_lin_float = []
             for i in list_keys_file_lin:
                 if "." in i[10:-5]: 
                    list_keys_file_lin_float.append(float(i[10:-5]))
                 else:
                    list_keys_file_lin_float.append(int(i[10:-5]))
             list_keys_file_lin_float.sort()

             list_keys_file_lin = [f"Дозировка {str(float)}.xlsx" for float in list_keys_file_lin_float]

             for i in list_keys_file_lin:
                 df = pd.read_excel(os.path.join("Папка для сохранения файлов",i))

                 file_name=i[10:-5]

                 st.subheader('Индивидуальные значения концентраций в дозировке ' +file_name+" "+ measure_unit_dose_lin)
                 
                 ###интерактивная таблица
                 df = edit_frame(df,i)

                 ###количество животных 
                 count_rows_number_lin= len(df.axes[0])

                 table_heading='Индивидуальные и усредненные значения концентраций в дозировке ' +file_name+" "+ measure_unit_dose_lin
                 list_heading_word.append(table_heading)

                 ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                 df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']

                 list_table_word.append(df_concat_round_str_transpose)

                 ########### графики    
                 
                 ######индивидуальные    

                 # в линейных координатах
                 col_mapping = df.columns.tolist()
                 col_mapping.remove('Номер')

                 count_row_df = len(df.axes[0])

                 list_time = []
                 for i in col_mapping:
                     numer=float(i)
                     list_time.append(numer)
                 list_t_graph.append(list_time) 

                 #if st.session_state["agree_injection - линейность"] == True: 
                    #list_time.remove(0)

                 for r in range(0,count_row_df):

                     list_concentration=df.iloc[r].tolist()

                     numer_animal=list_concentration[0]

                     list_concentration.pop(0) #удаление номера животного

                     list_concentration = [float(v) for v in list_concentration]

                     #if st.session_state["agree_injection - линейность"] == True:
                        #list_concentration.remove(0)

                     fig, ax = plt.subplots()
                     plt.plot(list_time,list_concentration,marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                     plt.xlabel(f"Время, {measure_unit_lin_time}")
                     plt.ylabel("Концентрация, "+measure_unit_lin_concentration)
                     
                     list_graphics_word.append(fig)
        
                     graphic='График индивидуального фармакокинетического профиля в линейных координатах в дозировке '  +file_name+" "+ measure_unit_dose_lin+',  '+numer_animal
                     list_heading_graphics_word.append(graphic) 

                  #в полулогарифмических координатах методом удаления точек
                     count_for_0_1=len(list_concentration)
                     list_range_for_0_1=range(0,count_for_0_1)

                     list_time_0=[]
                     list_for_log_1=[]
                     for i in list_range_for_0_1:
                         if list_concentration[i] !=0:
                            list_for_log_1.append(list_concentration[i])
                            list_time_0.append(list_time[i]) 

                     fig, ax = plt.subplots()
                     plt.plot(list_time_0,list_for_log_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
                     ax.set_yscale("log")
                     plt.xlabel(f"Время, {measure_unit_lin_time}")
                     plt.ylabel("Концентрация, "+measure_unit_lin_concentration)

                     
                     list_graphics_word.append(fig)
                     
                     graphic='График индивидуального фармакокинетического профиля в полулогарифмических координатах в дозировке ' +file_name+" "+ measure_unit_dose_lin+',  '+numer_animal
                     list_heading_graphics_word.append(graphic) 

              # объединенные индивидуальные в линейных координатах

                 df_for_plot_conc=df.drop(['Номер'], axis=1)
                 df_for_plot_conc_1 = df_for_plot_conc.transpose()

                 if st.session_state["agree_injection - линейность"] == True:
                    df_for_plot_conc_1=df_for_plot_conc_1.replace(0, None) ###т.к. внутривенное

                 list_numer_animal_for_plot=df['Номер'].tolist()
                 count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

                 list_color = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]

                 fig, ax = plt.subplots()

                 ax.set_prop_cycle(cycler(color=list_color))

                 plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

                 ax.set_xlabel(f"Время, {measure_unit_lin_time}")
                 ax.set_ylabel("Концентрация, "+measure_unit_lin_concentration)
                 if count_numer_animal > 20:
                    ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
                 else:
                    ax.legend(bbox_to_anchor=(1, 1))
                 
                 list_graphics_word.append(fig)
                 
                 graphic="Сравнение индивидуальных фармакокинетических профилей в линейных координатах в дозировке " +file_name+" "+ measure_unit_dose_lin
                 list_heading_graphics_word.append(graphic) 
          
              # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
                 df_for_plot_conc_1_log=df_for_plot_conc_1.replace(0, None)


                 fig, ax = plt.subplots()

                 ax.set_prop_cycle(cycler(color=list_color))

                 plt.plot(df_for_plot_conc_1_log,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

                 ax.set_xlabel(f"Время, {measure_unit_lin_time}")
                 ax.set_ylabel("Концентрация, "+measure_unit_lin_concentration)
                 ax.set_yscale("log")
                 if count_numer_animal > 20:
                    ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
                 else:
                    ax.legend(bbox_to_anchor=(1, 1))
                 
                 list_graphics_word.append(fig)
                 
                 graphic="Сравнение индивидуальных фармакокинетических профилей в полулогарифмических координатах в дозировке " +file_name+" "+ measure_unit_dose_lin
                 list_heading_graphics_word.append(graphic) 
                  ###усредненные    
              # в линейных координатах
                 list_time = []
                 for i in col_mapping:
                     numer=float(i)
                     list_time.append(numer)

                 df_averaged_concentrations=df.describe()
                 list_concentration=df_averaged_concentrations.loc['mean'].tolist()
                 err_y_1=df_averaged_concentrations.loc['std'].tolist()

                 #if st.session_state["agree_injection - линейность"] == True:
                    #list_time.remove(0) ###т.к. внутривенное
                    #list_concentration.remove(0)
                    #err_y_1.remove(0)

                 fig, ax = plt.subplots()
                 plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
                 plt.xlabel(f"Время, {measure_unit_lin_time}")
                 plt.ylabel("Концентрация, "+measure_unit_lin_concentration)
                  
                 list_graphics_word.append(fig)
                 
                 graphic='График усредненного фармакокинетического профиля в линейных координатах в дозировке ' +file_name+" "+ measure_unit_dose_lin
                 list_heading_graphics_word.append(graphic)

              #в полулогарифмических координатах
                 #для полулогарифм. посторим без нуля
                 if st.session_state["agree_injection - линейность"] == False:
                    list_time.remove(0)
                    list_concentration.remove(0)
                    err_y_1.remove(0) 

                 fig, ax = plt.subplots()
                 plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
                 ax.set_yscale("log")
                 plt.xlabel(f"Время, {measure_unit_lin_time}")
                 plt.ylabel("Концентрация, "+measure_unit_lin_concentration)

                 list_graphics_word.append(fig)
                 
                 graphic='График усредненного фармакокинетического профиля в полулогарифмических координатах ' +file_name+" "+ measure_unit_dose_lin
                 list_heading_graphics_word.append(graphic)

                 ############ Параметры ФК

                 if f"agree_cmax2 - линейность {file_name}" not in st.session_state:
                    st.session_state[f"agree_cmax2 - линейность {file_name}"] = False
                 
                 if st.session_state["agree_cmax2 - линейность"] == True:
                    st.session_state[f"agree_cmax2 - линейность {file_name}"] = True


                 if st.session_state["agree_injection - линейность"] == False:
                     result_PK = pk_parametrs_total_extravascular(df,f"линейность {file_name}",method_auc,float(file_name),measure_unit_lin_concentration,measure_unit_lin_time,measure_unit_dose_lin)
                 else:
                     result_PK = pk_parametrs_total_intravenously(df,f"линейность {file_name}",method_auc,float(file_name),measure_unit_lin_concentration,measure_unit_lin_time,measure_unit_dose_lin)

                 if result_PK is not None:
                     if st.session_state["agree_cmax2 - линейность"] == False:
                        df_total_PK_lin = result_PK["df_total_PK"]
                        df_concat_PK_lin = result_PK["df_concat_PK"]
                        list_cmax_1_lin = result_PK["list_cmax_1"]
                     if st.session_state["agree_cmax2 - линейность"] == True:
                        df_total_PK_lin = result_PK["df_total_PK"]
                        df_concat_PK_lin = result_PK["df_concat_PK"]
                        list_cmax_1_lin = result_PK["list_cmax_1"]
                        list_cmax_2_lin = result_PK["list_cmax_2"]
                        df_total_PK_additional_double_peaks_lin = result_PK["df_total_PK_additional_double_peaks"]
                         
                     st.session_state["df_total_PK_lin"] = df_total_PK_lin

                     table_heading='Фармакокинетические показатели препарата в дозировке ' +file_name +" "+ measure_unit_dose_lin
                     list_heading_word.append(table_heading)

                     list_table_word.append(df_total_PK_lin)

                     if st.session_state["agree_cmax2 - линейность"] == True:
                        table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле ' +file_name +" "+ measure_unit_dose_lin
                        list_heading_word.append(table_heading)
                        
                        list_table_word.append(df_total_PK_additional_double_peaks_lin)

                     #создание списков фреймов, доз и т.д.

                     ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                     df_concat = create_table_descriptive_statistics(df)['df_concat']

                     list_name_doses.append(file_name)
                     list_df_unrounded.append(df_concat_PK_lin)
                     list_df_for_mean_unround_for_graphics.append(df_concat)
                 else:
                     st.session_state["df_total_PK_lin"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                     st.error("Выберете необходимое количество значений Cmax и Cmax(2)")

             ###Кнопка активации дальнейших действий
             button_calculation = False
             
             if (list_keys_file_lin != []) and measure_unit_lin_concentration and measure_unit_dose_lin  and result_PK is not None:
              
                condition_cmax1 =  len(list_cmax_1_lin) == count_rows_number_lin
                
                if st.session_state["agree_cmax2 - линейность"] == True:
                   condition_cmax2 =  len(list_cmax_2_lin) == count_rows_number_lin
                
                if st.session_state["agree_cmax2 - линейность"] == True:
                   if (condition_cmax2):
                      button_calculation = True
                if st.session_state["agree_cmax2 - линейность"] == False:
                   if (condition_cmax1):
                      button_calculation = True

                if button_calculation == True:
                   custom_success('Расчеты произведены!')
                else:   
                   st.error('🔧Заполните все поля ввода и загрузите файлы!')
             
             if (list_keys_file_lin != []) and measure_unit_lin_concentration and measure_unit_dose_lin and button_calculation:
                
                
                list_list_PK_par_mean=[]
                for i in list_df_unrounded: 
                    mean_сmax=i['Cmax'].loc['mean']
                    mean_tmax=i['Tmax'].loc['mean']
                    mean_mrt0inf=i['MRT0→∞'].loc['mean']
                    mean_thalf=i['T1/2'].loc['mean']
                    mean_auc0t=i['AUC0-t'].loc['mean']
                    mean_auc0inf=i['AUC0→∞'].loc['mean']
                    mean_aumc0inf=i['AUMC0-∞'].loc['mean']
                    mean_сmaxdevaucot=i['Сmax/AUC0-t'].loc['mean']
                    mean_kel=i['Kel'].loc['mean']
                    if st.session_state["agree_injection - линейность"] == False:
                       mean_cl=i['Cl/F'].loc['mean']
                       mean_vd=i['Vz/F'].loc['mean']
                    else:
                       mean_cl=i['Cl'].loc['mean']
                       mean_vd=i['Vz'].loc['mean']
                    list_list_PK_par_mean.append([mean_сmax,mean_tmax,mean_mrt0inf,mean_thalf,mean_auc0t,mean_auc0inf,mean_aumc0inf,mean_сmaxdevaucot,mean_kel,mean_cl,mean_vd]) 

                list_name_doses_with_measure_unit=[]
                for i in list_name_doses:
                 j= i + " " + measure_unit_dose_lin
                 list_name_doses_with_measure_unit.append(j)

                ### получение итогового фрейма ФК параметров доз
                if st.session_state["agree_injection - линейность"] == False:
                   df_PK_doses_total = pd.DataFrame(list_list_PK_par_mean, columns =['Cmax ' +"("+measure_unit_lin_concentration+")",'Tmax ' +"("+f"{measure_unit_lin_time}"+")",'MRT0→∞ '+"("+f"{measure_unit_lin_time}"+")",'T1/2 '+"("+f"{measure_unit_lin_time}"+")",'AUC0-t '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}" +")",'AUC0→∞ '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}" +")",'AUMC0-∞ '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}\u00B2" +")",'Сmax/AUC0-t '+"("+f"{measure_unit_lin_time}\u207B\u00B9"+")",'Kel '+"("+f"{measure_unit_lin_time}\u207B\u00B9"+")",'Cl/F ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})/{measure_unit_lin_time}"+")",'Vz/F ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})"+")"],index=list_name_doses_with_measure_unit)
                else:
                   df_PK_doses_total = pd.DataFrame(list_list_PK_par_mean, columns =['Cmax ' +"("+measure_unit_lin_concentration+")",'Tmax ' +"("+f"{measure_unit_lin_time}"+")",'MRT0→∞ '+"("+f"{measure_unit_lin_time}"+")",'T1/2 '+"("+f"{measure_unit_lin_time}"+")",'AUC0-t '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}" +")",'AUC0→∞ '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}" +")",'AUMC0-∞ '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}\u00B2" +")",'Сmax/AUC0-t '+"("+f"{measure_unit_lin_time}\u207B\u00B9"+")",'Kel '+"("+f"{measure_unit_lin_time}\u207B\u00B9"+")",'Cl ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})/{measure_unit_lin_time}"+")",'Vz ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})"+")"],index=list_name_doses_with_measure_unit)
                
                df_PK_doses_total_transpose=df_PK_doses_total.transpose()

                #округление фрейма df_PK_doses_total_transpose

                df_doses_trans_trans=df_PK_doses_total_transpose.transpose()

                series_Cmax=df_doses_trans_trans['Cmax ' +"("+measure_unit_lin_concentration+")"].tolist() 
                series_Cmax=pd.Series([v for v in series_Cmax])

                series_Tmax=df_doses_trans_trans['Tmax ' +"("+f"{measure_unit_lin_time}"+")"].tolist()       
                series_Tmax=pd.Series([v for v in series_Tmax])

                series_MRT0_inf= df_doses_trans_trans['MRT0→∞ '+"("+f"{measure_unit_lin_time}"+")"].tolist()   
                series_MRT0_inf=pd.Series([v for v in series_MRT0_inf])

                series_half_live= df_doses_trans_trans['T1/2 '+"("+f"{measure_unit_lin_time}"+")"].tolist()   
                series_half_live=pd.Series([v for v in series_half_live]) 

                series_AUC0_t= df_doses_trans_trans['AUC0-t '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}" +")"].tolist()   
                series_AUC0_t=pd.Series([v for v in series_AUC0_t])

                series_AUC0_inf= df_doses_trans_trans['AUC0→∞ '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}" +")"].tolist()  
                series_AUC0_inf=pd.Series([v for v in series_AUC0_inf]) 

                series_AUMC0_inf= df_doses_trans_trans['AUMC0-∞ '+"("+measure_unit_lin_concentration+f"×{measure_unit_lin_time}\u00B2" +")"].tolist()   
                series_AUMC0_inf=pd.Series([v for v in series_AUMC0_inf])

                series_Сmax_dev_AUC0_t= df_doses_trans_trans['Сmax/AUC0-t '+"("+f"{measure_unit_lin_time}\u207B\u00B9"+")"].tolist()  
                series_Сmax_dev_AUC0_t=pd.Series([v for v in series_Сmax_dev_AUC0_t]) 

                series_Kel= df_doses_trans_trans['Kel '+"("+f"{measure_unit_lin_time}\u207B\u00B9"+")"].tolist()   
                series_Kel=pd.Series([v for v in series_Kel])
                
                if st.session_state["agree_injection - линейность"] == False:
                   series_CL= df_doses_trans_trans['Cl/F ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})/{measure_unit_lin_time}"+")"].tolist()  
                   series_CL=pd.Series([v for v in series_CL]) 

                   series_Vd= df_doses_trans_trans['Vz/F ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})"+")"].tolist()   
                   series_Vd=pd.Series([v for v in series_Vd])
                else:
                   series_CL= df_doses_trans_trans['Cl ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})/{measure_unit_lin_time}"+")"].tolist()  
                   series_CL=pd.Series([v for v in series_CL]) 

                   series_Vd= df_doses_trans_trans['Vz ' +"("+f"({measure_unit_dose_lin})/({measure_unit_lin_concentration})"+")"].tolist()   
                   series_Vd=pd.Series([v for v in series_Vd])
                
                df_total_total_doses = pd.concat([series_Cmax, series_Tmax,series_MRT0_inf,series_half_live,series_AUC0_t,series_AUC0_inf,series_AUMC0_inf,series_Сmax_dev_AUC0_t,series_Kel,series_CL,series_Vd], axis= 1)

                df_total_total_doses.index=df_PK_doses_total_transpose.columns.tolist()
                df_total_total_doses.columns=df_PK_doses_total_transpose.index.tolist() 

                df_total_total_doses_total= df_total_total_doses.transpose()
                df_total_total_doses_total.index.name = 'Параметры, размерность'
             
                table_heading='Фармакокинетические параметры препарата в различных дозировках'
                list_heading_word.append(table_heading)

                list_table_word.append(df_total_total_doses_total)

                ###построение графика "Фармакокинетический профиль в различных дозировках"

                ### в линейных координатах
                list_list_mean_conc=[]
                list_list_std_conc=[]
                for i in list_df_for_mean_unround_for_graphics: 
                    mean_conc_list=i.loc['mean'].tolist()
                    std_conc_list=i.loc['std'].tolist()
                    list_list_mean_conc.append(mean_conc_list)
                    list_list_std_conc.append(std_conc_list)

                list_name_doses_with_measure_unit_std=[]
                for i in list_name_doses_with_measure_unit:
                 j= i + " std"
                 list_name_doses_with_measure_unit_std.append(j)

                list_time_new_df = list_t_graph[0]

                #if st.session_state["agree_injection - линейность"] == True:
                   #list_time_new_df.insert(0,0)

                df_mean_conc_graph = pd.DataFrame(list_list_mean_conc, columns =list_time_new_df,index=list_name_doses_with_measure_unit)
                df_mean_conc_graph_1=df_mean_conc_graph.transpose()
                df_std_conc_graph = pd.DataFrame(list_list_std_conc, columns =list_time_new_df,index=list_name_doses_with_measure_unit_std)
                df_std_conc_graph_1=df_std_conc_graph.transpose()
                df_concat_mean_std= pd.concat([df_mean_conc_graph_1,df_std_conc_graph_1],sort=False,axis=1)

                list_colors = ["black","red","blue","green","#D6870C"]

                list_t_doses=list(df_concat_mean_std.index)

                #if st.session_state["agree_injection - линейность"] == True:
                   #list_t_doses.remove(0)
                   #df_concat_mean_std=df_concat_mean_std.drop([0])
                    
                list_zip_mean_std_colors=zip(list_name_doses_with_measure_unit,list_name_doses_with_measure_unit_std,list_colors)

                fig, ax = plt.subplots()
                for i,j,c in list_zip_mean_std_colors:
                     plt.errorbar(list_t_doses,df_concat_mean_std[i],yerr=df_concat_mean_std[j],color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,label=i)
                     plt.xlabel(f"Время, {measure_unit_lin_time}")
                     plt.ylabel("Концентрация, "+ measure_unit_lin_concentration)
                     ax.legend(fontsize = 8)
               
                list_graphics_word.append(fig)

                graphic='Сравнение фармакокинетических профилей (в линейных координатах) в различных дозировках'
                list_heading_graphics_word.append(graphic) 

                ### в полулог. координатах

                list_t_doses=list(df_concat_mean_std.index)

                if st.session_state["agree_injection - линейность"] == False:
                   list_t_doses.remove(0)
                   df_concat_mean_std=df_concat_mean_std.drop([0])
                
                list_zip_mean_std_colors=zip(list_name_doses_with_measure_unit,list_name_doses_with_measure_unit_std,list_colors)

                fig, ax = plt.subplots()
                for i,j,c in list_zip_mean_std_colors:
                     plt.errorbar(list_t_doses,df_concat_mean_std[i],yerr=df_concat_mean_std[j],color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,label=i)
                     ax.set_yscale("log")
                     plt.xlabel(f"Время, {measure_unit_lin_time}")
                     plt.ylabel("Концентрация, "+ measure_unit_lin_concentration)
                     ax.legend(fontsize = 8)
                
                list_graphics_word.append(fig)

                graphic='Сравнение фармакокинетических профилей (в полулогарифмических координатах) в различных дозировках'
                list_heading_graphics_word.append(graphic)
                
                # Линейность
                list_AUC0_inf_lin = []
                for i in list_df_unrounded: 
                    # Получаем значения AUC0→∞ для каждой дозы и добавляем в список
                    mean_auc0inf = i['AUC0→∞'][:'count'].iloc[:-1].to_list()
                    list_AUC0_inf_lin.extend(mean_auc0inf)  # Используем extend, чтобы создать плоский список

                # Создаем правильный список дозировок, повторяя каждый элемент нужное количество раз
                list_name_doses_lin_float = [float(dose) for dose in list_name_doses for _ in range(len(mean_auc0inf))]

                # Убедимся, что данные организованы правильно
                # Создаем DataFrame для анализа
                df_for_lin = pd.DataFrame({
                    'AUC0→∞': list_AUC0_inf_lin,
                    'doses': list_name_doses_lin_float
                })

                # Зависимая переменная
                AUC0_inf = df_for_lin['AUC0→∞']

                # Добавляем константу для модели
                doses_with_const = sm.add_constant(df_for_lin['doses'])

                # Строим модель линейной регрессии
                model = sm.OLS(AUC0_inf, doses_with_const).fit()
                
                df1_model = int(round(model.df_model,0))
                st.session_state['df1_model_lin'] = df1_model
                df2_model = int(round(model.df_resid,0))
                st.session_state['df2_model_lin'] = df2_model
                
                print_model = model.summary()

                # Выводим результаты модели
                #st.write(print_model)

                graphic='Зависимость значений AUC0→∞ от величин вводимых доз'
                list_heading_graphics_word.append(graphic)

                # Данные для графика
                list_AUC0_inf_lin_mean = []
                for i in list_df_unrounded: 
                    # Получаем значения AUC0→∞ для каждой дозы и добавляем в список
                    mean_auc0_inf_mean = i['AUC0→∞'].loc['mean']
                    list_AUC0_inf_lin_mean.append(mean_auc0_inf_mean)
                
                list_name_doses_lin_float = [float(i) for i in list_name_doses]


                # Создаем DataFrame для анализа
                df_for_lin_mean = pd.DataFrame({
                    'AUC0→∞_mean': list_AUC0_inf_lin_mean,
                    'doses': list_name_doses_lin_float
                })

                ###график
                fig, ax = plt.subplots()
                sns.regplot(x='doses',y='AUC0→∞_mean',data=df_for_lin_mean, color="black",ci=None,scatter_kws = {'s': 30}, line_kws = {'linewidth': 1})
                plt.xlabel("Дозировка, " +measure_unit_dose_lin)
                plt.ylabel("AUC0→∞, "+ measure_unit_lin_concentration + f"*{measure_unit_lin_time}")
                plt.annotate('y = ' + "%.4f" % round(model.params[1],4) +'x ' + "%.4f" % round(model.params[0],4), xy =(110, 530),xytext =(110, 530),fontsize=10)
                plt.annotate(r"$y = %.4f x + %.4f$" % (round(model.params[1], 4), round(model.params[0], 4)), xy=(110, 530), xytext=(110, 530), fontsize=10)
                
                list_graphics_word.append(fig)

                graphic='Коэффициент линейной регрессии и критерий Фишера значимости линейной регрессии для параметра AUC0→∞'
                list_heading_graphics_word.append(graphic)

                # параметры линейной регрессии
                fig, ax = plt.subplots()
                table_data_first=[
                 ["R","R²","F","df1","df2","p"],
                 ["%.3f" % round(np.sqrt(model.rsquared),3),"%.3f" % round(model.rsquared,3), "%.1f" % round(model.fvalue,1),int(round(model.df_model,0)),int(round(model.df_resid,0)), format_pvalue(model.pvalues[1])]
                 ]
                table = ax.table(cellText=table_data_first,cellLoc='left',bbox = [0, 0.7, 0.7, 0.1])
                plt.annotate('Model Fit Measures', xy =(0, 0.9),xytext =(0, 0.9),fontsize=10)
                plt.annotate('Overall Model Test', xy =(0, 0.85),xytext =(0, 0.85),fontsize=10)
                table_data_second=[
                 ['Predictor','Estimate','SE','t','p'],
                 ["Intercept","%.2f" % round(model.params[0],2),"%.3f" % round(model.bse[0],3),"%.2f" % round(model.tvalues[0],2), format_pvalue(model.pvalues[0]),],
                 ["B","%.2f" % round(model.params[1],2),"%.3f" % round(model.bse[1],3),"%.2f" % round(model.tvalues[1],2), format_pvalue(model.pvalues[1])]
                 ]
                table = ax.table(cellText=table_data_second,cellLoc='left',bbox = [0, 0.35, 0.7, 0.2])
                plt.annotate('Model Coefficients', xy =(0, 0.6),xytext =(0, 0.6),fontsize=10)
                plt.axis('off')
                
                list_graphics_word.append(fig)

         ###сохранение состояния 
         st.session_state["list_heading_word"] = list_heading_word
         st.session_state["list_table_word"] = list_table_word
         st.session_state["list_graphics_word"] = list_graphics_word
         st.session_state["list_heading_graphics_word"] = list_heading_graphics_word

   #отдельная панель, чтобы уменьшить размер вывода результатов

   col1, col2 = st.columns([0.66,0.34])
   
   with col1:      
      
      #####Создание word отчета
      if panel == "Таблицы":
         if st.session_state["df_total_PK_lin"] is not None: 
      
            list_heading_word = st.session_state["list_heading_word"]
            list_table_word = st.session_state["list_table_word"]
            
            ###вызов функции визуализации таблиц
            visualize_table(list_heading_word,list_table_word)

            with col2:
                 
                 selected = option_menu(None, ["Cформированный отчeт"], 
                 icons=['file-earmark-arrow-down-fill'], 
                 menu_icon="cast", default_index=0, orientation="vertical",
                 styles={
                        "container": {"padding": "0!important", "background-color": "#1f3b57"},
                        "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                        "nav-link-selected": {"background-color": "#73b5f2"},
                 })

                 if selected == "Cформированный отчeт":

                    ###вызов функции создания Word-отчета таблиц
                    create_table(list_heading_word,list_table_word)
         else:
             st.error("Введите и загрузите все необходимые данные!")

      if panel == "Графики":
         if st.session_state["df_total_PK_lin"] is not None: 
            list_graphics_word = st.session_state["list_graphics_word"]
            list_heading_graphics_word = st.session_state["list_heading_graphics_word"]
                
            #######визуализация

            #классификация графиков по кнопкам
            type_graphics = st.selectbox('Выберите вид графиков',
      ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля', "Сравнение фармакокинетических профилей в различных дозировках", "Зависимость значений AUC0→∞ от величин вводимых доз", "Коэффициент линейной регрессии и критерий Фишера значимости линейной регрессии для параметра AUC0→∞"),disabled = False, key = "Вид графика - ИО" )

            count_graphics_for_visual = len(list_heading_graphics_word)
            list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)
            
            for i in list_range_count_graphics_for_visual:
                if list_heading_graphics_word[i].__contains__("индивидуального"): 
                   if type_graphics == 'Индивидуальные фармакокинетические профили':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Сравнение индивидуальных"):   
                   if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("усредненного"):
                   if type_graphics == 'Графики усредненного фармакокинетического профиля':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Сравнение фармакокинетических"):
                   if type_graphics == 'Сравнение фармакокинетических профилей в различных дозировках':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Зависимость"):
                   if type_graphics == 'Зависимость значений AUC0→∞ от величин вводимых доз':
                      st.pyplot(list_graphics_word[i])
                      st.subheader(list_heading_graphics_word[i])
                if list_heading_graphics_word[i].__contains__("Коэффициент"):
                   if type_graphics == 'Коэффициент линейной регрессии и критерий Фишера значимости линейной регрессии для параметра AUC0→∞':

                      col3, col4 = st.columns([2, 1])

                      with col3:
                           st.pyplot(list_graphics_word[i])
                           st.subheader(list_heading_graphics_word[i])

                      with col4:
                           # Заголовок
                           st.text("Критическое значение F")

                           # Установка начальных значений для сессии
                           if 'alpha' not in st.session_state:
                               st.session_state.alpha = 0.05

                           if 'df1' not in st.session_state:
                               st.session_state.df1 = st.session_state['df1_model_lin']

                           if 'df2' not in st.session_state:
                               st.session_state.df2 = st.session_state['df2_model_lin']

                           # Ввод уровня значимости (alpha)
                           alpha = st.number_input("Уровень значимости (alpha)", min_value=0.01, max_value=0.10, value=st.session_state.alpha, step=0.01, format="%.2f")

                           # Ввод степеней свободы для числителя (df1)
                           df1 = st.number_input("Степени свободы для числителя (df1)", min_value=1, value=st.session_state.df1, step=1)

                           # Ввод степеней свободы для знаменателя (df2)
                           df2 = st.number_input("Степени свободы для знаменателя (df2)", min_value=1, value=st.session_state.df2, step=1)

                           # Обновление значений в сессии
                           st.session_state.alpha = alpha
                           st.session_state.df1 = df1
                           st.session_state.df2 = df2

                           # Кнопка для расчета
                           if st.button("Рассчитать"):
                               f_critical = calculate_f_critical(alpha, df1, df2)
                               st.write(f"Критическое значение F: {f_critical:.3f}")

            with col2:
                     
                 selected = option_menu(None, ["Cформированный отчeт"], 
                 icons=['file-earmark-arrow-down-fill'], 
                 menu_icon="cast", default_index=0, orientation="vertical",
                 styles={
                        "container": {"padding": "0!important", "background-color": "#1f3b57"},
                        "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                        "nav-link-selected": {"background-color": "#73b5f2"},
                 })
                  
                 if selected == "Cформированный отчeт":
                    ###вызов функции создания Word-отчета графиков
                    create_graphic(list_graphics_word,list_heading_graphics_word)
         else:
             st.error("Введите и загрузите все необходимые данные!")

###########################################################################################
if option == 'Экскреция препарата':
    
    st.header('Изучение экскреции препарата')

    col1, col2 = st.columns([0.66, 0.34])
    
    ####### основной экран
    with col1:         
         panel = st.radio(
            "⚙️Панель управления",
            ("Загрузка файлов", "Таблицы","Графики"),
            horizontal=True, key= "Загрузка файлов - Изучение экскреции препарата"
         )
                     
         #cписки для word-отчета
         list_heading_word=[]
         list_table_word=[]
         list_graphics_word=[]
         list_heading_graphics_word=[]

         if panel == "Загрузка файлов":
            

            #cостояние радио-кнопки "type_ex"
            if "index_type_ex" not in st.session_state:
                st.session_state["index_type_ex"] = 0

            type_excretion = st.radio('🧴 Выберите вид экскреции',('Фекалии', 'Моча', 'Желчь'), key = "Вид экскреции",index = st.session_state["index_type_ex"])
            
            if st.session_state["Вид экскреции"] == 'Фекалии':
               st.session_state["index_type_ex"] = 0
            if st.session_state["Вид экскреции"] == 'Моча':
               st.session_state["index_type_ex"] = 1
            if st.session_state["Вид экскреции"] == 'Желчь':
               st.session_state["index_type_ex"] = 2

            if type_excretion == 'Фекалии':
               excretion_tv = "фекалиями"
               excretion_pr = "фекалиях"
            if type_excretion == 'Моча':
               excretion_tv = "мочой"
               excretion_pr = "моче"
            if type_excretion == 'Желчь':
               excretion_tv = "желчью"
               excretion_pr = "желчи"

            st.subheader('Исследование экскреции с ' + excretion_tv)

            measure_unit_ex_time =select_time_unit("экскреция")
            measure_unit_ex_concentration = select_concentration_unit("экскреция")

            uploaded_file_excrement = st.file_uploader("Выбрать файл экскреции (формат XLSX)", key="Файл экскреции")

            if uploaded_file_excrement is not None:
                save_uploadedfile(uploaded_file_excrement)
                st.session_state["uploaded_file_excrement"] = uploaded_file_excrement.name
            
            if "uploaded_file_excrement" in st.session_state: 
               custom_success(f"Файл загружен: {st.session_state['uploaded_file_excrement']}")

            if "uploaded_file_excrement" in st.session_state and measure_unit_ex_concentration:
                
                df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_excrement"]))
                st.subheader('Индивидуальные значения концентраций в ' + excretion_pr)
                
                ###интерактивная таблица
                df = edit_frame(df,st.session_state["uploaded_file_excrement"])

                table_heading='Индивидуальные и усредненные значения концентраций в ' + excretion_pr
                list_heading_word.append(table_heading) 

                ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                df_concat_round_str_transpose = create_table_descriptive_statistics(df)['df_concat_round_str_transpose']

                list_table_word.append(df_concat_round_str_transpose)

                ########### диаграмма    
                
                col_mapping = df.columns.tolist()
                col_mapping.remove('Номер')

                list_time = []
                for i in col_mapping:
                    numer=float(i)
                    list_time.append(numer)
                
                df_averaged_concentrations=df.describe()
                list_concentration=df_averaged_concentrations.loc['mean'].tolist()

                list_concentration.remove(0)
                list_time.remove(0)

                fig, ax = plt.subplots()

                sns.barplot(x=list_time, y=list_concentration,color='blue',width=0.5)
                plt.xlabel(f"Время, {measure_unit_ex_time}")
                plt.ylabel("Концентрация, "+measure_unit_ex_concentration)

                list_graphics_word.append(fig)

                graphic='Выведение с ' + excretion_tv
                list_heading_graphics_word.append(graphic)
            else:
               st.write("")    
            
            ##############################################################################################################

            ###сохранение состояния 
            st.session_state["list_heading_word"] = list_heading_word
            st.session_state["list_table_word"] = list_table_word
            st.session_state["list_graphics_word"] = list_graphics_word
            st.session_state["list_heading_graphics_word"] = list_heading_graphics_word
         
    #отдельная панель, чтобы уменьшить размер вывода результатов

    col1, col2 = st.columns([0.66,0.34])
    
    with col1:

       #####Создание word отчета
       if panel == "Таблицы":

             list_heading_word = st.session_state["list_heading_word"]
             list_table_word = st.session_state["list_table_word"]

             ###вызов функции визуализации таблиц
             visualize_table(list_heading_word,list_table_word)

             with col2:
                  
                  selected = option_menu(None, ["Cформированный отчeт"], 
                  icons=['file-earmark-arrow-down-fill'], 
                  menu_icon="cast", default_index=0, orientation="vertical",
                  styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                  })

                  if selected == "Cформированный отчeт":

                     ###вызов функции создания Word-отчета таблиц
                     create_table(list_heading_word,list_table_word)

       if panel == "Графики":
             
             list_graphics_word = st.session_state["list_graphics_word"]
             list_heading_graphics_word = st.session_state["list_heading_graphics_word"]

             #######визуализация

             count_graphics_for_visual = len(list_heading_graphics_word)
             list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)
             
             for i in list_range_count_graphics_for_visual:
                 if list_heading_graphics_word[i].__contains__("Выведение"):
                    st.pyplot(list_graphics_word[i])
                    st.subheader(list_heading_graphics_word[i])
                    
             with col2:
             
                  selected = option_menu(None, ["Cформированный отчeт"], 
                  icons=['file-earmark-arrow-down-fill'], 
                  menu_icon="cast", default_index=0, orientation="vertical",
                  styles={
                     "container": {"padding": "0!important", "background-color": "#1f3b57"},
                     "icon": {"color": "#cbe4de", "font-size": "16px"}, 
                     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#92c4e6","color": "#ffffff"},
                     "nav-link-selected": {"background-color": "#73b5f2"},
                  })
                   
                  if selected == "Cформированный отчeт":
                     ###вызов функции создания Word-отчета графиков
                     create_graphic(list_graphics_word,list_heading_graphics_word) 


st.sidebar.caption('© 2024. Центр биофармацевтического анализа и метаболомных исследований')

