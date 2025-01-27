import streamlit as st
import os
import pandas as pd
from io import BytesIO
from docx import Document

import tempfile
import math

from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.shared import RGBColor


def save_session_lists_tables_graphics(option,list_heading_word,list_table_word,list_graphics_word,list_heading_graphics_word):
    ###сохранение состояния 
    st.session_state[f"list_heading_word_{option}"] = list_heading_word
    st.session_state[f"list_table_word_{option}"] = list_table_word
    st.session_state[f"list_graphics_word_{option}"] = list_graphics_word
    st.session_state[f"list_heading_graphics_word_{option}"] = list_heading_graphics_word

# Функция для сохранения DataFrame в формате Excel
def to_excel_results(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True)
    output.seek(0)  # Возвращаем курсор в начало файла
    return output


# Обертка для скачивания файла в формате Excel с поддержкой ключа
def download_excel_button(df, label, key, file_name):
    excel_data = to_excel_results(df)
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


#превращает df в excel файл-пример
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
    font.size = Pt(10)

    for heading, df in zip_heading_table:
        # Добавление заголовка для каждой таблицы
        paragraph = doc.add_paragraph(heading, style='Heading 1')
        run = paragraph.runs[0]
        run.font.color.rgb = RGBColor(0, 0, 0)

        # Преобразование колонок в DataFrame и добавление индексов
        name_columns = pd.DataFrame(df.columns.tolist()).T
        name_columns.columns = df.columns.tolist()
        df_columns = pd.concat([name_columns, df]).reset_index(drop=True)

        total_name_index = df.index.name or "Index"
        list_index_names = df.index.tolist()
        list_index_names.insert(0, total_name_index)
        series_index_names = pd.Series(list_index_names, name=total_name_index)
        df_series_index_names = series_index_names.to_frame()
        df_columns_indexes = pd.concat([df_series_index_names, df_columns], axis=1)

        # Создание таблицы
        t = doc.add_table(rows=df_columns_indexes.shape[0], cols=df_columns_indexes.shape[1])
        t.style = 'Table Grid'

        # Автоматическая настройка ширины колонок
        max_col_widths = [max([len(str(df_columns_indexes.iat[i, j])) for i in range(df_columns_indexes.shape[0])]) for j in range(df_columns_indexes.shape[1])]
        total_width = 26.0  # Доступная ширина в см
        col_widths = [min(w * 0.2, total_width / len(max_col_widths)) for w in max_col_widths]

        for j, width in enumerate(col_widths):
            for row in t.rows:
                row.cells[j].width = Cm(width)

        # Заполнение таблицы данными
        for i, row_data in df_columns_indexes.iterrows():
            for j, value in enumerate(row_data):
                cell = t.cell(i, j)
                cell.text = str(value)
                # Настройка стиля текста
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(8)
                        run.font.name = 'Times New Roman'

        # Центрирование текста
        for row in t.rows:
            for cell in row.cells:
                cell.vertical_alignment = 1  # Центрирование по вертикали

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

#визуализация и выгрузка в excel
def visualize_table(list_heading_word,list_table_word):
    zip_heading_table = zip(list_heading_word,list_table_word) ###еще раз объявляем, иначе не видит zip-объект
    #####визуализация
    for heading, df in zip_heading_table:
        st.subheader(heading)
        st.write(df)

        # Используем кастомные виджеты с уникальными ключами для выгрузки Excel
        download_excel_button(df, f"Cкачать файл {heading}", heading,f"{heading}.xlsx")

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