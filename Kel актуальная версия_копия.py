import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import math
##################################
#import statsmodels.formula.api as smf
import pandas as pd
import scipy as sci


##########################################

df=pd.read_excel("C:/Users/Павел/OneDrive/Рабочий стол/Проекты 2023 для валидации приложения/Этравирин/Папка с исходными данными/Этравирин_T.xlsx")
df.fillna('-',inplace=True) ### убрать все None
print(df)
list_columns=df.columns.tolist()
list_columns.remove("Номер")
list_range_df = range(0,df.shape[0])

list_kel_total_visual= []
for i in list_range_df: 
    
    list_iloc=df.iloc[i].tolist()
    list_iloc.pop(0)
    
    ### убрать все "-"
    
    count_el_list_iloc=len(list_iloc)
    list_el_list_iloc=range(0,count_el_list_iloc)
    
    list_iloc_new=[]
    for i in list_el_list_iloc:
        if list_iloc[i] !='-':
           list_iloc_new.append(list_iloc[i])
           
    list_iloc = list_iloc_new
       
    print(list_iloc)
    
    list_t=list_columns
    list_c=list_iloc
    
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
    ###############################################
    
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
        
        #fig, ax = plt.subplots()
        #plt.plot(np_t,np_c_log)
        #plt.show(fig)
    
    #делаем срезы списоков до rmax
    max_r=max(list_r)
    
    index_max_r= list_r.index(max_r)
    
    
    list_r1=list_r
    list_kel1=list_kel
    
    
    number_elem_list_r1=len(list_r1)
    
    print(list_r1)
    print(list_kel1)
    
    list_range_kel=range(0,number_elem_list_r1) 
    
    
    
    list_kel_total=[]
    for i in list_range_kel:
        
        #if len(list_r1)==1:
           #list_kel_total.append(list_kel1[i]*math.log(math.exp(1)))
           #break 
        
        if abs(list_r[index_max_r] - list_r1[i]) < 0.0001: #проверяем все точки справа и слева от rmax
           list_kel_total.append(list_kel1[i]*math.log(math.exp(1))) #отдаю предпочтение rmax с большим количеством точек
           break #самая ранняя удовлетовряющая условию
        
        #if len(list_kel_total) == 0:   
           #list_kel_total.append(list_kel[index_max_r])
       
    list_kel_total_visual.append(round(list_kel_total[0],4))
    


###сверяем с ОА
df_oleg=pd.read_excel("C:/Users/Павел/OneDrive/Рабочий стол/Проекты 2023 для валидации приложения/Этравирин/Папка с исходными данными/kel_T.xlsx")

list_oleg=df_oleg['T'].tolist()


list_zip = zip(list_kel_total_visual,list_oleg)

list_boolean=[]
for kel,oleg in list_zip:
    list_boolean.append(kel == round(oleg,4))

list_oleg_round=[]
for i in list_oleg:
    i = round(i,4)
    list_oleg_round.append(i)

list_numer = range(1,(df.shape[0]+1))
df_comparison = pd.DataFrame({'Pavel': list_kel_total_visual,'Oleg': list_oleg_round,'Boolean': list_boolean}, index=list_numer)
print(df_comparison)

               















