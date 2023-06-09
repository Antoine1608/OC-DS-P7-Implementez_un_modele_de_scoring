# -*- coding: utf-8 -*-

import streamlit as st
st.set_page_config(layout="wide")
import pickle
import pandas as pd
import numpy as np
import sklearn
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import json
import requests


#load data
df=pd.read_csv("data/df_.csv")[0:100]

# Charger les variables threshold et important features
# Opening JSON file
f = open('model/data.json')#'../model/data.json')

# returns JSON object as a dictionary
data = json.load(f)

# Charger le meilleur seuil
best_th = data['best_th']

# Charger la liste des features importantes
L_var = data['feat']

def main():

    # Prediction function
    @st.cache_data
    def predict (data):
        best_model = pickle.load(open('model/model.pkl', 'rb'))#'../model/model.pkl', 'rb'))
        y_te_pred = best_model.predict(data)
        y_te_pred = (y_te_pred >= best_th)

        y_proba = best_model.predict_proba(data)

        return y_te_pred, y_proba

    # Vizualisation function
    @st.cache_data
    def graphe(df, num, L_var, title):
        df_u = df.loc[df['TARGET']==df['TARGET'],L_var+['TARGET', 'SK_ID_CURR']]

        dfg = df_u.groupby('TARGET').mean()
        dfg = dfg.drop(columns='SK_ID_CURR')

        l = pd.concat([dfg,df.loc[df['SK_ID_CURR']==num, L_var]],ignore_index=True)
        # Transformation of data for better vizualisation
        l = l.abs()+1
        l = np.log(l)

        X = l.columns

        credit_accepted = l.iloc[0,:]
        if len(l)==3:
            credit_refused = l.iloc[1,:]
        customer = l.iloc[-1,:]

        X_axis = np.arange(l.shape[1])

        fig = plt.figure(figsize=(10,5))

        plt.bar(X_axis - 0.2, credit_accepted, 0.2, label = 'credit_accepted')
        try :
            plt.bar(X_axis + 0, credit_refused, 0.2, label = 'credit_refused')
        except :
            pass
        plt.bar(X_axis + 0.2, customer, 0.2, label = 'customer')

        plt.xticks(X_axis, X, rotation=45)
        #plt.xticks(rotation=45,fontsize=12)
        plt.xlabel("Features")
        plt.ylabel("Values")
        plt.title(title)
        plt.legend()
        #plt.show()

        return fig


    # Titre de la page
    st.title("Projet 7 - Implémentez un modèle de scoring")
    st.text("Données client : ")

    values = df['SK_ID_CURR'].values
    num = st.sidebar.selectbox(
        "Veuillez sélectionner un numéro de demande de prêt",
        values)
    st.sidebar.write(f"Situation familiale : {[mot[19:] for mot in df.columns if (('FAMILY' in mot)&(int(df.loc[df['SK_ID_CURR']==num,mot])))][0]}")
    st.sidebar.write(f"Nombre d'enfant(s) : {int(df.loc[df['SK_ID_CURR']==num,'CNT_CHILDREN'])}")
    st.sidebar.write(f"Age : {round(int(df.loc[df['SK_ID_CURR']==num, 'DAYS_BIRTH'])/(-364))}")    
    st.write(df.loc[df['SK_ID_CURR']==num, L_var])

    #Le bouton de prédiction
    input_data = {'SK_ID_CURR':int(num)}

    if st.button("Prediction"):
        result = requests.post(url="http://monapp.herokuapp.com/predict",data=json.dumps(input_data))
        #result = requests.post(url="http://127.0.0.1:8000/predict",data=json.dumps(input_data))
        result=result.json()
        p=result['prediction']
        st.text(f'Probabilité de défaillance (limite {best_th}): {p}')

    # Appeler la fonction graphe() à l'intérieur de st.pyplot()
    fig = graphe(df, num, L_var, 'customer vs total population')
    st.pyplot(fig)

    # Customer generic data
    sex = int(df.loc[df['SK_ID_CURR']== num, 'CODE_GENDER'])
    age = int(df.loc[df['SK_ID_CURR']== num, 'DAYS_BIRTH'])

    # Similar group 
    mask = (df['DAYS_BIRTH'] <= age+5*364) & (df['DAYS_BIRTH'] > age-5*364)
    df_s = df.loc[(mask==True)&(df['CODE_GENDER']==sex),:].reset_index(drop=True)

    fig = graphe(df_s, num, L_var, 'customer vs similar population')
    st.pyplot(fig)


# Tests unitaires    

import subprocess

def run_tests():
    command = "pytest ./tests/test_P7.py"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("Test réussi !")
        main()
    else:
        print("Test échoué.")
        print(result.stdout)
        st.title(f"Les tests ont échoué - code : {result.returncode}")

if __name__ == '__main__':
    run_tests()
