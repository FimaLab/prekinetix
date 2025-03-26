import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib.ticker import LogLocator, FuncFormatter
import re

#####Общие функции

def remove_first_element(kind_injection, *args):
    if kind_injection == "extravascular":
        return args if len(args) > 1 else args[0]

    results = []
    for obj in args:
        if isinstance(obj, list):  # Если список
            results.append(obj[1:] if obj else obj)
        elif isinstance(obj, pd.DataFrame):  # Если DataFrame
            results.append(obj.drop(index=obj.index[0]))
        else:
            results.append(obj)  # Оставляем неизменённые объекты

    return results if len(results) > 1 else results[0]  # Если один объект, возвращаем без списка

def radio_create_individual_graphics(option,list_keys_file,selected_subject=None,file_name=None):
    
    if selected_subject is not None:
        # Генерируем варианты выбора
        options = [f"{i}" for i in list_keys_file]
    else:
        options = [f"{i[:-5]}" for i in list_keys_file]

    if selected_subject is not None:

       # Отображаем радиокнопку с сохранением состояния
       if file_name is not None:
          selected = st.radio(f"Выберите субъект:", options, key = f'key_subject_radio_create_individual_graphics{option}_{file_name}',horizontal=True)
       else:
          selected = st.radio(f"Выберите субъект:", options, key = f'key_subject_radio_create_individual_graphics{option}',horizontal=True)
    else:

       selected = st.radio(f"Выберите вариант:", options, key = f'key_radio_create_individual_graphics{option}',horizontal=True)

    return selected

#функция отрисовки графиков с виджетами масштаба 

def rendering_graphs_with_scale_widgets(graph_id,option,i,kind_graphic,child_func_create_graphic, *args, **kwargs):

    col3, col4 = st.columns([2, 1])
                         
    with col4: 
        
        if kind_graphic == 'log':

           #Инициализация состояний видежтов параметров осей
           initializing_status_graph_scaling_widgets(graph_id,min_value_X=0.0,max_value_X=1.0,major_ticks_X=1.0,minor_ticks_X=1.0,
                                       min_value_Y=1.0,max_value_Y=1.0,major_ticks_Y=10.0,minor_ticks_Y=10.0)
           

           if f'y_settings_{graph_id}' not in st.session_state:
            st.session_state[f'y_settings_{graph_id}'] = {
                "min": 1.0,
                "max": 0,
                "major": 10.0,
                "minor": 10.0
            }

        else:
            
            #Инициализация состояний видежтов параметров осей
           initializing_status_graph_scaling_widgets(graph_id,min_value_X=0.0,max_value_X=1.0,major_ticks_X=1.0,minor_ticks_X=1.0,
                                       min_value_Y=0.0,max_value_Y=1.0,major_ticks_Y=1.0,minor_ticks_Y=1.0)
           
           if f'y_settings_{graph_id}' not in st.session_state:
            st.session_state[f'y_settings_{graph_id}'] = {
                "min": 0,
                "max": 0,
                "major": 0,
                "minor": 0
            }
        
        if f'x_settings_{graph_id}' not in st.session_state:
            st.session_state[f'x_settings_{graph_id}'] = {
                "min": 0,
                "max": 0,
                "major": 0,
                "minor": 0
            }
            
        
        
        if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}']:
            
            x_settings = st.session_state[f'x_settings_{graph_id}']

            y_settings = st.session_state[f'y_settings_{graph_id}']


        # Переключатель настройки осей
        custom_axis = st.checkbox("Настроить параметры графика вручную", value = st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'], key = f"Настроить параметры графика вручную {graph_id}")
        st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] = custom_axis

        new_kwargs = kwargs.copy() if kwargs else {}  # Создаем пустой словарь, если kwargs = None

        if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}']:
            
            # Инициализация состояния, если его еще нет
            if f'legend_x{graph_id}' not in st.session_state:
                st.session_state[f'legend_x{graph_id}'] = 0.8

            if f'legend_y{graph_id}' not in st.session_state:
                st.session_state[f'legend_y{graph_id}'] = 0.9

            #if f'fontsize_{graph_id}' not in st.session_state:
                #st.session_state[f'fontsize_{graph_id}'] = st.session_state[f'default_fontsize_{graph_id}']
            
            #if f'markerscale_{graph_id}' not in st.session_state:
                #st.session_state[f'markerscale_{graph_id}'] = st.session_state[f'default_markerscale_{graph_id}']

            #if f'handlelength_{graph_id}' not in st.session_state:
                #st.session_state[f'handlelength_{graph_id}'] = st.session_state[f'default_handlelength_{graph_id}']

            #if f'handleheight_{graph_id}' not in st.session_state:
                #st.session_state[f'handleheight_{graph_id}'] = st.session_state[f'default_handleheight_{graph_id}']
            
            with st.expander(f"Настройка легенды"):
                if graph_id != "Тканевая доступность в органах" and graph_id.__contains__("Выведение") == False:
                   legend_x = st.slider("X-позиция легенды", 0.0, 1.0, st.session_state[f'legend_x{graph_id}'], key = f'key_legend_x{graph_id}')
                   legend_y = st.slider("Y-позиция легенды", 0.0, 1.0, st.session_state[f'legend_y{graph_id}'], key = f'key_legend_y{graph_id}')

                #fontsize = st.slider("Размер шрифта", 1, 20, st.session_state[f'fontsize_{graph_id}'])
                #markerscale = st.slider("Размер маркеров", 0.1, 3.0, st.session_state[f'markerscale_{graph_id}'])
                #handlelength = st.slider("Длина линии", 0.5, 5.0, st.session_state[f'handlelength_{graph_id}'])
                #handleheight = st.slider("Высота линии", 0.5, 3.0, st.session_state[f'handleheight_{graph_id}'])

                # Обновление session_state при изменении слайдеров
                #st.session_state[f'fontsize_{graph_id}'] = fontsize
                #st.session_state[f'markerscale_{graph_id}'] = markerscale
                #st.session_state[f'handlelength_{graph_id}'] = handlelength
                #st.session_state[f'handleheight_{graph_id}'] = handleheight
            
            if graph_id != "Тканевая доступность в органах" and graph_id.__contains__("Выведение") == False:
               # Настройка осей через виджеты
               x_settings = axis_settings("X",graph_id,f"X_graphic_min_value_{graph_id}",f"X_graphic_max_value_{graph_id}",
                                           f"X_graphic_major_ticks_{graph_id}",f"X_graphic_minor_ticks_{graph_id}")  # Виджет для оси X
            else:
               x_settings = {
                   "min": 0.0,
                   "max": 0.0,
                   "major": 0.0,
                   "minor": 0.0,
               }

            y_settings = axis_settings("Y",graph_id,f"Y_graphic_min_value_{graph_id}",f"Y_graphic_max_value_{graph_id}",
                                        f"Y_graphic_major_ticks_{graph_id}",f"Y_graphic_minor_ticks_{graph_id}")  # Виджет для оси Y
            

            new_kwargs["x_settings"] = x_settings
            new_kwargs["y_settings"] = y_settings
            
            if graph_id != "Тканевая доступность в органах" and graph_id.__contains__("Выведение") == False:
               new_kwargs["legend_x"] = legend_x
               new_kwargs["legend_y"] = legend_y
            
            #new_kwargs["fontsize"] = fontsize
            #new_kwargs["markerscale"] = markerscale
            #new_kwargs["handlelength"] = handlelength
            #new_kwargs["handleheight"] = handleheight
            

            st.session_state[f'x_settings_{graph_id}'] = x_settings

            st.session_state[f'y_settings_{graph_id}'] = y_settings
            
            if st.button("Обновить график",key = f'Обновить график{graph_id}'):
                #вызов функции 
                fig = child_func_create_graphic(*args, **new_kwargs)         
                st.session_state[f"list_graphics_word_{option}"][i] = fig
                st.session_state[f"first_creating_graphic{graph_id}"] = False
                st.rerun()
        else:
            # Значения осей по умолчанию
            x_settings = {
                    "min": st.session_state[f"X_graphic_min_value_{graph_id}_default"],
                    "max": st.session_state[f"X_graphic_max_value_{graph_id}_default"],
                    "major": st.session_state[f"X_graphic_major_ticks_{graph_id}_default"],
                    "minor": st.session_state[f"X_graphic_minor_ticks_{graph_id}_default"]
            }

            if kind_graphic == 'log':

               y_settings = {
                       "min": 1.0,
                       "max": st.session_state[f"Y_graphic_max_value_{graph_id}_default"],
                       "major": 10.0,
                       "minor": 10.0
               }

            else:
               
               y_settings = {
                       "min": 0,
                       "max": st.session_state[f"Y_graphic_max_value_{graph_id}_default"],
                       "major": st.session_state[f"Y_graphic_major_ticks_{graph_id}_default"],
                       "minor": st.session_state[f"Y_graphic_minor_ticks_{graph_id}_default"]
               }
            
            new_kwargs["x_settings"] = x_settings
            new_kwargs["y_settings"] = y_settings

            #вызов функции 
            fig = child_func_create_graphic(*args, **new_kwargs)

            st.session_state[f"list_graphics_word_{option}"][i] = fig

    with col3:
        st.pyplot(st.session_state[f"list_graphics_word_{option}"][i])
        st.subheader(st.session_state[f"list_heading_graphics_word_{option}"][i])

#получение параметров осей
def get_parameters_axis(graph_id, ax,list_time=None):
    # Фиксация максимальных значений осей
    
    st.session_state[f"Y_graphic_max_value_{graph_id}"] = ax.get_ylim()[1]
    
    if "линейных" in graph_id:
       X_graphic_max_value_lin = ax.get_xlim()[1]
       st.session_state[f"X_graphic_max_value_{graph_id}"] = ax.get_xlim()[1]


    if "полулога" in graph_id and list_time is not None:
       st.session_state[f"X_graphic_max_value_{graph_id}"] = max(list_time)
    else:
       st.session_state[f"X_graphic_max_value_{graph_id}"] = ax.get_xlim()[1] #этот случай для объед графиков

    # Получение локаторов
    major_locator_X = ax.xaxis.get_major_locator()
    minor_locator_X = ax.xaxis.get_minor_locator()
    major_locator_Y = ax.yaxis.get_major_locator()
    minor_locator_Y = ax.yaxis.get_minor_locator()

    # Проверка типа локатора и получение шага
    def get_tick_step(locator, axis):
        if isinstance(locator, plt.MultipleLocator):
            return locator.base  # Если это MultipleLocator, берем base
        else:
            ticks = axis.get_majorticklocs()  # Получаем расположение тиков
            if len(ticks) > 1:
                return np.diff(ticks).mean()  # Берем среднюю разницу между тик-метками
            return None  # Если недостаточно тиков для расчета

    # Определение шагов
    st.session_state[f"X_graphic_major_ticks_{graph_id}"] = get_tick_step(major_locator_X, ax.xaxis)
    st.session_state[f"X_graphic_minor_ticks_{graph_id}"] = get_tick_step(minor_locator_X, ax.xaxis)
    st.session_state[f"Y_graphic_major_ticks_{graph_id}"] = get_tick_step(major_locator_Y, ax.yaxis)
    st.session_state[f"Y_graphic_minor_ticks_{graph_id}"] = get_tick_step(minor_locator_Y, ax.yaxis)

def create_session_type_graphics_checked_graphics(option,type_graphics):
    # Проверяем, есть ли в session_state ключ для данного чекбокса
    if f"{type_graphics}_{option}_checked_graphics" not in st.session_state:
       st.session_state[f"{type_graphics}_{option}_checked_graphics"] = False
    
    checked_graphics = st.checkbox("Показать графики", value = st.session_state[f"{type_graphics}_{option}_checked_graphics"], key=f"{type_graphics}")
    st.session_state[f"{type_graphics}_{option}_checked_graphics"] = checked_graphics

# Применение настроек осей

# Функция для форматирования чисел в целые значения
def format_y_ticks(value, _):
    return f"{int(value)}"

def applying_axis_settings(ax, x_settings, y_settings,kind_graphic):
    
    ymin, ymax = ax.get_ylim()
    padding_x_1 = (x_settings["max"] - x_settings["min"]) * 0.01
    padding_x_2 = (x_settings["max"] - x_settings["min"]) * 0.05
    padding_y_lin = (y_settings["max"] - y_settings["min"]) * 0.02
    
    if x_settings["min"] < x_settings["max"]:
       ax.set_xlim(0 - padding_x_1, x_settings["max"] + padding_x_2)
       ax.xaxis.set_major_locator(plt.MultipleLocator(x_settings["major"]))
       ax.xaxis.set_minor_locator(plt.MultipleLocator(x_settings["minor"]))

    if kind_graphic == 'log':
       
       if y_settings["min"] < y_settings["max"]:
          ax.set_ylim(ymin, y_settings["max"])
          ax.yaxis.set_major_locator(LogLocator(base=10.0))
          ax.yaxis.set_minor_locator(LogLocator(base=10.0))
          # Используем ScalarFormatter для отображения чисел в обычном формате
          ax.yaxis.set_major_formatter(FuncFormatter(format_y_ticks))

    else:
       
       if y_settings["min"] < y_settings["max"]:
           ax.set_ylim(0 - padding_y_lin,y_settings["max"])
           ax.yaxis.set_major_locator(plt.MultipleLocator(y_settings["major"]))
           ax.yaxis.set_minor_locator(plt.MultipleLocator(y_settings["minor"]))

def initializing_checkbox_status_graph_scaling_widgets(graph_id):
   if f'checkbox_status_graph_scaling_widgets_{graph_id}' not in st.session_state:
      st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] = False

# Функция для инициализации состояния параметров осей
def initializing_status_graph_scaling_widgets(graph_id,min_value_X,max_value_X,major_ticks_X,minor_ticks_X,
                                              min_value_Y,max_value_Y,major_ticks_Y,minor_ticks_Y):
     #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_min_value_{graph_id}" not in st.session_state:
          st.session_state[f"X_graphic_min_value_{graph_id}"] = min_value_X
      
      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_max_value_{graph_id}" not in st.session_state:
          st.session_state[f"X_graphic_max_value_{graph_id}"] = max_value_X

      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_major_ticks_{graph_id}" not in st.session_state:
          st.session_state[f"X_graphic_major_ticks_{graph_id}"] = major_ticks_X

      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_minor_ticks_{graph_id}" not in st.session_state:
          st.session_state[f"X_graphic_minor_ticks_{graph_id}"] = minor_ticks_X

      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_min_value_{graph_id}" not in st.session_state:
          st.session_state[f"Y_graphic_min_value_{graph_id}"] = min_value_Y
      
      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_max_value_{graph_id}" not in st.session_state:
          st.session_state[f"Y_graphic_max_value_{graph_id}"] = max_value_Y

      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_major_ticks_{graph_id}" not in st.session_state:
          st.session_state[f"Y_graphic_major_ticks_{graph_id}"] = major_ticks_Y

      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_minor_ticks_{graph_id}" not in st.session_state:
          st.session_state[f"Y_graphic_minor_ticks_{graph_id}"] = minor_ticks_Y


      ###
      #дефолтные значения осей без пользовательского указания
      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_min_value_{graph_id}_default" not in st.session_state:
          st.session_state[f"X_graphic_min_value_{graph_id}_default"] = min_value_X
      
      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_max_value_{graph_id}_default" not in st.session_state:
          st.session_state[f"X_graphic_max_value_{graph_id}_default"] = max_value_X

      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_major_ticks_{graph_id}_default" not in st.session_state:
          st.session_state[f"X_graphic_major_ticks_{graph_id}_default"] = major_ticks_X

      #Инизиализация состояния виджетов масштабирования графиков
      if f"X_graphic_minor_ticks_{graph_id}_default" not in st.session_state:
          st.session_state[f"X_graphic_minor_ticks_{graph_id}_default"] = minor_ticks_X

      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_min_value_{graph_id}_default" not in st.session_state:
          st.session_state[f"Y_graphic_min_value_{graph_id}_default"] = min_value_Y
      
      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_max_value_{graph_id}_default" not in st.session_state:
          st.session_state[f"Y_graphic_max_value_{graph_id}_default"] = max_value_Y

      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_major_ticks_{graph_id}_default" not in st.session_state:
          st.session_state[f"Y_graphic_major_ticks_{graph_id}_default"] = major_ticks_Y

      #Инизиализация состояния виджетов масштабирования графиков
      if f"Y_graphic_minor_ticks_{graph_id}_default" not in st.session_state:
          st.session_state[f"Y_graphic_minor_ticks_{graph_id}_default"] = minor_ticks_Y


# Функция для настройки осей
def axis_settings(axis_name,graph_id,min_value,max_value,major_ticks,minor_ticks):
    
    # Сохранение значений в сессии
    with st.expander(f"Настройка параметров оси {axis_name}"):
        
         min_value = st.session_state[min_value]
         st.session_state[f"{axis_name}_graphic_min_value_{graph_id}"] = min_value

         max_value = st.number_input(f"Граница Максимум ({axis_name})", value=st.session_state[max_value], step=1.0, key=f"{axis_name}_max_{graph_id}")
         st.session_state[f"{axis_name}_graphic_max_value_{graph_id}"] = max_value
         
         if "линейных" in graph_id:
            if axis_name == "X":
               major_ticks = st.number_input(f"Основная единица измерения ({axis_name})", value=st.session_state[major_ticks], step=0.1, key=f"{axis_name}_major_{graph_id}")
               st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks
            else:
               major_ticks = st.number_input(f"Основная единица измерения ({axis_name})", value=st.session_state[major_ticks], step=0.1, key=f"{axis_name}_major_{graph_id}")
               st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks
         elif "полулогариф" in graph_id:
              if axis_name == "X":
                 major_ticks = st.number_input(f"Основная единица измерения ({axis_name})", value=st.session_state[major_ticks], step=0.1, key=f"{axis_name}_major_{graph_id}")
                 st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks
              else:
                 major_ticks = st.session_state[major_ticks]
                 st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks
         else:
             if axis_name == "X":
               major_ticks = st.number_input(f"Основная единица измерения ({axis_name})", value=st.session_state[major_ticks], step=0.1, key=f"{axis_name}_major_{graph_id}")
               st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks
             else:
                major_ticks = st.number_input(f"Основная единица измерения ({axis_name})", value=st.session_state[major_ticks], step=0.1, key=f"{axis_name}_major_{graph_id}")
                st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks

         minor_ticks = st.session_state[minor_ticks]
         st.session_state[f"{axis_name}_graphic_minor_ticks_{graph_id}"] = minor_ticks

         # Проверка корректности значений
         errors = []
         if min_value >= max_value:
             errors.append("Максимальное значение должно быть больше минимального.")

         if major_ticks <= 0:
             errors.append("Основная единица измерения должна быть больше 0.")

         #if minor_ticks <= 0:
             #errors.append("Дополнительная единица измерения должна быть больше 0.")

         #if minor_ticks >= major_ticks:
             #errors.append("Дополнительная единица измерения должна быть меньше основной.")
         
         if ("линейных" in graph_id) or ("полулогариф" in graph_id and axis_name == "X"):
            range_size = max_value - min_value
            if range_size < major_ticks:
                errors.append("Основная единица измерения должна быть меньше диапазона оси.")

         #if range_size < minor_ticks:
             #errors.append("Дополнительная единица измерения должна быть меньше диапазона оси.")

         #if range_size % major_ticks != 0:
             #errors.append("Основная единица измерения не делит диапазон оси без остатка.")

         #if range_size % minor_ticks != 0:
             #errors.append("Дополнительная единица измерения не делит диапазон оси без остатка.")

         # Вывод ошибок
         if errors:
             for error in errors:
                 st.warning(error)

         return {
             "min": min_value,
             "max": max_value,
             "major": major_ticks,
             "minor": minor_ticks,
         }

#####частные функции

def checking_file_names_organ_graphs(option,file_name):
    if file_name == "Кровь":
        measure_unit_org = st.session_state[f'measure_unit_{option}_concentration']
    else:
        measure_unit_org = st.session_state[f'measure_unit_{option}_organs']
    
    return measure_unit_org

def create_individual_graphics(list_time,list_concentration,measure_unit_time, measure_unit_concentration, kind_graphic,graph_id,x_settings=None,y_settings=None,legend_x=None,legend_y=None):
    
    # Регулярное выражение для извлечения всего после "№"
    pattern = r"№\s*(\d+.*)"
    match = re.search(pattern, graph_id)
    number_animal = match.group(1)

    fig, ax = plt.subplots()

    plt.plot(list_time,list_concentration, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",zorder=10, label=f'{number_animal}')
    # Убираем рамку вокруг графика
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0)
    
    if kind_graphic == 'lin':
       ax.spines['bottom'].set_visible(False)
       ax.spines['left'].set_visible(False)
       # Добавляем пользовательские оси (чтобы маркеры не обрезались)
       ax.axhline(0, color='grey', linewidth=0.9, zorder=2)  # Ось X
       ax.axvline(0, color='grey', linewidth=0.9, zorder=2)  # Ось Y

    if kind_graphic == 'log':
        ax.set_yscale("log")
        ax.spines['bottom'].set_color('grey') # Ось X
        ax.spines['left'].set_color('grey') # Ось Y
    plt.xlabel(f"Время, {measure_unit_time}")
    plt.ylabel("Концентрация, "+measure_unit_concentration)

    # Добавляем легенду с номером животного
    legend = ax.legend(loc='upper right', frameon=True)  # Можно поменять loc на другой угол
    legend.set_draggable(True)  # Позволяет перетаскивать легенду
   
    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
                applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax,list_time)

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and legend_x is not None:
       # Добавляем легенду с пользовательскими координатами
       ax.legend(loc=(legend_x, legend_y))
    
    if (st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None) ==  False:
       ymin, ymax = ax.get_ylim()
       padding_x_1 = (max(list_time) - min(list_time)) * 0.01
       padding_x_2 = (max(list_time) - min(list_time)) * 0.05
       padding_y_lin = (np.nanmax(list_concentration) - np.nanmin(list_concentration)) * 0.02 #игнорировать Nan для полулогарифм

       ax.set_xlim(0 - padding_x_1, max(list_time) + padding_x_2)
       if kind_graphic == 'log':       
          ax.set_ylim(ymin, ymax)
          ax.yaxis.set_major_locator(LogLocator(base=10.0))
          ax.yaxis.set_minor_locator(LogLocator(base=10.0))
          # Используем ScalarFormatter для отображения чисел в обычном формате
          ax.yaxis.set_major_formatter(FuncFormatter(format_y_ticks))

       else:
          ax.set_ylim(0 - padding_y_lin,ymax)


    return fig

def first_creating_create_individual_graphics(graph_id,list_time,list_concentration,measure_unit_time,measure_unit_concentration,kind_graphic,add_or_replace_df_graph, child_args):
    #Инициализация состояния чекбокса параметров осей
    initializing_checkbox_status_graph_scaling_widgets(graph_id)

    #Сохранение состояний данных графика
    st.session_state[f"list_time{graph_id}"] = list_time
    st.session_state[f"list_concentration{graph_id}"] = list_concentration

    if f"first_creating_graphic{graph_id}" not in st.session_state:
        st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика

    if st.session_state[f"first_creating_graphic{graph_id}"]:
        
        fig = create_individual_graphics(list_time,list_concentration,measure_unit_time, measure_unit_concentration, kind_graphic,graph_id)

        add_or_replace_df_graph(*child_args,fig)

# объединенные индивидуальные в полулогарифмических координатах методом замены np.nan
def replace_value_less_one_plot_total_individual_pk_profiles(df_for_plot_conc_1):
    # объединенные индивидуальные в полулогарифмических координатах методом замены np.nan
    df_for_plot_conc_1_log = df_for_plot_conc_1.copy()  # Создаем копию исходного DataFrame
    df_for_plot_conc_1_log[df_for_plot_conc_1_log <= 0] = np.nan  # Заменяем значения меньше 1 на np.nan

    return df_for_plot_conc_1_log

#функция построения графика объединенного индивидуальных профелей
def plot_total_individual_pk_profiles(list_color,df_for_plot_conc_1,list_numer_animal_for_plot,measure_unit_time,measure_unit_concentration,count_numer_animal,kind_graphic,graph_id,
                                      x_settings=None,y_settings=None,legend_x=None,legend_y=None):
   
    fig, ax = plt.subplots()

    ax.set_prop_cycle(cycler(color=list_color))

    plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot,zorder=10)

    # Убираем рамку вокруг графика
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0)
    
    if kind_graphic == 'lin':
       ax.spines['bottom'].set_visible(False)
       ax.spines['left'].set_visible(False)
       # Добавляем пользовательские оси (чтобы маркеры не обрезались)
       ax.axhline(0, color='grey', linewidth=0.9, zorder=2)  # Ось X
       ax.axvline(0, color='grey', linewidth=0.9, zorder=2)  # Ось Y

    if kind_graphic == 'log':
        ax.set_yscale("log")
        ax.spines['bottom'].set_color('grey') # Ось X
        ax.spines['left'].set_color('grey') # Ось Y

    ax.set_xlabel(f"Время, {measure_unit_time}")
    ax.set_ylabel("Концентрация, "+ measure_unit_concentration)

    if count_numer_animal > 20:
        ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
    else:
        ax.legend(bbox_to_anchor=(1, 1))
    
    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
                applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)

        # Получаем объект легенды
        #legend = ax.get_legend()

        # Если легенда существует, извлекаем параметры
        #if legend:
            #fontsize = legend.get_texts()[0].get_fontsize()  # Размер шрифта
            #markerscale = legend.legendHandles[0].get_markersize() / plt.rcParams["lines.markersize"]  # Масштаб маркеров
            #handlelength = legend.legendHandles[0].get_linewidth()  # Длина маркеров (альтернативный способ)
            # Высота маркеров (нет прямого метода, но можно оценить через pad)
            #handleheight = legend.legendHandles[0].get_markersize() if legend.legendHandles else None 

            #if f'default_fontsize_{graph_id}' not in st.session_state:
                #st.session_state[f'default_fontsize_{graph_id}'] = int(fontsize)
            
            #if f'default_markerscale_{graph_id}' not in st.session_state:
                #st.session_state[f'default_markerscale_{graph_id}'] = markerscale

            #if f'default_handlelength_{graph_id}' not in st.session_state:
                #st.session_state[f'default_handlelength_{graph_id}'] = handlelength

            #if f'default_handleheight_{graph_id}' not in st.session_state:
                #st.session_state[f'default_handleheight_{graph_id}'] = handleheight


    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and legend_x is not None:
       # Добавляем легенду с пользовательскими координатами
       ax.legend(loc=(legend_x, legend_y))#prop={'size': fontsize},markerscale=markerscale,handlelength=handlelength,handleheight=handleheight)
       ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
    
    if (st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None) ==  False:
       ymin, ymax = ax.get_ylim()
       padding_x_1 = (max(df_for_plot_conc_1.index.tolist()) - min(df_for_plot_conc_1.index.tolist())) * 0.01
       padding_x_2 = (max(df_for_plot_conc_1.index.tolist()) - min(df_for_plot_conc_1.index.tolist())) * 0.05
       padding_y_lin = (np.nanmax(df_for_plot_conc_1.values) - np.nanmin(df_for_plot_conc_1.values)) * 0.02 #игнорировать Nan для полулогарифм

       ax.set_xlim(0 - padding_x_1, max(df_for_plot_conc_1.index.tolist()) + padding_x_2)
       if kind_graphic == 'log':       
          ax.set_ylim(ymin, ymax)
          ax.yaxis.set_major_locator(LogLocator(base=10.0))
          ax.yaxis.set_minor_locator(LogLocator(base=10.0))
          # Используем ScalarFormatter для отображения чисел в обычном формате
          ax.yaxis.set_major_formatter(FuncFormatter(format_y_ticks))

       else:
          ax.set_ylim(0 - padding_y_lin,ymax)

    return fig

def first_creating_plot_total_individual_pk_profiles(graph_id,list_color,df_for_plot_conc_1,list_numer_animal_for_plot,measure_unit_time,measure_unit_concentration,count_numer_animal,kind_graphic,add_or_replace_df_graph, child_args):
    #Инициализация состояния чекбокса параметров осей
    initializing_checkbox_status_graph_scaling_widgets(graph_id)

    #Сохранение состояний данных графика
    st.session_state[f"list_color{graph_id}"] = list_color
    st.session_state[f"df_for_plot_conc_1{graph_id}"] = df_for_plot_conc_1
    st.session_state[f"list_numer_animal_for_plot{graph_id}"] = list_numer_animal_for_plot
    st.session_state[f"count_numer_animal{graph_id}"] = count_numer_animal

    if f"first_creating_graphic{graph_id}" not in st.session_state:
        st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика

    if st.session_state[f"first_creating_graphic{graph_id}"]:
        #вызов функции построения графика индивидуального срединных профелей линейный
        fig = plot_total_individual_pk_profiles(list_color,df_for_plot_conc_1,list_numer_animal_for_plot,measure_unit_time,
                                                            measure_unit_concentration,count_numer_animal,kind_graphic,graph_id)

        add_or_replace_df_graph(*child_args,fig)

#функция построения графика индивидуального срединных профелей
def plot_pk_profile_individual_mean_std(list_time,list_concentration,err_y_1,measure_unit_time,measure_unit_concentration,kind_graphic,graph_id,file_name,x_settings=None,y_settings=None,legend_x=None,legend_y=None):
    

    fig, ax = plt.subplots()
    if kind_graphic == 'log':
       plt.plot(list_time,list_concentration, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black", zorder=10,label = file_name)
    else:
       plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,zorder=10,label = file_name)
    
    # Убираем рамку вокруг графика
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0)
    
    if kind_graphic == 'lin':
       ax.spines['bottom'].set_visible(False)
       ax.spines['left'].set_visible(False)
       # Добавляем пользовательские оси (чтобы маркеры не обрезались)
       ax.axhline(0, color='grey', linewidth=0.9, zorder=2)  # Ось X
       ax.axvline(0, color='grey', linewidth=0.9, zorder=2)  # Ось Y

    if kind_graphic == 'log':
        ax.set_yscale("log")
        ax.spines['bottom'].set_color('grey') # Ось X
        ax.spines['left'].set_color('grey') # Ось Y

    plt.xlabel(f"Время, {measure_unit_time}")
    plt.ylabel("Концентрация, "+measure_unit_concentration)

    ax.legend()

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
                applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax, list_time)

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and legend_x is not None:
       # Добавляем легенду с пользовательскими координатами
       ax.legend(loc=(legend_x, legend_y))
    
    if (st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None) ==  False:
       ymin, ymax = ax.get_ylim()
       padding_x_1 = (max(list_time) - min(list_time)) * 0.01
       padding_x_2 = (max(list_time) - min(list_time)) * 0.05
       padding_y_lin = (np.nanmax(list_concentration) - np.nanmin(list_concentration)) * 0.02 #игнорировать Nan для полулогарифм

       ax.set_xlim(0 - padding_x_1, max(list_time) + padding_x_2)
       if kind_graphic == 'log':       
          ax.set_ylim(ymin, ymax)
          ax.yaxis.set_major_locator(LogLocator(base=10.0))
          ax.yaxis.set_minor_locator(LogLocator(base=10.0))
          # Используем ScalarFormatter для отображения чисел в обычном формате
          ax.yaxis.set_major_formatter(FuncFormatter(format_y_ticks))

       else:
          ax.set_ylim(0 - padding_y_lin,ymax)

    return fig

def first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,measure_unit_time,measure_unit_concentration,kind_graphic,file_name,add_or_replace_df_graph, child_args):
    #Инициализация состояния чекбокса параметров осей
    initializing_checkbox_status_graph_scaling_widgets(graph_id)

    #Сохранение состояний данных графика
    st.session_state[f"list_time{graph_id}"] = list_time
    st.session_state[f"list_concentration{graph_id}"] = list_concentration
    st.session_state[f"err_y_1{graph_id}"] = err_y_1

    if f"first_creating_graphic{graph_id}" not in st.session_state:
        st.session_state[f"first_creating_graphic{graph_id}"] = True  # первое построение графика

    if st.session_state[f"first_creating_graphic{graph_id}"]:
        #вызов функции построения графика индивидуального срединных профелей линейный
        fig = plot_pk_profile_individual_mean_std(list_time,list_concentration,err_y_1,measure_unit_time,
                                                            measure_unit_concentration,kind_graphic,graph_id,file_name)

        add_or_replace_df_graph(*child_args,fig)

def replace_value_less_one_plot_pk_profile_total_mean_std_doses_organs(df_concat_mean_std):
    #замена всех нулей и значений меньше 1 на np.nan для данных концентрации для корректного отображения графика
    #Определяем колонки без "std" в названии
    cols_without_std = [col for col in df_concat_mean_std.columns if "std" not in col]
    # Применяем замену только к этим колонкам
    df_concat_mean_std[cols_without_std] = df_concat_mean_std[cols_without_std].mask(df_concat_mean_std[cols_without_std] <= 0, np.nan)

    return df_concat_mean_std

###построение графика "Фармакокинетический профиль в различных органах или дозировках" сравнительные срединные
def plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t,df_concat_mean_std,measure_unit_time,measure_unit_concentration,kind_graphic,graph_id,x_settings=None,y_settings=None,legend_x=None,legend_y=None):

    fig, ax = plt.subplots()

    for i,j,c in list_zip_mean_std_colors:
            if kind_graphic == 'log':
               plt.plot(list_t,df_concat_mean_std[i], color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,label=i,zorder=10)
            else:
               plt.errorbar(list_t,df_concat_mean_std[i],yerr=df_concat_mean_std[j],color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,label=i,zorder=10)
            
            # Убираем рамку вокруг графика
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            # Убираем основные и дополнительные насечки
            ax.tick_params(axis='both', which='both', length=0)
            
            if kind_graphic == 'lin':
               ax.spines['bottom'].set_visible(False)
               ax.spines['left'].set_visible(False)
               # Добавляем пользовательские оси (чтобы маркеры не обрезались)
               ax.axhline(0, color='grey', linewidth=0.9, zorder=2)  # Ось X
               ax.axvline(0, color='grey', linewidth=0.9, zorder=2)  # Ось Y

            if kind_graphic == 'log':
                ax.set_yscale("log")
                ax.spines['bottom'].set_color('grey') # Ось X
                ax.spines['left'].set_color('grey') # Ось Y

            plt.xlabel(f"Время, {measure_unit_time}")
            plt.ylabel("Концентрация, "+ measure_unit_concentration)
            ax.legend(fontsize = 8)
            
    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
        applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)
    
    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and legend_x is not None:
       # Добавляем легенду с пользовательскими координатами
       ax.legend(loc=(legend_x, legend_y))

    if (st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None) ==  False:
       ymin, ymax = ax.get_ylim()
       padding_x_1 = (max(list_t) - min(list_t)) * 0.01
       padding_x_2 = (max(list_t) - min(list_t)) * 0.05
       padding_y_lin = (np.nanmax(df_concat_mean_std.values) - np.nanmin(df_concat_mean_std.values)) * 0.02 #игнорировать Nan для полулогарифм

       ax.set_xlim(0 - padding_x_1, max(list_t) + padding_x_2)
       if kind_graphic == 'log':       
          ax.set_ylim(ymin, ymax)
          ax.yaxis.set_major_locator(LogLocator(base=10.0))
          ax.yaxis.set_minor_locator(LogLocator(base=10.0))
          # Используем ScalarFormatter для отображения чисел в обычном формате
          ax.yaxis.set_major_formatter(FuncFormatter(format_y_ticks))

       else:
          ax.set_ylim(0 - padding_y_lin,ymax)
          

    return fig

def plot_tissue_accessibility(list_name_organs,list_ft,list_ft_std,graph_id,x_settings=None,y_settings=None,legend_x=None,legend_y=None):
    ###построение диаграммы для тканевой доступности

    fig, ax = plt.subplots()
    sns.barplot(x=list_name_organs, y=list_ft,color='#42aaff',width=0.3)
    # Добавление усов вручную через errorbar
    plt.errorbar(x=np.arange(len(list_name_organs)), y=list_ft, yerr=list_ft_std, fmt='.', ecolor='black', elinewidth=0.7,capsize=1.9,capthick=0.9)
    plt.ylabel("Тканевая доступность")
    ax.set_xticklabels(list_name_organs,fontdict={'fontsize': 6.0})

    # Убираем рамку вокруг графика
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0)

    ax.spines['bottom'].set_color('grey') # Ось X
    ax.spines['left'].set_color('grey') # Ось Y
    # Добавляем пользовательские оси (чтобы маркеры не обрезались)

    kind_graphic = 'lin'

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
        applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)

    if (st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None) ==  False:
       ymin, ymax = ax.get_ylim()
       padding_y_lin = (np.nanmax(list_ft) - np.nanmin(list_ft)) * 0.02 #игнорировать Nan для полулогарифм

       ax.set_ylim(ymin,ymax)
    

    # Фиксация оси X (указав границы)
    ax.set_xlim(-0.5, len(list_name_organs) - 0.5)  # Подбирайте под количество категорий

    return fig

###линейная регрессия
def create_graphic_lin(df_for_lin_mean,measure_unit_dose_lin,measure_unit_lin_concentration,
                measure_unit_lin_time,graph_id,model,kind_graphic,x_settings=None,y_settings=None,legend_x=None,legend_y=None):

    fig, ax = plt.subplots()

    sns.regplot(x='doses',y='AUC0→∞_mean',data=df_for_lin_mean, color="black",ci=None,scatter_kws = {'s': 30}, line_kws = {'linewidth': 1})

    # Добавляем усы (ошибки)
    plt.errorbar(
        x=df_for_lin_mean['doses'],
        y=df_for_lin_mean['AUC0→∞_mean'],
        yerr=df_for_lin_mean['AUC0→∞_std'],
        fmt='o',
        color='black',
        ecolor='gray',
        elinewidth=1,
        capsize=3,
        zorder=10
    )

    # Убираем рамку вокруг графика
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0)
    
    if kind_graphic == 'lin':
       ax.spines['bottom'].set_visible(False)
       ax.spines['left'].set_visible(False)
       # Добавляем пользовательские оси (чтобы маркеры не обрезались)
       ax.axhline(0, color='grey', linewidth=0.9, zorder=2)  # Ось X
       ax.axvline(0, color='grey', linewidth=0.9, zorder=2)  # Ось Y


    plt.xlabel("Дозировка, " +measure_unit_dose_lin)
    plt.ylabel("AUC0→∞, "+ measure_unit_lin_concentration + f"*{measure_unit_lin_time}")

    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0) 

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}']:
        applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)

    
    # Определяем положение аннотации динамически
    max_y = df_for_lin_mean['AUC0→∞_mean'].max() + df_for_lin_mean['AUC0→∞_std'].max()  # Максимальное значение Y с учетом ошибок
    x_pos = df_for_lin_mean['doses'].mean()  # Среднее значение доз для X
    y_pos = max_y * 1.05  # Смещаем немного выше максимального значения
    
    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and legend_x is not None:
       # Получаем реальные границы графика
       x_min, x_max = plt.xlim()
       y_min, y_max = plt.ylim()
       # Добавляем легенду с пользовательскими координатами
       x_pos = x_min + legend_x * (x_max - x_min)  # Преобразуем относительное значение в реальные координаты X
       y_pos = y_min + legend_y * (y_max - y_min)  # Преобразуем относительное значение в реальные координаты Y

    
    plt.annotate(
        'y = {:.2f}x {} {:.2f}\n$R^2$ = {:.3f}'.format(
            round(model.params[1], 2),  # Коэффициент при x
            '-' if model.params[0] < 0 else '+',  # Условие для знака перед свободным членом
            abs(round(model.params[0], 2)),  # Модуль свободного члена
            round(model.rsquared, 3)  # Коэффициент детерминации
        ),
        xy=(x_pos, y_pos),  # Позиция аннотации
        xytext=(x_pos, y_pos),  # Текст аннотации
        fontsize=10,
        ha='center'  # Горизонтальное выравнивание
    )

    if (st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None) ==  False:
       ymin, ymax = ax.get_ylim()
       padding_x_1 = (max(df_for_lin_mean['doses']) - min(df_for_lin_mean['doses'])) * 0.01
       padding_x_2 = (max(df_for_lin_mean['doses']) - min(df_for_lin_mean['doses'])) * 0.05
       padding_y_lin = (np.nanmax(df_for_lin_mean['AUC0→∞_mean']) - np.nanmin(df_for_lin_mean['AUC0→∞_mean'])) * 0.02 #игнорировать Nan для полулогарифм

       ax.set_xlim(0 - padding_x_1, max(df_for_lin_mean['doses']) + padding_x_2)
       
       ax.set_ylim(0 - padding_y_lin,ymax)

    return fig

#рисунок параметры линейной регрессии
def create_graphic_lin_parameters(model):
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

    return fig

# Функция для вычисления критического значения F
def calculate_f_critical(alpha, df1, df2):
    return stats.f.ppf(1 - alpha, df1, df2)


def format_pvalue(pval, threshold=0.001):
    """Форматирует p-value для отображения"""
    return "< .001" if pval < threshold else f"{pval:.3f}"#нужно добавить инструмент округления

###диаграмма экскреции
def excretion_diagram(list_concentration,list_time,measure_unit_ex_time,measure_unit_ex_concentration,graph_id,x_settings=None,y_settings=None,legend_x=None,legend_y=None):

    fig, ax = plt.subplots()

    sns.barplot(x=list_time, y=list_concentration,color='#42aaff',width=0.5)
    plt.xlabel(f"Время, {measure_unit_ex_time}")
    plt.ylabel("Концентрация, "+measure_unit_ex_concentration)

    # Убираем рамку вокруг графика
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Убираем основные и дополнительные насечки
    ax.tick_params(axis='both', which='both', length=0)

    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    # Добавляем пользовательские оси (чтобы маркеры не обрезались)
    ax.axhline(0, color='grey', linewidth=1.1, zorder=2)  # Ось X
    ax.axvline(-0.5, color='grey', linewidth=0.9, zorder=2)  # Ось Y
    # Добавляем пользовательские оси (чтобы маркеры не обрезались)

    kind_graphic = 'lin'
    

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
        applying_axis_settings(ax, x_settings, y_settings,kind_graphic)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)



    # Фиксация оси X (указав границы)
    ax.set_xlim(-0.5, len(list_time) - 0.5)  # Подбирайте под количество категорий

    return fig