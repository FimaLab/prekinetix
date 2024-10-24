import streamlit as st
import os
import pandas as pd
from io import BytesIO
from docx import Document

import tempfile
import numpy as np
import scipy.stats as stat
import math
from sklearn.linear_model import LinearRegression
from scipy import stats



from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.shared import RGBColor

# Функция для сохранения DataFrame в формате Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)  # Возвращаем курсор в начало файла
    return output

# Обертка для скачивания файла в формате Excel с поддержкой ключа
def download_excel_button(df, label="Скачать Excel", file_name="data.xlsx", key=None):
    excel_data = to_excel(df)
    st.download_button(
        label=label,
        data=excel_data,
        file_name=file_name,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key=key  # Добавлен параметр key
    )

#округление до определенного значения значищих цифр
def round_to_significant_figures(num, sig_figs):
    # Проверка на строку "-"
    if num == "-":
        return num
    # Проверка на NaN
    elif isinstance(num, float) and math.isnan(num):
        return "-"
    # Проверка на нулевое значение
    elif num == 0:
        return 0
    # Округление для остальных значений
    else:
        # Округление числа до нужного количества значащих цифр
        rounded_num = round(num, sig_figs - int(math.floor(math.log10(abs(num))) + 1))
        
        # Если результат целое число, возвращаем его как int
        if rounded_num.is_integer():
            return int(rounded_num)
        else:
            return rounded_num


#сохранение загружаемых файлов 
def save_uploadedfile(uploadedfile):
    with open(os.path.join("Папка для сохранения файлов",uploadedfile.name),"wb") as f:
       f.write(uploadedfile.getbuffer())
     

#сохранение редактируемых файлов df_edit
def save_editfile(df_edit,uploadedfile_name):
    writer=pd.ExcelWriter(os.path.join("Папка для сохранения файлов",uploadedfile_name))
    df_edit.to_excel(writer,index=False)
    writer.save()

#превращает df в excel файл 
def to_excel(df_example_file):
       output = BytesIO()
       writer = pd.ExcelWriter(output, engine='xlsxwriter')
       df_example_file.to_excel(writer, index=False, sheet_name='Sheet1')
       workbook = writer.book
       worksheet = writer.sheets['Sheet1']
       format1 = workbook.add_format({'num_format': '0.00'}) 
       worksheet.set_column('A:A', None, format1)
       writer.save()  
       processed_data = output.getvalue()
       return processed_data
 
 ###возможность редактирования фрейма исходных данных
def edit_frame(df,uploadedfile_name):
       new_df = df
       list_columns_str = []
       for i in new_df.columns.tolist():
           i_new = str(i)
           list_columns_str.append(i_new)
       new_df.columns = list_columns_str

       edited_df = st.data_editor(new_df, key = ("edited_df" + uploadedfile_name))
       save_editfile(edited_df,uploadedfile_name)

       df_change = edited_df
       
       list_change_values = df_change.columns.tolist()
       list_change_values.remove("Номер")

       list_columns_number = []
       for i in list_change_values:
           i_new = float(i)
           list_columns_number.append(i_new)

       list_columns_number.insert(0,"Номер")

       df_change.columns = list_columns_number
       
       df = df_change
       return df

###создание Word-отчета
## функция создания отчета таблиц

def create_table(list_heading_word, list_table_word):
    ### таблицы
    zip_heading_table = zip(list_heading_word, list_table_word)

    doc = Document()

    # Устанавливаем горизонтальную ориентацию страницы
    section = doc.sections[-1]
    section.orientation = WD_ORIENT.LANDSCAPE
    new_width, new_height = section.page_height, section.page_width
    section.page_width = new_width
    section.page_height = new_height

    # Настройка стиля документа
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(8)
    
    for heading, df in zip_heading_table:
        # Добавление заголовка для каждой таблицы
        

        # Создание параграфа с заголовком
        paragraph = doc.add_paragraph(heading, style='Heading 1')

        # Настройка цвета заголовка
        run = paragraph.runs[0]
        run.font.color.rgb = RGBColor(0, 0, 0)  # Черный цвет

        # Преобразование колонок в DataFrame и добавление индексов
        name_columns = pd.DataFrame(df.columns.tolist()).T
        name_columns.columns = df.columns.tolist()
        df_columns = pd.concat([name_columns, df]).reset_index(drop=True)

        # Добавление индексов
        total_name_index = df.index.name
        list_index_names = df.index.tolist()
        list_index_names.insert(0, total_name_index)
        series_index_names = pd.Series(list_index_names, name=total_name_index)
        df_series_index_names = series_index_names.to_frame()

        # Соединение индексов с таблицей
        df_columns_indexes = pd.concat([df_series_index_names, df_columns], axis=1)

        # Создание таблицы в документе
        t = doc.add_table(rows=df_columns_indexes.shape[0], cols=df_columns_indexes.shape[1])
        t.style = 'Table Grid'

        # Задание ширины колонок в зависимости от максимальной длины текста в колонке
        for j in range(df_columns_indexes.shape[1]):
            # Вычисляем максимальную длину текста в колонке
            max_len = max([len(str(df_columns_indexes.iat[i, j])) for i in range(df_columns_indexes.shape[0])])
            width_cm = min(max_len * 0.2, 5)  # Устанавливаем максимальную ширину в 5 см
            for i in range(df_columns_indexes.shape[0]):
                t.cell(i, j).width = Cm(width_cm)

        # Заполнение таблицы данными
        for i, row_data in df_columns_indexes.iterrows():
            row = t.rows[i]
            for j, value in enumerate(row_data):
                row.cells[j].text = str(value)

    # Сохранение документа в память
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)

    # Кнопка для скачивания документа
    st.download_button(
        label="Сохранить таблицы 📃",
        data=bio.getvalue(),
        file_name="Таблицы.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

def visualize_table(list_heading_word,list_table_word):
    zip_heading_table = zip(list_heading_word,list_table_word) ###еще раз объявляем, иначе не видит zip-объект
    #####визуализация
    for heading, df in zip_heading_table:
        st.subheader(heading)
        st.write(df)

## функция создания отчета графиков
def create_graphic(list_graphics_word,list_heading_graphics_word):
    ### документ Word
    zip_graphics_heading = zip(list_graphics_word,list_heading_graphics_word)
    doc = Document()

    # Settings
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    buf = BytesIO() #костыль для того, чтобы не вылазила ошибка
    for fig, heading in zip_graphics_heading:
        buf = BytesIO()
        fig.savefig(buf, format="jpg", dpi=300, bbox_inches='tight')
        fp = tempfile.NamedTemporaryFile() 
        with open(f"{fp.name}.jpg",'wb') as ff:
             ff.write(buf.getvalue()) 
        doc.add_picture(buf)
        doc.add_paragraph(heading)
    
    doc.save(buf)
    if doc:
        st.download_button(
            label="Сохранить графики 📈",
            data=buf.getvalue(),
            file_name="Графики.docx",
            mime="docx",
            key = "graphics"
        )

## функция подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
def create_table_descriptive_statistics(df):
    col_mapping = df.columns.tolist()
    col_mapping.remove('Номер')

    list_gmean=[]
    list_cv=[]
    list_q1=[]
    list_q3=[]
    list_interquartile_range =[]
    list_confidence_interval = []
    for i in col_mapping:

        list_ser=df[i].tolist()
        list_ser_cv = list_ser#нужно с нулями для CV

        #убрать нули, т.к нули будут давать нулевое gmean
        count_for_range_ser=len(list_ser)
        list_range_ser=range(0,count_for_range_ser)
        
        list_ser_without_0=[]
        for i in list_range_ser:
            if list_ser[i] !=0:
               list_ser_without_0.append(list_ser[i])

        list_ser = list_ser_without_0

        def g_mean(list_ser):
            a=np.log(list_ser)
            return np.exp(a.mean())
        Gmean=g_mean(list_ser)
        list_gmean.append(Gmean)

        ###подсчет квартилей
        def quantile_exc(data, n):  # Where data is the data group, n is the quartile
            if n<1 or n>3:
                return False
            data.sort()
            position = (len(data) + 1)*n/4
            pos_integer = int(math.modf(position)[1])
            pos_decimal = position - pos_integer
            quartile = data[pos_integer - 1] + (data[pos_integer] - data[pos_integer - 1])*pos_decimal
            return quartile
        
        #ограничение в 4 точки минимум для q1,q3,мкд
        if len(list_ser_cv)>3:
            q1=quantile_exc(list_ser_cv, 1)
            q3=quantile_exc(list_ser_cv, 3)
            interquartile_range = q3 - q1
        else:
            q1=None
            q3=None
            interquartile_range = None

        list_q1.append(q1)
        list_q3.append(q3)
        list_interquartile_range.append(interquartile_range)

        ###расчет 95% интревала
        def confidence_interval(data):
            if len(data) <= 30:
                с_i = stat.t.interval(alpha=0.95, df=len(data)-1, 
                    loc=np.mean(data), ### или медиана
                    scale=stat.sem(data))
            else:
                с_i = stat.norm.interval(alpha=0.95, 
                 loc=np.mean(data), ### или медиана
                 scale=stat.sem(data))
            return с_i
        с_i=confidence_interval(list_ser_cv)

        list_confidence_interval.append(с_i)

        ####CV
        cv_std=lambda x: np.std(x, ddof= 1 )
        cv_mean=lambda x: np.mean(x)
        CV_std=cv_std(list_ser_cv)
        CV_mean=cv_mean(list_ser_cv)
        CV=CV_std/CV_mean * 100
        list_cv.append(CV)
        
    #для устранения None из фрейма
    # Обработка списка геометрического среднего
    list_gmean_processed = []
    for gmean in list_gmean:
        if gmean is None:
            list_gmean_processed.append("-")
        else:
            list_gmean_processed.append(gmean)

    # Обработка списка коэффициента вариации
    list_cv_processed = []
    for cv in list_cv:
        if cv is None:
            list_cv_processed.append("-")
        else:
            list_cv_processed.append(cv)

    list_gmean = list_gmean_processed
    list_cv = list_cv_processed
    
    df_averaged_concentrations=df.describe()
    df_averaged_concentrations_1= df_averaged_concentrations.drop(['25%','75%'],axis=0)
    df_averaged_concentrations_2= df_averaged_concentrations_1.rename(index={"50%": "median"})
    df_averaged_concentrations_2.loc[len(df_averaged_concentrations_2.index )] = list_gmean
    df_averaged_3 = df_averaged_concentrations_2.rename(index={6 : "Gmean"})
    df_averaged_3.loc[len(df_averaged_3.index )] = list_cv
    df_averaged_3 = df_averaged_3.rename(index={7 : "CV, %"})
    df_averaged_3.loc[len(df_averaged_3.index )] = list_q1
    df_averaged_3 = df_averaged_3.rename(index={8 : "25% квартиль"})
    df_averaged_3.loc[len(df_averaged_3.index )] = list_q3
    df_averaged_3 = df_averaged_3.rename(index={9 : "75% квартиль"})
    df_averaged_3.loc[len(df_averaged_3.index )] = list_interquartile_range
    df_averaged_3 = df_averaged_3.rename(index={10 : "МКД"})

    df_index=df.set_index('Номер')
    df_concat = pd.concat([df_index,df_averaged_3],sort=False,axis=0)
    
    df_concat_round=df_concat
    
    ###визуализация фрейма с нулями после округления
    col_mapping = df_concat_round.columns.tolist()

    list_list_series=[]
    for i in col_mapping:
        list_series = df_concat_round[i].tolist()
         
        list_series_round = []
        for i in list_series:
            value = i
            list_series_round.append(value)
             
        list_list_series.append(list_series_round)

    df_concat_round_str = pd.DataFrame(list_list_series, columns = df_concat_round.index.tolist(),index=col_mapping) 
    df_concat_round_str_transpose = df_concat_round_str.transpose()
    df_concat_round_str_transpose.index.name = 'Номер'
    
    #округление времени в качестве названий стоблцов
    list_time_round =[v for v in df_concat_round_str_transpose.columns.tolist()]
    df_concat_round_str_transpose.columns = list_time_round

    #округление количества субъектов до целого
    list_count_subjects_round =[float(v) for v in df_concat_round_str_transpose.loc["count"].tolist()]
    list_count_subjects_round =[int(v) for v in list_count_subjects_round]
    df_concat_round_str_transpose.loc["count"] = list_count_subjects_round

    ###добавление в таблицу доверительного интервала
    df_concat_round_str_transpose.loc[len(df_concat_round_str_transpose.index )] = list_confidence_interval
    index_c_i = df_concat_round_str_transpose.index.values.tolist()[-1]
    df_concat_round_str_transpose = df_concat_round_str_transpose.rename(index={index_c_i : "95% ДИ"})

    ##изменение названий параметров описательной статистики

    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-9,:],df_concat_round_str_transpose1.iloc[-1,:]=df_concat_round_str_transpose.iloc[-1,:],df_concat_round_str_transpose.iloc[-9,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-8,:],df_concat_round_str_transpose1.iloc[-6,:]=df_concat_round_str_transpose.iloc[-6,:],df_concat_round_str_transpose.iloc[-8,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-7,:],df_concat_round_str_transpose1.iloc[-5,:]=df_concat_round_str_transpose.iloc[-5,:],df_concat_round_str_transpose.iloc[-7,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-5,:],df_concat_round_str_transpose1.iloc[-4,:]=df_concat_round_str_transpose.iloc[-4,:],df_concat_round_str_transpose.iloc[-5,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-4,:],df_concat_round_str_transpose1.iloc[-3,:]=df_concat_round_str_transpose.iloc[-3,:],df_concat_round_str_transpose.iloc[-4,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-3,:],df_concat_round_str_transpose1.iloc[-2,:]=df_concat_round_str_transpose.iloc[-2,:],df_concat_round_str_transpose.iloc[-3,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose1=df_concat_round_str_transpose.copy()
    df_concat_round_str_transpose1.iloc[-2,:],df_concat_round_str_transpose1.iloc[-1,:]=df_concat_round_str_transpose.iloc[-1,:],df_concat_round_str_transpose.iloc[-2,:]
    df_concat_round_str_transpose=df_concat_round_str_transpose1
    df_concat_round_str_transpose = df_concat_round_str_transpose.rename({'min': "95% CI","95% ДИ": 'Минимум','median': "Gmean",'Gmean': "Медиана",'max': 'CV, %','CV, %': 'Максимум'}, axis='index')
    df_concat_round_str_transpose = df_concat_round_str_transpose.rename({'Максимум': 'Q1','25% квартиль': 'Максимум',}, axis='index')
    df_concat_round_str_transpose = df_concat_round_str_transpose.rename({'Максимум': 'Q3','75% квартиль': 'Максимум',}, axis='index')
    df_concat_round_str_transpose = df_concat_round_str_transpose.rename({'Максимум': 'IQR','МКД': 'Максимум',}, axis='index')
    df_concat_round_str_transpose = df_concat_round_str_transpose.rename({'Максимум': 'Минимум','Минимум': 'Максимум','count': 'N','std': 'SD','mean': 'Mean',}, axis='index')
    
    list_CI = df_concat_round_str_transpose.loc["95% CI"].tolist()

    list_left_CI = []
    list_right_CI = []
    for i,j in list_CI:
        
        if i and not pd.isna(i) and i != 'None':
            i_round = i
            j_round = j
        else:
            i_round = "-"
            j_round = "-"
        list_left_CI.append(i_round)
        list_right_CI.append(j_round)
    
    # Добавление новых строк с нижней и верхней границей доверительного интервала
    df_concat_round_str_transpose.loc['Lower 95% CI'] = list_left_CI
    df_concat_round_str_transpose.loc['Upper 95% CI'] = list_right_CI

    # Удаление строки 95% CI, если больше не нужно
    df_concat_round_str_transpose = df_concat_round_str_transpose.drop("95% CI")
    
    list_zero_time_zero_new = []
    if 0.0 in col_mapping:
       list_zero_time_zero = df_concat_round_str_transpose[0.0].tolist()
       for i in list_zero_time_zero:
           if i == 0.0 and i == 0:
              list_zero_time_zero_new.append(int(i))
           else:
              list_zero_time_zero_new.append(i)
       
       # Перезапись существующей колонки или добавление новой
       df_concat_round_str_transpose[0.0] = list_zero_time_zero_new
    
    #list_column_time_round = []
    #for i in col_mapping:
          # i = round_to_significant_figures(i, 4)
          # list_column_time_round.append(i)
    
    #df_concat_round_str_transpose.columns = list_column_time_round 
    
    #st.write(list_column_time_round)#

    #возвращение двух таблиц округленной и нет
    dict_descriptive_statistics = {'df_concat_round_str_transpose': df_concat_round_str_transpose,'df_concat': df_concat}
    return dict_descriptive_statistics

## функция подсчета опистательной статистики до ДИ 95% для ФК параметров
def create_table_descriptive_statistics_before_95CI_pk(df_PK):
    col_mapping_PK = df_PK.columns.tolist()

    list_gmean_PK=[]
    list_cv_PK=[]
    list_q1_PK=[]
    list_q3_PK=[]
    list_interquartile_range_PK =[]
    list_confidence_interval_PK = [] 

    for i in col_mapping_PK:

       list_ser_PK=df_PK[i].tolist()

       def g_mean(list_ser_PK):
             a=np.log(list_ser_PK)
             return np.exp(a.mean())
       Gmean_PK=g_mean(list_ser_PK)
       list_gmean_PK.append(Gmean_PK)

       ###подсчет квартилей
       def quantile_exc(data, n):  # Where data is the data group, n is the quartile
             if n<1 or n>3:
                return False
             data.sort()
             position = (len(data) + 1)*n/4
             pos_integer = int(math.modf(position)[1])
             pos_decimal = position - pos_integer
             quartile = data[pos_integer - 1] + (data[pos_integer] - data[pos_integer - 1])*pos_decimal
             return quartile
       
       #ограничение в 4 точки минимум для q1,q3,мкд
       if len(list_ser_PK)>3:
             q1=quantile_exc(list_ser_PK, 1)
             q3=quantile_exc(list_ser_PK, 3)
             interquartile_range = q3 - q1
       else:
             q1=None
             q3=None
             interquartile_range = None

       list_q1_PK.append(q1)
       list_q3_PK.append(q3)
       list_interquartile_range_PK.append(interquartile_range)

       ###расчет 95% интревала
       def confidence_interval(data):
             if len(data) <= 30:
                с_i = stat.t.interval(alpha=0.95, df=len(data)-1, 
                   loc=np.mean(data), ### или медиана
                   scale=stat.sem(data))
             else:
                с_i = stat.norm.interval(alpha=0.95, 
                loc=np.mean(data), ### или медиана
                scale=stat.sem(data))
             return с_i
       с_i=confidence_interval(list_ser_PK)

       list_confidence_interval_PK.append(с_i)

       ####CV
       cv_std_PK=lambda x: np.std(x, ddof= 1 )
       cv_mean_PK=lambda x: np.mean(x)

       CV_std_PK=cv_std_PK(list_ser_PK)
       CV_mean_PK=cv_mean_PK(list_ser_PK)

       CV_PK=(CV_std_PK/CV_mean_PK * 100)
       list_cv_PK.append(CV_PK)


    df_averaged_concentrations_PK=df_PK.describe()
    df_averaged_concentrations_1_PK= df_averaged_concentrations_PK.drop(['25%','75%'],axis=0)
    df_averaged_concentrations_2_PK= df_averaged_concentrations_1_PK.rename(index={"50%": "median"})
    df_averaged_concentrations_2_PK.loc[len(df_averaged_concentrations_2_PK.index )] = list_gmean_PK
    df_averaged_3_PK = df_averaged_concentrations_2_PK.rename(index={6 : "Gmean"})
    df_averaged_3_PK.loc[len(df_averaged_3_PK.index )] = list_cv_PK
    df_averaged_3_PK = df_averaged_3_PK.rename(index={7 : "CV, %"})
    df_averaged_3_PK.loc[len(df_averaged_3_PK.index )] = list_q1_PK
    df_averaged_3_PK = df_averaged_3_PK.rename(index={8 : "25% квартиль"})
    df_averaged_3_PK.loc[len(df_averaged_3_PK.index )] = list_q3_PK
    df_averaged_3_PK = df_averaged_3_PK.rename(index={9 : "75% квартиль"})
    df_averaged_3_PK.loc[len(df_averaged_3_PK.index )] = list_interquartile_range_PK
    df_averaged_3_PK = df_averaged_3_PK.rename(index={10 : "МКД"})

    return {"df_averaged_3_PK": df_averaged_3_PK,
              "list_confidence_interval_PK": list_confidence_interval_PK}

#округление количества субъектов до целого
def round_subjects_count(df_total_PK):
   list_count_subjects_round =[float(v) for v in df_total_PK.loc["count"].tolist()]
   list_count_subjects_round =[int(v) for v in list_count_subjects_round]
   df_total_PK.loc["count"] = list_count_subjects_round

###добавление в таблицу доверительного интервала
def add_ci_in_table(df_total_PK,list_confidence_interval_PK):
    df_total_PK.loc[len(df_total_PK.index )] = list_confidence_interval_PK
    index_c_i = df_total_PK.index.values.tolist()[-1]
    df_total_PK = df_total_PK.rename(index={index_c_i : "95% ДИ"})
    return df_total_PK

##изменение названий параметров описательной статистики
def rename_parametrs_descriptive_statistics(df_total_PK):
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-9,:],df_total_PK1.iloc[-1,:]=df_total_PK.iloc[-1,:],df_total_PK.iloc[-9,:]
    df_total_PK=df_total_PK1
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-8,:],df_total_PK1.iloc[-6,:]=df_total_PK.iloc[-6,:],df_total_PK.iloc[-8,:]
    df_total_PK=df_total_PK1
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-7,:],df_total_PK1.iloc[-5,:]=df_total_PK.iloc[-5,:],df_total_PK.iloc[-7,:]
    df_total_PK=df_total_PK1
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-5,:],df_total_PK1.iloc[-4,:]=df_total_PK.iloc[-4,:],df_total_PK.iloc[-5,:]
    df_total_PK=df_total_PK1
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-4,:],df_total_PK1.iloc[-3,:]=df_total_PK.iloc[-3,:],df_total_PK.iloc[-4,:]
    df_total_PK=df_total_PK1
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-3,:],df_total_PK1.iloc[-2,:]=df_total_PK.iloc[-2,:],df_total_PK.iloc[-3,:]
    df_total_PK=df_total_PK1
    df_total_PK1=df_total_PK.copy()
    df_total_PK1.iloc[-2,:],df_total_PK1.iloc[-1,:]=df_total_PK.iloc[-1,:],df_total_PK.iloc[-2,:]
    df_total_PK=df_total_PK1
    df_total_PK = df_total_PK.rename({'min': "95% CI","95% ДИ": 'Минимум','median': "Gmean",'Gmean': "Медиана",'max': 'CV, %','CV, %': 'Максимум'}, axis='index')
    df_total_PK = df_total_PK.rename({'Максимум': 'Q1','25% квартиль': 'Максимум',}, axis='index')
    df_total_PK = df_total_PK.rename({'Максимум': 'Q3','75% квартиль': 'Максимум',}, axis='index')
    df_total_PK = df_total_PK.rename({'Максимум': 'IQR','МКД': 'Максимум',}, axis='index')
    df_total_PK = df_total_PK.rename({'Максимум': 'Минимум','Минимум': 'Максимум','count': 'N','std': 'SD','mean': 'Mean',}, axis='index')

    list_CI = df_total_PK.loc["95% CI"].tolist()
    list_left_CI = []
    list_right_CI = []
    for i,j in list_CI:
        
        if i and not pd.isna(i) and i != 'None':
            i_round = i
            j_round = j
        else:
            i_round = "-"
            j_round = "-"
        list_left_CI.append(i_round)
        list_right_CI.append(j_round)
    
    # Добавление новых строк с нижней и верхней границей доверительного интервала
    df_total_PK.loc['Lower 95% CI'] = list_left_CI
    df_total_PK.loc['Upper 95% CI'] = list_right_CI

    # Удаление строки 95% CI, если больше не нужно
    df_total_PK = df_total_PK.drop("95% CI")

    return df_total_PK


def pk_parametrs_total_extravascular(df,selector_research,method_auc,dose,measure_unit_concentration,measure_unit_time,measure_unit_dose):
    
    ############ Параметры ФК

    df_without_numer=df.drop(['Номер'],axis=1)
    count_row=df_without_numer.shape[0]

    list_count_row=range(count_row)

    ###Cmax_True
    list_cmax_True_pk=[]
    for i in range(0,count_row):
        cmax=float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_cmax_True_pk.append(cmax)
    
    #выбор метода подсчета Сmax в зависимости от надобности Cmax2 (вкл)
    if st.session_state[f"agree_cmax2 - {selector_research}"] == True:
       ###создание состояния
       if f"selected_value_{selector_research}" not in st.session_state:
          st.session_state[f"selected_value_{selector_research}"] = []
       
       if f"feature_disable_selected_value_{selector_research}" not in st.session_state:
           st.session_state[f"feature_disable_selected_value_{selector_research}"] = True

       ###создание состояния
       st.info('Выбери Cmax:')
       list_columns_without_numer = df.columns.tolist()
       list_columns_without_numer.remove('Номер')

       selected_columns = st.multiselect('Выбери временную точку:', list_columns_without_numer, key=f'Выбери временную точку Cmax введения ЛС {selector_research}',max_selections=1)
       st.session_state[f"selected_columns_{selector_research}"] = selected_columns 

       list_keys_cmax = st.session_state[f"selected_value_{selector_research}"]
       if selected_columns != [] and st.session_state[f"feature_disable_selected_value_{selector_research}"]:
          selected_value = st.multiselect('Выбери значение концентрации:', df[selected_columns], key=f'Выбери значение концентрации Cmax введения ЛС {selector_research}',max_selections=1)
          list_keys_cmax.append(selected_value)

       if list_keys_cmax != []:
          st.session_state[f"selected_value_{selector_research}"] = list_keys_cmax

       list_keys_cmax = st.session_state[f"selected_value_{selector_research}"]
       list_keys_cmax_sample = [item for sublist in list_keys_cmax for item in sublist]

       if st.button('Очистить список Cmax', key=f"Очистка списка Cmax введения ЛС {selector_research}"):
          del st.session_state[f"selected_value_{selector_research}"]
          list_keys_cmax_sample = []
          selected_columns = st.session_state[f"selected_columns_{selector_research}"]
          st.session_state[f"feature_disable_selected_value_{selector_research}"] = True
                              
       st.write("Список Cmax:")
       st.write(list_keys_cmax_sample)
       
       if st.session_state[f"agree_cmax2 - {selector_research}"] == True: #данная проверка была введена, т.к истинное cmax отличается от выбранного, но при этом это нужно для последующих проверок
          list_cmax_1_pk=list_keys_cmax_sample
          list_cmax_2_pk=[]
          
    if st.session_state[f"agree_cmax2 - {selector_research}"] == False:
       list_cmax_1_pk=list_cmax_True_pk # допущение, чтобы не вылезали ошибки с неопределнной переменной
       

    if len(list_cmax_1_pk) == len(df.index.tolist()) and (st.session_state[f"agree_cmax2 - {selector_research}"] == True):
       st.session_state[f"feature_disable_selected_value_{selector_research}"] = False

       ######Cmax2

       if f"feature_disable_selected_value_{selector_research}_2" not in st.session_state:
        st.session_state[f"feature_disable_selected_value_{selector_research}_2"] = True

       st.info('Выбери Cmax(2):')
       
       selected_columns_2 = st.multiselect('Выбери временную точку:', list_columns_without_numer, key=f'Выбери временную точку Cmax2 введения ЛС {selector_research}', max_selections=1)
       st.session_state[f"selected_columns_2_{selector_research}"] = selected_columns_2

       ###создание состояния
       if f"selected_value_2_{selector_research}" not in st.session_state:
          st.session_state[f"selected_value_2_{selector_research}"] = []

       list_keys_cmax_2 = st.session_state[f"selected_value_2_{selector_research}"]
       if selected_columns_2 != [] and st.session_state[f"feature_disable_selected_value_{selector_research}_2"]:
          selected_value_2 = st.multiselect('Выбери значение концентрации:', df[selected_columns_2], key=f'Выбери значение концентрации Cmax2 введения ЛС {selector_research}', max_selections=1)
          list_keys_cmax_2.append(selected_value_2)

       if list_keys_cmax_2 != []:
          st.session_state[f"selected_value_2_{selector_research}"] = list_keys_cmax_2

       list_keys_cmax_2 = st.session_state[f"selected_value_2_{selector_research}"]
       list_keys_cmax_sample_2 = [item for sublist in list_keys_cmax_2 for item in sublist]

       if st.button('Очистить список Cmax(2)', key=f"Очистка списка Cmax(2) введения ЛС {selector_research}"):
          del st.session_state[f"selected_value_2_{selector_research}"]
          list_keys_cmax_sample_2 = []
          selected_columns_2 = st.session_state[f"selected_columns_2_{selector_research}"]
          st.session_state[f"feature_disable_selected_value_{selector_research}_2"] = True

       st.write("Список Cmax(2):")
       st.write(list_keys_cmax_sample_2)

       list_cmax_2_pk= list_keys_cmax_sample_2

       if len(list_cmax_2_pk) == len(df.index.tolist()):
          st.session_state[f"feature_disable_selected_value_{selector_research}_2"] = False
       
    ###Tmax_True   
    list_Tmax_True_pk=[]
    for cmax in list_cmax_True_pk:
        for column in df.columns:
            for num, row in df.iterrows():
                if df.iloc[num][column] == cmax:
                   list_Tmax_True_pk.append(f"{column}")
   
    list_Tmax_float_True_pk=[]           
    for i in list_Tmax_True_pk:
        Tmax=float(i)
        list_Tmax_float_True_pk.append(Tmax)

    if (len(list_cmax_1_pk) == len(df.index.tolist())) and (st.session_state[f"agree_cmax2 - {selector_research}"] == True):
       
       ###Tmax   
       list_Tmax_1=[]
       for cmax in list_cmax_1_pk:
           for column in df.columns:
               for num, row in df.iterrows():
                   if df.iloc[num][column] == cmax:
                      list_Tmax_1.append(f"{column}")
     
       list_Tmax_float_1=[]           
       for i in list_Tmax_1:
           Tmax=float(i)
           list_Tmax_float_1.append(Tmax)
       
       list_Tmax_2=[]
       for cmax in list_cmax_2_pk:
           for column in df.columns:
               for num, row in df.iterrows():
                   if df.iloc[num][column] == cmax:
                      list_Tmax_2.append(f"{column}")
     
       list_Tmax_float_2=[]           
       for i in list_Tmax_2:
           Tmax=float(i)
           list_Tmax_float_2.append(Tmax)  

    if (len(list_cmax_1_pk) == len(df.index.tolist())):
       
       ###AUC0-t
       list_AUC_0_T=[]
       if method_auc == 'linear':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ###удаление всех нулей сзади массива, т.к. AUC0-t это AUClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              list_conc_without_0=[]
              list_t_without_0=[]
              for i in list_range_for_remove_0:
                  if list_after_cmax[i] !=0:
                     list_conc_without_0.append(list_after_cmax[i])
                     list_t_without_0.append(list_after_cmax_t[i])

              list_concentration = list_before_cmax + list_conc_without_0
              list_columns_T = list_before_cmax_t + list_t_without_0
              ######################

              AUC_0_T=np.trapz(list_concentration,x=list_columns_T)
              list_AUC_0_T.append(AUC_0_T)

       if method_auc == 'linear-up/log-down':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ###удаление всех нулей сзади массива, т.к. AUC0-t это AUClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              list_conc_without_0=[]
              list_t_without_0=[]
              for i in list_range_for_remove_0:
                  if list_after_cmax[i] !=0:
                     list_conc_without_0.append(list_after_cmax[i])
                     list_t_without_0.append(list_after_cmax_t[i])

              list_concentration = list_before_cmax + list_conc_without_0
              list_columns_T = list_before_cmax_t + list_t_without_0
              ######################
              
              list_c = list_concentration
              list_t = list_columns_T
              
              count_i = len(list_c)
              list_range= range(0,count_i)
              
              list_AUC_0_T_ascending=[]
              list_AUC_0_T_descending = []
              AUC_0_T_ascending=0
              AUC_0_T_descending = 0
              a=0
              a1=0
              d=0
              d1=0
              for i in list_range:
                  if a1<count_i-1:
                     if list_c[i+1] > list_c[i]:
                        if a<count_i-1:
                            AUC_0_T_ascending += ((list_c[i]+list_c[i+1])*(list_t[i+1]-list_t[i]))/2
                            a+=1
                            list_AUC_0_T_ascending.append(AUC_0_T_ascending)
                  if d1<count_i-1:
                     if list_c[i+1] < list_c[i]:      
                        if d<count_i-1:
                            AUC_0_T_descending+=(list_t[i+1]-list_t[i])/(np.log(np.asarray(list_c[i])/np.asarray(list_c[i+1]))) *(list_c[i]-list_c[i+1])
                            d+=1
                            list_AUC_0_T_descending.append(AUC_0_T_descending)
                     a1+=1
                     d1+=1

              AUC_O_T = list_AUC_0_T_ascending[-1]+list_AUC_0_T_descending[-1]
              
              
              list_AUC_0_T.append(AUC_O_T)

       ####Сmax/AUC0-t
       list_Сmax_division_AUC0_t_for_division=zip(list_cmax_True_pk,list_AUC_0_T)
       list_Сmax_division_AUC0_t=[]
       for i,j in list_Сmax_division_AUC0_t_for_division:
               list_Сmax_division_AUC0_t.append(i/j)


       ####KEL
       list_kel_total=[]
       for i in range(0,count_row):
           list_columns_T=[]
           for column in df_without_numer.columns:
               list_columns_T.append(float(column))
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()
           list_concentration.remove(0)
           list_c=list_concentration

           list_time=df_without_numer.columns.tolist()
           list_time.remove(0) 

           list_t=[]
           for i in list_time:
               i=float(i)
               list_t.append(i)

           #срез_без_cmax
           max_value_c=max(list_c)
           index_cmax=list_c.index(max_value_c)

           list_c_without_cmax=list_c[index_cmax+1:]
           list_t_without_cmax=list_t[index_cmax+1:]

           #удаление всех нулей из массивов
           count_for_0_1=len(list_c_without_cmax)
           list_range_for_0_1=range(0,count_for_0_1)

           list_time_0=[]
           list_conc_0=[]
           for i in list_range_for_0_1:
               if list_c_without_cmax[i] !=0:
                  list_conc_0.append(list_c_without_cmax[i])
                  list_time_0.append(list_t_without_cmax[i]) 
           ################################

           n_points=len(list_conc_0)
           list_n_points = range(0,n_points)

           #создание списков с поочередно уменьщающемся кол, точек
           list_for_kel_c=[]
           for j in list_n_points:
               if j<n_points:
                  list_c_new=list_conc_0[j:n_points]
                  list_for_kel_c.append(list_c_new)
           list_for_kel_c.pop(-1) #удаление списка с одной точкой
           list_for_kel_c.pop(-1)  #удаление списка с двумя точками     

           list_for_kel_t=[]
           for j in list_n_points:
               if j<n_points:
                  list_t_new=list_time_0[j:n_points]
                  list_for_kel_t.append(list_t_new)
           list_for_kel_t.pop(-1) #удаление списка с одной точкой
           list_for_kel_t.pop(-1) #удаление списка с двумя точками 

           list_ct_zip=zip(list_for_kel_c,list_for_kel_t)

           list_kel=[]
           list_r=[]
           for i,j in list_ct_zip:

               n_points_r=len(i)

               np_c=np.asarray(i)
               np_t_1=np.asarray(j).reshape((-1,1))

               np_c_log=np.log(np_c)

               model = LinearRegression().fit(np_t_1,np_c_log)

               np_t=np.asarray(j)
               a=np.corrcoef(np_t, np_c_log)
               cor=((a[0])[1])
               r_sq=cor**2

               adjusted_r_sq=1-((1-r_sq)*((n_points_r-1))/(n_points_r-2))

               ########################################
               kel=abs(model.coef_[0])
               list_kel.append(kel)
               list_r.append(adjusted_r_sq)

           #делаем срезы списоков до rmax
           max_r=max(list_r)

           index_max_r= list_r.index(max_r)

           list_r1=list_r
           list_kel1=list_kel

           number_elem_list_r1=len(list_r1)

           list_range_kel=range(0,number_elem_list_r1) 

           list_kel_total_1=[]
           for i in list_range_kel:

               if abs(list_r[index_max_r] - list_r1[i]) < 0.0001: #проверяем все точки слева и справа от rmax
                  list_kel_total.append(list_kel1[i]*math.log(math.exp(1))) #отдаю предпочтение rmax с большим количеством точек
                  break #самая ранняя удовлетовряющая условию

           for i in list_kel_total_1:
               list_kel_total.append(i) 


       ####T1/2
       list_half_live=[]
       for i in list_kel_total:
           half_live=math.log(2)/i
           list_half_live.append(half_live)


       ###AUC0-inf 

       list_auc0_inf=[] 

       list_of_list_c=[]
       for i in range(0,count_row):
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()
           list_concentration.remove(0)
           list_c = list_concentration
           list_c.reverse() ### переворачиваем, для дальнейшей итерации с конца списка и поиска Clast не равное нулю
           list_of_list_c.append(list_c)

       list_zip_c_AUCt_inf=zip(list_kel_total,list_of_list_c)

           #AUCt-inf 
       list_auc_t_inf=[]     
       for i,j in list_zip_c_AUCt_inf:
           for clast in j:
               if clast != 0:
                  clast_true=clast
                  break
           auc_t_inf=clast_true/i
           list_auc_t_inf.append(auc_t_inf)

       list_auc_t_inf_and_AUC_0_T_zip=zip(list_AUC_0_T,list_auc_t_inf)

       for i,j in list_auc_t_inf_and_AUC_0_T_zip:
           auc0_inf=i+j    
           list_auc0_inf.append(auc0_inf)


       ####Cl_F
       list_Cl_F=[]

       for i in list_auc0_inf:
           Cl_F = float(dose)/i
           list_Cl_F.append(Cl_F) 


       ####Vz_F
       list_Vz_F=[]

       list_zip_kel_Cl_F=zip(list_kel_total,list_Cl_F)

       for i,j in list_zip_kel_Cl_F:
           Vz_F = j/i
           list_Vz_F.append(Vz_F)


       ###AUMC0-t и ###AUMC0-inf
       list_AUMCO_inf=[]

       list_AUMC0_t=[]
       

       list_C_last=[]
       list_T_last=[]

       if method_auc == 'linear':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ###удаление всех нулей сзади массива, т.к. AUMC0-t это AUMClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              list_conc_without_0=[]
              list_t_without_0=[]
              for i in list_range_for_remove_0:
                  if list_after_cmax[i] !=0:
                     list_conc_without_0.append(list_after_cmax[i])
                     list_t_without_0.append(list_after_cmax_t[i])

              list_concentration = list_before_cmax + list_conc_without_0
              list_columns_T = list_before_cmax_t + list_t_without_0
              ######################

              list_C_last.append(list_concentration[-1]) 
              list_T_last.append(list_columns_T[-1]) 

              list_len=len(list_concentration)

              list_aumc_i=[]
              for i in range(0,list_len):
                  AUMC=(list_columns_T[i] - list_columns_T[i-1]) *  ((list_concentration[i] * list_columns_T[i] + list_concentration[i-1] * list_columns_T[i-1])/2)
                  list_aumc_i.append(AUMC)

              list_aumc_i.pop(0)

              a=0
              list_AUMC0_t_1=[]
              for i in list_aumc_i:
                  a+=i
                  list_AUMC0_t_1.append(a)
              list_AUMC0_t.append(list_AUMC0_t_1[-1])
       
       if method_auc == 'linear-up/log-down':
          
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ###удаление всех нулей сзади массива, т.к. AUMC0-t это AUMClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              list_conc_without_0=[]
              list_t_without_0=[]
              for i in list_range_for_remove_0:
                  if list_after_cmax[i] !=0:
                     list_conc_without_0.append(list_after_cmax[i])
                     list_t_without_0.append(list_after_cmax_t[i])

              list_concentration = list_before_cmax + list_conc_without_0
              list_columns_T = list_before_cmax_t + list_t_without_0
              ######################

              list_C_last.append(list_concentration[-1]) 
              list_T_last.append(list_columns_T[-1])

              list_c = list_concentration
              list_t = list_columns_T

              count_i = len(list_c)
              list_range= range(0,count_i)

              list_AUMC_0_T_ascending=[]
              list_AUMC_0_T_descending = []
              AUMC_0_T_ascending=0
              AUMC_0_T_descending = 0
              a=0
              a1=0
              d=0
              d1=0
              for i in list_range:
                  if a1<count_i-1:
                      if list_c[i+1] > list_c[i]:
                          if a<count_i-1:
                              AUMC_0_T_ascending +=(list_t[i+1] - list_t[i]) *  ((list_c[i+1] * list_t[i+1] + list_c[i] * list_t[i])/2)
                              a+=1
                              list_AUMC_0_T_ascending.append(AUMC_0_T_ascending)
                  if d1<count_i-1:
                      if list_c[i+1] < list_c[i]:      
                          if d<count_i-1:
                              coeff = (list_t[i+1] - list_t[i]) / np.log(np.asarray(list_c[i+1])/np.asarray(list_c[i]))
                              AUMC_0_T_descending+= coeff * ((list_c[i+1] * list_t[i+1] - list_c[i] * list_t[i]) - coeff * (list_c[i+1] - list_c[i]))
                              d+=1
                              list_AUMC_0_T_descending.append(AUMC_0_T_descending)
                      a1+=1
                      d1+=1

              AUMC_O_T = list_AUMC_0_T_ascending[-1]+list_AUMC_0_T_descending[-1]

              list_AUMC0_t.append(AUMC_O_T)

       ########AUMC0-inf конечный подсчет
       list_zip_for_AUMC_inf=zip(list_kel_total,list_C_last,list_T_last)

       list_AUMCt_inf=[]
       for k,c,t in list_zip_for_AUMC_inf:
           AUMCt_inf=c*t/k+c/(k*k)
           list_AUMCt_inf.append(AUMCt_inf)


       list_AUMC_zip=zip(list_AUMC0_t,list_AUMCt_inf)

       for i,j in list_AUMC_zip:
           AUMCO_inf=i+j
           list_AUMCO_inf.append(AUMCO_inf)

       ###MRT0-t
       list_MRT0_t=[]

       list_zip_AUMCO_t_auc0_t = zip(list_AUMC0_t,list_AUC_0_T)

       for i,j in list_zip_AUMCO_t_auc0_t:
           MRT0_t=i/j
           list_MRT0_t.append(MRT0_t)

       ###MRT0-inf
       list_MRT0_inf=[]

       list_zip_AUMCO_inf_auc0_inf = zip(list_AUMCO_inf,list_auc0_inf)

       for i,j in list_zip_AUMCO_inf_auc0_inf:
           MRT0_inf=i/j
           list_MRT0_inf.append(MRT0_inf)
       

    
       ##################### Фрейм ФК параметров

       ### пользовательский индекс
       list_for_index=df["Номер"].tolist()
       df_PK=pd.DataFrame(list(zip(list_cmax_True_pk,list_Tmax_float_True_pk,list_C_last,list_T_last,list_MRT0_t,list_MRT0_inf,list_half_live,list_AUC_0_T,list_auc0_inf,list_AUMC0_t,list_AUMCO_inf,list_Сmax_division_AUC0_t,list_kel_total,list_Cl_F,list_Vz_F)),columns=['Cmax','Tmax','Clast','Tlast','MRT0→t','MRT0→∞','T1/2','AUC0-t','AUC0→∞','AUMC0-t','AUMC0-∞','Сmax/AUC0-t','Kel','Cl/F','Vz/F'],index=list_for_index)
    
    checking_condition_cmax2 = False

    if st.session_state[f"agree_cmax2 - {selector_research}"] == True:
        
       checking_condition_cmax2 = len(list_cmax_1_pk) == len(df.index.tolist()) and len(list_cmax_2_pk) == len(df.index.tolist()) and st.session_state[f"agree_cmax2 - {selector_research}"] == True
       
       if checking_condition_cmax2:
          
          zip_list_cmax_1_pk_cmax_2_pk = list(zip(list_cmax_1_pk, list_cmax_2_pk))

          zip_Tmax_float_1_Tmax_float_2 = list(zip(list_Tmax_float_1,list_Tmax_float_2))

          #CmaxH
          list_CmaxH = []
          
          for cmax_1_pk, cmax_2_pk in zip_list_cmax_1_pk_cmax_2_pk:
              CmaxH = max(cmax_1_pk, cmax_2_pk)
              list_CmaxH.append(CmaxH)

          #TmaxH
          list_TmaxH = []

          for Tmax_float_1, Tmax_float_2 in zip_Tmax_float_1_Tmax_float_2:
              TmaxH = max(Tmax_float_1, Tmax_float_2)
              list_TmaxH.append(TmaxH)

          #CmaxL/CmaxH
          list_CmaxL_CmaxH = []

          for cmax_1_pk, cmax_2_pk in zip_list_cmax_1_pk_cmax_2_pk:
              CmaxL_CmaxH = min(cmax_1_pk, cmax_2_pk)/max(cmax_1_pk, cmax_2_pk)
              list_CmaxL_CmaxH.append(CmaxL_CmaxH)

          #CmaxH-L
          list_CmaxH_L = []
          for cmax_1_pk, cmax_2_pk in zip_list_cmax_1_pk_cmax_2_pk:
              CmaxH_L = max(cmax_1_pk, cmax_2_pk) - min(cmax_1_pk, cmax_2_pk)
              list_CmaxH_L.append(CmaxH_L)

          #NumBtwPeaks
          list_NumBtwPeaks = []
          for Tmax_float_1, Tmax_float_2 in zip_Tmax_float_1_Tmax_float_2:
              if max(Tmax_float_1, Tmax_float_2) in list_Tmax_float_1:
                  index_max_Tmax_float = list_Tmax_float_1.index(max(Tmax_float_1, Tmax_float_2))
              else:
                  index_max_Tmax_float = list_Tmax_float_2.index(max(Tmax_float_1, Tmax_float_2))
              if min(Tmax_float_1, Tmax_float_2) in list_Tmax_float_1:
                  index_min_Tmax_float = list_Tmax_float_1.index(min(Tmax_float_1, Tmax_float_2))
              else:
                  index_min_Tmax_float = list_Tmax_float_2.index(min(Tmax_float_1, Tmax_float_2))

              NumBtwPeaks = index_max_Tmax_float - index_min_Tmax_float
              list_NumBtwPeaks.append(NumBtwPeaks)
          
          #DuraBtwPeaks
          list_DuraBtwPeaks = []
          for Tmax_float_1, Tmax_float_2 in zip_Tmax_float_1_Tmax_float_2:
              DuraBtwPeaks = max(Tmax_float_1, Tmax_float_2) - min(Tmax_float_1, Tmax_float_2)
              list_DuraBtwPeaks.append(DuraBtwPeaks)

          ### пользовательский индекс
          list_for_index=df["Номер"].tolist()
          df_PK_additional_double_peaks = pd.DataFrame(list(zip(list_cmax_1_pk,list_Tmax_float_1,list_cmax_2_pk,list_Tmax_float_2,list_CmaxH,list_TmaxH,list_CmaxL_CmaxH,list_CmaxH_L,list_NumBtwPeaks,list_DuraBtwPeaks)),columns=['Cmax1','Tmax1','Cmax2','Tmax2','CmaxH','TmaxH','CmaxL/CmaxH','CmaxH-L','Количество точек между пиками',
          'Время между пиками'],index=list_for_index)

          ###округление дополнительных ФК параметров

          series_Cmax_1=df_PK_additional_double_peaks['Cmax1']
          list_Cmax_str_f_1=[v for v in series_Cmax_1.tolist()]
          series_Cmax_1=pd.Series(list_Cmax_str_f_1, index = df_PK_additional_double_peaks.index.tolist(), name='Cmax1 ' +"("+measure_unit_concentration+")")

          series_Tmax_1=df_PK_additional_double_peaks['Tmax1']
          list_Tmax_str_f_1=[v for v in series_Tmax_1.tolist()]
          series_Tmax_1=pd.Series(list_Tmax_str_f_1, index = df_PK_additional_double_peaks.index.tolist(), name='Tmax1 ' +"("+f"{measure_unit_time}"+")")

          series_Cmax_2=df_PK_additional_double_peaks['Cmax2']
          list_Cmax_str_f_2=[v for v in series_Cmax_2.tolist()]
          series_Cmax_2=pd.Series(list_Cmax_str_f_2, index = df_PK_additional_double_peaks.index.tolist(), name='Cmax2 ' +"("+measure_unit_concentration+")")

          series_Tmax_2=df_PK_additional_double_peaks['Tmax2']
          list_Tmax_str_f_2=[v for v in series_Tmax_2.tolist()]
          series_Tmax_2=pd.Series(list_Tmax_str_f_2, index = df_PK_additional_double_peaks.index.tolist(), name='Tmax2 ' +"("+f"{measure_unit_time}"+")")

          series_CmaxH=df_PK_additional_double_peaks['CmaxH']
          list_CmaxH_str_f=[v for v in series_CmaxH.tolist()]
          series_CmaxH =pd.Series(list_CmaxH_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='CmaxH ' +"("+measure_unit_concentration+")")

          series_TmaxH=df_PK_additional_double_peaks['TmaxH']
          list_TmaxH_str_f=[v for v in series_TmaxH.tolist()]
          series_TmaxH=pd.Series(list_TmaxH_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='TmaxH ' +"("+f"{measure_unit_time}"+")")

          series_CmaxL_CmaxH=df_PK_additional_double_peaks['CmaxL/CmaxH']
          list_CmaxL_CmaxH_str_f=[v for v in series_CmaxL_CmaxH.tolist()]
          series_CmaxL_CmaxH=pd.Series(list_CmaxL_CmaxH_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='CmaxL/CmaxH')

          series_CmaxH_L=df_PK_additional_double_peaks['CmaxH-L']
          list_CmaxH_L_str_f=[v for v in series_CmaxH_L.tolist()]
          series_CmaxH_L=pd.Series(list_CmaxH_L_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='CmaxH-L ' +"("+measure_unit_concentration+")")

          series_NumBtwPeaks=df_PK_additional_double_peaks['Количество точек между пиками']
          list_NumBtwPeaks_str_f=[v for v in series_NumBtwPeaks.tolist()]
          series_NumBtwPeaks=pd.Series(list_NumBtwPeaks_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='Количество точек между пиками ')

          series_DuraBtwPeaks=df_PK_additional_double_peaks['Время между пиками']
          list_DuraBtwPeaks_str_f=[v for v in series_DuraBtwPeaks.tolist()]
          series_DuraBtwPeaks=pd.Series(list_DuraBtwPeaks_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='Время между пиками ' +"("+f"{measure_unit_time}"+")")
          
          df_total_PK_additional_double_peaks = pd.concat([series_Cmax_1, series_Tmax_1, series_Cmax_2, series_Tmax_2, series_CmaxH, series_TmaxH, 
          series_CmaxL_CmaxH, series_CmaxH_L,series_NumBtwPeaks,series_DuraBtwPeaks], axis= 1)
        
          df_total_PK_additional_double_peaks.index.name = 'Номер'
      
    if checking_condition_cmax2 or (len(list_cmax_1_pk) == len(df.index.tolist()) and (st.session_state[f"agree_cmax2 - {selector_research}"] == False)):
    
       ###описательная статистика

       dict_df_averaged_3_PK = create_table_descriptive_statistics_before_95CI_pk(df_PK)
       df_averaged_3_PK = dict_df_averaged_3_PK.get("df_averaged_3_PK")

       df_concat_PK_pk= pd.concat([df_PK,df_averaged_3_PK],sort=False,axis=0)

       ###округление описательной статистики и ФК параметров

       series_Cmax=df_concat_PK_pk['Cmax']
       list_Cmax_str_f=[v for v in series_Cmax.tolist()]
       series_Cmax=pd.Series(list_Cmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax ' +"("+measure_unit_concentration+")")

       series_Tmax=df_concat_PK_pk['Tmax']
       list_Tmax_str_f=[v for v in series_Tmax.tolist()]
       series_Tmax=pd.Series(list_Tmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Tmax ' +"("+f"{measure_unit_time}"+")")

       series_Clast=df_concat_PK_pk['Clast']
       list_Clast_str_f=[v for v in series_Clast.tolist()]
       series_Clast=pd.Series(list_Clast_str_f, index = df_concat_PK_pk.index.tolist(), name='Clast ' +"("+measure_unit_concentration+")")

       series_Tlast=df_concat_PK_pk['Tlast']
       list_Tlast_str_f=[v for v in series_Tlast.tolist()]
       series_Tlast=pd.Series(list_Tlast_str_f, index = df_concat_PK_pk.index.tolist(), name='Tlast ' +"("+f"{measure_unit_time}"+")")
       
       series_MRT0_t= df_concat_PK_pk['MRT0→t']
       list_MRT0_t_str_f=[v for v in series_MRT0_t.tolist()]
       series_MRT0_t=pd.Series(list_MRT0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='MRT0→t '+"("+f"{measure_unit_time}"+")")

       series_MRT0_inf= df_concat_PK_pk['MRT0→∞']
       list_MRT0_inf_str_f=[v for v in series_MRT0_inf.tolist()]
       series_MRT0_inf=pd.Series(list_MRT0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='MRT0→∞ '+"("+f"{measure_unit_time}"+")")

       series_half_live= df_concat_PK_pk['T1/2']
       list_half_live_str_f=[v for v in series_half_live.tolist()]
       series_half_live=pd.Series(list_half_live_str_f, index = df_concat_PK_pk.index.tolist(), name='T1/2 '+"("+f"{measure_unit_time}"+")")

       series_AUC0_t= df_concat_PK_pk['AUC0-t']
       list_AUC0_t_str_f=[v for v in series_AUC0_t.tolist()]
       series_AUC0_t=pd.Series(list_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")

       series_AUC0_inf= df_concat_PK_pk['AUC0→∞']
       list_AUC0_inf_str_f=[v for v in series_AUC0_inf.tolist()]
       series_AUC0_inf=pd.Series(list_AUC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")
       
       series_AUMC0_t= df_concat_PK_pk['AUMC0-t']
       list_AUMC0_t_str_f=[v for v in series_AUMC0_t.tolist()]
       series_AUMC0_t=pd.Series(list_AUMC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_AUMC0_inf= df_concat_PK_pk['AUMC0-∞']
       list_AUMC0_inf_str_f=[v for v in series_AUMC0_inf.tolist()]
       series_AUMC0_inf=pd.Series(list_AUMC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_Сmax_dev_AUC0_t= df_concat_PK_pk['Сmax/AUC0-t']
       list_Сmax_dev_AUC0_t_str_f=[v for v in series_Сmax_dev_AUC0_t.tolist()]
       series_Сmax_dev_AUC0_t=pd.Series(list_Сmax_dev_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='Сmax/AUC0-t '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_Kel= df_concat_PK_pk['Kel']
       list_Kel_str_f=[v for v in series_Kel.tolist()]
       series_Kel=pd.Series(list_Kel_str_f, index = df_concat_PK_pk.index.tolist(), name='Kel '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_Cl_F= df_concat_PK_pk['Cl/F']
       list_Cl_F_str_f=[v for v in series_Cl_F.tolist()]
       series_Cl_F=pd.Series(list_Cl_F_str_f, index = df_concat_PK_pk.index.tolist(), name='Cl/F ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})/{measure_unit_time}"+")")

       series_Vz_F= df_concat_PK_pk['Vz/F']
       list_Vz_F_str_f=[v for v in series_Vz_F.tolist()]
       series_Vz_F=pd.Series(list_Vz_F_str_f, index = df_concat_PK_pk.index.tolist(), name='Vz/F ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")
       
       df_total_PK_pk = pd.concat([series_Cmax, series_Tmax, series_Clast, series_Tlast, series_MRT0_t, series_MRT0_inf,series_half_live,series_AUC0_t,series_AUC0_inf,series_AUMC0_t,series_AUMC0_inf,series_Сmax_dev_AUC0_t,series_Kel,series_Cl_F,series_Vz_F], axis= 1) 
        
       
       df_total_PK_pk.index.name = 'Номер'

       #округление количества субъектов до целого
       round_subjects_count(df_total_PK_pk)
       
       #получение списка значений доверительного интервала
       list_confidence_interval_PK = dict_df_averaged_3_PK.get("list_confidence_interval_PK")

       ###добавление в таблицу доверительного интервала
       df_total_PK_pk = add_ci_in_table(df_total_PK_pk,list_confidence_interval_PK)

       ##изменение названий параметров описательной статистики

       df_total_PK_pk = rename_parametrs_descriptive_statistics(df_total_PK_pk)

       if st.session_state[f"agree_cmax2 - {selector_research}"] == False:
          dict_PK_parametrs = {
              "df_total_PK": df_total_PK_pk,
              "df_PK":df_PK,
              "df_concat_PK":df_concat_PK_pk,
              "list_cmax_1": list_cmax_True_pk #здесь такое допущение, в целом ничего страшного, просто лень меня название ключа словаря, это не как не помешает проверка в коде основго скрипта
          }
       else:
          dict_PK_parametrs = {
              "df_total_PK": df_total_PK_pk,
              "df_PK":df_PK,
              "df_concat_PK":df_concat_PK_pk,
              "list_cmax_1": list_cmax_1_pk,
              "list_cmax_2": list_cmax_2_pk,
              "df_total_PK_additional_double_peaks": df_total_PK_additional_double_peaks
          }

       return dict_PK_parametrs
       























def pk_parametrs_total_intravenously(df,selector_research,method_auc,dose,measure_unit_concentration,measure_unit_time,measure_unit_dose):
    
    ############ Параметры ФК

    df_without_numer=df.drop(['Номер'],axis=1)
    count_row=df_without_numer.shape[0]

    list_count_row=range(count_row)

    ###Cmax_True
    list_cmax_True_pk=[]
    for i in range(0,count_row):
        cmax=float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_cmax_True_pk.append(cmax)
    
    #выбор метода подсчета Сmax в зависимости от надобности Cmax2 (вкл)
    if st.session_state[f"agree_cmax2 - {selector_research}"] == True:
       ###создание состояния
       if f"selected_value_{selector_research}" not in st.session_state:
          st.session_state[f"selected_value_{selector_research}"] = []
       
       if f"feature_disable_selected_value_{selector_research}" not in st.session_state:
           st.session_state[f"feature_disable_selected_value_{selector_research}"] = True

       ###создание состояния
       st.info('Выбери Cmax:')
       list_columns_without_numer = df.columns.tolist()
       list_columns_without_numer.remove('Номер')
       selected_columns = st.multiselect('Выбери временную точку:', list_columns_without_numer, key=f'Выбери временную точку Cmax введения ЛС {selector_research}',max_selections=1)
       st.session_state[f"selected_columns_{selector_research}"] = selected_columns 

       list_keys_cmax = st.session_state[f"selected_value_{selector_research}"]
       if selected_columns != [] and st.session_state[f"feature_disable_selected_value_{selector_research}"]:
          selected_value = st.multiselect('Выбери значение концентрации:', df[selected_columns], key=f'Выбери значение концентрации Cmax введения ЛС {selector_research}',max_selections=1)
          list_keys_cmax.append(selected_value)

       if list_keys_cmax != []:
          st.session_state[f"selected_value_{selector_research}"] = list_keys_cmax

       list_keys_cmax = st.session_state[f"selected_value_{selector_research}"]
       list_keys_cmax_sample = [item for sublist in list_keys_cmax for item in sublist]

       if st.button('Очистить список Cmax', key=f"Очистка списка Cmax введения ЛС {selector_research}"):
          del st.session_state[f"selected_value_{selector_research}"]
          list_keys_cmax_sample = []
          selected_columns = st.session_state[f"selected_columns_{selector_research}"]
          st.session_state[f"feature_disable_selected_value_{selector_research}"] = True
                              
       st.write("Список Cmax:")
       st.write(list_keys_cmax_sample)
       
       if st.session_state[f"agree_cmax2 - {selector_research}"] == True: #данная проверка была введена, т.к истинное cmax отличается от выбранного, но при этом это нужно для последующих проверок
          list_cmax_1_pk=list_keys_cmax_sample
          list_cmax_2_pk=[]
          
    if st.session_state[f"agree_cmax2 - {selector_research}"] == False:
       list_cmax_1_pk=list_cmax_True_pk # допущение, чтобы не вылезали ошибки с неопределнной переменной

    if len(list_cmax_1_pk) == len(df.index.tolist()) and (st.session_state[f"agree_cmax2 - {selector_research}"] == True):
       st.session_state[f"feature_disable_selected_value_{selector_research}"] = False

       ######Cmax2

       if f"feature_disable_selected_value_{selector_research}_2" not in st.session_state:
        st.session_state[f"feature_disable_selected_value_{selector_research}_2"] = True

       st.info('Выбери Cmax(2):')
       
       selected_columns_2 = st.multiselect('Выбери временную точку:', list_columns_without_numer, key=f'Выбери временную точку Cmax2 введения ЛС {selector_research}', max_selections=1)
       st.session_state[f"selected_columns_2_{selector_research}"] = selected_columns_2

       ###создание состояния
       if f"selected_value_2_{selector_research}" not in st.session_state:
          st.session_state[f"selected_value_2_{selector_research}"] = []

       list_keys_cmax_2 = st.session_state[f"selected_value_2_{selector_research}"]
       if selected_columns_2 != [] and st.session_state[f"feature_disable_selected_value_{selector_research}_2"]:
          selected_value_2 = st.multiselect('Выбери значение концентрации:', df[selected_columns_2], key=f'Выбери значение концентрации Cmax2 введения ЛС {selector_research}', max_selections=1)
          list_keys_cmax_2.append(selected_value_2)

       if list_keys_cmax_2 != []:
          st.session_state[f"selected_value_2_{selector_research}"] = list_keys_cmax_2

       list_keys_cmax_2 = st.session_state[f"selected_value_2_{selector_research}"]
       list_keys_cmax_sample_2 = [item for sublist in list_keys_cmax_2 for item in sublist]

       if st.button('Очистить список Cmax(2)', key=f"Очистка списка Cmax(2) введения ЛС {selector_research}"):
          del st.session_state[f"selected_value_2_{selector_research}"]
          list_keys_cmax_sample_2 = []
          selected_columns_2 = st.session_state[f"selected_columns_2_{selector_research}"]
          st.session_state[f"feature_disable_selected_value_{selector_research}_2"] = True

       st.write("Список Cmax(2):")
       st.write(list_keys_cmax_sample_2)

       list_cmax_2_pk= list_keys_cmax_sample_2

       if len(list_cmax_2_pk) == len(df.index.tolist()):
          st.session_state[f"feature_disable_selected_value_{selector_research}_2"] = False

    ###Tmax_True   
    list_Tmax_True_pk=[]
    for cmax in list_cmax_True_pk:
        for column in df.columns:
            for num, row in df.iterrows():
                if df.iloc[num][column] == cmax:
                   list_Tmax_True_pk.append(f"{column}")
   
    list_Tmax_float_True_pk=[]           
    for i in list_Tmax_True_pk:
        Tmax=float(i)
        list_Tmax_float_True_pk.append(Tmax)

    if (len(list_cmax_1_pk) == len(df.index.tolist())) and (st.session_state[f"agree_cmax2 - {selector_research}"] == True):
       
       ###Tmax   
       list_Tmax_1=[]
       for cmax in list_cmax_1_pk:
           for column in df.columns:
               for num, row in df.iterrows():
                   if df.iloc[num][column] == cmax:
                      list_Tmax_1.append(f"{column}")
     
       list_Tmax_float_1=[]           
       for i in list_Tmax_1:
           Tmax=float(i)
           list_Tmax_float_1.append(Tmax)

       list_Tmax_2=[]
       for cmax in list_cmax_2_pk:
           for column in df.columns:
               for num, row in df.iterrows():
                   if df.iloc[num][column] == cmax:
                      list_Tmax_2.append(f"{column}")
     
       list_Tmax_float_2=[]           
       for i in list_Tmax_2:
           Tmax=float(i)
           list_Tmax_float_2.append(Tmax)  

    if (len(list_cmax_1_pk) == len(df.index.tolist())):
       
       ###C0
       list_C0_total = []
       for i in range(0,count_row):
             list_columns_T=[]
             for column in df_without_numer.columns:
                 list_columns_T.append(float(column))
             list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()
             
             # Оценка C₀ через логарифмическую линейную регрессию для первых двух точек
             if list_concentration[0] > 0 and list_concentration[1] > 0:
                 log_conc = np.log(list_concentration[:2])
                 slope, intercept, r_value, p_value, std_err = stats.linregress(list_columns_T[:2], log_conc)

                 if slope < 0:
                     # Оценка C₀ через экстраполяцию
                     C0 = np.exp(intercept)
                     list_C0_total.append(C0)
                 else:
                     # Если наклон >= 0, используем первое наблюдаемое значение
                     C0 = list_concentration[0]
                     list_C0_total.append(C0)
             else:
                 C0 = list_concentration[0]
                 list_C0_total.append(C0)

       ###AUC0-t
       list_AUC_0_T=[]
       if method_auc == 'linear':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ###C0
              list_C0 = []
              # Оценка C₀ через логарифмическую линейную регрессию для первых двух точек
              if list_concentration[0] > 0 and list_concentration[1] > 0:
                  log_conc = np.log(list_concentration[:2])
                  slope, intercept, r_value, p_value, std_err = stats.linregress(list_columns_T[:2], log_conc)

                  if slope < 0:
                      # Оценка C₀ через экстраполяцию
                      C0 = np.exp(intercept)
                      list_C0.append(C0)
                  else:
                      # Если наклон >= 0, используем первое наблюдаемое значение
                      C0 = list_concentration[0]
                      list_C0.append(C0)
              else:
                  C0 = list_concentration[0]
                  list_C0.append(C0)

              ###удаление всех нулей сзади массива, т.к. AUC0-t это AUClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              list_conc_without_0=[]
              list_t_without_0=[]
              for i in list_range_for_remove_0:
                  if list_after_cmax[i] !=0:
                     list_conc_without_0.append(list_after_cmax[i])
                     list_t_without_0.append(list_after_cmax_t[i])

              list_concentration = list_before_cmax + list_conc_without_0
              list_columns_T = list_before_cmax_t + list_t_without_0
              ######################
              # добавили эксрополяцию для подсчета AUC
              AUC_0_T=np.trapz(list_C0 + list_concentration,[0] + list_columns_T)
              list_AUC_0_T.append(AUC_0_T)

       if method_auc == 'linear-up/log-down':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              # Оценка C₀ через логарифмическую линейную регрессию для первых двух точек
              if list_concentration[0] > 0 and list_concentration[1] > 0:
                  log_conc = np.log(list_concentration[:2])
                  slope, intercept, _, _, _ = stats.linregress(list_columns_T[:2], log_conc)
                  if slope < 0:
                      C0 = np.exp(intercept)
                  else:
                      C0 = list_concentration[0]
              else:
                  C0 = list_concentration[0]

              # Удаление нулей в конце массива
              while list_concentration and list_concentration[-1] == 0:
                  list_concentration.pop()
                  list_columns_T.pop()

              # Вставка C₀ в начало списков
              if list_columns_T[0] != 0:
                  list_columns_T.insert(0, 0)
                  list_concentration.insert(0, C0)

              # Вычисление AUC
              AUC_0_T = 0
              for i in range(len(list_concentration) - 1):
                  delta_t = list_columns_T[i+1] - list_columns_T[i]
                  c_current = list_concentration[i]
                  c_next = list_concentration[i+1]

                  if c_next > c_current:
                      # Линейный метод
                      AUC_increment = ((c_current + c_next) / 2) * delta_t
                  elif c_next < c_current and c_next > 0 and c_current > 0:
                      # Логарифмический метод
                      AUC_increment = (c_current - c_next) * delta_t / np.log(c_current / c_next)
                  else:
                      # Линейный метод для равных или нулевых концентраций
                      AUC_increment = ((c_current + c_next) / 2) * delta_t

                  AUC_0_T += AUC_increment

              list_AUC_0_T.append(AUC_0_T)

       ####Сmax/AUC0-t
       list_Сmax_division_AUC0_t_for_division=zip(list_cmax_True_pk,list_AUC_0_T)
       list_Сmax_division_AUC0_t=[]
       for i,j in list_Сmax_division_AUC0_t_for_division:
               list_Сmax_division_AUC0_t.append(i/j)


       ####KEL
       list_kel_total=[]
       for i in range(0,count_row):
           list_columns_T=[]
           for column in df_without_numer.columns:
               list_columns_T.append(float(column))
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()
           list_c=list_concentration

           list_time=df_without_numer.columns.tolist()

           list_t=[]
           for i in list_time:
               i=float(i)
               list_t.append(i)

           #срез_без_cmax
           max_value_c=max(list_c)
           index_cmax=list_c.index(max_value_c)
           
           #сохраняем cmax, списки названы по старому
           list_c_without_cmax=list_c[index_cmax:]
           list_t_without_cmax=list_t[index_cmax:]

           #удаление всех нулей из массивов
           count_for_0_1=len(list_c_without_cmax)
           list_range_for_0_1=range(0,count_for_0_1)

           list_time_0=[]
           list_conc_0=[]
           for i in list_range_for_0_1:
               if list_c_without_cmax[i] !=0:
                  list_conc_0.append(list_c_without_cmax[i])
                  list_time_0.append(list_t_without_cmax[i]) 
           ################################

           n_points=len(list_conc_0)
           list_n_points = range(0,n_points)

           #создание списков с поочередно уменьщающемся кол, точек
           list_for_kel_c=[]
           for j in list_n_points:
               if j<n_points:
                  list_c_new=list_conc_0[j:n_points]
                  list_for_kel_c.append(list_c_new)
           list_for_kel_c.pop(-1) #удаление списка с одной точкой
           #list_for_kel_c.pop(-1)  #удаление списка с двумя точками     

           list_for_kel_t=[]
           for j in list_n_points:
               if j<n_points:
                  list_t_new=list_time_0[j:n_points]
                  list_for_kel_t.append(list_t_new)
           list_for_kel_t.pop(-1) #удаление списка с одной точкой
           #list_for_kel_t.pop(-1) #удаление списка с двумя точками 

           list_ct_zip=zip(list_for_kel_c,list_for_kel_t)

           list_kel=[]
           list_r=[]
           for i,j in list_ct_zip:

               n_points_r=len(i)

               np_c=np.asarray(i)
               np_t_1=np.asarray(j).reshape((-1,1))

               np_c_log=np.log(np_c)

               model = LinearRegression().fit(np_t_1,np_c_log)

               np_t=np.asarray(j)
               a=np.corrcoef(np_t, np_c_log)
               cor=((a[0])[1])
               r_sq=cor**2

               adjusted_r_sq=1-((1-r_sq)*((n_points_r-1))/(n_points_r-2))

               ########################################
               kel=abs(model.coef_[0])
               list_kel.append(kel)
               list_r.append(adjusted_r_sq)

           #делаем срезы списоков до rmax
           max_r=max(list_r)

           index_max_r= list_r.index(max_r)

           list_r1=list_r
           list_kel1=list_kel

           number_elem_list_r1=len(list_r1)

           list_range_kel=range(0,number_elem_list_r1) 

           list_kel_total_1=[]
           for i in list_range_kel:

               if abs(list_r[index_max_r] - list_r1[i]) < 0.0001: #проверяем все точки слева и справа от rmax
                  list_kel_total.append(list_kel1[i]*math.log(math.exp(1))) #отдаю предпочтение rmax с большим количеством точек
                  break #самая ранняя удовлетовряющая условию

           for i in list_kel_total_1:
               list_kel_total.append(i) 


       ####T1/2
       list_half_live=[]
       for i in list_kel_total:
           half_live=math.log(2)/i
           list_half_live.append(half_live)


       ###AUC0-inf 

       list_auc0_inf=[] 

       list_of_list_c=[]
       
       for i in range(0,count_row):
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

           list_c = list_concentration
           list_c.reverse() ### переворачиваем, для дальнейшей итерации с конца списка и поиска Clast не равное нулю
           list_of_list_c.append(list_c)

       list_zip_c_AUCt_inf=zip(list_kel_total,list_of_list_c)

           #AUCt-inf 
       list_auc_t_inf=[]     
       for i,j in list_zip_c_AUCt_inf:
           for clast in j:
               if clast != 0:
                  clast_true=clast
                  break
           auc_t_inf=clast_true/i
           list_auc_t_inf.append(auc_t_inf)

       list_auc_t_inf_and_AUC_0_T_zip=zip(list_AUC_0_T,list_auc_t_inf)

       for i,j in list_auc_t_inf_and_AUC_0_T_zip:
           auc0_inf=i+j    
           list_auc0_inf.append(auc0_inf)


       ####Cl
       list_cl=[]

       for i in list_auc0_inf:
           cl = float(dose)/i
           list_cl.append(cl) 


       ####Vz
       list_Vz=[]

       list_zip_kel_cl=zip(list_kel_total,list_cl)

       for i,j in list_zip_kel_cl:
           Vz = j/i
           list_Vz.append(Vz)


       ###AUMC0-t и ###AUMC0-inf
       list_AUMCO_inf=[]

       list_AUMC0_t=[]
       

       list_C_last=[]
       list_T_last=[]

       if method_auc == 'linear':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ###C0
              list_C0 = []
              # Оценка C₀ через логарифмическую линейную регрессию для первых двух точек
              if list_concentration[0] > 0 and list_concentration[1] > 0:
                  log_conc = np.log(list_concentration[:2])
                  slope, intercept, r_value, p_value, std_err = stats.linregress(list_columns_T[:2], log_conc)

                  if slope < 0:
                      # Оценка C₀ через экстраполяцию
                      C0 = np.exp(intercept)
                      list_C0.append(C0)
                  else:
                      # Если наклон >= 0, используем первое наблюдаемое значение
                      C0 = list_concentration[0]
                      list_C0.append(C0)
              else:
                  C0 = list_concentration[0]
                  list_C0.append(C0)

              ###удаление всех нулей сзади массива, т.к. AUMC0-t это AUMClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              list_conc_without_0=[]
              list_t_without_0=[]
              for i in list_range_for_remove_0:
                  if list_after_cmax[i] !=0:
                     list_conc_without_0.append(list_after_cmax[i])
                     list_t_without_0.append(list_after_cmax_t[i])
              
              list_concentration = list_before_cmax + list_conc_without_0
              list_columns_T = list_before_cmax_t + list_t_without_0
              #прибавляем эктрополяцию к начальным данным
              list_concentration.insert(0, list_C0[0])
              list_columns_T.insert(0, 0)
              ######################

              list_C_last.append(list_concentration[-1]) 
              list_T_last.append(list_columns_T[-1]) 

              list_len=len(list_concentration)

              list_aumc_i=[]
              for i in range(0,list_len):
                  AUMC=(list_columns_T[i] - list_columns_T[i-1]) *  ((list_concentration[i] * list_columns_T[i] + list_concentration[i-1] * list_columns_T[i-1])/2)
                  list_aumc_i.append(AUMC)

              list_aumc_i.pop(0)

              a=0
              list_AUMC0_t_1=[]
              for i in list_aumc_i:
                  a+=i
                  list_AUMC0_t_1.append(a)
              list_AUMC0_t.append(list_AUMC0_t_1[-1])
       
       if method_auc == 'linear-up/log-down':
          
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              ### C₀
              if list_concentration[0] > 0 and list_concentration[1] > 0:
                  log_conc = np.log(list_concentration[:2])
                  slope, intercept, _, _, _ = stats.linregress(list_columns_T[:2], log_conc)
                  if slope < 0:
                      C0 = np.exp(intercept)
                  else:
                      C0 = list_concentration[0]
              else:
                  C0 = list_concentration[0]

              ### Удаление нулей сзади массива
              while list_concentration and list_concentration[-1] == 0:
                  list_concentration.pop()
                  list_columns_T.pop()

              # Вставка C₀
              list_concentration.insert(0, C0)
              list_columns_T.insert(0, 0)

              # Запоминание последней концентрации и времени
              list_C_last.append(list_concentration[-1])
              list_T_last.append(list_columns_T[-1])

              ### AUMC расчет
              AUMC_0_T = 0
              for i in range(len(list_concentration) - 1):
                  delta_t = list_columns_T[i+1] - list_columns_T[i]
                  c_current = list_concentration[i]
                  c_next = list_concentration[i+1]

                  if c_next > c_current:
                      # Линейный метод
                      AUMC_increment = delta_t * ((c_next * list_columns_T[i+1] + c_current * list_columns_T[i]) / 2)
                  elif c_next < c_current and c_next > 0 and c_current > 0:
                      # Логарифмический метод
                      coeff = delta_t / np.log(c_next / c_current)
                      AUMC_increment = coeff * ((c_next * list_columns_T[i+1] - c_current * list_columns_T[i]) - coeff * (c_next - c_current))
                  else:
                      # Обработка равных или нулевых концентраций
                      AUMC_increment = delta_t * ((c_next * list_columns_T[i+1] + c_current * list_columns_T[i]) / 2)

                  AUMC_0_T += AUMC_increment

              list_AUMC0_t.append(AUMC_0_T)

       ########AUMC0-inf конечный подсчет
       list_zip_for_AUMC_inf=zip(list_kel_total,list_C_last,list_T_last)

       list_AUMCt_inf=[]
       for k,c,t in list_zip_for_AUMC_inf:
           AUMCt_inf=c*t/k+c/(k*k)
           list_AUMCt_inf.append(AUMCt_inf)


       list_AUMC_zip=zip(list_AUMC0_t,list_AUMCt_inf)

       for i,j in list_AUMC_zip:
           AUMCO_inf=i+j
           list_AUMCO_inf.append(AUMCO_inf)

       ###MRT0-t
       list_MRT0_t=[]

       list_zip_AUMCO_t_auc0_t = zip(list_AUMC0_t,list_AUC_0_T)

       for i,j in list_zip_AUMCO_t_auc0_t:
           MRT0_t=i/j
           list_MRT0_t.append(MRT0_t)

       ###MRT0-inf
       list_MRT0_inf=[]

       list_zip_AUMCO_inf_auc0_inf = zip(list_AUMCO_inf,list_auc0_inf)

       for i,j in list_zip_AUMCO_inf_auc0_inf:
           MRT0_inf=i/j
           list_MRT0_inf.append(MRT0_inf)

       ####Vss
       list_Vss=[]

       list_zip_MRT0_inf_cl=zip(list_MRT0_inf,list_cl)

       for i,j in list_zip_MRT0_inf_cl:
           Vss = j*i
           list_Vss.append(Vss)
    
       ##################### Фрейм ФК параметров

       ### пользовательский индекс
       list_for_index=df["Номер"].tolist()
       df_PK=pd.DataFrame(list(zip(list_cmax_True_pk,list_Tmax_float_True_pk,list_C0_total,list_C_last,list_T_last,list_MRT0_t,list_MRT0_inf,list_half_live,list_AUC_0_T,list_auc0_inf,list_AUMC0_t,list_AUMCO_inf,list_Сmax_division_AUC0_t,list_kel_total,list_cl,list_Vz,list_Vss)),columns=['Cmax','Tmax','C0','Clast','Tlast','MRT0→t','MRT0→∞','T1/2','AUC0-t','AUC0→∞','AUMC0-t','AUMC0-∞','Сmax/AUC0-t','Kel','Cl','Vz','Vss'],index=list_for_index)
    
    checking_condition_cmax2 = False

    if st.session_state[f"agree_cmax2 - {selector_research}"] == True:
        
       checking_condition_cmax2 = len(list_cmax_1_pk) == len(df.index.tolist()) and len(list_cmax_2_pk) == len(df.index.tolist()) and st.session_state[f"agree_cmax2 - {selector_research}"] == True
       
       if checking_condition_cmax2:
          
          zip_list_cmax_1_pk_cmax_2_pk = list(zip(list_cmax_1_pk, list_cmax_2_pk))

          zip_Tmax_float_1_Tmax_float_2 = list(zip(list_Tmax_float_1,list_Tmax_float_2))

          #CmaxH
          list_CmaxH = []
          
          for cmax_1_pk, cmax_2_pk in zip_list_cmax_1_pk_cmax_2_pk:
              CmaxH = max(cmax_1_pk, cmax_2_pk)
              list_CmaxH.append(CmaxH)

          #TmaxH
          list_TmaxH = []

          for Tmax_float_1, Tmax_float_2 in zip_Tmax_float_1_Tmax_float_2:
              TmaxH = max(Tmax_float_1, Tmax_float_2)
              list_TmaxH.append(TmaxH)

          #CmaxL/CmaxH
          list_CmaxL_CmaxH = []

          for cmax_1_pk, cmax_2_pk in zip_list_cmax_1_pk_cmax_2_pk:
              CmaxL_CmaxH = min(cmax_1_pk, cmax_2_pk)/max(cmax_1_pk, cmax_2_pk)
              list_CmaxL_CmaxH.append(CmaxL_CmaxH)

          #CmaxH-L
          list_CmaxH_L = []
          for cmax_1_pk, cmax_2_pk in zip_list_cmax_1_pk_cmax_2_pk:
              CmaxH_L = max(cmax_1_pk, cmax_2_pk) - min(cmax_1_pk, cmax_2_pk)
              list_CmaxH_L.append(CmaxH_L)

          #NumBtwPeaks
          list_NumBtwPeaks = []
          for Tmax_float_1, Tmax_float_2 in zip_Tmax_float_1_Tmax_float_2:
              if max(Tmax_float_1, Tmax_float_2) in list_Tmax_float_1:
                  index_max_Tmax_float = list_Tmax_float_1.index(max(Tmax_float_1, Tmax_float_2))
              else:
                  index_max_Tmax_float = list_Tmax_float_2.index(max(Tmax_float_1, Tmax_float_2))
              if min(Tmax_float_1, Tmax_float_2) in list_Tmax_float_1:
                  index_min_Tmax_float = list_Tmax_float_1.index(min(Tmax_float_1, Tmax_float_2))
              else:
                  index_min_Tmax_float = list_Tmax_float_2.index(min(Tmax_float_1, Tmax_float_2))

              NumBtwPeaks = index_max_Tmax_float - index_min_Tmax_float
              list_NumBtwPeaks.append(NumBtwPeaks)
          
          #DuraBtwPeaks
          list_DuraBtwPeaks = []
          for Tmax_float_1, Tmax_float_2 in zip_Tmax_float_1_Tmax_float_2:
              DuraBtwPeaks = max(Tmax_float_1, Tmax_float_2) - min(Tmax_float_1, Tmax_float_2)
              list_DuraBtwPeaks.append(DuraBtwPeaks)

          ### пользовательский индекс
          list_for_index=df["Номер"].tolist()
          df_PK_additional_double_peaks = pd.DataFrame(list(zip(list_cmax_1_pk,list_Tmax_float_1,list_cmax_2_pk,list_Tmax_float_2,list_CmaxH,list_TmaxH,list_CmaxL_CmaxH,list_CmaxH_L,list_NumBtwPeaks,list_DuraBtwPeaks)),columns=['Cmax1','Tmax1','Cmax2','Tmax2','CmaxH','TmaxH','CmaxL/CmaxH','CmaxH-L','Количество точек между пиками',
          'Время между пиками'],index=list_for_index)

          ###округление дополнительных ФК параметров

          series_Cmax_1=df_PK_additional_double_peaks['Cmax1']
          list_Cmax_str_f_1=[v for v in series_Cmax_1.tolist()]
          series_Cmax_1=pd.Series(list_Cmax_str_f_1, index = df_PK_additional_double_peaks.index.tolist(), name='Cmax1 ' +"("+measure_unit_concentration+")")

          series_Tmax_1=df_PK_additional_double_peaks['Tmax1']
          list_Tmax_str_f_1=[v for v in series_Tmax_1.tolist()]
          series_Tmax_1=pd.Series(list_Tmax_str_f_1, index = df_PK_additional_double_peaks.index.tolist(), name='Tmax1 ' +"("+f"{measure_unit_time}"+")")

          series_Cmax_2=df_PK_additional_double_peaks['Cmax2']
          list_Cmax_str_f_2=[v for v in series_Cmax_2.tolist()]
          series_Cmax_2=pd.Series(list_Cmax_str_f_2, index = df_PK_additional_double_peaks.index.tolist(), name='Cmax2 ' +"("+measure_unit_concentration+")")

          series_Tmax_2=df_PK_additional_double_peaks['Tmax2']
          list_Tmax_str_f_2=[v for v in series_Tmax_2.tolist()]
          series_Tmax_2=pd.Series(list_Tmax_str_f_2, index = df_PK_additional_double_peaks.index.tolist(), name='Tmax2 ' +"("+f"{measure_unit_time}"+")")

          series_CmaxH=df_PK_additional_double_peaks['CmaxH']
          list_CmaxH_str_f=[v for v in series_CmaxH.tolist()]
          series_CmaxH =pd.Series(list_CmaxH_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='CmaxH ' +"("+measure_unit_concentration+")")

          series_TmaxH=df_PK_additional_double_peaks['TmaxH']
          list_TmaxH_str_f=[v for v in series_TmaxH.tolist()]
          series_TmaxH=pd.Series(list_TmaxH_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='TmaxH ' +"("+f"{measure_unit_time}"+")")

          series_CmaxL_CmaxH=df_PK_additional_double_peaks['CmaxL/CmaxH']
          list_CmaxL_CmaxH_str_f=[v for v in series_CmaxL_CmaxH.tolist()]
          series_CmaxL_CmaxH=pd.Series(list_CmaxL_CmaxH_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='CmaxL/CmaxH')

          series_CmaxH_L=df_PK_additional_double_peaks['CmaxH-L']
          list_CmaxH_L_str_f=[v for v in series_CmaxH_L.tolist()]
          series_CmaxH_L=pd.Series(list_CmaxH_L_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='CmaxH-L ' +"("+measure_unit_concentration+")")

          series_NumBtwPeaks=df_PK_additional_double_peaks['Количество точек между пиками']
          list_NumBtwPeaks_str_f=[v for v in series_NumBtwPeaks.tolist()]
          series_NumBtwPeaks=pd.Series(list_NumBtwPeaks_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='Количество точек между пиками ')

          series_DuraBtwPeaks=df_PK_additional_double_peaks['Время между пиками']
          list_DuraBtwPeaks_str_f=[v for v in series_DuraBtwPeaks.tolist()]
          series_DuraBtwPeaks=pd.Series(list_DuraBtwPeaks_str_f, index = df_PK_additional_double_peaks.index.tolist(), name='Время между пиками ' +"("+f"{measure_unit_time}"+")")
          
          df_total_PK_additional_double_peaks = pd.concat([series_Cmax_1, series_Tmax_1, series_Cmax_2, series_Tmax_2, series_CmaxH, series_TmaxH, 
          series_CmaxL_CmaxH, series_CmaxH_L,series_NumBtwPeaks,series_DuraBtwPeaks], axis= 1)
        
          df_total_PK_additional_double_peaks.index.name = 'Номер'

    if checking_condition_cmax2 or (len(list_cmax_1_pk) == len(df.index.tolist()) and (st.session_state[f"agree_cmax2 - {selector_research}"] == False)):
    
       ###описательная статистика

       dict_df_averaged_3_PK = create_table_descriptive_statistics_before_95CI_pk(df_PK)
       df_averaged_3_PK = dict_df_averaged_3_PK.get("df_averaged_3_PK")

       df_concat_PK_pk= pd.concat([df_PK,df_averaged_3_PK],sort=False,axis=0)

       ###округление описательной статистики и ФК параметров

       series_Cmax=df_concat_PK_pk['Cmax']
       list_Cmax_str_f=[v for v in series_Cmax.tolist()]
       series_Cmax=pd.Series(list_Cmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax ' +"("+measure_unit_concentration+")")

       series_Tmax=df_concat_PK_pk['Tmax']
       list_Tmax_str_f=[v for v in series_Tmax.tolist()]
       series_Tmax=pd.Series(list_Tmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Tmax ' +"("+f"{measure_unit_time}"+")")

       series_C0=df_concat_PK_pk['C0']
       list_C0_str_f=[v for v in series_C0.tolist()]
       series_C0=pd.Series(list_C0_str_f, index = df_concat_PK_pk.index.tolist(), name='C0 ' +"("+measure_unit_concentration+")")

       series_Clast=df_concat_PK_pk['Clast']
       list_Clast_str_f=[v for v in series_Clast.tolist()]
       series_Clast=pd.Series(list_Clast_str_f, index = df_concat_PK_pk.index.tolist(), name='Clast ' +"("+measure_unit_concentration+")")

       series_Tlast=df_concat_PK_pk['Tlast']
       list_Tlast_str_f=[v for v in series_Tlast.tolist()]
       series_Tlast=pd.Series(list_Tlast_str_f, index = df_concat_PK_pk.index.tolist(), name='Tlast ' +"("+f"{measure_unit_time}"+")")
       
       series_MRT0_t= df_concat_PK_pk['MRT0→t']
       list_MRT0_t_str_f=[v for v in series_MRT0_t.tolist()]
       series_MRT0_t=pd.Series(list_MRT0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='MRT0→t '+"("+f"{measure_unit_time}"+")")

       series_MRT0_inf= df_concat_PK_pk['MRT0→∞']
       list_MRT0_inf_str_f=[v for v in series_MRT0_inf.tolist()]
       series_MRT0_inf=pd.Series(list_MRT0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='MRT0→∞ '+"("+f"{measure_unit_time}"+")")

       series_half_live= df_concat_PK_pk['T1/2']
       list_half_live_str_f=[v for v in series_half_live.tolist()]
       series_half_live=pd.Series(list_half_live_str_f, index = df_concat_PK_pk.index.tolist(), name='T1/2 '+"("+f"{measure_unit_time}"+")")

       series_AUC0_t= df_concat_PK_pk['AUC0-t']
       list_AUC0_t_str_f=[v for v in series_AUC0_t.tolist()]
       series_AUC0_t=pd.Series(list_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")

       series_AUC0_inf= df_concat_PK_pk['AUC0→∞']
       list_AUC0_inf_str_f=[v for v in series_AUC0_inf.tolist()]
       series_AUC0_inf=pd.Series(list_AUC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")
       
       series_AUMC0_t= df_concat_PK_pk['AUMC0-t']
       list_AUMC0_t_str_f=[v for v in series_AUMC0_t.tolist()]
       series_AUMC0_t=pd.Series(list_AUMC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_AUMC0_inf= df_concat_PK_pk['AUMC0-∞']
       list_AUMC0_inf_str_f=[v for v in series_AUMC0_inf.tolist()]
       series_AUMC0_inf=pd.Series(list_AUMC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_Сmax_dev_AUC0_t= df_concat_PK_pk['Сmax/AUC0-t']
       list_Сmax_dev_AUC0_t_str_f=[v for v in series_Сmax_dev_AUC0_t.tolist()]
       series_Сmax_dev_AUC0_t=pd.Series(list_Сmax_dev_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='Сmax/AUC0-t '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_Kel= df_concat_PK_pk['Kel']
       list_Kel_str_f=[v for v in series_Kel.tolist()]
       series_Kel=pd.Series(list_Kel_str_f, index = df_concat_PK_pk.index.tolist(), name='Kel '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_CL= df_concat_PK_pk['Cl']
       list_CL_str_f=[v for v in series_CL.tolist()]
       series_CL=pd.Series(list_CL_str_f, index = df_concat_PK_pk.index.tolist(), name='Cl ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})/{measure_unit_time}"+")")

       series_Vz= df_concat_PK_pk['Vz']
       list_Vz_str_f=[v for v in series_Vz.tolist()]
       series_Vz=pd.Series(list_Vz_str_f, index = df_concat_PK_pk.index.tolist(), name='Vz ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")

       series_Vss= df_concat_PK_pk['Vss']
       list_Vss_str_f=[v for v in series_Vss.tolist()]
       series_Vss=pd.Series(list_Vss_str_f, index = df_concat_PK_pk.index.tolist(), name='Vss ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")
       
       df_total_PK_pk = pd.concat([series_Cmax, series_Tmax,series_C0,series_Clast, series_Tlast, series_MRT0_t, series_MRT0_inf,series_half_live,series_AUC0_t,series_AUC0_inf,series_AUMC0_t,series_AUMC0_inf,series_Сmax_dev_AUC0_t,series_Kel,series_CL,series_Vz,series_Vss], axis= 1) 
       
       df_total_PK_pk.index.name = 'Номер'

       #округление количества субъектов до целого
       round_subjects_count(df_total_PK_pk)
       
       #получение списка значений доверительного интервала
       list_confidence_interval_PK = dict_df_averaged_3_PK.get("list_confidence_interval_PK")

       ###добавление в таблицу доверительного интервала
       df_total_PK_pk = add_ci_in_table(df_total_PK_pk,list_confidence_interval_PK)

       ##изменение названий параметров описательной статистики

       df_total_PK_pk = rename_parametrs_descriptive_statistics(df_total_PK_pk)

       if st.session_state[f"agree_cmax2 - {selector_research}"] == False:
           dict_PK_parametrs = {
               "df_total_PK": df_total_PK_pk,
               "df_PK":df_PK,
               "df_concat_PK":df_concat_PK_pk,
               "list_cmax_1": list_cmax_1_pk
           }
       else:
          dict_PK_parametrs = {
              "df_total_PK": df_total_PK_pk,
              "df_PK":df_PK,
              "df_concat_PK": df_concat_PK_pk,
              "list_cmax_1": list_cmax_1_pk,
              "list_cmax_2": list_cmax_2_pk,
              "df_total_PK_additional_double_peaks": df_total_PK_additional_double_peaks
          }

       return dict_PK_parametrs
