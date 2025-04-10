###### Подключение пакетов
import streamlit as st

#предварительный просмотр общего доступа
st.set_page_config(page_title="Доклинические исследования", page_icon="favicon.png", layout="centered", initial_sidebar_state="auto", menu_items=None)

import pandas as pd
import numpy as np
import statistics  
import statsmodels.api as sm
import os
from utils.functions import *
from utils.functions_graphics import *
from utils.functions_calculation import *
from utils.radio_unit import *
from style_python.style import *
import re

from streamlit_sortables import sort_items


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

############### файлы примеры

with open("Архив примеров.rar", "rb") as file:
    archive_bytes = file.read()

st.sidebar.download_button(
    label='Примеры файлов',
    data=archive_bytes,
    file_name='Архив примеров.rar',
    mime='application/x-rar-compressed',
    icon=":material/description:"
)

############ Руководство пользователя

# Путь к файлу
file_path = 'Руководство пользователя_v1.docx'

# Открываем файл для чтения в бинарном режиме
with open(file_path, 'rb') as file:
    st.sidebar.download_button('Руководство пользователя', file, file_name='Руководство пользователя_v1.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document', icon=":material/draft:")

#Инизиализация состояния фреймов с результатами исследований
initializing_session_state_frames_research_results(['Фармакокинетика','Биодоступность', 'Распределение по органам', 'Линейность дозирования'])

###############################
if option == 'Фармакокинетика':

    st.header('Расчет фармакокинетических параметров')

    col1, col2 = st.columns([0.66, 0.34])
   
    ####### основной экран
    with col1:
        
        panel = main_radio_button_study(option)
      
        initialization_dose_infusion_time_session(option)

        #cписки для word-отчета
        list_heading_word=[]
        list_table_word=[]
        list_graphics_word=[]
        list_heading_graphics_word=[]
        initializing_session_lists_tables_graphics(option,list_heading_word,list_table_word,list_graphics_word,list_heading_graphics_word)

        if panel == "Загрузка файлов":
           
           if f"file_name_{option}" not in st.session_state:
            st.session_state[f"file_name_{option}"] = ''

           file_name = st.text_input("Введите название файла для оформления графиков и подписей:", st.session_state[f"file_name_{option}"], key = f"key_file_name_{option}")
           
           st.session_state[f"file_name_{option}"] = file_name
           
           ######### боковое меню справа
           with col2:
                
                with st.container(border=True):
                     #настройки дополнительных параметров исследования
                     settings_additional_research_parameters(option,custom_success)
           
           measure_unit_pk_time  = select_time_unit(f"select_time_unit{option}")
           measure_unit_pk_concentration  = select_concentration_unit(f"select_concentration_unit{option}")
           measure_unit_pk_dose  = select_dose_unit(f"select_dose_unit{option}")
           #сохранение состояния выбора единиц измерения для данного исследования
           save_session_state_measure_unit_value(measure_unit_pk_time,measure_unit_pk_concentration,f"{option}",measure_unit_pk_dose) 

           #cостояние радио-кнопки "method_auc"
           if f"index_method_auc - {option}" not in st.session_state:
               st.session_state[f"index_method_auc - {option}"] = 0

           method_auc = st.radio("Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = f"Метод подсчёта AUC и AUMC - {option}", index = st.session_state[f"index_method_auc - {option}"])
           
           if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == 'linear':
              st.session_state[f"index_method_auc - {option}"] = 0
           if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == "linear-up/log-down":
              st.session_state[f"index_method_auc - {option}"] = 1
           
           if st.session_state[f"agree_injection - {option}"] == "intravenously":
              # Инициализация состояния
              if f"extrapolate_first_points_{option}" not in st.session_state:
                  st.session_state[f"extrapolate_first_points_{option}"] = False

              # Интерфейс переключателя (toggle)
              extrapolate_first_points = st.toggle(
                  "Экстраполяция для первых точек",
                  value=st.session_state[f"extrapolate_first_points_{option}"],
                  key=f"toggle_extrapolate_{option}"
              )

              st.session_state[f"extrapolate_first_points_{option}"] = extrapolate_first_points

           uploaded_file_pk = st.file_uploader(f"Выбрать файл концентраций {file_name} (формат XLSX)", key=f'Файл введения {file_name} при расчете {option}')
           
           #сохранение файла
           if uploaded_file_pk is not None:
              save_uploadedfile(uploaded_file_pk)
              st.session_state[f"uploaded_file_{option}"] = uploaded_file_pk.name

           if f'uploaded_file_{option}' in st.session_state:
              custom_success(f"Файл загружен: {st.session_state[f'uploaded_file_{option}']}")
              

           dose_pk = st.number_input(f"Доза при введении {file_name}", key=f'Доза при введении {file_name} при расчете {option}', value = st.session_state[f"dose_{option}"],step=0.1)
           
           st.session_state[f"dose_{option}"] = dose_pk

           if st.session_state[f"agree_injection - {option}"] == "infusion":
              infusion_time = st.number_input("Время введения инфузии", key=f'Время введения инфузии при расчете {option}', value = st.session_state[f"infusion_time_{option}"],step=0.1)
              st.session_state[f"infusion_time_{option}"] = infusion_time
           
           if (f"uploaded_file_{option}" in st.session_state and st.session_state[f'measure_unit_{option}_concentration']):
              start = True
           else:
              start = False

           if start:

              df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state[f"uploaded_file_{option}"]))

              st.subheader(f'Индивидуальные значения концентраций в крови после введения {file_name}')
              
              ###интерактивная таблица
              df = edit_frame(df,st.session_state[f"uploaded_file_{option}"])
           
              ###количество животных 
              count_rows_number_pk= len(df.axes[0])
        
              table_heading=f'Индивидуальные и усредненные значения концентраций в крови после введения {file_name}'
              add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

              ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
              df_stats = create_table_descriptive_statistics(df)
              # Сбрасываем индекс статистики, чтобы перенести в колонку "Номер"
              df_stats_reset = df_stats.reset_index()
              # Переименовываем колонку индекса
              df_stats_reset.rename(columns={'index': 'Номер'}, inplace=True)
              # Продолжаем индексы (начинаем после последнего индекса df)
              df_stats_reset.index = range(df.index.max() + 1, df.index.max() + 1 + len(df_stats_reset))
              # Объединяем таблицы
              df_concat_round_str_transpose = pd.concat([df, df_stats_reset], axis=0, ignore_index=False)

              
              add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_concat_round_str_transpose)

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

              list_time = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time)

              list_number_animal = []
              
              for r in range(0,count_row_df):

                  list_concentration=df.iloc[r].tolist()

                  numer_animal=list_concentration[0]

                  list_number_animal.append(numer_animal)

                  list_concentration.pop(0) #удаление номера животного

                  list_concentration = [float(v) for v in list_concentration]

                  list_concentration = remove_first_element(st.session_state[f"agree_injection - {option}"], list_concentration)

                  graphic=f'График индивидуального фармакокинетического профиля в крови (в линейных координатах) после введения {file_name},  '+numer_animal
                  graph_id = graphic
                  add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                  first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                            st.session_state[f'measure_unit_{option}_concentration'],"lin",add_or_replace_df_graph, 
                                                            (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                           st.session_state[f"list_graphics_word_{option}"],graphic))  

                  #в полулогарифмических координатах методом удаления точек
                  list_concentration = [np.nan if x <= 0 else x for x in list_concentration]

                  graphic=f'График индивидуального фармакокинетического профиля в крови (в полулогарифмических координатах) после введения {file_name},  '+numer_animal
                  graph_id = graphic
                  add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)
                  
                  first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                            st.session_state[f'measure_unit_{option}_concentration'],"log",add_or_replace_df_graph, 
                                                            (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                           st.session_state[f"list_graphics_word_{option}"],graphic))
                   
              st.session_state[f'list_number_animal_{option}'] = list_number_animal

              # объединенные индивидуальные в линейных координатах

              df_for_plot_conc=df.drop(['Номер'], axis=1)
              df_for_plot_conc_1 = df_for_plot_conc.transpose()

              list_numer_animal_for_plot=df['Номер'].tolist()
              count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

              list_color = [
                   "blue", "green", "red", "#D6870C", "violet", "gold", "indigo", "magenta", "lime", "tan", 
                   "teal", "coral", "pink", "#510099", "lightblue", "yellowgreen", "cyan", "salmon", "brown", "black",
                   "darkblue", "darkgreen", "darkred", "navy", "purple", "orangered", "darkgoldenrod", "slateblue", 
                   "deepskyblue", "mediumseagreen", "chocolate", "peru", "crimson", "olive", "cadetblue", "chartreuse", 
                   "darkcyan", "lightcoral", "mediumvioletred", "midnightblue", "sienna", "tomato", "turquoise", 
                   "wheat", "plum", "thistle", "aquamarine", "dodgerblue", "lawngreen", "rosybrown", "seagreen"
               ]
              
              df_for_plot_conc_1 = remove_first_element(st.session_state[f"agree_injection - {option}"], df_for_plot_conc_1)

              graphic=f"Сравнение индивидуальных фармакокинетических профилей (в линейных координатах) после введения {file_name}"
              graph_id = graphic
              add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

              first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                               st.session_state[f'measure_unit_{option}_concentration'],count_numer_animal,
                                                               'lin',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                           st.session_state[f"list_graphics_word_{option}"],graphic)) 

              # объединенные индивидуальные в полулогарифмических координатах методом замены  np.nan
              df_for_plot_conc_1 = replace_value_less_one_plot_total_individual_pk_profiles(df_for_plot_conc_1)

              graphic=f"Сравнение индивидуальных фармакокинетических профилей (в полулогарифмических координатах) после введения {file_name}"
              graph_id = graphic
              add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

              first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                               st.session_state[f'measure_unit_{option}_concentration'],count_numer_animal,
                                                               'log',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                           st.session_state[f"list_graphics_word_{option}"],graphic))        
              ### усреденные    
              #в линейных    

              list_time = []
              for i in col_mapping:
                  numer=float(i)
                  list_time.append(numer)
              
              list_time = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time)

              df_averaged_concentrations=df_stats
              list_concentration=df_averaged_concentrations.loc['Mean'].tolist()
              err_y_pk=df_averaged_concentrations.loc['SD'].tolist()
              
              list_concentration,err_y_pk = remove_first_element(st.session_state[f"agree_injection - {option}"], list_concentration,err_y_pk)

              graphic=f'График усредненного фармакокинетического профиля в крови (в линейных координатах) после введения {file_name}'
              graph_id = graphic
              add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)  

              first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_pk,st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],'lin',file_name,
                                                                    add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

              #в полулогарифмических координатах
              list_concentration = [np.nan if x <= 0 else x for x in list_concentration]

              graphic=f'График усредненного фармакокинетического профиля в крови (в полулогарифмических координатах) после введения {file_name}'
              graph_id = graphic
              add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

              first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_pk,st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],'log',file_name,
                                                                    add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic)) 

              ############ Параметры ФК
              if st.session_state[f"agree_injection - {option}"] == "extravascular":
                  result_PK = pk_parametrs_total_extravascular(df,f"{option}",method_auc,dose_pk,st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
              elif st.session_state[f"agree_injection - {option}"] == "intravenously":
                  if st.session_state[f"extrapolate_first_points_{option}"]:
                     df = remove_second_column(df)
                  result_PK = pk_parametrs_total_intravenously(df,f"{option}",method_auc,dose_pk,st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
              else:
                  result_PK = pk_parametrs_total_infusion(df,f"{option}",method_auc,dose_pk,st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'],infusion_time)
              
              if result_PK is not None:
                  if st.session_state[f"agree_cmax2 - {option}"] == False:
                     df_total_PK_pk = result_PK["df_total_PK"]
                  if st.session_state[f"agree_cmax2 - {option}"] == True:
                     df_total_PK_pk = result_PK["df_total_PK"]
                     df_total_PK_additional_double_peaks_pk = result_PK["df_total_PK_additional_double_peaks"]
                  
                  st.session_state[f"df_total_PK_{option}"] = df_total_PK_pk

                  table_heading=f'Фармакокинетические показатели в крови после введения {file_name}'
                  add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)
                  
                  add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_PK_pk)

                  if st.session_state[f"agree_cmax2 - {option}"] == True:
                     table_heading='Дополнительные фармакокинетические показатели при наличии двух пиков в ФК профиле'
                     add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)
                     
                     add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_PK_additional_double_peaks_pk)
              else:
                  st.session_state[f"df_total_PK_{option}"] = None #данный сброс нужен для того, чтобы если пользователь вначале загрузил данные без выбора cmax2, а потом решил все такие добавить функцию выбора данного параметра
                  st.error("Выберите необходимое количество значений Cmax и Cmax(2)",icon=":material/warning:")

              custom_success('Расчеты произведены!')
                 
           else:   
              st.error('Заполните все поля ввода и загрузите файлы!',icon=":material/warning:") 
          
    #отдельная панель, чтобы уменьшить размер вывода результатов

    col1, col2 = st.columns([0.66,0.34])

    #####Создание word отчета
    if panel == "Таблицы":
       if st.session_state[f"df_total_PK_{option}"] is not None:
          
          ###вызов функции визуализации таблиц
          visualize_table(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],option)

       else:
          st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")

    with col1:
       
       if panel == "Графики":
          if st.session_state[f"df_total_PK_{option}"] is not None:
             #######визуализация

             #классификация графиков по кнопкам
             type_graphics = st.selectbox('Выберите вид графиков',
       ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля'),disabled = False, key = f"Вид графика - {option}" )

             count_graphics_for_visual = len(st.session_state[f"list_heading_graphics_word_{option}"])
             list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)

             #создание чекбокса и инициация состояния, отвеч. за отрисовку графиков
             create_session_type_graphics_checked_graphics(option,type_graphics)

             if type_graphics == 'Индивидуальные фармакокинетические профили':

                selected_subject_individual_graphics = radio_create_individual_graphics(option,st.session_state[f'list_number_animal_{option}'],True)
             
             if st.session_state[f"{type_graphics}_{option}_checked_graphics"]:
                for i in list_range_count_graphics_for_visual:
                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("индивидуального"): 
                       if type_graphics == 'Индивидуальные фармакокинетические профили':
                          
                          graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                          match =  (re.match(r".*№(\S+)", graph_id))
                          number_animal = "№" + match.group(1)

                          if selected_subject_individual_graphics == number_animal:
                             if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                                kind_graphic = 'lin'
                             else:
                                kind_graphic = 'log'

                             rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,create_individual_graphics, st.session_state[f"list_time{graph_id}"],
                                                                    st.session_state[f"list_concentration{graph_id}"],
                                                                    st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],
                                                                    kind_graphic,graph_id)

                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение индивидуальных"):   
                       if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                          
                          graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                          if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                             kind_graphic = 'lin'
                          else:
                             kind_graphic = 'log'

                          rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_total_individual_pk_profiles, st.session_state[f"list_color{graph_id}"],
                                                                    st.session_state[f"df_for_plot_conc_1{graph_id}"],
                                                                    st.session_state[f"list_numer_animal_for_plot{graph_id}"],
                                                                    st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'], 
                                                                    len(st.session_state[f"list_numer_animal_for_plot{graph_id}"]),
                                                                    kind_graphic,graph_id)

                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("усредненного"):
                       if type_graphics == 'Графики усредненного фармакокинетического профиля':
                          graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                          if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                             kind_graphic = 'lin'
                          else:
                             kind_graphic = 'log'

                          rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_individual_mean_std, st.session_state[f"list_time{graph_id}"],
                                                                    st.session_state[f"list_concentration{graph_id}"],
                                                                    st.session_state[f"err_y_1{graph_id}"],
                                                                    st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],
                                                                    kind_graphic,graph_id,st.session_state[f"file_name_{option}"])

             with col2:
                  
                  #вызов функции оформлительского элемента сформированный отчет
                  selected = style_icon_report()
                   
                  if selected == "Cформированный отчeт":
                     ###вызов функции создания Word-отчета графиков
                     if st.button("Сформировать отчет"):
                        create_graphic(st.session_state[f"list_graphics_word_{option}"],st.session_state[f"list_heading_graphics_word_{option}"]) 
          else:
              st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")
######################################################################################################################################

if option == 'Биодоступность':
   
    st.header('Исследование биодоступности')

    col1, col2 = st.columns([0.66, 0.34])
    
    ####### основной экран
    with col1:
        
        panel = main_radio_button_study(option)

        #cписки для word-отчета
        list_heading_word=[]
        list_table_word=[]
        list_graphics_word=[]
        list_heading_graphics_word=[]
        initializing_session_lists_tables_graphics(option,list_heading_word,list_table_word,list_graphics_word,list_heading_graphics_word)

        if f"selected_edges_{option}" not in st.session_state:
           st.session_state[f"selected_edges_{option}"] = []

        if panel == "Загрузка файлов":
           
           measure_unit_bioavailability_time = select_time_unit(f"select_time_unit{option}")
           measure_unit_bioavailability_concentration = select_concentration_unit(f"select_concentration_unit{option}")
           measure_unit_dose_bioavailability = select_dose_unit(f"select_dose_unit{option}")
           #сохранение состояния выбора единиц измерения для данного исследования
           save_session_state_measure_unit_value(measure_unit_bioavailability_time,measure_unit_bioavailability_concentration,f"{option}",measure_unit_dose_bioavailability)

           #cостояние радио-кнопки "method_auc"
           if f"index_method_auc - {option}" not in st.session_state:
               st.session_state[f"index_method_auc - {option}"] = 0

           method_auc = st.radio("Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = f"Метод подсчёта AUC и AUMC - {option}", index = st.session_state[f"index_method_auc - {option}"])
           
           if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == 'linear':
              st.session_state[f"index_method_auc - {option}"] = 0
           if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == "linear-up/log-down":
              st.session_state[f"index_method_auc - {option}"] = 1

           file_uploader = st.file_uploader("",accept_multiple_files=True, key=f'Файлы при исследовании {option}',help = "Выберите нужное количество файлов (минимум два). В названии файла обязательно должно присутствовать слово с нижним подчеркиванием «Биодоступность_» в верхнем регистре, после этого текстовая часть, которая будет использована для оформления легенды графиков, названий таблиц и прочего.")
           
           if 'list_files_name_bioavailability' not in st.session_state:
             st.session_state['list_files_name_bioavailability'] = []

           ###сохранение файла
           list_files_name_bioavailability = []
           if file_uploader is not None:
              for i in file_uploader:
                  save_uploadedfile(i)
                  st.session_state[str(i.name)] = i.name
                  list_files_name_bioavailability.append(i.name)
           
           st.session_state['list_files_name_bioavailability'] = list_files_name_bioavailability
           
           if st.session_state['list_files_name_bioavailability'] != []: 
                custom_success(f"Файлы загружены: {', '.join(st.session_state['list_files_name_bioavailability'])}")
           
           list_keys_file_bioavailability = []
           for i in st.session_state.keys():
               if i.__contains__("xlsx") and (i.__contains__("Биодоступность")) and (not i.__contains__("edited_df")) and (not i.__contains__("select")) and ((not i.__contains__("del"))): ###слово био нужно, чтобы отличать файлы от других xlsx органов, т.к там тоже ключи имя файла; #обрезаем фразу ненужного добавления названия "edited_df"
                  list_keys_file_bioavailability.append(i)
         
           if 'sorted_list_keys_file_bioavailability' not in st.session_state and st.session_state['list_files_name_bioavailability'] != []:
              st.session_state['sorted_list_keys_file_bioavailability'] = st.session_state['list_files_name_bioavailability']
           
           if 'sorted_list_keys_file_bioavailability' in st.session_state:
              #сортировка
              list_keys_file_bioavailability = sort_items(st.session_state['sorted_list_keys_file_bioavailability'],direction="vertical")
              st.session_state['sorted_list_keys_file_bioavailability'] = list_keys_file_bioavailability
           
                                                        
           ###создание виджетов дозы и времени введения при инфузии

           if list_keys_file_bioavailability != []:
              
              list_keys_file_bioavailability_name = []
              for i in list_keys_file_bioavailability:
                   list_keys_file_bioavailability_name.append(i[15:-5])

              list_keys_file_bioavailability = [f"{str(name)}" for name in list_keys_file_bioavailability_name]
              
              for file_name in list_keys_file_bioavailability:

                   with col2:
                        with st.container(border=True):

                             #настройки дополнительных параметров исследования
                             settings_additional_research_parameters(f"{option}",custom_success,f"{option}",file_name)
                             
                             if st.session_state[f"agree_injection - {option}_{file_name}"] == "intravenously":
                                # Инициализация состояния
                                if f"extrapolate_first_points_{option}_{file_name}" not in st.session_state:
                                     st.session_state[f"extrapolate_first_points_{option}_{file_name}"] = False
                                 
                                # Интерфейс переключателя (toggle)
                                extrapolate_first_points = st.toggle(
                                    "Экстраполяция для первых точек",
                                    value=st.session_state[f"extrapolate_first_points_{option}_{file_name}"],
                                    key=f"toggle_extrapolate_{option}_{file_name}"
                                )

                                st.session_state[f"extrapolate_first_points_{option}_{file_name}"] = extrapolate_first_points

                             initialization_dose_infusion_time_session(option,file_name)
                             
                             dose = st.number_input(f"Доза препарата для набора данных «{file_name}»", key='Доза препарата ' + f"dose_{option}_{file_name}", value = st.session_state[f"dose_{option}_{file_name}"],step=0.1)

                             st.session_state[f"dose_{option}_{file_name}"] = dose

                             if st.session_state[f"agree_injection - {option}_{file_name}"] == "infusion":
                                  
                                  infusion_time = st.number_input(f"Время введения инфузии для набора данных {file_name}", key='Время введения инфузии ' + f"infusion_time_{option}_{file_name}", value = st.session_state[f"infusion_time_{option}_{file_name}"],step=0.1)
                                  st.session_state[f"infusion_time_{option}_{file_name}"] = infusion_time


           if ((list_keys_file_bioavailability != [])):
                start = True
           else:
              start = False
           
           if start == True:
              
              get_color(file_name)

              selected_edges = visualize_mapping(list_keys_file_bioavailability)

              st.session_state[f"selected_edges_{option}"] = selected_edges

              #проверяем первую связь существует ли она
              if st.session_state[f"selected_edges_{option}"] != [] and st.session_state[f"selected_edges_{option}"] is not None:
                  with st.expander("Итоговые связи:", True):
                       for edge in selected_edges:
                           st.write(f'№{selected_edges.index(edge)+1} {edge}')  # Выводит каждую связь в новом ряду
              
              else:
                  st.write("Нет связей для отображения")

              if st.session_state[f"selected_edges_{option}"] != [] and st.session_state[f"selected_edges_{option}"] is not None:
                 
                 list_keys_file_bioavailability_without_bioavailability = [f"{str(name)}.xlsx" for name in list_keys_file_bioavailability]

                 st.session_state[f'list_keys_file_{option}'] = list_keys_file_bioavailability_without_bioavailability

                 list_keys_file_bioavailability = [f"Биодоступность_{str(name)}.xlsx" for name in list_keys_file_bioavailability]
                 
                 list_name_bioavailability = []
                 list_df_unrounded=[]
                 list_df_for_mean_unround_for_graphics=[]
                 list_t_graph=[]

                 for i in list_keys_file_bioavailability:
                     df = pd.read_excel(os.path.join("Папка для сохранения файлов",i))

                     file_name=i[15:-5]
                     list_name_bioavailability.append(file_name)

                     st.subheader('Индивидуальные значения концентраций для набора данных «' +file_name+"»")
                     
                     ###интерактивная таблица
                     df = edit_frame(df,i)

                     ###количество животных 
                     count_rows_number_lin= len(df.axes[0])

                     table_heading='Индивидуальные и усредненные значения концентраций для набора данных «' +file_name+"»"
                     add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                     ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                     df_stats = create_table_descriptive_statistics(df)
                     # Сбрасываем индекс статистики, чтобы перенести в колонку "Номер"
                     df_stats_reset = df_stats.reset_index()
                     # Переименовываем колонку индекса
                     df_stats_reset.rename(columns={'index': 'Номер'}, inplace=True)
                     # Продолжаем индексы (начинаем после последнего индекса df)
                     df_stats_reset.index = range(df.index.max() + 1, df.index.max() + 1 + len(df_stats_reset))
                     # Объединяем таблицы
                     df_concat_round_str_transpose = pd.concat([df, df_stats_reset], axis=0, ignore_index=False)

                     add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_concat_round_str_transpose)
                     
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
                     
                     list_time = remove_first_element(st.session_state[f"agree_injection - {option}_{file_name}"], list_time)

                     list_number_animal = []

                     for r in range(0,count_row_df):

                         list_concentration=df.iloc[r].tolist()

                         numer_animal=list_concentration[0]

                         list_number_animal.append(numer_animal)

                         list_concentration.pop(0) #удаление номера животного

                         list_concentration = [float(v) for v in list_concentration]

                         list_concentration = remove_first_element(st.session_state[f"agree_injection - {option}_{file_name}"], list_concentration)

                         graphic='График индивидуального фармакокинетического профиля в линейных координатах «'  +file_name+"» "+',  '+numer_animal
                         graph_id = graphic
                         add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                         first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                                   st.session_state[f'measure_unit_{option}_concentration'],"lin",add_or_replace_df_graph, 
                                                                   (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                                  st.session_state[f"list_graphics_word_{option}"],graphic))

                         #в полулогарифмических координатах методом np.nan
                         graphic='График индивидуального фармакокинетического профиля в полулогарифмических координатах «' +file_name+"» "+',  '+numer_animal
                         graph_id = graphic
                         add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                         # Заменяем все значения меньше 1 на np.nan
                         list_concentration = [np.nan if x <= 0 else x for x in list_concentration]
                         
                         first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                                   st.session_state[f'measure_unit_{option}_concentration'],"log",add_or_replace_df_graph, 
                                                                   (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                                  st.session_state[f"list_graphics_word_{option}"],graphic))
                     
                     st.session_state[f'list_number_animal_{option}_{f"{file_name}"}'] = list_number_animal

                     # объединенные индивидуальные в линейных координатах

                     df_for_plot_conc=df.drop(['Номер'], axis=1)
                     df_for_plot_conc_1 = df_for_plot_conc.transpose()

                     list_numer_animal_for_plot=df['Номер'].tolist()
                     count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

                     list_color = [
                         "blue", "green", "red", "#D6870C", "violet", "gold", "indigo", "magenta", "lime", "tan", 
                         "teal", "coral", "pink", "#510099", "lightblue", "yellowgreen", "cyan", "salmon", "brown", "black",
                         "darkblue", "darkgreen", "darkred", "navy", "purple", "orangered", "darkgoldenrod", "slateblue", 
                         "deepskyblue", "mediumseagreen", "chocolate", "peru", "crimson", "olive", "cadetblue", "chartreuse", 
                         "darkcyan", "lightcoral", "mediumvioletred", "midnightblue", "sienna", "tomato", "turquoise", 
                         "wheat", "plum", "thistle", "aquamarine", "dodgerblue", "lawngreen", "rosybrown", "seagreen"
                     ]
                     
                     df_for_plot_conc_1 = remove_first_element(st.session_state[f"agree_injection - {option}_{file_name}"], df_for_plot_conc_1)

                     graphic="Сравнение индивидуальных фармакокинетических профилей в линейных координатах «" +file_name+"» "
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 

                     first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                                      st.session_state[f'measure_unit_{option}_concentration'],count_numer_animal,
                                                                      'lin',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                                  st.session_state[f"list_graphics_word_{option}"],graphic))
                     
                     # объединенные индивидуальные в полулогарифмических координатах методом замены np.nan
                     df_for_plot_conc_1 = replace_value_less_one_plot_total_individual_pk_profiles(df_for_plot_conc_1)

                     graphic="Сравнение индивидуальных фармакокинетических профилей в полулогарифмических координатах «" +file_name+"» "
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                     first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                                      st.session_state[f'measure_unit_{option}_concentration'],count_numer_animal,
                                                                      'log',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                                  st.session_state[f"list_graphics_word_{option}"],graphic))

                      ###усредненные    
                     # в линейных координатах
                     graphic='График усредненного фармакокинетического профиля в линейных координатах «' +file_name+"» "
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                     list_time = []
                     for i in col_mapping:
                         numer=float(i)
                         list_time.append(numer)
                     
                     list_time = remove_first_element(st.session_state[f"agree_injection - {option}_{file_name}"], list_time)

                     df_averaged_concentrations=df_stats
                     list_concentration=df_averaged_concentrations.loc['Mean'].tolist()
                     err_y_1=df_averaged_concentrations.loc['SD'].tolist()

                     list_concentration,err_y_1 = remove_first_element(st.session_state[f"agree_injection - {option}_{file_name}"], list_concentration,err_y_1)

                     first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,st.session_state[f'measure_unit_{option}_time'],
                                                                        st.session_state[f'measure_unit_{option}_concentration'],'lin',file_name,
                                                                        add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                                  st.session_state[f"list_graphics_word_{option}"],graphic))

                     #в полулогарифмических координатах
                     #для полулогарифм. посторим без нуля
                     # Заменяем все значения меньше 1 на np.nan
                     graphic='График усредненного фармакокинетического профиля в полулогарифмических координатах «' +file_name+"» "
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                     list_concentration = [np.nan if x <= 0 else x for x in list_concentration]

                     first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,st.session_state[f'measure_unit_{option}_time'],
                                                                        st.session_state[f'measure_unit_{option}_concentration'],'log',file_name,
                                                                        add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                                  st.session_state[f"list_graphics_word_{option}"],graphic))
                     
                     ############ Параметры ФК
                     if f"agree_cmax2 - {option}_{file_name}" not in st.session_state:
                        st.session_state[f"agree_cmax2 - {option}_{file_name}"] = False

                     if st.session_state[f"agree_injection - {option}_{file_name}"] == "extravascular":
                         result_PK = pk_parametrs_total_extravascular(df,f"{option}_{file_name}",method_auc,st.session_state[f"dose_{option}_{file_name}"],st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
                     elif st.session_state[f"agree_injection - {option}_{file_name}"] == "intravenously":
                         if st.session_state[f"extrapolate_first_points_{option}_{file_name}"]:
                            df = remove_second_column(df)
                         result_PK = pk_parametrs_total_intravenously(df,f"{option}_{file_name}",method_auc,st.session_state[f"dose_{option}_{file_name}"],st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
                     else:
                         result_PK = pk_parametrs_total_infusion(df,f"{option}_{file_name}",method_auc,st.session_state[f"dose_{option}_{file_name}"],st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'],st.session_state[f"infusion_time_{option}_{file_name}"])

                     if result_PK is not None:

                         df_total_PK_bioavailability = result_PK["df_total_PK"]
                         df_concat_PK_bioavailability = result_PK["df_concat_PK"]
                         list_cmax_1_bioavailability = result_PK["list_cmax_1"]
                         
                         st.session_state[f"df_total_PK_{option}"] = df_total_PK_bioavailability

                         table_heading='Фармакокинетические показатели препарата в дозировке «' +file_name +"» "
                         add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                         add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_PK_bioavailability)

                         #создание списков фреймов, доз и т.д.
                         list_df_unrounded.append(df_concat_PK_bioavailability)
                         list_df_for_mean_unround_for_graphics.append(df_stats)

                 list_list_PK_par_mean=[]
                 for i,file_name in list(zip(list_df_unrounded,list_name_bioavailability)): 
                     mean_сmax=i['Cmax'].loc['Mean']
                     mean_tmax=i['Tmax'].loc['Mean']
                     mean_mrt0inf=i['MRT0→∞'].loc['Mean']
                     mean_thalf=i['T1/2'].loc['Mean']
                     mean_auc0t=i['AUC0-t'].loc['Mean']
                     mean_auc0inf=i['AUC0→∞'].loc['Mean']
                     mean_aumc0inf=i['AUMC0-∞'].loc['Mean']
                     mean_сmaxdevaucot=i['Сmax/AUC0-t'].loc['Mean']
                     mean_kel=i['Kel'].loc['Mean']

                     if st.session_state[f"agree_injection - {option}_{file_name}"] == "extravascular":
                        mean_cl=i['Cl/F'].loc['Mean']
                        mean_vd=i['Vz/F'].loc['Mean']
                     else:
                        mean_cl=i['Cl'].loc['Mean']
                        mean_vd=i['Vz'].loc['Mean']
                     list_list_PK_par_mean.append([mean_сmax,mean_tmax,mean_mrt0inf,mean_thalf,mean_auc0t,mean_auc0inf,mean_aumc0inf,mean_сmaxdevaucot,mean_kel,mean_cl,mean_vd])
                 
                 list_df_PK_bioavailability_total = []

                 for list_PK_par_mean,file_name in list(zip(list_list_PK_par_mean,list_name_bioavailability)):
                     
                     ### получение итогового фрейма ФК параметров
                     if st.session_state[f"agree_injection - {option}_{file_name}"] == "extravascular":
                        df_PK_bioavailability_total = pd.DataFrame(list_PK_par_mean, index =['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")",'Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")",'Сmax/AUC0-t '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Cl/F ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})/{st.session_state[f'measure_unit_{option}_time']}"+")",'Vz/F ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})"+")"],columns=[file_name])
                     else:
                        df_PK_bioavailability_total = pd.DataFrame(list_PK_par_mean, index =['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")",'Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")",'Сmax/AUC0-t '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Cl ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})/{st.session_state[f'measure_unit_{option}_time']}"+")",'Vz ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})"+")"],columns=[file_name])
 
                     df_PK_bioavailability_total.index.name = 'Параметры, размерность'
                     list_df_PK_bioavailability_total.append(df_PK_bioavailability_total)
                 
                 # Выбираем нужные колонки из каждого DataFrame
                 selected_df_PK_bioavailability_total = [df[[col]] for df, col in zip(list_df_PK_bioavailability_total, list_name_bioavailability)]
                 # Объединяем их в один DataFrame
                 merged_df_PK_bioavailability_total = pd.concat(selected_df_PK_bioavailability_total, axis=1)
  
                 table_heading='Среднее арифметическое фармакокинетических параметров'
                 add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                 add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,merged_df_PK_bioavailability_total)
                 
                 list_bioavailability_label = []
                 list_bioavailability = []
                 for comparison in st.session_state[f"selected_edges_{option}"]:

                     # 1. Разделяем строку по " → "
                     reference_drug, test_drug = map(str.strip, comparison.split("→"))

                     # 2. Находим строку, содержащую "AUC0-t"
                     def find_auc_value(df, column_name):
                         auc_row = df[df["Параметры, размерность"].str.contains(r"AUC0-t", regex=True, na=False)]
                         return auc_row[column_name].values[0] if not auc_row.empty else None
                     
                     def find_auc_value(df, column_name):
                         auc_row = df[df.index.str.contains(r"AUC0-t", regex=True, na=False)]
                         return auc_row[column_name].values[0] if not auc_row.empty else None

                     # 3. Получаем значения AUC0-t из соответствующих DataFrame-ов
                     auc_ref = find_auc_value(merged_df_PK_bioavailability_total, reference_drug)
                     auc_test = find_auc_value(merged_df_PK_bioavailability_total, test_drug)
                     
                     # 4. Вычисляем биодоступность (если значения найдены)
                     if auc_ref and auc_test:
                         if float(st.session_state[f"dose_{option}_{test_drug}"]) != 0 and float(st.session_state[f"dose_{option}_{reference_drug}"]) != 0:
                            bioavailability = ((auc_test * float(st.session_state[f"dose_{option}_{test_drug}"]))/ (auc_ref * float(st.session_state[f"dose_{option}_{reference_drug}"]))) * 100
                         else:
                            bioavailability = (auc_test/auc_ref) * 100
                         list_bioavailability_label.append((f"{test_drug} относительно {reference_drug}"))
                         list_bioavailability.append(bioavailability)
                     else:
                         st.write("Ошибка: Не удалось найти значения AUC0-t для одного из препаратов")

                 df_bioavailability = pd.DataFrame({"Биодоступность": list_bioavailability}, index=list_bioavailability_label)

                 table_heading='Таблица биодоступности'
                 add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                 add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_bioavailability)
                 
                 ###построение графика "Фармакокинетический профиль при различных лек. формах"
                 graphic='Сравнение фармакокинетических профилей (в линейных координатах) в исследовании биодоступности'
                 graph_id= graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 

                 ### в линейных координатах
                 list_list_mean_conc=[]
                 list_list_std_conc=[]
                 for i in list_df_for_mean_unround_for_graphics: 
                     mean_conc_list=i.loc['Mean'].tolist()
                     std_conc_list=i.loc['SD'].tolist()
                     list_list_mean_conc.append(mean_conc_list)
                     list_list_std_conc.append(std_conc_list)

                 list_name_bioavailability_std=[]
                 for i in list_name_bioavailability:
                  j= i + " std"
                  list_name_bioavailability_std.append(j)

                 list_time_new_df = list_t_graph[0]
                 
                 df_mean_conc_graph = pd.DataFrame(list_list_mean_conc, columns =list_time_new_df,index=list_name_bioavailability)
                 df_mean_conc_graph_1=df_mean_conc_graph.transpose()
                 df_std_conc_graph = pd.DataFrame(list_list_std_conc, columns =list_time_new_df,index=list_name_bioavailability_std)
                 df_std_conc_graph_1=df_std_conc_graph.transpose()
                 df_concat_mean_std= pd.concat([df_mean_conc_graph_1,df_std_conc_graph_1],sort=False,axis=1)
                 
                 
                 # Регулярное выражение для поиска нужных колонок
                 pattern = re.compile(r"Внутривенное|Инфузионное|Внутривенное std|Инфузионное std")

                 # Проверяем все колонки и заменяем первое значение, если оно равно 0
                 for col in df_concat_mean_std.columns:
                     if pattern.search(col) and df_concat_mean_std[col].iloc[0] == 0:
                         df_concat_mean_std.at[0, col] = np.nan  # Заменяем 0 на np.nan

                 list_colors = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]

                 list_t_doses=list(df_concat_mean_std.index)

                 list_zip_mean_std_colors=list(zip(list_name_bioavailability,list_name_bioavailability_std,list_colors))
                 
                 #Инициализация состояния чекбокса параметров осей
                 initializing_checkbox_status_graph_scaling_widgets(graph_id)
                 
                 #Сохранение состояний данных графика
                 st.session_state[f"list_zip_mean_std_colors{graph_id}"] = list_zip_mean_std_colors
                 st.session_state[f"list_t_doses{graph_id}"] = list_t_doses
                 st.session_state[f"df_concat_mean_std{graph_id}"] = df_concat_mean_std

                 if f"first_creating_graphic{graph_id}" not in st.session_state:
                     st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                 
                 if st.session_state[f"first_creating_graphic{graph_id}"]:
                    #вызов функции построения графика сравнения срединных профелей линейные
                    fig = plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t_doses,df_concat_mean_std,st.session_state[f'measure_unit_{option}_time'],
                                                                 st.session_state[f'measure_unit_{option}_concentration'],'lin',graph_id)
                    add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)
                    

                 ### в полулог. координатах
                 graphic='Сравнение фармакокинетических профилей (в полулогарифмических координатах) в исследовании биодоступности'
                 graph_id= graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)
                 
                 #замена всех нулей и значений меньше 1 на np.nan для данных концентрации для корректного отображения графика
                 df_concat_mean_std = df_concat_mean_std.copy(deep=True)
                 df_concat_mean_std = replace_value_less_one_plot_pk_profile_total_mean_std_doses_organs(df_concat_mean_std)

                 list_zip_mean_std_colors=list(zip(list_name_bioavailability,list_name_bioavailability_std,list_colors))
                 
                 #Инициализация состояния чекбокса параметров осей
                 initializing_checkbox_status_graph_scaling_widgets(graph_id) 

                 #Сохранение состояний данных графика
                 st.session_state[f"list_zip_mean_std_colors{graph_id}"] = list_zip_mean_std_colors
                 st.session_state[f"list_t_doses{graph_id}"] = list_t_doses
                 st.session_state[f"df_concat_mean_std{graph_id}"] = df_concat_mean_std
                 
                 if f"first_creating_graphic{graph_id}" not in st.session_state:
                     st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                 
                 if st.session_state[f"first_creating_graphic{graph_id}"]:
                    #вызов функции построения графика сравнения срединных профелей полулогарифм
                    fig = plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t_doses,df_concat_mean_std,st.session_state[f'measure_unit_{option}_time'],
                                                                 st.session_state[f'measure_unit_{option}_concentration'],'log',graph_id)
                    add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)

                 custom_success('Расчеты произведены!')
                 
              else:   
                 st.error('Выберите дизайн исследования!',icon=":material/warning:")      

    #отдельная панель, чтобы уменьшить размер вывода результатов
    col1, col2 = st.columns([0.66,0.34])
    
    #####Создание word отчета
    if panel == "Таблицы": 
       if st.session_state[f"df_total_PK_{option}"] is not None:
          
          list_keys = [x[:-5] for x in st.session_state[f"list_keys_file_{option}"]]
          st.session_state[f"list_heading_word_{option}"], index_mapping = sort_by_keys_with_indices(st.session_state[f"list_heading_word_{option}"], list_keys)
          st.session_state[f"list_table_word_{option}"] = reorder_list_by_mapping(st.session_state[f"list_table_word_{option}"], index_mapping)

          ###вызов функции визуализации таблиц
          visualize_table(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],option)

       else:
           st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")

    with col1:
          
       if panel == "Графики":
          if st.session_state[f"df_total_PK_{option}"] is not None: 
             #######визуализация
             list_keys = [x[:-5] for x in st.session_state[f"list_keys_file_{option}"]]
             st.session_state[f"list_heading_graphics_word_{option}"], index_mapping = sort_by_keys_with_indices(st.session_state[f"list_heading_graphics_word_{option}"], list_keys)
             st.session_state[f"list_graphics_word_{option}"] = reorder_list_by_mapping(st.session_state[f"list_graphics_word_{option}"], index_mapping)

             #классификация графиков по кнопкам
             type_graphics = st.selectbox('Выберите вид графиков',
       ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля','Сравнение фармакокинетических профилей в исследовании биодоступности'),disabled = False, key = f"Вид графика - {option}" )

             count_graphics_for_visual = len(st.session_state[f"list_heading_graphics_word_{option}"])
             list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)

             #создание чекбокса и инициация состояния, отвеч. за отрисовку графиков
             create_session_type_graphics_checked_graphics(option,type_graphics)

             if type_graphics == 'Индивидуальные фармакокинетические профили' or type_graphics == 'Сравнение индивидуальных фармакокинетических профилей' or type_graphics == 'Графики усредненного фармакокинетического профиля':
                selected_kind_individual_graphics = radio_create_individual_graphics(option,st.session_state[f'list_keys_file_{option}'])

                if type_graphics == 'Индивидуальные фармакокинетические профили':
                   selected_subject_individual_graphics = radio_create_individual_graphics(option,st.session_state[f'list_number_animal_{option}_{selected_kind_individual_graphics}'],True,selected_kind_individual_graphics)

             if st.session_state[f"{type_graphics}_{option}_checked_graphics"]:
                for i in list_range_count_graphics_for_visual:
                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("индивидуального"): 
                       if type_graphics == 'Индивидуальные фармакокинетические профили':
                          
                          graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                          match = re.findall(r'«(.*?)»', graph_id)
                          file_name = match[0]

                          match =  (re.match(r".*№(\S+)", graph_id))
                          number_animal = "№" + match.group(1)

                          if selected_kind_individual_graphics == file_name and selected_subject_individual_graphics == number_animal:
                             if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                                kind_graphic = 'lin'
                             else:
                                kind_graphic = 'log'

                             rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,create_individual_graphics, st.session_state[f"list_time{graph_id}"],
                                                                    st.session_state[f"list_concentration{graph_id}"],
                                                                    st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],
                                                                    kind_graphic,graph_id)
                             
                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение индивидуальных"):   
                       if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                             
                          graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                          match = re.findall(r'«(.*?)»', graph_id)
                          file_name = match[0]

                          if selected_kind_individual_graphics == file_name:
                             if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                                kind_graphic = 'lin'
                             else:
                                kind_graphic = 'log'

                             rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_total_individual_pk_profiles, st.session_state[f"list_color{graph_id}"],
                                                                       st.session_state[f"df_for_plot_conc_1{graph_id}"],
                                                                       st.session_state[f"list_numer_animal_for_plot{graph_id}"],
                                                                       st.session_state[f'measure_unit_{option}_time'],
                                                                       st.session_state[f'measure_unit_{option}_concentration'], 
                                                                       len(st.session_state[f"list_numer_animal_for_plot{graph_id}"]),
                                                                       kind_graphic,graph_id)

                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("усредненного"):
                       if type_graphics == 'Графики усредненного фармакокинетического профиля':
                             
                          graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                          match = re.findall(r'«(.*?)»', graph_id)
                          file_name = match[0]

                          if selected_kind_individual_graphics == file_name:
                             
                             if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                                kind_graphic = 'lin'
                             else:
                                kind_graphic = 'log'

                             rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_individual_mean_std, st.session_state[f"list_time{graph_id}"],
                                                                       st.session_state[f"list_concentration{graph_id}"],
                                                                       st.session_state[f"err_y_1{graph_id}"],
                                                                       st.session_state[f'measure_unit_{option}_time'],
                                                                       st.session_state[f'measure_unit_{option}_concentration'],
                                                                       kind_graphic,graph_id,file_name)
                             
                    if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение фармакокинетических"):
                      if type_graphics == 'Сравнение фармакокинетических профилей в исследовании биодоступности':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                          
                         file_name = [i[15:-5] for i in st.session_state[f'list_keys_file_{option}']][0] #костыль, там вверху также только последнего вставляются значения, нужно решить как оставим
                         
                         if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                            kind_graphic = 'lin'
                         else:
                            kind_graphic = 'log'

                         rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_total_mean_std_doses_organs, st.session_state[f"list_zip_mean_std_colors{graph_id}"],
                                                                   st.session_state[f"list_t_doses{graph_id}"],
                                                                   st.session_state[f"df_concat_mean_std{graph_id}"],
                                                                   st.session_state[f'measure_unit_{option}_time'],
                                                                   st.session_state[f'measure_unit_{option}_concentration'],
                                                                   kind_graphic,graph_id)         
             with col2:
                     
                 #вызов функции оформлительского элемента сформированный отчет
                 selected = style_icon_report()
                  
                 if selected == "Cформированный отчeт":
                    ###вызов функции создания Word-отчета графиков
                    if st.button("Сформировать отчет"):
                       create_graphic(st.session_state[f"list_graphics_word_{option}"],st.session_state[f"list_heading_graphics_word_{option}"])
          else:
              st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")

#####################################################################        
if option == 'Распределение по органам':
   
   st.header('Исследование ФК параметров для органов животных')
   
   col1, col2 = st.columns([0.66, 0.34])
   
   with col1:
       
      panel = main_radio_button_study(option)

      initialization_dose_infusion_time_session(option)
      
      #cписки для word-отчета
      list_heading_word=[]
      list_table_word=[]
      list_graphics_word=[]
      list_heading_graphics_word=[]
      initializing_session_lists_tables_graphics(option,list_heading_word,list_table_word,list_graphics_word,list_heading_graphics_word)
       
      if panel == "Загрузка файлов":
         
         ######### боковое меню справа
         with col2:
              with st.container(border=True):
                  #настройки дополнительных параметров исследования
                  settings_additional_research_parameters(option,custom_success)

         measure_unit_org_time = select_time_unit(f"select_time_unit{option}")
         measure_unit_org_blood = select_concentration_unit(f"select_concentration_unit{option}")
         measure_unit_org_organs = select_organ_concentration_unit(f"select_organ_concentration_unit{option}")
         measure_unit_org_dose = select_dose_unit(f"select_dose_unit{option}")
         #сохранение состояния выбора единиц измерения для данного исследования
         save_session_state_measure_unit_value(measure_unit_org_time,measure_unit_org_blood,f"{option}",measure_unit_org_dose,measure_unit_org_organs=measure_unit_org_organs)
         
         dose = st.number_input("Доза препарата", key='Доза препарата при изучении фармакокинетики в органах животных', value = st.session_state[f"dose_{option}"],step=0.1)

         st.session_state[f"dose_{option}"] = dose

         if st.session_state[f"agree_injection - {option}"] == "infusion":
              
              infusion_time = st.number_input("Время введения инфузии", key=f'Время введения инфузии при расчете {option}', value = st.session_state[f"infusion_time_{option}"],step=0.1)
              st.session_state[f"infusion_time_{option}"] = infusion_time

         #cостояние радио-кнопки "method_auc"
         if f"index_method_auc - {option}" not in st.session_state:
             st.session_state[f"index_method_auc - {option}"] = 0

         method_auc = st.radio("Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = f"Метод подсчёта AUC и AUMC - {option}", index = st.session_state[f"index_method_auc - {option}"])
         
         if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == 'linear':
            st.session_state[f"index_method_auc - {option}"] = 0
         if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == "linear-up/log-down":
            st.session_state[f"index_method_auc - {option}"] = 1
         
         if st.session_state[f"agree_injection - {option}"] == "intravenously":
              # Инициализация состояния
              if f"extrapolate_first_points_{option}" not in st.session_state:
                  st.session_state[f"extrapolate_first_points_{option}"] = False

              # Интерфейс переключателя (toggle)
              extrapolate_first_points = st.toggle(
                  "Экстраполяция для первых точек",
                  value=st.session_state[f"extrapolate_first_points_{option}"],
                  key=f"toggle_extrapolate_{option}"
              )

              st.session_state[f"extrapolate_first_points_{option}"] = extrapolate_first_points

         file_uploader = st.file_uploader("",accept_multiple_files=True, key='Файлы при изучении фармакокинетики в органах животных',help = "Выберите нужное количество файлов соответственно количеству исследуемых органов; файл должен быть назван соотвественно органу; исходный файл крови должен быть назван 'Кровь'")

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
             if i.__contains__("xlsx") and (not i.__contains__("Дозировка")) and (not i.__contains__("Болюс")) and (not i.__contains__("Инфузионное")) and (not i.__contains__("Внесосудистое")) and (not i.__contains__("edited_df")):### чтобы не перекрывалось с lin; #обрезаем фразу ненужного добавления названия "edited_df"
                list_keys_file_org.append(i)

         if 'sorted_list_keys_file_organs' not in st.session_state and st.session_state['list_files_name_organs'] != []:
                  st.session_state['sorted_list_keys_file_organs'] = st.session_state['list_files_name_organs']
               
         if 'sorted_list_keys_file_organs' in st.session_state:
            #сортировка по алфавиту
            list_keys_file_org = sort_items(st.session_state['sorted_list_keys_file_organs'],direction="vertical")
            st.session_state['sorted_list_keys_file_organs'] = list_keys_file_org

         st.session_state[f"list_keys_file_{option}"] = list_keys_file_org
         
         if ((list_keys_file_org != []) and st.session_state[f'measure_unit_{option}_concentration'] and st.session_state[f'measure_unit_{option}_organs']):
              start = True
         else:
            start = False

         if start:

             list_name_organs=[]
             list_df_unrounded=[]
             list_df_for_mean_unround_for_graphics=[]
             list_t_graph=[]
             
             for i in list_keys_file_org:
                 df = pd.read_excel(os.path.join("Папка для сохранения файлов",i))

                 file_name=st.session_state[i][:-5]

                 st.subheader('Индивидуальные значения концентраций ' + "("+file_name+")")
                 
                 ###интерактивная таблица
                 df = edit_frame(df,i)

                 ###количество животных 
                 count_rows_number_org = len(df.axes[0])
                 
                 table_heading='Индивидуальные и усредненные значения концентраций ' + "("+file_name+")"
                 
                 add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                 df_stats = create_table_descriptive_statistics(df)
                 # Сбрасываем индекс статистики, чтобы перенести в колонку "Номер"
                 df_stats_reset = df_stats.reset_index()
                 # Переименовываем колонку индекса
                 df_stats_reset.rename(columns={'index': 'Номер'}, inplace=True)
                 # Продолжаем индексы (начинаем после последнего индекса df)
                 df_stats_reset.index = range(df.index.max() + 1, df.index.max() + 1 + len(df_stats_reset))
                 # Объединяем таблицы
                 df_concat_round_str_transpose = pd.concat([df, df_stats_reset], axis=0, ignore_index=False)

                 add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_concat_round_str_transpose)
                 
                 #вызов функции проверки названия файла для правильного опредления единиц измерения
                 measure_unit_org = checking_file_names_organ_graphs(option,file_name)

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

                 list_time = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time)
                 
                 list_number_animal = []

                 for r in range(0,count_row_df):

                     list_concentration=df.iloc[r].tolist()

                     numer_animal=list_concentration[0]

                     list_number_animal.append(numer_animal)

                     list_concentration.pop(0) #удаление номера животного

                     list_concentration = [float(v) for v in list_concentration]

                     list_concentration = remove_first_element(st.session_state[f"agree_injection - {option}"], list_concentration)

                     graphic='График индивидуального фармакокинетического профиля в линейных координатах '  + "("+file_name+")"',  '+numer_animal
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)  

                     first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                               measure_unit_org,"lin",add_or_replace_df_graph, 
                                                               (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))
                     #в полулогарифмических координатах методом np.nan
                     # Заменяем все значения меньше 1 на np.nan
                     list_concentration = [np.nan if x <= 0 else x for x in list_concentration]

                     graphic='График индивидуального фармакокинетического профиля в полулогарифмических координатах ' + "("+file_name+")"',  '+numer_animal
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 

                     first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                               measure_unit_org,"log",add_or_replace_df_graph, 
                                                               (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

                 st.session_state[f'list_number_animal_{option}_{file_name}'] = list_number_animal

                 # объединенные индивидуальные в линейных координатах

                 df_for_plot_conc=df.drop(['Номер'], axis=1)
                 df_for_plot_conc_1 = df_for_plot_conc.transpose()
                 
                 list_numer_animal_for_plot=df['Номер'].tolist()
                 count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

                 list_color = [
                   "blue", "green", "red", "#D6870C", "violet", "gold", "indigo", "magenta", "lime", "tan", 
                   "teal", "coral", "pink", "#510099", "lightblue", "yellowgreen", "cyan", "salmon", "brown", "black",
                   "darkblue", "darkgreen", "darkred", "navy", "purple", "orangered", "darkgoldenrod", "slateblue", 
                   "deepskyblue", "mediumseagreen", "chocolate", "peru", "crimson", "olive", "cadetblue", "chartreuse", 
                   "darkcyan", "lightcoral", "mediumvioletred", "midnightblue", "sienna", "tomato", "turquoise", 
                   "wheat", "plum", "thistle", "aquamarine", "dodgerblue", "lawngreen", "rosybrown", "seagreen"
                 ]
                 
                 df_for_plot_conc_1 = remove_first_element(st.session_state[f"agree_injection - {option}"], df_for_plot_conc_1)

                 graphic="Сравнение индивидуальных фармакокинетических профилей в линейных координатах " + "("+file_name+")"
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 
                 
                 first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                                  measure_unit_org,count_numer_animal,
                                                                  'lin',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

                 # объединенные индивидуальные в полулогарифмических координатах методом замены 0 на None
                 df_for_plot_conc_1 = replace_value_less_one_plot_total_individual_pk_profiles(df_for_plot_conc_1)

                 graphic="Сравнение индивидуальных фармакокинетических профилей в полулогарифмических координатах " + "("+file_name+")"
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                 first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                                  measure_unit_org,count_numer_animal,
                                                                  'log',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

                 ###усредненные    
                 # в линейных координатах
                 list_time = []
                 for i in col_mapping:
                     numer=float(i)
                     list_time.append(numer)
                 
                 list_time = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time)

                 df_averaged_concentrations=df_stats
                 list_concentration=df_averaged_concentrations.loc['Mean'].tolist()
                 err_y_1=df_averaged_concentrations.loc['SD'].tolist()
                 
                 list_concentration,err_y_1 = remove_first_element(st.session_state[f"agree_injection - {option}"], list_concentration,err_y_1)

                 graphic='График усредненного фармакокинетического профиля в линейных координатах ' + "("+file_name+")"
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                 first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,st.session_state[f'measure_unit_{option}_time'],
                                                                    measure_unit_org,'lin',file_name,
                                                                    add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))
                 #в полулогарифмических координатах
                 #для полулогарифм. посторим без нуля
                 # Заменяем все значения меньше 1 на np.nan
                 list_concentration = [np.nan if x <= 0 else x for x in list_concentration]

                 graphic='График усредненного фармакокинетического профиля в полулогарифмических координатах ' + "("+file_name+")"
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                 first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,st.session_state[f'measure_unit_{option}_time'],
                                                                    measure_unit_org,'log',file_name,
                                                                    add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))
                 

                 ############ Параметры ФК
                 if f"agree_cmax2 - {option} {file_name}" not in st.session_state:
                    st.session_state[f"agree_cmax2 - {option} {file_name}"] = False

                 if st.session_state[f"agree_injection - {option}"] == "extravascular":
                     result_PK = pk_parametrs_total_extravascular(df,f"{option} {file_name}",method_auc,dose,measure_unit_org,st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
                 elif st.session_state[f"agree_injection - {option}"] == "intravenously":
                     if st.session_state[f"extrapolate_first_points_{option}"]:
                        df = remove_second_column(df)
                     result_PK = pk_parametrs_total_intravenously(df,f"{option} {file_name}",method_auc,dose,measure_unit_org,st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
                 else:
                     result_PK = pk_parametrs_total_infusion(df,f"{option} {file_name}",method_auc,dose,measure_unit_org,st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'],infusion_time)
                 

                 if result_PK is not None:

                     df_total_PK_org = result_PK["df_total_PK"]
                     df_concat_PK_org = result_PK["df_concat_PK"]
                     list_cmax_1_org = result_PK["list_cmax_1"]

                     st.session_state[f"df_total_PK_{option}"] = df_total_PK_org

                     table_heading='Фармакокинетические показатели ' + "("+file_name+")"
                     add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)
                     
                     add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_PK_org)
                     
                     #создание списков фреймов, названий органов и т.д.

                     list_name_organs.append(file_name)
                     list_df_unrounded.append(df_concat_PK_org)
                     list_df_for_mean_unround_for_graphics.append(df_stats)

             ###Кнопка активации дальнейших действий
             button_calculation = False
             
             if (list_keys_file_org != []) and st.session_state[f'measure_unit_{option}_concentration'] and st.session_state[f'measure_unit_{option}_organs'] and result_PK is not None:
              
                condition_cmax1 =  len(list_cmax_1_org) == count_rows_number_org

                button_calculation = True
                
                if button_calculation == True:
                   custom_success('Расчеты произведены!')
                else:   
                   st.error('Заполните все поля ввода и загрузите файлы!',icon=":material/warning:")
             
             if (list_keys_file_org != []) and st.session_state[f'measure_unit_{option}_concentration'] and st.session_state[f'measure_unit_{option}_organs'] and button_calculation:
                
                list_list_PK_par_mean=[]
                for i in list_df_unrounded: 
                    mean_сmax=i['Cmax'].loc['Mean']
                    mean_tmax=i['Tmax'].loc['Mean']
                    mean_mrt0inf=i['MRT0→∞'].loc['Mean']
                    mean_thalf=i['T1/2'].loc['Mean']
                    mean_auc0t=i['AUC0-t'].loc['Mean']
                    mean_auc0inf=i['AUC0→∞'].loc['Mean']
                    mean_aumc0inf=i['AUMC0-∞'].loc['Mean']
                    mean_kel=i['Kel'].loc['Mean']
                    list_list_PK_par_mean.append([mean_сmax,mean_tmax,mean_mrt0inf,mean_thalf,mean_auc0t,mean_auc0inf,mean_aumc0inf,mean_kel])
                
                list_list_PK_par_std=[]
                for i in list_df_unrounded: 
                    std_сmax=i['Cmax'].loc['SD']
                    std_tmax=i['Tmax'].loc['SD']
                    std_mrt0inf=i['MRT0→∞'].loc['SD']
                    std_thalf=i['T1/2'].loc['SD']
                    std_auc0t=i['AUC0-t'].loc['SD']
                    std_auc0inf=i['AUC0→∞'].loc['SD']
                    std_aumc0inf=i['AUMC0-∞'].loc['SD']
                    std_kel=i['Kel'].loc['SD']
                    list_list_PK_par_std.append([std_сmax,std_tmax,std_mrt0inf,std_thalf,std_auc0t,std_auc0inf,std_aumc0inf,std_kel])

                ### получение итогового фрейма ФК параметров органов
                
                df_PK_organs_total = pd.DataFrame(list_list_PK_par_mean, columns =['Cmax','Tmax','MRT0→∞','T1/2','AUC0-t','AUC0→∞','AUMC0-∞','Kel'],index=list_name_organs) 
                df_PK_organs_total_transpose=df_PK_organs_total.transpose()
                
                df_PK_organs_total_std = pd.DataFrame(list_list_PK_par_std, columns =['Cmax','Tmax','MRT0→∞','T1/2','AUC0-t','AUC0→∞','AUMC0-∞','Kel'],index=list_name_organs) 
                df_PK_organs_total_std_transpose=df_PK_organs_total_std.transpose()
                
                ###ft
                list_aucot_for_ft=[]
                list_columns_df_PK_organs_total_transpose=df_PK_organs_total_transpose.columns.tolist()
                for i in list_columns_df_PK_organs_total_transpose:
                    aucot=df_PK_organs_total_transpose[i].loc['AUC0-t']
                    list_aucot_for_ft.append(aucot)

                list_ft=[]
                for i in list_aucot_for_ft:
                    ft=i/df_PK_organs_total_transpose["Кровь"].loc['AUC0-t']
                    list_ft.append(ft)

                ###ft
                list_aucot_for_ft_std=[]
                list_columns_df_PK_organs_total_std_transpose=df_PK_organs_total_std_transpose.columns.tolist()
                for i in list_columns_df_PK_organs_total_std_transpose:
                    aucot_std=df_PK_organs_total_std_transpose[i].loc['AUC0-t']
                    list_aucot_for_ft_std.append(aucot_std)

                list_ft_std=[]
                for i in list_aucot_for_ft_std:
                    ft_std=i/df_PK_organs_total_std_transpose["Кровь"].loc['AUC0-t']
                    list_ft_std.append(ft_std)

                df_PK_organs_total_transpose.loc[ len(df_PK_organs_total_transpose.index )] = list_ft


                df_PK_organs_total_transpose.index=['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")",'Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")",'Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'fт']
                
                #округление фрейма df_PK_organs_total_transpose

                df_organs_trans_trans=df_PK_organs_total_transpose.transpose()


                series_Cmax=df_organs_trans_trans['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")"].tolist() 
                series_Cmax=pd.Series([v for v in series_Cmax])

                series_Tmax=df_organs_trans_trans['Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()       
                series_Tmax=pd.Series([v for v in series_Tmax]) 
                
                series_MRT0_inf= df_organs_trans_trans['MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()   
                series_MRT0_inf=pd.Series([v for v in series_MRT0_inf])

                series_half_live= df_organs_trans_trans['T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()   
                series_half_live=pd.Series([v for v in series_half_live]) 

                series_AUC0_t= df_organs_trans_trans['AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")"].tolist()   
                series_AUC0_t=pd.Series([v for v in series_AUC0_t])

                series_AUC0_inf= df_organs_trans_trans['AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")"].tolist()  
                series_AUC0_inf=pd.Series([v for v in series_AUC0_inf]) 

                series_AUMC0_inf= df_organs_trans_trans['AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")"].tolist()   
                series_AUMC0_inf=pd.Series([v for v in series_AUMC0_inf])
          
                series_Kel= df_organs_trans_trans['Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")"].tolist()   
                series_Kel=pd.Series([v for v in series_Kel])

                series_ft= df_organs_trans_trans['fт'].tolist()
                series_ft=pd.Series(series_ft)
                
                df_total_total_organs = pd.concat([series_Cmax,series_Tmax,series_MRT0_inf,series_half_live,series_AUC0_t,series_AUC0_inf,series_AUMC0_inf,series_Kel,series_ft], axis= 1)

                df_total_total_organs.index=df_PK_organs_total_transpose.columns.tolist()
                df_total_total_organs.columns=df_PK_organs_total_transpose.index.tolist() 

                df_total_total_organs_total= df_total_total_organs.transpose()
                df_total_total_organs_total.index.name = 'Параметры, размерность'

                table_heading='Среднее арифметическое фармакокинетических параметров в различных тканях'
                add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading) 

                add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_total_organs_total) 

                ###построение графика "Фармакокинетический профиль в органах"

                ### в линейных координатах
                graphic='Сравнение фармакокинетических профилей (в линейных координатах) в органах'
                graph_id = graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 

                list_list_mean_conc=[]
                list_list_std_conc=[]
                for i in list_df_for_mean_unround_for_graphics: 
                    mean_conc_list=i.loc['Mean'].tolist()
                    std_conc_list=i.loc['SD'].tolist()
                    list_list_mean_conc.append(mean_conc_list)
                    list_list_std_conc.append(std_conc_list)

                list_name_organs_std=[]
                for i in list_name_organs:
                 j= i + " std"
                 list_name_organs_std.append(j)
                
                list_time_new_df = list_t_graph[0]
                
                if st.session_state[f"agree_injection - {option}"] == "intravenously":
                   if st.session_state[f"extrapolate_first_points_{option}"]:
                      #список времени для общего срединного графика
                      list_time_new_df = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time_new_df)

                df_mean_conc_graph = pd.DataFrame(list_list_mean_conc, columns =list_time_new_df,index=list_name_organs)
                df_mean_conc_graph_1=df_mean_conc_graph.transpose()
                df_std_conc_graph = pd.DataFrame(list_list_std_conc, columns =list_time_new_df,index=list_name_organs_std)
                df_std_conc_graph_1=df_std_conc_graph.transpose()
                df_concat_mean_std = pd.concat([df_mean_conc_graph_1,df_std_conc_graph_1],sort=False,axis=1)
                
                df_concat_mean_std = remove_first_element(st.session_state[f"agree_injection - {option}"], df_concat_mean_std)

                list_colors = ["blue","green","red","#D6870C","violet","gold","indigo","magenta","lime","tan","teal","coral","pink","#510099","lightblue","yellowgreen","cyan","salmon","brown","black"]
                
                list_t_organs=list(df_concat_mean_std.index) #уже ноль удален в случае внутривенного болюса

                list_zip_mean_std_colors=list(zip(list_name_organs,list_name_organs_std,list_colors))

                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id)

                #Сохранение состояний данных графика
                st.session_state[f"list_zip_mean_std_colors{graph_id}"] = list_zip_mean_std_colors
                st.session_state[f"list_t_organs{graph_id}"] = list_t_organs
                st.session_state[f"df_concat_mean_std{graph_id}"] = df_concat_mean_std

                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                
                if st.session_state[f"first_creating_graphic{graph_id}"]:
                   #вызов функции построения графика сравнения срединных профелей линейные
                   fig = plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t_organs,df_concat_mean_std,st.session_state[f'measure_unit_{option}_time'],
                                                                st.session_state[f'measure_unit_{option}_concentration'],'lin',graph_id)
                   
                   add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)  

                ### в полулог. координатах
                graphic='Сравнение фармакокинетических профилей (в полулогарифмических координатах) в органах'
                graph_id = graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                #замена всех нулей и значений меньше 1 на np.nan для данных концентрации для корректного отображения графика
                df_concat_mean_std = replace_value_less_one_plot_pk_profile_total_mean_std_doses_organs(df_concat_mean_std)

                list_zip_mean_std_colors=list(zip(list_name_organs,list_name_organs_std,list_colors))

                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id)

                #Сохранение состояний данных графика
                st.session_state[f"list_zip_mean_std_colors{graph_id}"] = list_zip_mean_std_colors
                st.session_state[f"list_t_organs{graph_id}"] = list_t_organs
                st.session_state[f"df_concat_mean_std{graph_id}"] = df_concat_mean_std
                
                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                
                if st.session_state[f"first_creating_graphic{graph_id}"]:
                   #вызов функции построения графика сравнения срединных профелей полулогарифм
                   fig = plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t_organs,df_concat_mean_std,st.session_state[f'measure_unit_{option}_time'],
                                                                st.session_state[f'measure_unit_{option}_concentration'],'log',graph_id)
                   add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)

                ###построение диаграммы для тканевой доступности
                graphic='Тканевая доступность в органах'
                graph_id = graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)
            
                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id)

                #Сохранение состояний данных графика 
                st.session_state[f"list_name_organs{graph_id}"] = list_name_organs
                st.session_state[f"list_ft{graph_id}"] = list_ft
                st.session_state[f"list_ft_std{graph_id}"] = list_ft_std

                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика 
                
                if st.session_state[f"first_creating_graphic{graph_id}"]:
                   fig = plot_tissue_accessibility(list_name_organs,list_ft,list_ft_std,graph_id)

                   add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)
                
   #отдельная панель, чтобы уменьшить размер вывода результатов

   col1, col2 = st.columns([0.66,0.34])
   
   #####Создание word отчета
   if panel == "Таблицы": 
      if st.session_state[f"df_total_PK_{option}"] is not None:
         
         list_keys = [x[:-5] for x in st.session_state[f"list_keys_file_{option}"]]
         st.session_state[f"list_heading_word_{option}"], index_mapping = sort_by_keys_with_indices(st.session_state[f"list_heading_word_{option}"], list_keys)
         st.session_state[f"list_table_word_{option}"] = reorder_list_by_mapping(st.session_state[f"list_table_word_{option}"], index_mapping)

         ###вызов функции визуализации таблиц
         visualize_table(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],option)

      else:
          st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")

   with col1:
      if panel == "Графики":
         if st.session_state[f"df_total_PK_{option}"] is not None:
            
            list_keys = [x[:-5] for x in st.session_state[f"list_keys_file_{option}"]]
            st.session_state[f"list_heading_graphics_word_{option}"], index_mapping = sort_by_keys_with_indices(st.session_state[f"list_heading_graphics_word_{option}"], list_keys)
            st.session_state[f"list_graphics_word_{option}"] = reorder_list_by_mapping(st.session_state[f"list_graphics_word_{option}"], index_mapping)

            #######визуализация

            #классификация графиков по кнопкам
            type_graphics = st.selectbox('Выберите вид графиков',
      ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля', "Сравнение фармакокинетических профилей в различных органах", "Тканевая доступность в органах"),disabled = False, key = f"Вид графика - {option}" )

            count_graphics_for_visual = len(st.session_state[f"list_heading_graphics_word_{option}"])
            list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)

            #создание чекбокса и инициация состояния, отвеч. за отрисовку графиков
            create_session_type_graphics_checked_graphics(option,type_graphics)

            if type_graphics == 'Индивидуальные фармакокинетические профили' or type_graphics == 'Сравнение индивидуальных фармакокинетических профилей' or type_graphics == 'Графики усредненного фармакокинетического профиля':
               selected_kind_individual_graphics = radio_create_individual_graphics(option,st.session_state[f"list_keys_file_{option}"])
               
               if type_graphics == 'Индивидуальные фармакокинетические профили':
                  selected_subject_individual_graphics = radio_create_individual_graphics(option,st.session_state[f'list_number_animal_{option}_{selected_kind_individual_graphics}'],True,selected_kind_individual_graphics)

            if st.session_state[f"{type_graphics}_{option}_checked_graphics"]:
               for i in list_range_count_graphics_for_visual:
                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("индивидуального"): 
                      if type_graphics == 'Индивидуальные фармакокинетические профили':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                         match = re.search(r'\(([^)]+)\)', graph_id)
                         file_name = match.group(1)
                         
                         measure_unit_org = checking_file_names_organ_graphs(option,file_name)

                         match =  (re.match(r".*№(\S+)", graph_id))
                         number_animal = "№" + match.group(1)
                         
                         if selected_kind_individual_graphics == file_name and selected_subject_individual_graphics == number_animal:
                         
                            if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                               kind_graphic = 'lin'
                            else:
                               kind_graphic = 'log'

                            rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,create_individual_graphics, st.session_state[f"list_time{graph_id}"],
                                                                      st.session_state[f"list_concentration{graph_id}"],
                                                                      st.session_state[f'measure_unit_{option}_time'],
                                                                      measure_unit_org,
                                                                      kind_graphic,graph_id)

                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение индивидуальных"):   
                      if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                         match = re.search(r'\(([^)]+)\)$', graph_id)
                         file_name = match.group(1)
                         
                         measure_unit_org = checking_file_names_organ_graphs(option,file_name)
                         
                         if selected_kind_individual_graphics == file_name:
                            if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                               kind_graphic = 'lin'
                            else:
                               kind_graphic = 'log'

                            rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_total_individual_pk_profiles, st.session_state[f"list_color{graph_id}"],
                                                                      st.session_state[f"df_for_plot_conc_1{graph_id}"],
                                                                      st.session_state[f"list_numer_animal_for_plot{graph_id}"],
                                                                      st.session_state[f'measure_unit_{option}_time'],
                                                                      measure_unit_org, 
                                                                      len(st.session_state[f"list_numer_animal_for_plot{graph_id}"]),
                                                                      kind_graphic,graph_id)

                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("усредненного"):
                      if type_graphics == 'Графики усредненного фармакокинетического профиля':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                         
                         match = re.search(r'\(([^)]+)\)$', graph_id)
                         file_name = match.group(1)
                         
                         measure_unit_org = checking_file_names_organ_graphs(option,file_name)

                         if selected_kind_individual_graphics == file_name:

                            if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                               kind_graphic = 'lin'
                            else:
                               kind_graphic = 'log'

                            rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_individual_mean_std, st.session_state[f"list_time{graph_id}"],
                                                                      st.session_state[f"list_concentration{graph_id}"],
                                                                      st.session_state[f"err_y_1{graph_id}"],
                                                                      st.session_state[f'measure_unit_{option}_time'],
                                                                      measure_unit_org,
                                                                      kind_graphic,graph_id,file_name)
                         
                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение фармакокинетических"):
                      if type_graphics == 'Сравнение фармакокинетических профилей в различных органах':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                         if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                            kind_graphic = 'lin'
                         else:
                            kind_graphic = 'log'

                         rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_total_mean_std_doses_organs, st.session_state[f"list_zip_mean_std_colors{graph_id}"],
                                                                   st.session_state[f"list_t_organs{graph_id}"],
                                                                   st.session_state[f"df_concat_mean_std{graph_id}"],
                                                                   st.session_state[f'measure_unit_{option}_time'],
                                                                   st.session_state[f'measure_unit_{option}_concentration'],
                                                                   kind_graphic,graph_id)
                         
                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Тканевая"):
                      if type_graphics == 'Тканевая доступность в органах':
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                         
                         kind_graphic = 'lin'

                         rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_tissue_accessibility, st.session_state[f"list_name_organs{graph_id}"],
                                                                   st.session_state[f"list_ft{graph_id}"],st.session_state[f"list_ft_std{graph_id}"],
                                                                  graph_id)
            
            with col2:
                     
                 #вызов функции оформлительского элемента сформированный отчет
                 selected = style_icon_report()
                  
                 if selected == "Cформированный отчeт":
                    ###вызов функции создания Word-отчета графиков
                    if st.button("Сформировать отчет"):
                       create_graphic(st.session_state[f"list_graphics_word_{option}"],st.session_state[f"list_heading_graphics_word_{option}"])
         else:
             st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")
################################################################################################

if option == 'Линейность дозирования':
   
   st.header('Исследование линейности дозирования')
   
   col1, col2 = st.columns([0.66, 0.34])

   with col1:

      panel = main_radio_button_study(option)

      #cписки для word-отчета
      list_heading_word=[]
      list_table_word=[]
      list_graphics_word=[]
      list_heading_graphics_word=[]
      initializing_session_lists_tables_graphics(option,list_heading_word,list_table_word,list_graphics_word,list_heading_graphics_word)

      if panel == "Загрузка файлов":
         
         ######### боковое меню справа
         with col2:
              with st.container(border=True):
                   #настройки дополнительных параметров исследования
                   settings_additional_research_parameters(option,custom_success)

         measure_unit_lin_time = select_time_unit(f"select_time_unit{option}")
         measure_unit_lin_concentration = select_concentration_unit(f"select_concentration_unit{option}")
         measure_unit_dose_lin = select_dose_unit(f"select_dose_unit{option}")
         #сохранение состояния выбора единиц измерения для данного исследования
         save_session_state_measure_unit_value(measure_unit_lin_time,measure_unit_lin_concentration,f"{option}",measure_unit_dose_lin)

         #cостояние радио-кнопки "method_auc"
         if f"index_method_auc - {option}" not in st.session_state:
             st.session_state[f"index_method_auc - {option}"] = 0

         method_auc = st.radio("Метод подсчёта AUC и AUMC",('linear',"linear-up/log-down"),key = f"Метод подсчёта AUC и AUMC - {option}", index = st.session_state[f"index_method_auc - {option}"])
         
         if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == 'linear':
            st.session_state[f"index_method_auc - {option}"] = 0
         if st.session_state[f"Метод подсчёта AUC и AUMC - {option}"] == "linear-up/log-down":
            st.session_state[f"index_method_auc - {option}"] = 1

         if st.session_state[f"agree_injection - {option}"] == "intravenously":
              # Инициализация состояния
              if f"extrapolate_first_points_{option}" not in st.session_state:
                  st.session_state[f"extrapolate_first_points_{option}"] = False

              # Интерфейс переключателя (toggle)
              extrapolate_first_points = st.toggle(
                  "Экстраполяция для первых точек",
                  value=st.session_state[f"extrapolate_first_points_{option}"],
                  key=f"toggle_extrapolate_{option}"
              )

              st.session_state[f"extrapolate_first_points_{option}"] = extrapolate_first_points   
            
         file_uploader = st.file_uploader("",accept_multiple_files=True, key='Файлы при исследовании линейности дозирования', help = "Выберите нужное количество файлов соответственно количеству исследуемых дозировок (не менее 3-х файлов); файл должен быть назван соотвественно своей дозировке, например: 'Дозировка 50'. Слово 'Дозировка' обязательно в верхнем регистре!")
         
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
         
         ###создание виджетов дозы и времени введения при инфузии

         if list_keys_file_lin != []:
            
            list_keys_file_lin_float = []
            for i in list_keys_file_lin:
                if "." in i[10:-5]: 
                   list_keys_file_lin_float.append(float(i[10:-5]))
                else:
                   list_keys_file_lin_float.append(int(i[10:-5]))
            list_keys_file_lin_float.sort()

            list_keys_file_lin = [f"Дозировка {str(float)}.xlsx" for float in list_keys_file_lin_float]

            for i in list_keys_file_lin:
                 
                 file_name=i[10:-5]

                 initialization_dose_infusion_time_session(option,file_name)
                 
                 col3, col4 = st.columns([0.34,0.66])

                 with col2:
                     
                     with st.container(border=True):

                          dose = st.number_input(f"Доза препарата для набора данных с дозировкой {file_name}", key='Доза препарата ' + f"dose_{option}_{file_name}", value = st.session_state[f"dose_{option}_{file_name}"],step=0.1)
                          
                          st.session_state[f"dose_{option}_{file_name}"] = dose

                          if st.session_state[f"agree_injection - {option}"] == "infusion":
                               
                               infusion_time = st.number_input(f"Время введения инфузии для набора данных с дозировкой {file_name}", key='Время введения инфузии ' + f"infusion_time_{option}_{file_name}", value = st.session_state[f"infusion_time_{option}_{file_name}"],step=0.1)
                               st.session_state[f"infusion_time_{option}_{file_name}"] = infusion_time
         
         
         # Проверка, заполнены ли все необходимые дозы
         missing_doses = []
         for file_name in list_keys_file_lin:
             file_name=file_name[10:-5]
             dose = st.session_state[f"dose_{option}_{file_name}"]
             if dose != 0.0:
                missing_doses.append(dose)

         if len(missing_doses) == len(list_keys_file_lin):
            cheking_doses = True
         else:
            cheking_doses = False

         if ((list_keys_file_lin != []) and cheking_doses and st.session_state[f'measure_unit_{option}_concentration']):
              start = True
         else:
            start = False

         if start:

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
             st.session_state[f'list_keys_file_{option}'] = list_keys_file_lin

             for i in list_keys_file_lin:
                 df = pd.read_excel(os.path.join("Папка для сохранения файлов",i))

                 file_name=i[10:-5]

                 st.subheader('Индивидуальные значения концентраций в дозировке ' +file_name+" "+ st.session_state[f'measure_unit_{option}_dose'])
                 
                 ###интерактивная таблица
                 df = edit_frame(df,i)

                 ###количество животных 
                 count_rows_number_lin= len(df.axes[0])

                 table_heading='Индивидуальные и усредненные значения концентраций в дозировке ' +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']
                 add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                 df_stats = create_table_descriptive_statistics(df)
                 # Сбрасываем индекс статистики, чтобы перенести в колонку "Номер"
                 df_stats_reset = df_stats.reset_index()
                 # Переименовываем колонку индекса
                 df_stats_reset.rename(columns={'index': 'Номер'}, inplace=True)
                 # Продолжаем индексы (начинаем после последнего индекса df)
                 df_stats_reset.index = range(df.index.max() + 1, df.index.max() + 1 + len(df_stats_reset))
                 # Объединяем таблицы
                 df_concat_round_str_transpose = pd.concat([df, df_stats_reset], axis=0, ignore_index=False)

                 add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_concat_round_str_transpose)

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
                 
                 list_time = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time)

                 list_number_animal = []

                 for r in range(0,count_row_df):

                     list_concentration=df.iloc[r].tolist()

                     numer_animal=list_concentration[0]

                     list_number_animal.append(numer_animal)

                     list_concentration.pop(0) #удаление номера животного

                     list_concentration = [float(v) for v in list_concentration]

                     list_concentration = remove_first_element(st.session_state[f"agree_injection - {option}"], list_concentration)

                     graphic='График индивидуального фармакокинетического профиля в линейных координатах в дозировке '  +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']+',  '+numer_animal
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                     first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                               st.session_state[f'measure_unit_{option}_concentration'],"lin",add_or_replace_df_graph, 
                                                               (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))
 
                     #в полулогарифмических координатах методом np.nan
                     graphic='График индивидуального фармакокинетического профиля в полулогарифмических координатах в дозировке ' +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']+',  '+numer_animal
                     graph_id = graphic
                     add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                     # Заменяем все значения меньше 1 на np.nan
                     list_concentration = [np.nan if x <= 0 else x for x in list_concentration]
                     
                     first_creating_create_individual_graphics(graph_id,list_time,list_concentration,st.session_state[f'measure_unit_{option}_time'],
                                                               st.session_state[f'measure_unit_{option}_concentration'],"log",add_or_replace_df_graph, 
                                                               (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))
                 
                 st.session_state[f'list_number_animal_{option}_{f"Дозировка {file_name}"}'] = list_number_animal

                 # объединенные индивидуальные в линейных координатах

                 df_for_plot_conc=df.drop(['Номер'], axis=1)
                 df_for_plot_conc_1 = df_for_plot_conc.transpose()

                 list_numer_animal_for_plot=df['Номер'].tolist()
                 count_numer_animal = len(list_numer_animal_for_plot) ### для регулирования пропорции легенды

                 list_color = [
                   "blue", "green", "red", "#D6870C", "violet", "gold", "indigo", "magenta", "lime", "tan", 
                   "teal", "coral", "pink", "#510099", "lightblue", "yellowgreen", "cyan", "salmon", "brown", "black",
                   "darkblue", "darkgreen", "darkred", "navy", "purple", "orangered", "darkgoldenrod", "slateblue", 
                   "deepskyblue", "mediumseagreen", "chocolate", "peru", "crimson", "olive", "cadetblue", "chartreuse", 
                   "darkcyan", "lightcoral", "mediumvioletred", "midnightblue", "sienna", "tomato", "turquoise", 
                   "wheat", "plum", "thistle", "aquamarine", "dodgerblue", "lawngreen", "rosybrown", "seagreen"
                 ]
                 
                 df_for_plot_conc_1 = remove_first_element(st.session_state[f"agree_injection - {option}"], df_for_plot_conc_1)

                 graphic="Сравнение индивидуальных фармакокинетических профилей в линейных координатах в дозировке " +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 

                 first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                                  st.session_state[f'measure_unit_{option}_concentration'],count_numer_animal,
                                                                  'lin',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))
                 
                 # объединенные индивидуальные в полулогарифмических координатах методом замены np.nan
                 df_for_plot_conc_1 = replace_value_less_one_plot_total_individual_pk_profiles(df_for_plot_conc_1)

                 graphic="Сравнение индивидуальных фармакокинетических профилей в полулогарифмических координатах в дозировке " +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                 first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,st.session_state[f'measure_unit_{option}_time'],
                                                                  st.session_state[f'measure_unit_{option}_concentration'],count_numer_animal,
                                                                  'log',add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

                  ###усредненные    
                 # в линейных координатах
                 graphic='График усредненного фармакокинетического профиля в линейных координатах в дозировке ' +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                 list_time = []
                 for i in col_mapping:
                     numer=float(i)
                     list_time.append(numer)
                 
                 list_time = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time)

                 df_averaged_concentrations=df_stats
                 list_concentration=df_averaged_concentrations.loc['Mean'].tolist()
                 err_y_1=df_averaged_concentrations.loc['SD'].tolist()

                 list_concentration,err_y_1 = remove_first_element(st.session_state[f"agree_injection - {option}"], list_concentration,err_y_1)
                 
                 special_file_name = file_name.replace("Дозировка", "") + " " + st.session_state[f'measure_unit_{option}_dose']
                 

                 first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],'lin',special_file_name,
                                                                    add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

                 #в полулогарифмических координатах
                 #для полулогарифм. посторим без нуля
                 # Заменяем все значения меньше 1 на np.nan
                 graphic='График усредненного фармакокинетического профиля в полулогарифмических координатах в дозировке ' +file_name+" "+ st.session_state[f'measure_unit_{option}_dose']
                 graph_id = graphic
                 add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                 list_concentration = [np.nan if x <= 0 else x for x in list_concentration]
                 
                 special_file_name = file_name.replace("Дозировка", "") + " " + st.session_state[f'measure_unit_{option}_dose']

                 first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,st.session_state[f'measure_unit_{option}_time'],
                                                                    st.session_state[f'measure_unit_{option}_concentration'],'log',special_file_name,
                                                                    add_or_replace_df_graph, (st.session_state[f"list_heading_graphics_word_{option}"],
                                                                                              st.session_state[f"list_graphics_word_{option}"],graphic))

                 ############ Параметры ФК

                 if f"agree_cmax2 - {option} {file_name}" not in st.session_state:
                    st.session_state[f"agree_cmax2 - {option} {file_name}"] = False

                 if st.session_state[f"agree_injection - {option}"] == "extravascular":
                     result_PK = pk_parametrs_total_extravascular(df,f"{option} {file_name}",method_auc,st.session_state[f"dose_{option}_{file_name}"],st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
                 elif st.session_state[f"agree_injection - {option}"] == "intravenously":
                     if st.session_state[f"extrapolate_first_points_{option}"]:
                        df = remove_second_column(df)
                     result_PK = pk_parametrs_total_intravenously(df,f"{option} {file_name}",method_auc,st.session_state[f"dose_{option}_{file_name}"],st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'])
                 else:
                     result_PK = pk_parametrs_total_infusion(df,f"{option} {file_name}",method_auc,st.session_state[f"dose_{option}_{file_name}"],st.session_state[f'measure_unit_{option}_concentration'],st.session_state[f'measure_unit_{option}_time'],st.session_state[f'measure_unit_{option}_dose'],st.session_state[f"infusion_time_{option}_{file_name}"])

                 if result_PK is not None:

                     df_total_PK_lin = result_PK["df_total_PK"]
                     df_concat_PK_lin = result_PK["df_concat_PK"]
                     list_cmax_1_lin = result_PK["list_cmax_1"]
                         
                     st.session_state[f"df_total_PK_{option}"] = df_total_PK_lin

                     table_heading='Фармакокинетические показатели препарата в дозировке ' +file_name +" "+ st.session_state[f'measure_unit_{option}_dose']
                     add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                     add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_PK_lin)

                     #создание списков фреймов, доз и т.д.

                     list_name_doses.append(file_name)
                     list_df_unrounded.append(df_concat_PK_lin)
                     list_df_for_mean_unround_for_graphics.append(df_stats)

             ###Кнопка активации дальнейших действий
             button_calculation = False
             
             if (list_keys_file_lin != []) and st.session_state[f'measure_unit_{option}_concentration'] and st.session_state[f'measure_unit_{option}_dose']  and result_PK is not None:
              
                condition_cmax1 =  len(list_cmax_1_lin) == count_rows_number_lin

                button_calculation = True
                
                if button_calculation == True:
                   custom_success('Расчеты произведены!')
                else:   
                   st.error('Заполните все поля ввода и загрузите файлы!',icon=":material/warning:")
             
             if (list_keys_file_lin != []) and st.session_state[f'measure_unit_{option}_concentration'] and st.session_state[f'measure_unit_{option}_dose'] and button_calculation:
                
                
                list_list_PK_par_mean=[]
                for i in list_df_unrounded: 
                    mean_сmax=i['Cmax'].loc['Mean']
                    mean_tmax=i['Tmax'].loc['Mean']
                    mean_mrt0inf=i['MRT0→∞'].loc['Mean']
                    mean_thalf=i['T1/2'].loc['Mean']
                    mean_auc0t=i['AUC0-t'].loc['Mean']
                    mean_auc0inf=i['AUC0→∞'].loc['Mean']
                    mean_aumc0inf=i['AUMC0-∞'].loc['Mean']
                    mean_сmaxdevaucot=i['Сmax/AUC0-t'].loc['Mean']
                    mean_kel=i['Kel'].loc['Mean']
                    if st.session_state[f"agree_injection - {option}"] == "extravascular":
                       mean_cl=i['Cl/F'].loc['Mean']
                       mean_vd=i['Vz/F'].loc['Mean']
                    else:
                       mean_cl=i['Cl'].loc['Mean']
                       mean_vd=i['Vz'].loc['Mean']
                    list_list_PK_par_mean.append([mean_сmax,mean_tmax,mean_mrt0inf,mean_thalf,mean_auc0t,mean_auc0inf,mean_aumc0inf,mean_сmaxdevaucot,mean_kel,mean_cl,mean_vd]) 

                list_name_doses_with_measure_unit=[]
                for i in list_name_doses:
                 j= i + " " + st.session_state[f'measure_unit_{option}_dose']
                 list_name_doses_with_measure_unit.append(j)

                ### получение итогового фрейма ФК параметров доз
                if st.session_state[f"agree_injection - {option}"] == "extravascular":
                   df_PK_doses_total = pd.DataFrame(list_list_PK_par_mean, columns =['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")",'Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")",'Сmax/AUC0-t '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Cl/F ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})/{st.session_state[f'measure_unit_{option}_time']}"+")",'Vz/F ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})"+")"],index=list_name_doses_with_measure_unit)
                else:
                   df_PK_doses_total = pd.DataFrame(list_list_PK_par_mean, columns =['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")",'Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")",'AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")",'AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")",'Сmax/AUC0-t '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")",'Cl ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})/{st.session_state[f'measure_unit_{option}_time']}"+")",'Vz ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})"+")"],index=list_name_doses_with_measure_unit)
                
                df_PK_doses_total_transpose=df_PK_doses_total.transpose()

                #округление фрейма df_PK_doses_total_transpose

                df_doses_trans_trans=df_PK_doses_total_transpose.transpose()

                series_Cmax=df_doses_trans_trans['Cmax ' +"("+st.session_state[f'measure_unit_{option}_concentration']+")"].tolist() 
                series_Cmax=pd.Series([v for v in series_Cmax])

                series_Tmax=df_doses_trans_trans['Tmax ' +"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()       
                series_Tmax=pd.Series([v for v in series_Tmax])

                series_MRT0_inf= df_doses_trans_trans['MRT0→∞ '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()   
                series_MRT0_inf=pd.Series([v for v in series_MRT0_inf])

                series_half_live= df_doses_trans_trans['T1/2 '+"("+f"{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()   
                series_half_live=pd.Series([v for v in series_half_live]) 

                series_AUC0_t= df_doses_trans_trans['AUC0-t '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")"].tolist()   
                series_AUC0_t=pd.Series([v for v in series_AUC0_t])

                series_AUC0_inf= df_doses_trans_trans['AUC0→∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}" +")"].tolist()  
                series_AUC0_inf=pd.Series([v for v in series_AUC0_inf]) 

                series_AUMC0_inf= df_doses_trans_trans['AUMC0-∞ '+"("+st.session_state[f'measure_unit_{option}_concentration']+f"×{st.session_state[f'measure_unit_{option}_time']}\u00B2" +")"].tolist()   
                series_AUMC0_inf=pd.Series([v for v in series_AUMC0_inf])

                series_Сmax_dev_AUC0_t= df_doses_trans_trans['Сmax/AUC0-t '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")"].tolist()  
                series_Сmax_dev_AUC0_t=pd.Series([v for v in series_Сmax_dev_AUC0_t]) 

                series_Kel= df_doses_trans_trans['Kel '+"("+f"{st.session_state[f'measure_unit_{option}_time']}\u207B\u00B9"+")"].tolist()   
                series_Kel=pd.Series([v for v in series_Kel])
                
                if st.session_state[f"agree_injection - {option}"] == "extravascular":
                   series_CL= df_doses_trans_trans['Cl/F ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})/{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()  
                   series_CL=pd.Series([v for v in series_CL]) 

                   series_Vd= df_doses_trans_trans['Vz/F ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})"+")"].tolist()   
                   series_Vd=pd.Series([v for v in series_Vd])
                else:
                   series_CL= df_doses_trans_trans['Cl ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})/{st.session_state[f'measure_unit_{option}_time']}"+")"].tolist()  
                   series_CL=pd.Series([v for v in series_CL]) 

                   series_Vd= df_doses_trans_trans['Vz ' +"("+f"({st.session_state[f'measure_unit_{option}_dose']})/({st.session_state[f'measure_unit_{option}_concentration']})"+")"].tolist()   
                   series_Vd=pd.Series([v for v in series_Vd])
                
                df_total_total_doses = pd.concat([series_Cmax, series_Tmax,series_MRT0_inf,series_half_live,series_AUC0_t,series_AUC0_inf,series_AUMC0_inf,series_Сmax_dev_AUC0_t,series_Kel,series_CL,series_Vd], axis= 1)

                df_total_total_doses.index=df_PK_doses_total_transpose.columns.tolist()
                df_total_total_doses.columns=df_PK_doses_total_transpose.index.tolist() 

                df_total_total_doses_total= df_total_total_doses.transpose()
                df_total_total_doses_total.index.name = 'Параметры, размерность'
             
                table_heading='Среднее арифметическое фармакокинетических параметров в различных дозировках'
                add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading)

                add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_total_total_doses_total)

                ###построение графика "Фармакокинетический профиль в различных дозировках"

                graphic='Сравнение фармакокинетических профилей (в линейных координатах) в различных дозировках'
                graph_id= graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic) 

                ### в линейных координатах
                list_list_mean_conc=[]
                list_list_std_conc=[]
                for i in list_df_for_mean_unround_for_graphics: 
                    mean_conc_list=i.loc['Mean'].tolist()
                    std_conc_list=i.loc['SD'].tolist()
                    list_list_mean_conc.append(mean_conc_list)
                    list_list_std_conc.append(std_conc_list)

                list_name_doses_with_measure_unit_std=[]
                for i in list_name_doses_with_measure_unit:
                 j= i + " std"
                 list_name_doses_with_measure_unit_std.append(j)

                list_time_new_df = list_t_graph[0]

                if st.session_state[f"agree_injection - {option}"] == "intravenously":
                   if st.session_state[f"extrapolate_first_points_{option}"]:
                      #список времени для общего срединного графика
                      list_time_new_df = remove_first_element(st.session_state[f"agree_injection - {option}"], list_time_new_df)

                df_mean_conc_graph = pd.DataFrame(list_list_mean_conc, columns =list_time_new_df,index=list_name_doses_with_measure_unit)
                df_mean_conc_graph_1=df_mean_conc_graph.transpose()
                df_std_conc_graph = pd.DataFrame(list_list_std_conc, columns =list_time_new_df,index=list_name_doses_with_measure_unit_std)
                df_std_conc_graph_1=df_std_conc_graph.transpose()
                df_concat_mean_std= pd.concat([df_mean_conc_graph_1,df_std_conc_graph_1],sort=False,axis=1)

                df_concat_mean_std = remove_first_element(st.session_state[f"agree_injection - {option}"], df_concat_mean_std)

                list_colors = ["black","red","blue","green","#D6870C"]

                list_t_doses=list(df_concat_mean_std.index)

                list_zip_mean_std_colors=list(zip(list_name_doses_with_measure_unit,list_name_doses_with_measure_unit_std,list_colors))
                
                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id)
                
                #Сохранение состояний данных графика
                st.session_state[f"list_zip_mean_std_colors{graph_id}"] = list_zip_mean_std_colors
                st.session_state[f"list_t_doses{graph_id}"] = list_t_doses
                st.session_state[f"df_concat_mean_std{graph_id}"] = df_concat_mean_std

                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                
                if st.session_state[f"first_creating_graphic{graph_id}"]:
                   #вызов функции построения графика сравнения срединных профелей линейные
                   fig = plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t_doses,df_concat_mean_std,st.session_state[f'measure_unit_{option}_time'],
                                                                st.session_state[f'measure_unit_{option}_concentration'],'lin',graph_id)
                   add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)

                ### в полулог. координатах
                graphic='Сравнение фармакокинетических профилей (в полулогарифмических координатах) в различных дозировках'
                graph_id= graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)
                
                #замена всех нулей и значений меньше 1 на np.nan для данных концентрации для корректного отображения графика
                df_concat_mean_std = df_concat_mean_std.copy(deep=True)
                df_concat_mean_std = replace_value_less_one_plot_pk_profile_total_mean_std_doses_organs(df_concat_mean_std)

                list_zip_mean_std_colors=list(zip(list_name_doses_with_measure_unit,list_name_doses_with_measure_unit_std,list_colors))
                
                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id) 

                #Сохранение состояний данных графика
                st.session_state[f"list_zip_mean_std_colors{graph_id}"] = list_zip_mean_std_colors
                st.session_state[f"list_t_doses{graph_id}"] = list_t_doses
                st.session_state[f"df_concat_mean_std{graph_id}"] = df_concat_mean_std
                
                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                
                if st.session_state[f"first_creating_graphic{graph_id}"]:
                   #вызов функции построения графика сравнения срединных профелей полулогарифм
                   fig = plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t_doses,df_concat_mean_std,st.session_state[f'measure_unit_{option}_time'],
                                                                st.session_state[f'measure_unit_{option}_concentration'],'log',graph_id)
                   add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)
 
                # Линейность дозирования
                list_AUC0_inf_lin = []
                for i in list_df_unrounded: 
                    # Получаем значения AUC0→∞ для каждой дозы и добавляем в список
                    mean_auc0inf = i['AUC0→∞'][:'N'].iloc[:-1].to_list()
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

                graphic='Зависимость значений AUC0→∞ от величин вводимых доз'
                graph_id = graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                # Данные для графика
                list_AUC0_inf_lin_mean = []
                list_AUC0_inf_lin_std = []
                for i in list_df_unrounded: 
                    # Получаем значения AUC0→∞ для каждой дозы и добавляем в список
                    mean_auc0_inf = i['AUC0→∞'].loc['Mean']
                    std_auc0_inf = i['AUC0→∞'].loc['SD']
                    list_AUC0_inf_lin_mean.append(mean_auc0_inf)
                    list_AUC0_inf_lin_std.append(std_auc0_inf)
                
                list_name_doses_lin_float = [float(i) for i in list_name_doses]


                # Создаем DataFrame для анализа
                df_for_lin_mean = pd.DataFrame({
                    'AUC0→∞_mean': list_AUC0_inf_lin_mean,
                    'AUC0→∞_std': list_AUC0_inf_lin_std,
                    'doses': list_name_doses_lin_float
                    
                })

                if 'df1_model_lin' not in st.session_state:
                   st.session_state['df1_model_lin'] = 1

                if 'df2_model_lin' not in st.session_state:
                   st.session_state['df2_model_lin'] = 1

                ###график линейной регресии

                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id)

                #Сохранение состояний данных графика
                st.session_state.df_for_lin_mean = df_for_lin_mean  # Здесь можно задать начальное значение, например, DataFrame
                st.session_state.model = model  # Модель линейной регрессии

                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика
                
                if st.session_state[f"first_creating_graphic{graph_id}"]:
                   #вызов функции графика линейной регрессии
                   kind_graphic = 'lin'
                   fig = create_graphic_lin(df_for_lin_mean,st.session_state[f'measure_unit_{option}_dose'],st.session_state[f'measure_unit_{option}_concentration'],
                   st.session_state[f'measure_unit_{option}_time'],graph_id, model,kind_graphic)
    
                   add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)

                graphic='Коэффициент линейной регрессии и критерий Фишера значимости линейной регрессии для параметра AUC0→∞'
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                #вызов функции построения рисунка параметры линейной регрессии
                fig = create_graphic_lin_parameters(model)
                
                add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)

   #отдельная панель, чтобы уменьшить размер вывода результатов

   col1, col2 = st.columns([0.66,0.34])
         
   #####Создание word отчета
   if panel == "Таблицы":
      if st.session_state[f"df_total_PK_{option}"] is not None: 

         ###вызов функции визуализации таблиц
         visualize_table(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],option)

      else:
          st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")

   with col1:
      if panel == "Графики":
         if st.session_state[f"df_total_PK_{option}"] is not None: 
            #######визуализация

            #классификация графиков по кнопкам
            type_graphics = st.selectbox('Выберите вид графиков',
      ('Индивидуальные фармакокинетические профили', 'Сравнение индивидуальных фармакокинетических профилей', 'Графики усредненного фармакокинетического профиля', "Сравнение фармакокинетических профилей в различных дозировках", "Зависимость значений AUC0→∞ от величин вводимых доз", "Коэффициент линейной регрессии и критерий Фишера значимости линейной регрессии для параметра AUC0→∞"),disabled = False, key = "Вид графика - ИЛ" )

            count_graphics_for_visual = len(st.session_state[f"list_heading_graphics_word_{option}"])
            list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)

            #создание чекбокса и инициация состояния, отвеч. за отрисовку графиков
            create_session_type_graphics_checked_graphics(option,type_graphics)

            if type_graphics == 'Индивидуальные фармакокинетические профили' or type_graphics == 'Сравнение индивидуальных фармакокинетических профилей' or type_graphics == 'Графики усредненного фармакокинетического профиля':
               selected_kind_individual_graphics = radio_create_individual_graphics(option,st.session_state[f'list_keys_file_{option}'])

               if type_graphics == 'Индивидуальные фармакокинетические профили':
                  selected_subject_individual_graphics = radio_create_individual_graphics(option,st.session_state[f'list_number_animal_{option}_{selected_kind_individual_graphics}'],True,selected_kind_individual_graphics)

            if st.session_state[f"{type_graphics}_{option}_checked_graphics"]:
               for i in list_range_count_graphics_for_visual:
                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("индивидуального"): 
                      if type_graphics == 'Индивидуальные фармакокинетические профили':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                         match = re.search(r'\bдозировке\s+(\d+(?:[.,]\d+)*)', graph_id)
                         number = match.group(1)
                         file_name = f"Дозировка {number}"

                         match =  (re.match(r".*№(\S+)", graph_id))
                         number_animal = "№" + match.group(1)

                         if selected_kind_individual_graphics == file_name and selected_subject_individual_graphics == number_animal:
                            if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                               kind_graphic = 'lin'
                            else:
                               kind_graphic = 'log'

                            rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,create_individual_graphics, st.session_state[f"list_time{graph_id}"],
                                                                   st.session_state[f"list_concentration{graph_id}"],
                                                                   st.session_state[f'measure_unit_{option}_time'],
                                                                   st.session_state[f'measure_unit_{option}_concentration'],
                                                                   kind_graphic,graph_id)
                            
                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение индивидуальных"):   
                      if type_graphics == 'Сравнение индивидуальных фармакокинетических профилей':
                            
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                         match = re.search(r'\bдозировке\s+(\d+(?:[.,]\d+)*)', graph_id)
                         number = match.group(1)
                         file_name = f"Дозировка {number}"

                         if selected_kind_individual_graphics == file_name:
                            if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                               kind_graphic = 'lin'
                            else:
                               kind_graphic = 'log'

                            rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_total_individual_pk_profiles, st.session_state[f"list_color{graph_id}"],
                                                                      st.session_state[f"df_for_plot_conc_1{graph_id}"],
                                                                      st.session_state[f"list_numer_animal_for_plot{graph_id}"],
                                                                      st.session_state[f'measure_unit_{option}_time'],
                                                                      st.session_state[f'measure_unit_{option}_concentration'], 
                                                                      len(st.session_state[f"list_numer_animal_for_plot{graph_id}"]),
                                                                      kind_graphic,graph_id)

                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("усредненного"):
                      if type_graphics == 'Графики усредненного фармакокинетического профиля':
                            
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]

                         match = re.search(r'\bдозировке\s+(\d+(?:[.,]\d+)*)', graph_id)
                         number = match.group(1)
                         file_name = f"Дозировка {number}"
                         special_file_name = file_name.replace("Дозировка", "") + " " + st.session_state[f'measure_unit_{option}_dose']

                         if selected_kind_individual_graphics == file_name:
                            
                            if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                               kind_graphic = 'lin'
                            else:
                               kind_graphic = 'log'

                            rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_individual_mean_std, st.session_state[f"list_time{graph_id}"],
                                                                      st.session_state[f"list_concentration{graph_id}"],
                                                                      st.session_state[f"err_y_1{graph_id}"],
                                                                      st.session_state[f'measure_unit_{option}_time'],
                                                                      st.session_state[f'measure_unit_{option}_concentration'],
                                                                      kind_graphic,graph_id,special_file_name)
     

                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Сравнение фармакокинетических"):
                      if type_graphics == 'Сравнение фармакокинетических профилей в различных дозировках':
                         
                         graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                         if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("линейных"):
                            kind_graphic = 'lin'
                         else:
                            kind_graphic = 'log'

                         rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,plot_pk_profile_total_mean_std_doses_organs, st.session_state[f"list_zip_mean_std_colors{graph_id}"],
                                                                   st.session_state[f"list_t_doses{graph_id}"],
                                                                   st.session_state[f"df_concat_mean_std{graph_id}"],
                                                                   st.session_state[f'measure_unit_{option}_time'],
                                                                   st.session_state[f'measure_unit_{option}_concentration'],
                                                                   kind_graphic,graph_id)

                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Зависимость"):
                      if type_graphics == 'Зависимость значений AUC0→∞ от величин вводимых доз':
                         
                         graph_id = 'Зависимость значений AUC0→∞ от величин вводимых доз'

                         kind_graphic = 'lin'

                         rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,create_graphic_lin, st.session_state["df_for_lin_mean"],
                                                             st.session_state[f'measure_unit_{option}_dose'],
                                                             st.session_state[f"measure_unit_{option}_concentration"],
                                                             st.session_state[f"measure_unit_{option}_time"],
                                                             graph_id,st.session_state["model"],kind_graphic)

                   if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Коэффициент"):
                      if type_graphics == 'Коэффициент линейной регрессии и критерий Фишера значимости линейной регрессии для параметра AUC0→∞':

                         col3, col4 = st.columns([2, 1])

                         with col3:
                              st.pyplot(st.session_state[f"list_graphics_word_{option}"][i])
                              st.subheader(st.session_state[f"list_heading_graphics_word_{option}"][i])

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
                     
                 #вызов функции оформлительского элемента сформированный отчет
                 selected = style_icon_report()
                  
                 if selected == "Cформированный отчeт":
                    ###вызов функции создания Word-отчета графиков
                    if st.button("Сформировать отчет"):
                       create_graphic(st.session_state[f"list_graphics_word_{option}"],st.session_state[f"list_heading_graphics_word_{option}"])
         else:
             st.error("Введите и загрузите все необходимые данные!",icon=":material/warning:")

###########################################################################################
if option == 'Экскреция препарата':
    
    st.header('Изучение экскреции препарата')

    col1, col2 = st.columns([0.66, 0.34])
    
    ####### основной экран
    with col1:
                  
         panel = main_radio_button_study(option)
                     
         #cписки для word-отчета
         list_heading_word=[]
         list_table_word=[]
         list_graphics_word=[]
         list_heading_graphics_word=[]
         initializing_session_lists_tables_graphics(option,list_heading_word,list_table_word,list_graphics_word,list_heading_graphics_word)

         if panel == "Загрузка файлов":
            
            #cостояние радио-кнопки "type_ex"
            if "index_type_ex" not in st.session_state:
                st.session_state["index_type_ex"] = 0

            type_excretion = st.radio('Выберите вид экскреции',('Фекалии', 'Моча', 'Желчь'), key = "Вид экскреции",index = st.session_state["index_type_ex"])
            
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

            measure_unit_ex_time = select_time_unit("select_time_unitэкскреция")
            measure_unit_ex_concentration = select_concentration_unit("select_time_unitэкскреция")
            #сохранение состояния выбора единиц измерения для данного исследования
            save_session_state_measure_unit_value(measure_unit_ex_time,measure_unit_ex_concentration,"экскреция")

            uploaded_file_excrement = st.file_uploader("Выбрать файл экскреции (формат XLSX)", key="Файл экскреции")

            if uploaded_file_excrement is not None:
                save_uploadedfile(uploaded_file_excrement)
                st.session_state["uploaded_file_excrement"] = uploaded_file_excrement.name
            
            if "uploaded_file_excrement" in st.session_state: 
               custom_success(f"Файл загружен: {st.session_state['uploaded_file_excrement']}")

            if "uploaded_file_excrement" in st.session_state:
                
                df = pd.read_excel(os.path.join("Папка для сохранения файлов",st.session_state["uploaded_file_excrement"]))
                st.subheader('Индивидуальные значения концентраций в ' + excretion_pr)
                
                ###интерактивная таблица
                df = edit_frame(df,st.session_state["uploaded_file_excrement"])

                table_heading='Индивидуальные и усредненные значения концентраций в ' + excretion_pr
                add_or_replace(st.session_state[f"list_heading_word_{option}"], table_heading) 

                ## вызов функции подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
                df_stats = create_table_descriptive_statistics(df)
                # Сбрасываем индекс статистики, чтобы перенести в колонку "Номер"
                df_stats_reset = df_stats.reset_index()
                # Переименовываем колонку индекса
                df_stats_reset.rename(columns={'index': 'Номер'}, inplace=True)
                # Продолжаем индексы (начинаем после последнего индекса df)
                df_stats_reset.index = range(df.index.max() + 1, df.index.max() + 1 + len(df_stats_reset))
                # Объединяем таблицы
                df_concat_round_str_transpose = pd.concat([df, df_stats_reset], axis=0, ignore_index=False)

                add_or_replace_df_graph(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],table_heading,df_concat_round_str_transpose)

                ########### диаграмма экскреции
                graphic='Выведение с ' + excretion_tv
                graph_id = graphic
                add_or_replace(st.session_state[f"list_heading_graphics_word_{option}"], graphic)

                #Инициализация состояния чекбокса параметров осей
                initializing_checkbox_status_graph_scaling_widgets(graph_id)

                col_mapping = df.columns.tolist()
                col_mapping.remove('Номер')

                list_time = []
                for i in col_mapping:
                    numer=float(i)
                    list_time.append(numer)
                
                df_averaged_concentrations=df.describe()
                list_concentration=df_averaged_concentrations.loc['mean'].tolist()

                if 0 in list_concentration:
                   list_concentration.remove(0)
                if 0 in list_time:
                   list_time.remove(0)

                st.session_state[f"list_concentration{graph_id}"] = list_concentration
                st.session_state[f"list_time{graph_id}"] = list_time

                if f"first_creating_graphic{graph_id}" not in st.session_state:
                    st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика   

                if st.session_state[f"first_creating_graphic{graph_id}"]:
                  fig = excretion_diagram(list_concentration,list_time,st.session_state['measure_unit_экскреция_time'],st.session_state['measure_unit_экскреция_concentration'],graph_id)

                  add_or_replace_df_graph(st.session_state[f"list_heading_graphics_word_{option}"],st.session_state[f"list_graphics_word_{option}"],graphic,fig)

            else:
               st.write("")    
            
            ##############################################################################################################
         
    #отдельная панель, чтобы уменьшить размер вывода результатов

    col1, col2 = st.columns([0.66,0.34])
    
    #####Создание word отчета
    if panel == "Таблицы":

          ###вызов функции визуализации таблиц
          visualize_table(st.session_state[f"list_heading_word_{option}"],st.session_state[f"list_table_word_{option}"],option)

    with col1:
       if panel == "Графики":

             #######визуализация

             count_graphics_for_visual = len(st.session_state[f"list_heading_graphics_word_{option}"])
             list_range_count_graphics_for_visual = range(0,count_graphics_for_visual)
             
             for i in list_range_count_graphics_for_visual:

                 if st.session_state[f"list_heading_graphics_word_{option}"][i].__contains__("Выведение"):
                    graph_id = st.session_state[f"list_heading_graphics_word_{option}"][i]
                    
                    kind_graphic = 'lin'

                    rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,excretion_diagram, st.session_state[f"list_concentration{graph_id}"],st.session_state[f"list_time{graph_id}"],
                                                        st.session_state['measure_unit_экскреция_time'],st.session_state['measure_unit_экскреция_concentration'],graph_id)
                    
             with col2:
             
                  #вызов функции оформлительского элемента сформированный отчет
                  selected = style_icon_report()
                   
                  if selected == "Cформированный отчeт":
                     ###вызов функции создания Word-отчета графиков
                     if st.button("Сформировать отчет"):
                        create_graphic(st.session_state[f"list_graphics_word_{option}"],st.session_state[f"list_heading_graphics_word_{option}"]) 


st.sidebar.caption('© 2025. Центр биофармацевтического анализа и метаболомных исследований (Сеченовский университет)')


