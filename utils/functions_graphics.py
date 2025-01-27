import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def create_session_type_graphics_checked_graphics(option,type_graphics):
    # Проверяем, есть ли в session_state ключ для данного чекбокса
    if f"{type_graphics}_{option}_checked_graphics" not in st.session_state:
       st.session_state[f"{type_graphics}_{option}_checked_graphics"] = False
    
    checked_graphics = st.checkbox("Отрисовать графики", value = st.session_state[f"{type_graphics}_{option}_checked_graphics"], key=f"{type_graphics}")
    st.session_state[f"{type_graphics}_{option}_checked_graphics"] = checked_graphics

def create_graphic_lin(df_for_lin_mean,measure_unit_dose_lin,measure_unit_lin_concentration,
                measure_unit_lin_time,graph_id,x_settings,y_settings,model):

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


# Функция для вычисления критического значения F
def calculate_f_critical(alpha, df1, df2):
    return stats.f.ppf(1 - alpha, df1, df2)


def format_pvalue(pval, threshold=0.001):
    """Форматирует p-value для отображения"""
    return "< .001" if pval < threshold else f"{pval:.3f}"#нужно добавить инструмент округления