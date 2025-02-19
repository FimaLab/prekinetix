import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np
import pandas as pd
from cycler import cycler

#####Общие функции

#функция отрисовки графиков с виджетами масштаба 

def rendering_graphs_with_scale_widgets(graph_id,option,i,child_func_create_graphic, *args, **kwargs):

    col3, col4 = st.columns([2, 1])
                         
    with col4: 
            
        #Инициализация состояний видежтов параметров осей
        initializing_status_graph_scaling_widgets(graph_id,min_value_X=0.0,max_value_X=1.0,major_ticks_X=1.0,minor_ticks_X=1.0,
                                    min_value_Y=0.0,max_value_Y=1.0,major_ticks_Y=1.0,minor_ticks_Y=1.0)
        
        if f'x_settings_{graph_id}' not in st.session_state:
            st.session_state[f'x_settings_{graph_id}'] = {
                "min": 0,
                "max": 0,
                "major": 0,
                "minor": 0
            }
            
        if f'y_settings_{graph_id}' not in st.session_state:
            st.session_state[f'y_settings_{graph_id}'] = {
                "min": 0,
                "max": 0,
                "major": 0,
                "minor": 0
            }
        
        if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}']:
            
            x_settings = st.session_state[f'x_settings_{graph_id}']

            y_settings = st.session_state[f'y_settings_{graph_id}']


        # Переключатель настройки осей
        custom_axis = st.checkbox("Настроить параметры осей вручную", value = st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'], key = f"Настроить параметры осей вручную {graph_id}")
        st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] = custom_axis

        new_kwargs = kwargs.copy() if kwargs else {}  # Создаем пустой словарь, если kwargs = None

        if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}']:
            # Настройка осей через виджеты
            x_settings = axis_settings("X",graph_id,f"X_graphic_min_value_{graph_id}",f"X_graphic_max_value_{graph_id}",
                                        f"X_graphic_major_ticks_{graph_id}",f"X_graphic_minor_ticks_{graph_id}")  # Виджет для оси X
            y_settings = axis_settings("Y",graph_id,f"Y_graphic_min_value_{graph_id}",f"Y_graphic_max_value_{graph_id}",
                                        f"Y_graphic_major_ticks_{graph_id}",f"Y_graphic_minor_ticks_{graph_id}")  # Виджет для оси Y
            
            new_kwargs["x_settings"] = x_settings
            new_kwargs["y_settings"] = y_settings
            
            st.session_state[f'x_settings_{graph_id}'] = x_settings

            st.session_state[f'y_settings_{graph_id}'] = y_settings
            
            if st.button("Перерисовать график",key = f'Перерисовать график{graph_id}'):
                #вызов функции 
                fig = child_func_create_graphic(*args, **new_kwargs)         
                st.session_state[f"list_graphics_word_{option}"][i] = fig
                st.session_state[f"first_creating_graphic{graph_id}"] = False
                st.experimental_rerun()
        else:
            # Значения осей по умолчанию
            x_settings = {
                    "min": st.session_state[f"X_graphic_min_value_{graph_id}_default"],
                    "max": st.session_state[f"X_graphic_max_value_{graph_id}_default"],
                    "major": st.session_state[f"X_graphic_major_ticks_{graph_id}_default"],
                    "minor": st.session_state[f"X_graphic_minor_ticks_{graph_id}_default"]
            }
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
def get_parameters_axis(graph_id, ax):
    # Фиксация максимальных значений осей
    st.session_state[f"X_graphic_max_value_{graph_id}"] = ax.get_xlim()[1]
    st.session_state[f"Y_graphic_max_value_{graph_id}"] = ax.get_ylim()[1]

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
    
    checked_graphics = st.checkbox("Отрисовать графики", value = st.session_state[f"{type_graphics}_{option}_checked_graphics"], key=f"{type_graphics}")
    st.session_state[f"{type_graphics}_{option}_checked_graphics"] = checked_graphics

# Применение настроек осей
def applying_axis_settings(ax, x_settings, y_settings):
  if x_settings["min"] < x_settings["max"]:
      ax.set_xlim(x_settings["min"], x_settings["max"])
      ax.xaxis.set_major_locator(plt.MultipleLocator(x_settings["major"]))
      ax.xaxis.set_minor_locator(plt.MultipleLocator(x_settings["minor"]))

  if y_settings["min"] < y_settings["max"]:
      ax.set_ylim(y_settings["min"], y_settings["max"])
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
    with st.expander(f"Настройка параметров оси {axis_name} '{graph_id}'"):
         min_value = st.number_input(f"Граница Минимум ({axis_name})", value=st.session_state[min_value], step=1.0, key=f"{axis_name}_min_{graph_id}")
         st.session_state[f"{axis_name}_graphic_min_value_{graph_id}"] = min_value

         max_value = st.number_input(f"Граница Максимум ({axis_name})", value=st.session_state[max_value], step=1.0, key=f"{axis_name}_max_{graph_id}")
         st.session_state[f"{axis_name}_graphic_max_value_{graph_id}"] = max_value

         major_ticks = st.number_input(f"Основная единица измерения ({axis_name})", value=st.session_state[major_ticks], step=0.1, key=f"{axis_name}_major_{graph_id}")
         st.session_state[f"{axis_name}_graphic_major_ticks_{graph_id}"] = major_ticks

         minor_ticks = st.number_input(f"Дополнительная единица измерения ({axis_name})", value=st.session_state[minor_ticks], step=0.1, key=f"{axis_name}_minor_{graph_id}")
         st.session_state[f"{axis_name}_graphic_minor_ticks_{graph_id}"] = minor_ticks


         # Проверка корректности значений
         errors = []
         if min_value >= max_value:
             errors.append("Минимальное значение должно быть меньше максимального.")

         if major_ticks <= 0:
             errors.append("Основная единица измерения должна быть больше 0.")

         if minor_ticks <= 0:
             errors.append("Дополнительная единица измерения должна быть больше 0.")

         if minor_ticks >= major_ticks:
             errors.append("Дополнительная единица измерения должна быть меньше основной.")

         range_size = max_value - min_value
         if range_size < major_ticks:
             errors.append("Основная единица измерения должна быть меньше диапазона оси.")

         if range_size < minor_ticks:
             errors.append("Дополнительная единица измерения должна быть меньше диапазона оси.")

         if range_size % major_ticks != 0:
             errors.append("Основная единица измерения не делит диапазон оси без остатка.")

         if range_size % minor_ticks != 0:
             errors.append("Дополнительная единица измерения не делит диапазон оси без остатка.")

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

def checking_file_names_organ_graphs(file_name):
    if file_name == "Кровь":
        measure_unit_org = st.session_state['measure_unit_органы_concentration']
    else:
        measure_unit_org = st.session_state['measure_unit_органы_organs']
    
    return measure_unit_org

def create_individual_graphics(list_time,list_concentration,measure_unit_time, measure_unit_concentration, kind_graphic):
    fig, ax = plt.subplots()
    plt.plot(list_time,list_concentration, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black")
    if kind_graphic == 'log':
        ax.set_yscale("log")
    plt.xlabel(f"Время, {measure_unit_time}")
    plt.ylabel("Концентрация, "+measure_unit_concentration)

    return fig

# объединенные индивидуальные в полулогарифмических координатах методом замены np.nan
def replace_value_less_one_plot_total_individual_pk_profiles(df_for_plot_conc_1):
    # объединенные индивидуальные в полулогарифмических координатах методом замены np.nan
    df_for_plot_conc_1_log = df_for_plot_conc_1.copy()  # Создаем копию исходного DataFrame
    df_for_plot_conc_1_log[df_for_plot_conc_1_log < 1] = np.nan  # Заменяем значения меньше 1 на np.nan

    return df_for_plot_conc_1_log

#функция построения графика объединенного индивидуальных профелей
def plot_total_individual_pk_profiles(list_color,df_for_plot_conc_1,list_numer_animal_for_plot,measure_unit_time,measure_unit_concentration,count_numer_animal,kind_graphic):
    fig, ax = plt.subplots()

    ax.set_prop_cycle(cycler(color=list_color))

    plt.plot(df_for_plot_conc_1,marker='o',markersize=4.0,label = list_numer_animal_for_plot)

    ax.set_xlabel(f"Время, {measure_unit_time}")
    ax.set_ylabel("Концентрация, "+ measure_unit_concentration)
    if kind_graphic == 'log':
        ax.set_yscale("log")
    if count_numer_animal > 20:
        ax.legend(fontsize=(160/count_numer_animal),bbox_to_anchor=(1, 1))
    else:
        ax.legend(bbox_to_anchor=(1, 1))

    return fig

#функция построения графика индивидуального срединных профелей
def plot_pk_profile_individual_mean_std(list_time,list_concentration,err_y_1,measure_unit_time,measure_unit_concentration,kind_graphic,graph_id,x_settings=None,y_settings=None):
    fig, ax = plt.subplots()
    plt.errorbar(list_time,list_concentration,yerr=err_y_1, marker='o',markersize=4.0,color = "black",markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0)
    if kind_graphic == 'log':
        ax.set_yscale("log")
    plt.xlabel(f"Время, {measure_unit_time}")
    plt.ylabel("Концентрация, "+measure_unit_concentration)

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
                applying_axis_settings(ax, x_settings, y_settings)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)

    return fig

def first_creating_plot_pk_profile_individual_mean_std(graph_id,list_time,list_concentration,err_y_1,measure_unit_time,measure_unit_concentration,kind_graphic,add_or_replace_df_graph, child_args):
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
                                                            measure_unit_concentration,kind_graphic,graph_id)

        add_or_replace_df_graph(*child_args,fig)

def replace_value_less_one_plot_pk_profile_total_mean_std_doses_organs(df_concat_mean_std):
    #замена всех нулей и значений меньше 1 на np.nan для данных концентрации для корректного отображения графика
    #Определяем колонки без "std" в названии
    cols_without_std = [col for col in df_concat_mean_std.columns if "std" not in col]
    # Применяем замену только к этим колонкам
    df_concat_mean_std[cols_without_std] = df_concat_mean_std[cols_without_std].mask(df_concat_mean_std[cols_without_std] < 1, np.nan)

    return df_concat_mean_std

###построение графика "Фармакокинетический профиль в различных органах или дозировках" сравнительные срединные
def plot_pk_profile_total_mean_std_doses_organs(list_zip_mean_std_colors,list_t,df_concat_mean_std,measure_unit_time,measure_unit_concentration,kind_graphic,graph_id,x_settings=None,y_settings=None):
    fig, ax = plt.subplots()
    for i,j,c in list_zip_mean_std_colors:
            plt.errorbar(list_t,df_concat_mean_std[i],yerr=df_concat_mean_std[j],color= c, marker='o',markersize=4.0,markeredgecolor=c,markerfacecolor=c,ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0,label=i)
            if kind_graphic == 'log':
               ax.set_yscale("log")
            plt.xlabel(f"Время, {measure_unit_time}")
            plt.ylabel("Концентрация, "+ measure_unit_concentration)
            ax.legend(fontsize = 8)
            
            if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}'] and x_settings is not None:
                applying_axis_settings(ax, x_settings, y_settings)

            #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
            else:
                get_parameters_axis(graph_id, ax)

    return fig

#сравнение разных видов введения
def plot_total_mean_pk_profiles_bioavailability(list_time,list_concentration__intravenous_substance,
                                                list_concentration__oral_substance,
                                                list_concentration__oral_rdf,
                                                err_y_1,err_y_2,err_y_3,
                                                measure_unit_rb_time,measure_unit_rb_concentration,kind_graphic):
    fig, ax = plt.subplots()    

    plt.errorbar(list_time,list_concentration__intravenous_substance,yerr=err_y_1,color="black", marker='o',markersize=4.0,markeredgecolor="black",markerfacecolor="black",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = 'внутривенное введение')
    plt.errorbar(list_time,list_concentration__oral_substance,yerr=err_y_2,color= "red", marker='o',markersize=4.0,markeredgecolor="red",markerfacecolor="red",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = 'пероральное введение субстанции')
    plt.errorbar(list_time,list_concentration__oral_rdf,yerr=err_y_3,color= "blue", marker='o',markersize=4.0,markeredgecolor="blue",markerfacecolor="blue",ecolor="black",elinewidth=0.8,capsize=2.0,capthick=1.0, label = 'пероральное введение ГЛФ')
    if kind_graphic == 'log':
       ax.set_yscale("log")
    ax.set_xlabel(f"Время, {measure_unit_rb_time}")
    ax.set_ylabel("Концентрация, "+measure_unit_rb_concentration)
    ax.legend()

    return fig

def plot_tissue_accessibility(list_name_organs,list_ft):
    ###построение диаграммы для тканевой доступности
    list_name_organs.remove("Кровь")

    fig, ax = plt.subplots()
    sns.barplot(x=list_name_organs, y=list_ft,color='blue',width=0.3)
    plt.ylabel("Тканевая доступность")
    ax.set_xticklabels(list_name_organs,fontdict={'fontsize': 6.0})

    return fig

###линейная регрессия
def create_graphic_lin(df_for_lin_mean,measure_unit_dose_lin,measure_unit_lin_concentration,
                measure_unit_lin_time,graph_id,model,x_settings=None,y_settings=None):

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
        capsize=3
    )

    plt.xlabel("Дозировка, " +measure_unit_dose_lin)
    plt.ylabel("AUC0→∞, "+ measure_unit_lin_concentration + f"*{measure_unit_lin_time}")

    if st.session_state[f'checkbox_status_graph_scaling_widgets_{graph_id}']:
        applying_axis_settings(ax, x_settings, y_settings)

    #Установка значений из автомат подобранных библиотекой состояния виджетов масштабирования графиков
    else:
        get_parameters_axis(graph_id, ax)

    # Определяем положение аннотации динамически
    max_y = df_for_lin_mean['AUC0→∞_mean'].max() + df_for_lin_mean['AUC0→∞_std'].max()  # Максимальное значение Y с учетом ошибок
    x_pos = df_for_lin_mean['doses'].mean()  # Среднее значение доз для X
    y_pos = max_y * 1.05  # Смещаем немного выше максимального значения

    ax.set_ylim(ax.get_ylim()[0], y_pos * 1.1)

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
def excretion_diagram(df,measure_unit_ex_time,measure_unit_ex_concentration):

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

    return fig