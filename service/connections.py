import pandas as pd
import streamlit as st
import os

def limpar_df(df, colunas_remover=[]):
    st.write()
    date_columns = [col for col in df.columns if 'Data' in col]
    if 'StatusFinal' in df.columns:
        date_columns.append("StatusFinal")
    df = pd.DataFrame(df)
    if(colunas_remover):
        df = df.drop(columns=colunas_remover)
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], format='mixed')
        df[col] = df[col].dt.strftime('%d/%m/%Y')
    return df

def processar_arquivos_carregados(uploaded_files):
    """
    Recebe os arquivos carregados e retorna um dicionário de DataFrames.
    Esta função APENAS processa os dados, não mostra o widget de upload.
    """
    dados_carregados = {}
    
    # É uma boa prática verificar se a lista não está vazia
    if not uploaded_files:
        return None

    for upload_file in uploaded_files:
        print(f"Processando o arquivo: {upload_file.name}")
        
        if(upload_file.name == 'CTS.xlsx'):
            # xls = pd.ExcelFile(upload_file)
            # print(f"Available sheets: {xls.sheet_names}")
            # print(upload_file.name)
            df_time = pd.read_excel(upload_file, sheet_name="cts")
            dados_carregados["df_time"] = df_time

        elif(upload_file.name == "Clientes.xlsx"):
                df_clientes = pd.read_excel(upload_file, sheet_name="clientes")
                df_temp = df_clientes.set_index('KA')
                series_de_listas = df_temp.apply(lambda linha: linha.dropna().tolist(), axis=1)
                divisoes = series_de_listas.to_dict()
                divisoes_pesquisa = {}
                dados_carregados["divisoes"] = divisoes

        elif(upload_file.name == 'Conexoes_NOC_RVT.xlsx'):
            df_noc1 = pd.read_excel(upload_file, sheet_name="NOC")
            df_noc = limpar_df(df_noc1, ['ClienteId'])
            dados_carregados["df_noc"] = df_noc
            
            df_rvt1 = pd.read_excel(upload_file, sheet_name="RVT")
            df_rvt = df_rvt1.drop(columns=['Cliente__c', 'ResponsavelBall__c'])
            dados_carregados["df_rvt"] = df_rvt
            
            df_consulta1 = pd.read_excel(upload_file, sheet_name="NOC_e_RVT")
            unnamedcol = [col for col in df_consulta1 if "Unnamed" in col]
            unnamedcol.append("NOC__c")
            unnamedcol.append("RVT__c")
            df_consulta = limpar_df(df_consulta1, unnamedcol)
            dados_carregados["df_consulta"] = df_consulta
            
        elif(upload_file.name == 'Conexoes_RessarceBall.xlsx'):
            df_r_brasil = pd.read_excel(upload_file, sheet_name="RES_Brasil")
            dados_carregados["df_r_brasil"] = df_r_brasil
            
            df_d_brasil = pd.read_excel(upload_file, sheet_name="DEV_Brasil")
            dados_carregados["df_d_brasil"] = df_d_brasil
            
            df_argentina = pd.read_excel(upload_file, sheet_name="Argentina")
            dados_carregados["df_argentina"] = df_argentina
            
            df_chile = pd.read_excel(upload_file, sheet_name="Chile")
            dados_carregados["df_chile"] = df_chile
            
            df_paraguai = pd.read_excel(upload_file, sheet_name="Paraguay")
            dados_carregados["df_paraguai"] = df_paraguai
        
        
    return dados_carregados
