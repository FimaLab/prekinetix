import numpy as np
import scipy.stats as stat
from sklearn.linear_model import LinearRegression
from scipy import stats
import math
import pandas as pd
import streamlit as st
from utils.des_stat import *

import numpy as np

#Для Tlag
def find_first_positive_index(lst):
    for i, num in enumerate(lst):
        if num > 0:
            return i

def calculate_aucall(list_list_concentration, list_list_columns_T, list_AUClast):
    

    list_AUCall = []
    
    for list_concentration,list_columns_T, AUC_last in list(zip(list_list_concentration,list_list_columns_T,list_AUClast)):
        

        # Проверяем, является ли последний замер концентрации положительным
        if list_concentration[-1] > 0:
            AUCall = AUC_last
            list_AUCall.append(AUCall)
        else:
            time = np.array(list_columns_T)
            conc = np.array(list_concentration)
            # Последняя положительная концентрация
            last_pos_index = np.max(np.where(conc > 0))

            # AUCall включает дополнительную область от последнего положительного значения до нуля
            extended_time = time[last_pos_index:]
            extended_conc = conc[last_pos_index:]

            AUC_extra = np.trapz(extended_conc, extended_time)

            AUCall = AUC_last + AUC_extra

            list_AUCall.append(AUCall)

    return list_AUCall


def remove_second_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Удаляет вторую колонку из DataFrame.

    :param df: DataFrame, из которого нужно удалить вторую колонку.
    :return: Новый DataFrame без второй колонки.
    """
    if df.shape[1] > 1:  # Проверяем, что в DataFrame есть хотя бы две колонки
        return df.drop(columns=df.columns[1])
    else:
        print("В DataFrame недостаточно колонок для удаления второй.")
        return df

## функция подсчета опистательной статистики и создания соотвествующей таблицы с округлениями
def create_table_descriptive_statistics(df):
    col_mapping = df.columns.tolist()
    if 'Номер' in col_mapping:
       col_mapping.remove('Номер')

    stats_df = pd.DataFrame({col: calculate_statistics(df[col].tolist()) for col in col_mapping}).T

    return stats_df.T

#округление количества субъектов до целого
def round_subjects_count(df_total_PK):
   list_count_subjects_round =[float(v) for v in df_total_PK.loc["count"].tolist()]
   list_count_subjects_round =[int(v) for v in list_count_subjects_round]
   df_total_PK.loc["count"] = list_count_subjects_round



def pk_parametrs_total_extravascular(df,selector_research,method_auc,dose,measure_unit_concentration,measure_unit_time,measure_unit_dose):
    
    ############ Параметры ФК

    df_without_numer=df.drop(['Номер'],axis=1)
    count_row=df_without_numer.shape[0]

    list_count_row=range(count_row)
    
    ###N_Samples
    list_N_Samples=[]
    for i in range(0,count_row):
        Sample=int(len(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_N_Samples.append(Sample)

    ###Dose
    list_Dose=[]
    for i in range(0,count_row):
        Dose=float(dose)
        list_Dose.append(Dose)

    ###Cmax_True
    list_cmax_True_pk=[]
    for i in range(0,count_row):
        cmax=float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_cmax_True_pk.append(cmax)

    ###Cmax_D
    list_cmax_D_pk=[]
    for i in range(0,count_row):
        cmax_d =float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))/float(dose)
        list_cmax_D_pk.append(cmax_d)
    
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

              ### Обрезка только конечных нулей, а не всех после Cmax для корректной обработки также и нулей в середине
              while list_after_cmax and list_after_cmax[-1] == 0:
                  list_after_cmax.pop()
                  list_after_cmax_t.pop()

              list_concentration = list_before_cmax + list_after_cmax
              list_columns_T = list_before_cmax_t + list_after_cmax_t
              ######################

              AUC_0_T=np.trapz(list_concentration,x=list_columns_T)
              list_AUC_0_T.append(AUC_0_T)

       if method_auc == 'linear-up/log-down':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              
              # Удаление нулей в конце массива
              while list_concentration and list_concentration[-1] == 0:
                  list_concentration.pop()
                  list_columns_T.pop()

              ######################
              
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
       
       ###AUC0-t/D
       list_AUC_0_T_D=[]
       for i in list_AUC_0_T:
           AUC_0_T_D = i/float(dose)
           list_AUC_0_T_D.append(AUC_0_T_D)

       ####AUCall
       list_list_columns_T = []
       list_list_concentration = []

       for i in range(0,count_row):
           list_columns_T=[]
           for column in df_without_numer.columns:
               list_columns_T.append(float(column))

           list_list_columns_T.append(list_columns_T)

           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

           list_list_concentration.append(list_concentration)

       list_AUCall = calculate_aucall(list_list_concentration, list_list_columns_T, list_AUC_0_T)
       
       ###Tlag
       list_Tlag=[]
       for i in range(0,count_row):
           
           list_columns_T=[]
           for column in df_without_numer.columns:
               list_columns_T.append(float(column))
           Tlag = list_columns_T[find_first_positive_index(df_without_numer.iloc[[i]].iloc[0].tolist())-1]
           
           list_Tlag.append(Tlag)

       ####Сmax/AUC0-t
       list_Сmax_division_AUC0_t_for_division=list(zip(list_cmax_True_pk,list_AUC_0_T))
       list_Сmax_division_AUC0_t=[]
       for i,j in list_Сmax_division_AUC0_t_for_division:
               list_Сmax_division_AUC0_t.append(i/j)


       ####KEL,Rsq_adjusted,Rsq,Corr_XY,No_points_lambda_z,Lambda_z_intercept,Lambda_z_lower,Lambda_z_upper
       list_kel_total=[]
       list_Rsq_adjusted=[]
       list_Rsq = []
       list_Corr_XY = []
       list_No_points_lambda_z = []
       list_Lambda_z_intercept = []
       list_Lambda_z_lower = []
       list_Lambda_z_upper = []
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

           list_ct_zip=list(zip(list_for_kel_c,list_for_kel_t))

           list_kel=[]
           list_r=[]
           list_r_orig=[]
           list_Corr = []
           list_n_points_used = []
           list_intercept = []
           list_Lambda_lower = []
           list_Lambda_upper = []
           for i,j in list_ct_zip:

               n_points_r=len(i)
               
               list_n_points_used.append(n_points_r)
               list_Lambda_lower.append(min(j))
               list_Lambda_upper.append(max(j))

               np_c=np.asarray(i)
               np_t_1=np.asarray(j).reshape((-1,1))

               np_c_log=np.log(np_c)

               model = LinearRegression().fit(np_t_1,np_c_log)

               np_t=np.asarray(j)
               a=np.corrcoef(np_t, np_c_log)
               cor=((a[0])[1])
               r_sq=cor**2

               list_Corr.append(cor)
               list_r_orig.append(r_sq)
               list_intercept.append(model.intercept_)

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
                  list_Rsq_adjusted.append(list_r1[i])
                  list_Rsq.append(list_r_orig[i])
                  list_Corr_XY.append(list_Corr[i])
                  list_No_points_lambda_z.append(list_n_points_used[i])
                  list_Lambda_z_intercept.append(list_intercept[i])
                  list_Lambda_z_lower.append(list_Lambda_lower[i])
                  list_Lambda_z_upper.append(list_Lambda_upper[i])
                  break #самая ранняя удовлетовряющая условию

           for i in list_kel_total_1:
               list_kel_total.append(i)  


       ####T1/2
       list_half_live=[]
       for i in list_kel_total:
           half_live=math.log(2)/i
           list_half_live.append(half_live)
       
       ####Span
       list_Span=[]
       for upper,lower,half_live in list(zip(list_Lambda_z_upper,list_Lambda_z_lower,list_half_live)):
           Span= (upper - lower)/half_live
           list_Span.append(Span)

       ###AUC0-inf 

       list_auc0_inf=[] 

       list_of_list_c=[]
       for i in range(0,count_row):
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()
           list_concentration.remove(0)
           list_c = list_concentration
           list_c.reverse() ### переворачиваем, для дальнейшей итерации с конца списка и поиска Clast не равное нулю
           list_of_list_c.append(list_c)

       list_zip_c_AUCt_inf=list(zip(list_kel_total,list_of_list_c))

       #AUCt-inf 
       list_auc_t_inf=[]     
       for i,j in list_zip_c_AUCt_inf:
           for clast in j:
               if clast != 0:
                  clast_true=clast
                  break
           auc_t_inf=clast_true/i
           list_auc_t_inf.append(auc_t_inf)

       list_auc_t_inf_and_AUC_0_T_zip=list(zip(list_AUC_0_T,list_auc_t_inf))

       for i,j in list_auc_t_inf_and_AUC_0_T_zip:
           auc0_inf=i+j    
           list_auc0_inf.append(auc0_inf)
       
       ###AUC0-inf/D
       list_auc0_inf_D=[]
       for i in list_auc0_inf:
           auc0_inf_D = i/float(dose)
           list_auc0_inf_D.append(auc0_inf_D)


       ###AUC_%Extrap
       list_AUC_extrap=[]
       for i,j in list(zip(list_auc0_inf,list_AUC_0_T)):
           AUC_extrap = ((i-j)/i)*100
           list_AUC_extrap.append(AUC_extrap)
 
       ####Cl_F
       list_Cl_F=[]

       for i in list_auc0_inf:
           Cl_F = float(dose)/i
           list_Cl_F.append(Cl_F) 


       ####Vz_F
       list_Vz_F=[]

       list_zip_kel_Cl_F=list(zip(list_kel_total,list_Cl_F))

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

              ### Обрезка только конечных нулей, а не всех после Cmax для корректной обработки также и нулей в середине
              while list_after_cmax and list_after_cmax[-1] == 0:
                  list_after_cmax.pop()
                  list_after_cmax_t.pop()

              list_concentration = list_before_cmax + list_after_cmax
              list_columns_T = list_before_cmax_t + list_after_cmax_t
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

             
              ### Удаление нулей сзади массива
              while list_concentration and list_concentration[-1] == 0:
                  list_concentration.pop()
                  list_columns_T.pop()

              ######################
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
       list_zip_for_AUMC_inf=list(zip(list_kel_total,list_C_last,list_T_last))

       list_AUMCt_inf=[]
       for k,c,t in list_zip_for_AUMC_inf:
           AUMCt_inf=c*t/k+c/(k*k)
           list_AUMCt_inf.append(AUMCt_inf)


       list_AUMC_zip=list(zip(list_AUMC0_t,list_AUMCt_inf))

       for i,j in list_AUMC_zip:
           AUMCO_inf=i+j
           list_AUMCO_inf.append(AUMCO_inf)
       
       ###AUMC_%Extrap
       list_AUMC_extrap=[]
       for i,j in list(zip(list_AUMCO_inf,list_AUMC0_t)):
           AUMC_extrap = ((i-j)/i)*100
           list_AUMC_extrap.append(AUMC_extrap)

       ###MRT0-t
       list_MRT0_t=[]

       list_zip_AUMCO_t_auc0_t = list(zip(list_AUMC0_t,list_AUC_0_T))

       for i,j in list_zip_AUMCO_t_auc0_t:
           MRT0_t=i/j
           list_MRT0_t.append(MRT0_t)

       ###MRT0-inf
       list_MRT0_inf=[]

       list_zip_AUMCO_inf_auc0_inf = list(zip(list_AUMCO_inf,list_auc0_inf))

       for i,j in list_zip_AUMCO_inf_auc0_inf:
           MRT0_inf=i/j
           list_MRT0_inf.append(MRT0_inf)
       

    
       ##################### Фрейм ФК параметров

       ### пользовательский индекс
       list_for_index=df["Номер"].tolist()
       df_PK=pd.DataFrame(list(zip(list_N_Samples,list_Dose,list_cmax_True_pk,list_cmax_D_pk,list_Tmax_float_True_pk,list_C_last,list_T_last,list_MRT0_t,list_MRT0_inf,list_half_live,list_AUC_0_T,list_AUC_0_T_D,list_AUCall,list_auc0_inf,list_auc0_inf_D,list_AUC_extrap,list_AUMC0_t,list_AUMCO_inf,list_AUMC_extrap,list_Сmax_division_AUC0_t,list_kel_total,list_Rsq_adjusted,list_Rsq,list_Corr_XY,list_No_points_lambda_z,list_Lambda_z_intercept,list_Lambda_z_lower,list_Lambda_z_upper,list_Span,list_Tlag,list_Cl_F,list_Vz_F)),columns=['N_Samples','Dose','Cmax','Cmax/D','Tmax','Clast','Tlast','MRT0→t','MRT0→∞','T1/2','AUC0-t','AUC0-t/D','AUCall','AUC0→∞','AUC0→∞/D',f'AUC_%Extrap','AUMC0-t','AUMC0-∞',f'AUMC_%Extrap','Сmax/AUC0-t','Kel','Rsq_adjusted','Rsq','Corr_XY','No_points_lambda_z','Lambda_z_intercept','Lambda_z_lower','Lambda_z_upper','Span','Tlag','Cl/F','Vz/F'],index=list_for_index)

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

       df_averaged_3_PK = create_table_descriptive_statistics(df_PK)
       df_concat_PK_pk= pd.concat([df_PK,df_averaged_3_PK],sort=False,axis=0)

       ###округление описательной статистики и ФК параметров
       
       series_N_Samples=df_concat_PK_pk['N_Samples']
       list_N_Samples_str_f=[v for v in series_N_Samples.tolist()]
       series_N_Samples=pd.Series(list_N_Samples_str_f, index = df_concat_PK_pk.index.tolist(), name='N_Samples')

       series_Dose=df_concat_PK_pk['Dose']
       list_Dose_str_f=[v for v in series_Dose.tolist()]
       series_Dose=pd.Series(list_Dose_str_f, index = df_concat_PK_pk.index.tolist(), name='Dose')

       series_Cmax=df_concat_PK_pk['Cmax']
       list_Cmax_str_f=[v for v in series_Cmax.tolist()]
       series_Cmax=pd.Series(list_Cmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax ' +"("+measure_unit_concentration+")")

       series_Cmax_D=df_concat_PK_pk['Cmax/D']
       list_Cmax_D_str_f=[v for v in series_Cmax_D.tolist()]
       series_Cmax_D=pd.Series(list_Cmax_D_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax/D ' +"("+measure_unit_concentration+'/'+'('+measure_unit_dose+')'+")")

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
       
       series_AUC0_t_D= df_concat_PK_pk['AUC0-t/D']
       list_AUC0_t_D_str_f=[v for v in series_AUC0_t_D.tolist()]
       series_AUC0_t_D=pd.Series(list_AUC0_t_D_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0-t/D '+"("+measure_unit_concentration+f"×{measure_unit_time}"+'/('+measure_unit_dose+')' +")")
       
       series_AUCall= df_concat_PK_pk['AUCall']
       list_AUCall_str_f=[v for v in series_AUCall.tolist()]
       series_AUCall=pd.Series(list_AUCall_str_f, index = df_concat_PK_pk.index.tolist(), name='AUCall '+"("+measure_unit_concentration+f"×{measure_unit_time}"+")")

       series_AUC0_inf= df_concat_PK_pk['AUC0→∞']
       list_AUC0_inf_str_f=[v for v in series_AUC0_inf.tolist()]
       series_AUC0_inf=pd.Series(list_AUC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")
       
       series_AUC0_inf_D= df_concat_PK_pk['AUC0→∞/D']
       list_AUC0_inf_D_str_f=[v for v in series_AUC0_inf_D.tolist()]
       series_AUC0_inf_D=pd.Series(list_AUC0_inf_D_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞/D '+"("+measure_unit_concentration+f"×{measure_unit_time}"+'/('+measure_unit_dose+')' +")")
       
       series_AUC_extrap= df_concat_PK_pk[f'AUC_%Extrap']
       list_AUC_extrap_str_f=[v for v in series_AUC_extrap.tolist()]
       series_AUC_extrap=pd.Series(list_AUC_extrap_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUC_%Extrap '+"("+"%"+")")

       series_AUMC0_t= df_concat_PK_pk['AUMC0-t']
       list_AUMC0_t_str_f=[v for v in series_AUMC0_t.tolist()]
       series_AUMC0_t=pd.Series(list_AUMC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_AUMC0_inf= df_concat_PK_pk['AUMC0-∞']
       list_AUMC0_inf_str_f=[v for v in series_AUMC0_inf.tolist()]
       series_AUMC0_inf=pd.Series(list_AUMC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")
       
       series_AUMC_extrap= df_concat_PK_pk[f'AUMC_%Extrap']
       list_AUMC_extrap_str_f=[v for v in series_AUMC_extrap.tolist()]
       series_AUMC_extrap=pd.Series(list_AUMC_extrap_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUMC_%Extrap '+"("+"%"+")")

       series_Сmax_dev_AUC0_t= df_concat_PK_pk['Сmax/AUC0-t']
       list_Сmax_dev_AUC0_t_str_f=[v for v in series_Сmax_dev_AUC0_t.tolist()]
       series_Сmax_dev_AUC0_t=pd.Series(list_Сmax_dev_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='Сmax/AUC0-t '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_Kel= df_concat_PK_pk['Kel']
       list_Kel_str_f=[v for v in series_Kel.tolist()]
       series_Kel=pd.Series(list_Kel_str_f, index = df_concat_PK_pk.index.tolist(), name='Kel '+"("+f"{measure_unit_time}\u207B\u00B9"+")")
       
       series_Rsq_adjusted= df_concat_PK_pk['Rsq_adjusted']
       list_Rsq_adjusted_str_f=[v for v in series_Rsq_adjusted.tolist()]
       series_Rsq_adjusted=pd.Series(list_Rsq_adjusted_str_f, index = df_concat_PK_pk.index.tolist(), name='Rsq_adjusted')

       series_Rsq= df_concat_PK_pk['Rsq']
       list_Rsq_str_f=[v for v in series_Rsq.tolist()]
       series_Rsq=pd.Series(list_Rsq_str_f, index = df_concat_PK_pk.index.tolist(), name='Rsq')

       series_Corr_XY= df_concat_PK_pk['Corr_XY']
       list_Corr_XY_str_f=[v for v in series_Corr_XY.tolist()]
       series_Corr_XY=pd.Series(list_Corr_XY_str_f, index = df_concat_PK_pk.index.tolist(), name='Corr_XY')

       series_No_points_lambda_z= df_concat_PK_pk['No_points_lambda_z']
       list_No_points_lambda_z_str_f=[v for v in series_No_points_lambda_z.tolist()]
       series_No_points_lambda_z=pd.Series(list_No_points_lambda_z_str_f, index = df_concat_PK_pk.index.tolist(), name='No_points_lambda_z')
       
       series_Lambda_z_intercept= df_concat_PK_pk['Lambda_z_intercept']
       list_Lambda_z_intercept_str_f=[v for v in series_Lambda_z_intercept.tolist()]
       series_Lambda_z_intercept=pd.Series(list_Lambda_z_intercept_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_intercept')

       series_Lambda_z_lower= df_concat_PK_pk['Lambda_z_lower']
       list_Lambda_z_lower_str_f=[v for v in series_Lambda_z_lower.tolist()]
       series_Lambda_z_lower=pd.Series(list_Lambda_z_lower_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_lower')

       series_Lambda_z_upper = df_concat_PK_pk['Lambda_z_upper']
       list_Lambda_z_upper_str_f=[v for v in series_Lambda_z_upper.tolist()]
       series_Lambda_z_upper=pd.Series(list_Lambda_z_upper_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_upper')

       series_Span = df_concat_PK_pk['Span']
       list_Span_str_f=[v for v in series_Span.tolist()]
       series_Span=pd.Series(list_Span_str_f, index = df_concat_PK_pk.index.tolist(), name='Span')

       series_Tlag = df_concat_PK_pk['Tlag']
       list_Tlag_str_f=[v for v in series_Tlag.tolist()]
       series_Tlag=pd.Series(list_Tlag_str_f, index = df_concat_PK_pk.index.tolist(), name='Tlag')

       series_Cl_F= df_concat_PK_pk['Cl/F']
       list_Cl_F_str_f=[v for v in series_Cl_F.tolist()]
       series_Cl_F=pd.Series(list_Cl_F_str_f, index = df_concat_PK_pk.index.tolist(), name='Cl/F ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})/{measure_unit_time}"+")")

       series_Vz_F= df_concat_PK_pk['Vz/F']
       list_Vz_F_str_f=[v for v in series_Vz_F.tolist()]
       series_Vz_F=pd.Series(list_Vz_F_str_f, index = df_concat_PK_pk.index.tolist(), name='Vz/F ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")
       
       df_total_PK_pk = pd.concat([series_N_Samples,series_Dose,series_Rsq,series_Rsq_adjusted,series_Corr_XY,series_No_points_lambda_z,series_Kel,series_Lambda_z_intercept,series_Lambda_z_lower,series_Lambda_z_upper,series_half_live,series_Span,series_Tlag,series_Tmax,series_Cmax,series_Cmax_D,series_Tlast, series_Clast,series_AUC0_t,series_AUC0_t_D,series_AUCall,series_AUC0_inf,series_AUC0_inf_D,series_AUC_extrap,series_Vz_F,series_Cl_F,series_AUMC0_t,series_AUMC0_inf,series_AUMC_extrap, series_MRT0_t, series_MRT0_inf,series_Сmax_dev_AUC0_t], axis= 1) 
       
       df_total_PK_pk.index.name = 'Номер'

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
    
    ###N_Samples
    list_N_Samples=[]
    for i in range(0,count_row):
        Sample=int(len(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_N_Samples.append(Sample)

    ###Dose
    list_Dose=[]
    for i in range(0,count_row):
        Dose=float(dose)
        list_Dose.append(Dose)

    ###Cmax_True
    list_cmax_True_pk=[]
    for i in range(0,count_row):
        cmax=float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_cmax_True_pk.append(cmax)

    ###Cmax_D
    list_cmax_D_pk=[]
    for i in range(0,count_row):
        cmax_d =float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))/float(dose)
        list_cmax_D_pk.append(cmax_d)
    
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

       ###AUC0-t,AUC_Back_Ext
       list_AUC_0_T=[]
       list_AUC_Back_Ext=[]
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

              ### Обрезка только конечных нулей, а не всех после Cmax для корректной обработки также и нулей в середине
              while list_after_cmax and list_after_cmax[-1] == 0:
                  list_after_cmax.pop()
                  list_after_cmax_t.pop()

              list_concentration = list_before_cmax + list_after_cmax
              list_columns_T = list_before_cmax_t + list_after_cmax_t



              ######################
              # добавили эксрополяцию для подсчета AUC
              AUC_0_T=np.trapz(list_C0 + list_concentration,[0] + list_columns_T)
              list_AUC_0_T.append(AUC_0_T)
              if list_C0[0] == 0:
                 list_AUC_Back_Ext.append(0)
              else:
                 list_AUC_Back_Ext.append(AUC_0_T-np.trapz(list_concentration,list_columns_T))

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
              

              # Вычисление AUC без экстраполяции

              AUC_0_T_without_ext = 0
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

                  AUC_0_T_without_ext += AUC_increment

              # Вставка C₀ в начало списков
              if list_columns_T[0] != 0:
                  list_columns_T.insert(0, 0)
                  list_concentration.insert(0, C0)

              # Вычисление AUC с С0
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
              
              ###AUC_Back_Ext
              list_AUC_Back_Ext.append(AUC_0_T-AUC_0_T_without_ext)
              
       
       ###AUC0-t/D
       list_AUC_0_T_D=[]
       for i in list_AUC_0_T:
           AUC_0_T_D = i/float(dose)
           list_AUC_0_T_D.append(AUC_0_T_D)

       ####AUCall
       list_list_columns_T = []
       list_list_concentration = []

       for i in range(0,count_row):
           list_columns_T=[]
           for column in df_without_numer.columns:
               list_columns_T.append(float(column))

           list_list_columns_T.append(list_columns_T)

           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

           list_list_concentration.append(list_concentration)

       list_AUCall = calculate_aucall(list_list_concentration, list_list_columns_T, list_AUC_0_T)

       ####Сmax/AUC0-t
       list_Сmax_division_AUC0_t_for_division=list(zip(list_cmax_True_pk,list_AUC_0_T))
       list_Сmax_division_AUC0_t=[]
       for i,j in list_Сmax_division_AUC0_t_for_division:
               list_Сmax_division_AUC0_t.append(i/j)


       ####KEL,Rsq_adjusted,Rsq,Corr_XY,No_points_lambda_z,Lambda_z_intercept,Lambda_z_lower,Lambda_z_upper
       list_kel_total=[]
       list_Rsq_adjusted=[]
       list_Rsq = []
       list_Corr_XY = []
       list_No_points_lambda_z = []
       list_Lambda_z_intercept = []
       list_Lambda_z_lower = []
       list_Lambda_z_upper = []
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

           list_ct_zip=list(zip(list_for_kel_c,list_for_kel_t))

           list_kel=[]
           list_r=[]
           list_r_orig=[]
           list_Corr = []
           list_n_points_used = []
           list_intercept = []
           list_Lambda_lower = []
           list_Lambda_upper = []
           for i,j in list_ct_zip:

               n_points_r=len(i)
               
               list_n_points_used.append(n_points_r)
               list_Lambda_lower.append(min(j))
               list_Lambda_upper.append(max(j))

               np_c=np.asarray(i)
               np_t_1=np.asarray(j).reshape((-1,1))

               np_c_log=np.log(np_c)

               model = LinearRegression().fit(np_t_1,np_c_log)

               np_t=np.asarray(j)
               a=np.corrcoef(np_t, np_c_log)
               cor=((a[0])[1])
               r_sq=cor**2

               list_Corr.append(cor)
               list_r_orig.append(r_sq)
               list_intercept.append(model.intercept_)

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
                  list_Rsq_adjusted.append(list_r1[i])
                  list_Rsq.append(list_r_orig[i])
                  list_Corr_XY.append(list_Corr[i])
                  list_No_points_lambda_z.append(list_n_points_used[i])
                  list_Lambda_z_intercept.append(list_intercept[i])
                  list_Lambda_z_lower.append(list_Lambda_lower[i])
                  list_Lambda_z_upper.append(list_Lambda_upper[i])
                  break #самая ранняя удовлетовряющая условию

           for i in list_kel_total_1:
               list_kel_total.append(i) 

       ####T1/2
       list_half_live=[]
       for i in list_kel_total:
           half_live=math.log(2)/i
           list_half_live.append(half_live)
       
       ####Span
       list_Span=[]
       for upper,lower,half_live in list(zip(list_Lambda_z_upper,list_Lambda_z_lower,list_half_live)):
           Span= (upper - lower)/half_live
           list_Span.append(Span)

       ###AUC0-inf 

       list_auc0_inf=[] 

       list_of_list_c=[]
       
       for i in range(0,count_row):
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

           list_c = list_concentration
           list_c.reverse() ### переворачиваем, для дальнейшей итерации с конца списка и поиска Clast не равное нулю
           list_of_list_c.append(list_c)

       list_zip_c_AUCt_inf=list(zip(list_kel_total,list_of_list_c))

       #AUCt-inf 
       list_auc_t_inf=[]     
       for i,j in list_zip_c_AUCt_inf:
           for clast in j:
               if clast != 0:
                  clast_true=clast
                  break
           auc_t_inf=clast_true/i
           list_auc_t_inf.append(auc_t_inf)

       list_auc_t_inf_and_AUC_0_T_zip=list(zip(list_AUC_0_T,list_auc_t_inf))

       for i,j in list_auc_t_inf_and_AUC_0_T_zip:
           auc0_inf=i+j    
           list_auc0_inf.append(auc0_inf)

       ###AUC0-inf/D
       list_auc0_inf_D=[]
       for i in list_auc0_inf:
           auc0_inf_D = i/float(dose)
           list_auc0_inf_D.append(auc0_inf_D)


       ###AUC_%Extrap
       list_AUC_extrap=[]
       for i,j in list(zip(list_auc0_inf,list_AUC_0_T)):
           AUC_extrap = ((i-j)/i)*100
           list_AUC_extrap.append(AUC_extrap)
       
       ###AUC_%Back_Ext
       list_AUC_perc_Back_Ext=[]
       for i,j in list(zip(list_AUC_Back_Ext,list_auc0_inf)):
           AUC_perc_Back_Ext = i/j*100
           list_AUC_perc_Back_Ext.append(AUC_perc_Back_Ext)

       ####Cl
       list_Cl=[]

       for i in list_auc0_inf:
           Cl = float(dose)/i
           list_Cl.append(Cl) 


       ####Vz
       list_Vz=[]

       list_zip_kel_cl=list(zip(list_kel_total,list_Cl))

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

              ### Обрезка только конечных нулей, а не всех после Cmax для корректной обработки также и нулей в середине
              while list_after_cmax and list_after_cmax[-1] == 0:
                  list_after_cmax.pop()
                  list_after_cmax_t.pop()

              list_concentration = list_before_cmax + list_after_cmax
              list_columns_T = list_before_cmax_t + list_after_cmax_t

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
       list_zip_for_AUMC_inf=list(zip(list_kel_total,list_C_last,list_T_last))

       list_AUMCt_inf=[]
       for k,c,t in list_zip_for_AUMC_inf:
           AUMCt_inf=c*t/k+c/(k*k)
           list_AUMCt_inf.append(AUMCt_inf)


       list_AUMC_zip=list(zip(list_AUMC0_t,list_AUMCt_inf))

       for i,j in list_AUMC_zip:
           AUMCO_inf=i+j
           list_AUMCO_inf.append(AUMCO_inf)
       
       ###AUMC_%Extrap
       list_AUMC_extrap=[]
       for i,j in list(zip(list_AUMCO_inf,list_AUMC0_t)):
           AUMC_extrap = ((i-j)/i)*100
           list_AUMC_extrap.append(AUMC_extrap)
       
       ###MRT0-t
       list_MRT0_t=[]

       list_zip_AUMCO_t_auc0_t = list(zip(list_AUMC0_t,list_AUC_0_T))

       for i,j in list_zip_AUMCO_t_auc0_t:
           MRT0_t=i/j
           list_MRT0_t.append(MRT0_t)

       ###MRT0-inf
       list_MRT0_inf=[]

       list_zip_AUMCO_inf_auc0_inf = list(zip(list_AUMCO_inf,list_auc0_inf))

       for i,j in list_zip_AUMCO_inf_auc0_inf:
           MRT0_inf=i/j
           list_MRT0_inf.append(MRT0_inf)

       ####Vss
       list_Vss=[]

       list_zip_MRT0_inf_cl=list(zip(list_MRT0_inf,list_Cl))

       for i,j in list_zip_MRT0_inf_cl:
           Vss = j*i
           list_Vss.append(Vss)
    
       ##################### Фрейм ФК параметров

       ### пользовательский индекс
       list_for_index=df["Номер"].tolist()
       df_PK=pd.DataFrame(list(zip(list_N_Samples,list_Dose,list_cmax_True_pk,list_cmax_D_pk,list_C0_total,list_Tmax_float_True_pk,list_C_last,list_T_last,list_MRT0_t,list_MRT0_inf,list_half_live,list_AUC_0_T,list_AUC_0_T_D,list_AUCall,list_auc0_inf,list_auc0_inf_D,list_AUC_extrap,list_AUC_perc_Back_Ext,list_AUMC0_t,list_AUMCO_inf,list_AUMC_extrap,list_Сmax_division_AUC0_t,list_kel_total,list_Rsq_adjusted,list_Rsq,list_Corr_XY,list_No_points_lambda_z,list_Lambda_z_intercept,list_Lambda_z_lower,list_Lambda_z_upper,list_Span,list_Cl,list_Vz,list_Vss)),columns=['N_Samples','Dose','Cmax','Cmax/D','C0','Tmax','Clast','Tlast','MRT0→t','MRT0→∞','T1/2','AUC0-t','AUC0-t/D','AUCall','AUC0→∞','AUC0→∞/D',f'AUC_%Extrap',f'AUC_%Back_Ext','AUMC0-t','AUMC0-∞',f'AUMC_%Extrap','Сmax/AUC0-t','Kel','Rsq_adjusted','Rsq','Corr_XY','No_points_lambda_z','Lambda_z_intercept','Lambda_z_lower','Lambda_z_upper','Span','Cl','Vz','Vss'],index=list_for_index)
    
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

       df_averaged_3_PK = create_table_descriptive_statistics(df_PK)

       df_concat_PK_pk= pd.concat([df_PK,df_averaged_3_PK],sort=False,axis=0)

       ###округление описательной статистики и ФК параметров

       series_N_Samples=df_concat_PK_pk['N_Samples']
       list_N_Samples_str_f=[v for v in series_N_Samples.tolist()]
       series_N_Samples=pd.Series(list_N_Samples_str_f, index = df_concat_PK_pk.index.tolist(), name='N_Samples')

       series_Dose=df_concat_PK_pk['Dose']
       list_Dose_str_f=[v for v in series_Dose.tolist()]
       series_Dose=pd.Series(list_Dose_str_f, index = df_concat_PK_pk.index.tolist(), name='Dose')

       series_Cmax=df_concat_PK_pk['Cmax']
       list_Cmax_str_f=[v for v in series_Cmax.tolist()]
       series_Cmax=pd.Series(list_Cmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax ' +"("+measure_unit_concentration+")")

       series_Cmax_D=df_concat_PK_pk['Cmax/D']
       list_Cmax_D_str_f=[v for v in series_Cmax_D.tolist()]
       series_Cmax_D=pd.Series(list_Cmax_D_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax/D ' +"("+measure_unit_concentration+'/'+'('+measure_unit_dose+')'+")")

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
       
       series_AUC0_t_D= df_concat_PK_pk['AUC0-t/D']
       list_AUC0_t_D_str_f=[v for v in series_AUC0_t_D.tolist()]
       series_AUC0_t_D=pd.Series(list_AUC0_t_D_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0-t/D '+"("+measure_unit_concentration+f"×{measure_unit_time}"+'/('+measure_unit_dose+')' +")")
       
       series_AUCall= df_concat_PK_pk['AUCall']
       list_AUCall_str_f=[v for v in series_AUCall.tolist()]
       series_AUCall=pd.Series(list_AUCall_str_f, index = df_concat_PK_pk.index.tolist(), name='AUCall '+"("+measure_unit_concentration+f"×{measure_unit_time}"+")")

       series_AUC0_inf= df_concat_PK_pk['AUC0→∞']
       list_AUC0_inf_str_f=[v for v in series_AUC0_inf.tolist()]
       series_AUC0_inf=pd.Series(list_AUC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")
       
       series_AUC0_inf_D= df_concat_PK_pk['AUC0→∞/D']
       list_AUC0_inf_D_str_f=[v for v in series_AUC0_inf_D.tolist()]
       series_AUC0_inf_D=pd.Series(list_AUC0_inf_D_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞/D '+"("+measure_unit_concentration+f"×{measure_unit_time}"+'/('+measure_unit_dose+')' +")")
       
       series_AUC_extrap= df_concat_PK_pk[f'AUC_%Extrap']
       list_AUC_extrap_str_f=[v for v in series_AUC_extrap.tolist()]
       series_AUC_extrap=pd.Series(list_AUC_extrap_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUC_%Extrap '+"("+"%"+")")
       
       series_AUC_perc_Back_Ext= df_concat_PK_pk[ f'AUC_%Back_Ext']
       list_AUC_perc_Back_Ext_str_f=[v for v in series_AUC_perc_Back_Ext.tolist()]
       series_AUC_perc_Back_Ext=pd.Series(list_AUC_perc_Back_Ext_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUC_%Back_Ext '+"("+"%"+")")

       series_AUMC0_t= df_concat_PK_pk['AUMC0-t']
       list_AUMC0_t_str_f=[v for v in series_AUMC0_t.tolist()]
       series_AUMC0_t=pd.Series(list_AUMC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_AUMC0_inf= df_concat_PK_pk['AUMC0-∞']
       list_AUMC0_inf_str_f=[v for v in series_AUMC0_inf.tolist()]
       series_AUMC0_inf=pd.Series(list_AUMC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")
       
       series_AUMC_extrap= df_concat_PK_pk[f'AUMC_%Extrap']
       list_AUMC_extrap_str_f=[v for v in series_AUMC_extrap.tolist()]
       series_AUMC_extrap=pd.Series(list_AUMC_extrap_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUMC_%Extrap '+"("+"%"+")")

       series_Сmax_dev_AUC0_t= df_concat_PK_pk['Сmax/AUC0-t']
       list_Сmax_dev_AUC0_t_str_f=[v for v in series_Сmax_dev_AUC0_t.tolist()]
       series_Сmax_dev_AUC0_t=pd.Series(list_Сmax_dev_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='Сmax/AUC0-t '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_Kel= df_concat_PK_pk['Kel']
       list_Kel_str_f=[v for v in series_Kel.tolist()]
       series_Kel=pd.Series(list_Kel_str_f, index = df_concat_PK_pk.index.tolist(), name='Kel '+"("+f"{measure_unit_time}\u207B\u00B9"+")")
       
       series_Rsq_adjusted= df_concat_PK_pk['Rsq_adjusted']
       list_Rsq_adjusted_str_f=[v for v in series_Rsq_adjusted.tolist()]
       series_Rsq_adjusted=pd.Series(list_Rsq_adjusted_str_f, index = df_concat_PK_pk.index.tolist(), name='Rsq_adjusted')

       series_Rsq= df_concat_PK_pk['Rsq']
       list_Rsq_str_f=[v for v in series_Rsq.tolist()]
       series_Rsq=pd.Series(list_Rsq_str_f, index = df_concat_PK_pk.index.tolist(), name='Rsq')

       series_Corr_XY= df_concat_PK_pk['Corr_XY']
       list_Corr_XY_str_f=[v for v in series_Corr_XY.tolist()]
       series_Corr_XY=pd.Series(list_Corr_XY_str_f, index = df_concat_PK_pk.index.tolist(), name='Corr_XY')

       series_No_points_lambda_z= df_concat_PK_pk['No_points_lambda_z']
       list_No_points_lambda_z_str_f=[v for v in series_No_points_lambda_z.tolist()]
       series_No_points_lambda_z=pd.Series(list_No_points_lambda_z_str_f, index = df_concat_PK_pk.index.tolist(), name='No_points_lambda_z')
       
       series_Lambda_z_intercept= df_concat_PK_pk['Lambda_z_intercept']
       list_Lambda_z_intercept_str_f=[v for v in series_Lambda_z_intercept.tolist()]
       series_Lambda_z_intercept=pd.Series(list_Lambda_z_intercept_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_intercept')

       series_Lambda_z_lower= df_concat_PK_pk['Lambda_z_lower']
       list_Lambda_z_lower_str_f=[v for v in series_Lambda_z_lower.tolist()]
       series_Lambda_z_lower=pd.Series(list_Lambda_z_lower_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_lower')

       series_Lambda_z_upper = df_concat_PK_pk['Lambda_z_upper']
       list_Lambda_z_upper_str_f=[v for v in series_Lambda_z_upper.tolist()]
       series_Lambda_z_upper=pd.Series(list_Lambda_z_upper_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_upper')

       series_Span = df_concat_PK_pk['Span']
       list_Span_str_f=[v for v in series_Span.tolist()]
       series_Span=pd.Series(list_Span_str_f, index = df_concat_PK_pk.index.tolist(), name='Span')

       series_Cl= df_concat_PK_pk['Cl']
       list_Cl_str_f=[v for v in series_Cl.tolist()]
       series_Cl=pd.Series(list_Cl_str_f, index = df_concat_PK_pk.index.tolist(), name='Cl ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})/{measure_unit_time}"+")")

       series_Vz= df_concat_PK_pk['Vz']
       list_Vz_str_f=[v for v in series_Vz.tolist()]
       series_Vz=pd.Series(list_Vz_str_f, index = df_concat_PK_pk.index.tolist(), name='Vz ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")

       series_Vss= df_concat_PK_pk['Vss']
       list_Vss_str_f=[v for v in series_Vss.tolist()]
       series_Vss=pd.Series(list_Vss_str_f, index = df_concat_PK_pk.index.tolist(), name='Vss ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")
       
       df_total_PK_pk = pd.concat([series_N_Samples,series_Dose,series_Rsq,series_Rsq_adjusted,series_Corr_XY,series_No_points_lambda_z,series_Kel,series_Lambda_z_intercept,series_Lambda_z_lower,series_Lambda_z_upper,series_half_live,series_Span,series_Tmax,series_Cmax,series_Cmax_D,series_C0,series_Tlast, series_Clast,series_AUC0_t,series_AUC0_t_D,series_AUCall,series_AUC0_inf,series_AUC0_inf_D,series_AUC_extrap,series_AUC_perc_Back_Ext,series_Vz,series_Cl,series_AUMC0_t,series_AUMC0_inf,series_AUMC_extrap, series_MRT0_t, series_MRT0_inf,series_Vss,series_Сmax_dev_AUC0_t], axis= 1) 
       df_total_PK_pk.index.name = 'Номер'

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
    

def pk_parametrs_total_infusion(df,selector_research,method_auc,dose,measure_unit_concentration,measure_unit_time,measure_unit_dose,infusion_time):
    
    ############ Параметры ФК

    df_without_numer=df.drop(['Номер'],axis=1)
    count_row=df_without_numer.shape[0]

    list_count_row=range(count_row)

    ###N_Samples
    list_N_Samples=[]
    for i in range(0,count_row):
        Sample=int(len(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_N_Samples.append(Sample)

    ###Dose
    list_Dose=[]
    for i in range(0,count_row):
        Dose=float(dose)
        list_Dose.append(Dose)

    ###infusion_time
    list_infusion_time=[]
    for i in range(0,count_row):
        infusion_time=float(infusion_time)
        list_infusion_time.append(infusion_time)

    ###Cmax_True
    list_cmax_True_pk=[]
    for i in range(0,count_row):
        cmax=float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))
        list_cmax_True_pk.append(cmax)

    ###Cmax_D
    list_cmax_D_pk=[]
    for i in range(0,count_row):
        cmax_d =float(max(df_without_numer.iloc[[i]].iloc[0].tolist()))/float(dose)
        list_cmax_D_pk.append(cmax_d)
    
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

              ### Обрезка только конечных нулей, а не всех после Cmax для корректной обработки также и нулей в середине
              while list_after_cmax and list_after_cmax[-1] == 0:
                  list_after_cmax.pop()
                  list_after_cmax_t.pop()

              list_concentration = list_before_cmax + list_after_cmax
              list_columns_T = list_before_cmax_t + list_after_cmax_t

              ######################

              AUC_0_T=np.trapz(list_concentration,x=list_columns_T)
              list_AUC_0_T.append(AUC_0_T)

       if method_auc == 'linear-up/log-down':
          for i in range(0,count_row):
              list_columns_T=[]
              for column in df_without_numer.columns:
                  list_columns_T.append(float(column))
              list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

              # Удаление нулей в конце массива
              while list_concentration and list_concentration[-1] == 0:
                  list_concentration.pop()
                  list_columns_T.pop()
              ######################
              
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

       ###AUC0-t/D
       list_AUC_0_T_D=[]
       for i in list_AUC_0_T:
           AUC_0_T_D = i/float(dose)
           list_AUC_0_T_D.append(AUC_0_T_D)

       ####AUCall
       list_list_columns_T = []
       list_list_concentration = []

       for i in range(0,count_row):
           list_columns_T=[]
           for column in df_without_numer.columns:
               list_columns_T.append(float(column))

           list_list_columns_T.append(list_columns_T)

           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()

           list_list_concentration.append(list_concentration)

       list_AUCall = calculate_aucall(list_list_concentration, list_list_columns_T, list_AUC_0_T)
       
       ####Сmax/AUC0-t
       list_Сmax_division_AUC0_t_for_division=list(zip(list_cmax_True_pk,list_AUC_0_T))
       list_Сmax_division_AUC0_t=[]
       for i,j in list_Сmax_division_AUC0_t_for_division:
               list_Сmax_division_AUC0_t.append(i/j)


       ####KEL,Rsq_adjusted,Rsq,Corr_XY,No_points_lambda_z,Lambda_z_intercept,Lambda_z_lower,Lambda_z_upper
       list_kel_total=[]
       list_Rsq_adjusted=[]
       list_Rsq = []
       list_Corr_XY = []
       list_No_points_lambda_z = []
       list_Lambda_z_intercept = []
       list_Lambda_z_lower = []
       list_Lambda_z_upper = []
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

           list_ct_zip=list(zip(list_for_kel_c,list_for_kel_t))

           list_kel=[]
           list_r=[]
           list_r_orig=[]
           list_Corr = []
           list_n_points_used = []
           list_intercept = []
           list_Lambda_lower = []
           list_Lambda_upper = []
           for i,j in list_ct_zip:

               n_points_r=len(i)
               
               list_n_points_used.append(n_points_r)
               list_Lambda_lower.append(min(j))
               list_Lambda_upper.append(max(j))

               np_c=np.asarray(i)
               np_t_1=np.asarray(j).reshape((-1,1))

               np_c_log=np.log(np_c)

               model = LinearRegression().fit(np_t_1,np_c_log)

               np_t=np.asarray(j)
               a=np.corrcoef(np_t, np_c_log)
               cor=((a[0])[1])
               r_sq=cor**2

               list_Corr.append(cor)
               list_r_orig.append(r_sq)
               list_intercept.append(model.intercept_)

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
                  list_Rsq_adjusted.append(list_r1[i])
                  list_Rsq.append(list_r_orig[i])
                  list_Corr_XY.append(list_Corr[i])
                  list_No_points_lambda_z.append(list_n_points_used[i])
                  list_Lambda_z_intercept.append(list_intercept[i])
                  list_Lambda_z_lower.append(list_Lambda_lower[i])
                  list_Lambda_z_upper.append(list_Lambda_upper[i])
                  break #самая ранняя удовлетовряющая условию

           for i in list_kel_total_1:
               list_kel_total.append(i) 
       
       ####T1/2
       list_half_live=[]
       for i in list_kel_total:
           half_live=math.log(2)/i
           list_half_live.append(half_live)

       ####Span
       list_Span=[]
       for upper,lower,half_live in list(zip(list_Lambda_z_upper,list_Lambda_z_lower,list_half_live)):
           Span= (upper - lower)/half_live
           list_Span.append(Span)

       ###AUC0-inf 

       list_auc0_inf=[] 

       list_of_list_c=[]
       for i in range(0,count_row):
           list_concentration=df_without_numer.iloc[[i]].iloc[0].tolist()
           list_concentration.remove(0)
           list_c = list_concentration
           list_c.reverse() ### переворачиваем, для дальнейшей итерации с конца списка и поиска Clast не равное нулю
           list_of_list_c.append(list_c)

       list_zip_c_AUCt_inf=list(zip(list_kel_total,list_of_list_c))

       #AUCt-inf 
       list_auc_t_inf=[]     
       for i,j in list_zip_c_AUCt_inf:
           for clast in j:
               if clast != 0:
                  clast_true=clast
                  break
           auc_t_inf=clast_true/i
           list_auc_t_inf.append(auc_t_inf)

       list_auc_t_inf_and_AUC_0_T_zip=list(zip(list_AUC_0_T,list_auc_t_inf))

       for i,j in list_auc_t_inf_and_AUC_0_T_zip:
           auc0_inf=i+j    
           list_auc0_inf.append(auc0_inf)

       ###AUC0-inf/D
       list_auc0_inf_D=[]
       for i in list_auc0_inf:
           auc0_inf_D = i/float(dose)
           list_auc0_inf_D.append(auc0_inf_D)


       ###AUC_%Extrap
       list_AUC_extrap=[]
       for i,j in list(zip(list_auc0_inf,list_AUC_0_T)):
           AUC_extrap = ((i-j)/i)*100
           list_AUC_extrap.append(AUC_extrap)

       ####Cl
       list_Cl=[]

       for i in list_auc0_inf:
           Cl = float(dose)/i
           list_Cl.append(Cl) 


       ####Vz
       list_Vz=[]

       list_zip_kel_Cl=list(zip(list_kel_total,list_Cl))

       for i,j in list_zip_kel_Cl:
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

              ###удаление всех нулей сзади массива, т.к. AUMC0-t это AUMClast (до последней определяемой точки, а не наблюдаемой)
              cmax = max(list_concentration)
              index_cmax = list_concentration.index(cmax)
              list_before_cmax = list_concentration[0:index_cmax]
              list_after_cmax = list_concentration[index_cmax:]
              list_before_cmax_t = list_columns_T[0:index_cmax]
              list_after_cmax_t = list_columns_T[index_cmax:]

              count_list_concentration = len(list_after_cmax)
              list_range_for_remove_0 = range(0,count_list_concentration)

              ### Обрезка только конечных нулей, а не всех после Cmax для корректной обработки также и нулей в середине
              while list_after_cmax and list_after_cmax[-1] == 0:
                  list_after_cmax.pop()
                  list_after_cmax_t.pop()

              list_concentration = list_before_cmax + list_after_cmax
              list_columns_T = list_before_cmax_t + list_after_cmax_t
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

              ### Удаление нулей сзади массива
              while list_concentration and list_concentration[-1] == 0:
                  list_concentration.pop()
                  list_columns_T.pop()
              ######################

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
       list_zip_for_AUMC_inf=list(zip(list_kel_total,list_C_last,list_T_last))

       list_AUMCt_inf=[]
       for k,c,t in list_zip_for_AUMC_inf:
           AUMCt_inf=c*t/k+c/(k*k)
           list_AUMCt_inf.append(AUMCt_inf)


       list_AUMC_zip=list(zip(list_AUMC0_t,list_AUMCt_inf))

       for i,j in list_AUMC_zip:
           AUMCO_inf=i+j
           list_AUMCO_inf.append(AUMCO_inf)
       
       ###AUMC_%Extrap
       list_AUMC_extrap=[]
       for i,j in list(zip(list_AUMCO_inf,list_AUMC0_t)):
           AUMC_extrap = ((i-j)/i)*100
           list_AUMC_extrap.append(AUMC_extrap)

       ###MRT0-t
       list_MRT0_t=[]

       list_zip_AUMCO_t_auc0_t = list(zip(list_AUMC0_t,list_AUC_0_T))

       for i,j in list_zip_AUMCO_t_auc0_t:
           MRT0_t=i/j  - float(infusion_time)/2
           list_MRT0_t.append(MRT0_t)

       ###MRT0-inf
       list_MRT0_inf=[]

       list_zip_AUMCO_inf_auc0_inf = list(zip(list_AUMCO_inf,list_auc0_inf))

       for i,j in list_zip_AUMCO_inf_auc0_inf:
           MRT0_inf=i/j - float(infusion_time)/2
           list_MRT0_inf.append(MRT0_inf)

       ####Vss
       list_Vss=[]

       list_zip_MRT0_inf_cl=list(zip(list_MRT0_inf,list_Cl))

       for i,j in list_zip_MRT0_inf_cl:
           Vss = j*i
           list_Vss.append(Vss)
       
    
       ##################### Фрейм ФК параметров

       ### пользовательский индекс
       list_for_index=df["Номер"].tolist()
       df_PK=pd.DataFrame(list(zip(list_N_Samples,list_Dose,list_infusion_time,list_cmax_True_pk,list_cmax_D_pk,list_Tmax_float_True_pk,list_C_last,list_T_last,list_MRT0_t,list_MRT0_inf,list_half_live,list_AUC_0_T,list_AUC_0_T_D,list_AUCall,list_auc0_inf,list_auc0_inf_D,list_AUC_extrap,list_AUMC0_t,list_AUMCO_inf,list_AUMC_extrap,list_Сmax_division_AUC0_t,list_kel_total,list_Rsq_adjusted,list_Rsq,list_Corr_XY,list_No_points_lambda_z,list_Lambda_z_intercept,list_Lambda_z_lower,list_Lambda_z_upper,list_Span,list_Cl,list_Vz,list_Vss)),columns=['N_Samples','Dose','Length of infusion','Cmax','Cmax/D','Tmax','Clast','Tlast','MRT0→t','MRT0→∞','T1/2','AUC0-t','AUC0-t/D','AUCall','AUC0→∞','AUC0→∞/D',f'AUC_%Extrap','AUMC0-t','AUMC0-∞',f'AUMC_%Extrap','Сmax/AUC0-t','Kel','Rsq_adjusted','Rsq','Corr_XY','No_points_lambda_z','Lambda_z_intercept','Lambda_z_lower','Lambda_z_upper','Span','Cl','Vz','Vss'],index=list_for_index)
    
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

       df_averaged_3_PK = create_table_descriptive_statistics(df_PK)
       df_concat_PK_pk= pd.concat([df_PK,df_averaged_3_PK],sort=False,axis=0)

       ###округление описательной статистики и ФК параметров
       series_N_Samples=df_concat_PK_pk['N_Samples']
       list_N_Samples_str_f=[v for v in series_N_Samples.tolist()]
       series_N_Samples=pd.Series(list_N_Samples_str_f, index = df_concat_PK_pk.index.tolist(), name='N_Samples')

       series_Dose=df_concat_PK_pk['Dose']
       list_Dose_str_f=[v for v in series_Dose.tolist()]
       series_Dose=pd.Series(list_Dose_str_f, index = df_concat_PK_pk.index.tolist(), name='Dose')

       series_Length_infusion=df_concat_PK_pk['Length of infusion']
       list_Length_infusion_str_f=[v for v in series_Length_infusion.tolist()]
       series_Length_infusion=pd.Series(list_Length_infusion_str_f, index = df_concat_PK_pk.index.tolist(), name='Length of infusion ' +"("+measure_unit_time+")" )

       series_Cmax=df_concat_PK_pk['Cmax']
       list_Cmax_str_f=[v for v in series_Cmax.tolist()]
       series_Cmax=pd.Series(list_Cmax_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax ' +"("+measure_unit_concentration+")")

       series_Cmax_D=df_concat_PK_pk['Cmax/D']
       list_Cmax_D_str_f=[v for v in series_Cmax_D.tolist()]
       series_Cmax_D=pd.Series(list_Cmax_D_str_f, index = df_concat_PK_pk.index.tolist(), name='Cmax/D ' +"("+measure_unit_concentration+'/'+'('+measure_unit_dose+')'+")")

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
       
       series_AUC0_t_D= df_concat_PK_pk['AUC0-t/D']
       list_AUC0_t_D_str_f=[v for v in series_AUC0_t_D.tolist()]
       series_AUC0_t_D=pd.Series(list_AUC0_t_D_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0-t/D '+"("+measure_unit_concentration+f"×{measure_unit_time}"+'/('+measure_unit_dose+')' +")")
       
       series_AUCall= df_concat_PK_pk['AUCall']
       list_AUCall_str_f=[v for v in series_AUCall.tolist()]
       series_AUCall=pd.Series(list_AUCall_str_f, index = df_concat_PK_pk.index.tolist(), name='AUCall '+"("+measure_unit_concentration+f"×{measure_unit_time}"+")")

       series_AUC0_inf= df_concat_PK_pk['AUC0→∞']
       list_AUC0_inf_str_f=[v for v in series_AUC0_inf.tolist()]
       series_AUC0_inf=pd.Series(list_AUC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}" +")")
       
       series_AUC0_inf_D= df_concat_PK_pk['AUC0→∞/D']
       list_AUC0_inf_D_str_f=[v for v in series_AUC0_inf_D.tolist()]
       series_AUC0_inf_D=pd.Series(list_AUC0_inf_D_str_f, index = df_concat_PK_pk.index.tolist(), name='AUC0→∞/D '+"("+measure_unit_concentration+f"×{measure_unit_time}"+'/('+measure_unit_dose+')' +")")
       
       series_AUC_extrap= df_concat_PK_pk[f'AUC_%Extrap']
       list_AUC_extrap_str_f=[v for v in series_AUC_extrap.tolist()]
       series_AUC_extrap=pd.Series(list_AUC_extrap_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUC_%Extrap '+"("+"%"+")")

       series_AUMC0_t= df_concat_PK_pk['AUMC0-t']
       list_AUMC0_t_str_f=[v for v in series_AUMC0_t.tolist()]
       series_AUMC0_t=pd.Series(list_AUMC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-t '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")

       series_AUMC0_inf= df_concat_PK_pk['AUMC0-∞']
       list_AUMC0_inf_str_f=[v for v in series_AUMC0_inf.tolist()]
       series_AUMC0_inf=pd.Series(list_AUMC0_inf_str_f, index = df_concat_PK_pk.index.tolist(), name='AUMC0-∞ '+"("+measure_unit_concentration+f"×{measure_unit_time}\u00B2" +")")
       
       series_AUMC_extrap= df_concat_PK_pk[f'AUMC_%Extrap']
       list_AUMC_extrap_str_f=[v for v in series_AUMC_extrap.tolist()]
       series_AUMC_extrap=pd.Series(list_AUMC_extrap_str_f, index = df_concat_PK_pk.index.tolist(), name=f'AUMC_%Extrap '+"("+"%"+")")

       series_Сmax_dev_AUC0_t= df_concat_PK_pk['Сmax/AUC0-t']
       list_Сmax_dev_AUC0_t_str_f=[v for v in series_Сmax_dev_AUC0_t.tolist()]
       series_Сmax_dev_AUC0_t=pd.Series(list_Сmax_dev_AUC0_t_str_f, index = df_concat_PK_pk.index.tolist(), name='Сmax/AUC0-t '+"("+f"{measure_unit_time}\u207B\u00B9"+")")

       series_Kel= df_concat_PK_pk['Kel']
       list_Kel_str_f=[v for v in series_Kel.tolist()]
       series_Kel=pd.Series(list_Kel_str_f, index = df_concat_PK_pk.index.tolist(), name='Kel '+"("+f"{measure_unit_time}\u207B\u00B9"+")")
       
       series_Rsq_adjusted= df_concat_PK_pk['Rsq_adjusted']
       list_Rsq_adjusted_str_f=[v for v in series_Rsq_adjusted.tolist()]
       series_Rsq_adjusted=pd.Series(list_Rsq_adjusted_str_f, index = df_concat_PK_pk.index.tolist(), name='Rsq_adjusted')

       series_Rsq= df_concat_PK_pk['Rsq']
       list_Rsq_str_f=[v for v in series_Rsq.tolist()]
       series_Rsq=pd.Series(list_Rsq_str_f, index = df_concat_PK_pk.index.tolist(), name='Rsq')

       series_Corr_XY= df_concat_PK_pk['Corr_XY']
       list_Corr_XY_str_f=[v for v in series_Corr_XY.tolist()]
       series_Corr_XY=pd.Series(list_Corr_XY_str_f, index = df_concat_PK_pk.index.tolist(), name='Corr_XY')

       series_No_points_lambda_z= df_concat_PK_pk['No_points_lambda_z']
       list_No_points_lambda_z_str_f=[v for v in series_No_points_lambda_z.tolist()]
       series_No_points_lambda_z=pd.Series(list_No_points_lambda_z_str_f, index = df_concat_PK_pk.index.tolist(), name='No_points_lambda_z')
       
       series_Lambda_z_intercept= df_concat_PK_pk['Lambda_z_intercept']
       list_Lambda_z_intercept_str_f=[v for v in series_Lambda_z_intercept.tolist()]
       series_Lambda_z_intercept=pd.Series(list_Lambda_z_intercept_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_intercept')

       series_Lambda_z_lower= df_concat_PK_pk['Lambda_z_lower']
       list_Lambda_z_lower_str_f=[v for v in series_Lambda_z_lower.tolist()]
       series_Lambda_z_lower=pd.Series(list_Lambda_z_lower_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_lower')

       series_Lambda_z_upper = df_concat_PK_pk['Lambda_z_upper']
       list_Lambda_z_upper_str_f=[v for v in series_Lambda_z_upper.tolist()]
       series_Lambda_z_upper=pd.Series(list_Lambda_z_upper_str_f, index = df_concat_PK_pk.index.tolist(), name='Lambda_z_upper')

       series_Span = df_concat_PK_pk['Span']
       list_Span_str_f=[v for v in series_Span.tolist()]
       series_Span=pd.Series(list_Span_str_f, index = df_concat_PK_pk.index.tolist(), name='Span')

       series_Cl= df_concat_PK_pk['Cl']
       list_Cl_str_f=[v for v in series_Cl.tolist()]
       series_Cl=pd.Series(list_Cl_str_f, index = df_concat_PK_pk.index.tolist(), name='Cl ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})/{measure_unit_time}"+")")

       series_Vz= df_concat_PK_pk['Vz']
       list_Vz_str_f=[v for v in series_Vz.tolist()]
       series_Vz=pd.Series(list_Vz_str_f, index = df_concat_PK_pk.index.tolist(), name='Vz ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")
       
       series_Vss= df_concat_PK_pk['Vss']
       list_Vss_str_f=[v for v in series_Vss.tolist()]
       series_Vss=pd.Series(list_Vss_str_f, index = df_concat_PK_pk.index.tolist(), name='Vss ' +"("+f"({measure_unit_dose})/({measure_unit_concentration})"+")")

       df_total_PK_pk = pd.concat([series_N_Samples,series_Dose,series_Length_infusion,series_Rsq,series_Rsq_adjusted,series_Corr_XY,series_No_points_lambda_z,series_Kel,series_Lambda_z_intercept,series_Lambda_z_lower,series_Lambda_z_upper,series_half_live,series_Span,series_Tmax,series_Cmax,series_Cmax_D,series_Tlast, series_Clast,series_AUC0_t,series_AUC0_t_D,series_AUCall,series_AUC0_inf,series_AUC0_inf_D,series_AUC_extrap,series_Vz,series_Cl,series_AUMC0_t,series_AUMC0_inf,series_AUMC_extrap, series_MRT0_t, series_MRT0_inf,series_Vss,series_Сmax_dev_AUC0_t], axis= 1) 

       df_total_PK_pk.index.name = 'Номер'

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