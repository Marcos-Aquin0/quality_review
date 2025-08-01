import pandas as pd
from datetime import datetime
from collections import defaultdict
import streamlit as st
import unidecode
import altair as alt
import io
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import time
import string
import json

@st.cache_data
def load_translation(language):
    """Carrega o arquivo JSON de tradução para o idioma selecionado."""
    filepath = os.path.join("locale", f"{language}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Função para obter o texto traduzido
def get_text(key, **kwargs):
    """
    Obtém o texto traduzido para uma chave específica.
    Usa o idioma armazenado no session_state.
    Permite a formatação de strings com .format().
    """
    lang = st.session_state.get("language", "pt") 
    translations = load_translation(lang)
    text = translations.get(key, f"Texto não encontrado para a chave: {key}")
    if kwargs:
        return text.format(**kwargs)
    return text

nocs_nao_cadastradas = []

dict_meses = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez"
}

def clientes_clean(cliente):
    cliente = str(cliente)
    cliente = cliente.lower()
    cliente = unidecode.unidecode(cliente)
    cliente = cliente.replace('\xa0', "").strip()
    # limpeza realizada no power query
    # cliente = cliente.replace('.', "").strip()
    # cliente = cliente.replace('s.a', "sa").strip()
    # cliente = cliente.replace('s.a.', "sa").strip()
    # cliente = cliente.replace('&', "").strip()
    # cliente = cliente.replace('s a', "sa").strip()
    # cliente = cliente.replace('s r l', "srl").strip()
    # cliente = cliente.replace('/', "").strip()
    return cliente
  
def categorizar_divisao(cliente):
    divisoes = st.session_state.dados_carregados.get('divisoes')
    if pd.isna(cliente):
        return 'outros'
    cliente = clientes_clean(cliente)
    if 'ball' in cliente:
        return 'planta_ball'
    for chave, lista_de_strings in divisoes.items():
        for s in lista_de_strings:
            if cliente in s:  # ignora maiúsculas/minúsculas
                return chave
    st.info(get_text("unclassified_client_info", cliente=cliente))
    return 'outros'

def filtrar_por_mes(df, campo_data, mes, ano):
    df_aux_copy = df.copy()
    if mes == '' or df.empty:
        return df
    df_aux_copy[campo_data] = pd.to_datetime(df_aux_copy[campo_data], format="mixed", dayfirst=False)
    return df[(df_aux_copy[campo_data].dt.month == int(mes)) & (df_aux_copy[campo_data].dt.year == int(ano))]

def filtrar_por_ytd(df, campo_data, mes, ano):
    df_aux_copy = df.copy()
    if mes == '' or df.empty:
        return df
    df_aux_copy[campo_data] = pd.to_datetime(df_aux_copy[campo_data], format="%d/%m/%Y", dayfirst=False)
    return df[(df_aux_copy[campo_data].dt.month <= int(mes)) & (df_aux_copy[campo_data].dt.year == int(ano))]

def get_visitas_por_divisao(df_rvt, mes, ano):
    df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes, ano)
    visitas = defaultdict(lambda: defaultdict(int))
    
    for index, row in df_filtrado.iterrows():
        cliente = row['Clientes']
        motivo = row['Motivo']
        
        div = categorizar_divisao(cliente)
        # if div == 'outros':
        #     print(cliente)
        # Incrementa total
        visitas[div]['total'] += 1
        
        visitas[div][motivo] += 1
    st.dataframe(dict(visitas))

def get_tipos_visitas_rvt(df_rvt, mes, ano):
    df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes, ano) #por que data início e não data de criação do RVT?
    dados_atuais = {'preventiva':0, 'corretiva':0}
    for tipo in df_filtrado['Tipo']:
        if tipo == 'PREVENTIVA' or tipo == 'ATENDIMENTO REMOTO - PREVENTIVO':
            dados_atuais['preventiva'] += 1
        else: dados_atuais['corretiva'] += 1

    if mes == 1: 
        mes = 12
        ano = ano-1
    else: mes = mes-1
    
    # Dados do período anterior
    df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes, ano)
    dados_anteriores = {'preventiva':0, 'corretiva':0}
    for tipo in df_filtrado['Tipo']:
        # dados_anteriores['total'] += 1
        if tipo == 'PREVENTIVA' or tipo == 'ATENDIMENTO REMOTO - PREVENTIVO':
            dados_anteriores['preventiva'] += 1
        else: dados_anteriores['corretiva'] += 1

    col1, col2 = st.columns(2)
    with col1:
        st.write("atual")
        st.dataframe(dados_atuais)
    with col2:
        st.write("mês passado")
        st.dataframe(dados_anteriores)

    col1, col2 = st.columns(2)
    col1.metric("Preventiva", dados_atuais['preventiva'], f"{round((dados_atuais['preventiva']*100/dados_anteriores['preventiva'])-100,2) if dados_anteriores['preventiva'] !=0 else 0}% (anterior: {dados_anteriores['preventiva']})")
    col2.metric("Corretiva", dados_atuais['corretiva'], f"{round((dados_atuais['corretiva']*100/dados_anteriores['corretiva'])-100,2) if dados_anteriores['corretiva'] !=0 else 0}% (anterior: {dados_anteriores['corretiva']})", "inverse")

    source = pd.DataFrame({
        "Categoria": dados_atuais.keys(),
        "Quantidade": dados_atuais.values()
    })

    total = dados_atuais['preventiva'] + dados_atuais['corretiva']

    base = alt.Chart(source).encode(
        theta=alt.Theta("Quantidade", stack=True)
    )

    donut = base.mark_arc(innerRadius=55, outerRadius=110).encode(
        color=alt.Color("Categoria:N", scale=alt.Scale(scheme='blues')), # Aplica as cores personalizadas
        order=alt.Order("Quantidade", sort="descending"), # Opcional: ordena as fatias
        tooltip=["Categoria", "Quantidade"] # Adiciona tooltip
    )

    text = base.mark_text(radius=130, fontSize=16, fontWeight='bold').encode(
        text=alt.Text("Quantidade"),
        order=alt.Order("Quantidade", sort="descending"),
        color=alt.value("black")
    )

    center_text_data = pd.DataFrame([{"text": f"Total: {total}"}])

    center_text = alt.Chart(center_text_data).mark_text(
        align='center',
        baseline='middle',
        fontSize=20, 
        fontWeight='bold',
        color='black' 
    ).encode(
        text=alt.Text("text")
    )

    chart = (donut + text + center_text).properties(
        title="Visitas Preventivas e Corretivas" 
    )
    col1, col2 = st.columns([3,1])
    with col1:
        st.altair_chart(chart.configure(background='#ffffff00').properties(width=650, height=330), use_container_width=False)
    with col2:
        st.info(get_text("qr_afternoon_chart_info"))

def get_qtd_treinamentos(df_rvt, mes, ano):
    divisoes = st.session_state.dados_carregados.get('divisoes')
    df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes, ano)
    treinamentos = 0
    tipo_treinamento = {'treinamento', 'treinamento cts','treinamento cliente', 'treinamento on-site', 'treinamento fabrica', 'treinamento outros'}
    tipo_treinamentos = defaultdict(int)
    indice = 0
    for motivo in df_filtrado['Motivo']:
        if(str(motivo).lower() == 'treinamento'):
            if(str(df_filtrado['Clientes'].iloc[indice]).lower() in divisoes['planta_ball']):
                tipo_treinamentos['treinamento fabrica'] +=1
            else:
                tipo_treinamentos['treinamento cliente'] +=1
            treinamentos +=1
        elif any(str(motivo).lower() in tipo.lower() for tipo in tipo_treinamento):
            tipo_treinamentos[motivo.lower()] += 1
            treinamentos += 1
        indice +=1
    col1, col2 = st.columns(2)
    col1.metric("Treinamentos", treinamentos)
    with col2:
        st.dataframe(tipo_treinamentos)

def get_qtd_quality(df_rvt, mes, ano):
    df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes, ano)
    quality = defaultdict(int)
    cidades = {}
    indice = 0
    for motivo in df_filtrado['Motivo']:
        if str(motivo).lower() == "quality review":
            div = categorizar_divisao(df_filtrado['Clientes'].iloc[indice]) #linha desse cliente
            if div == "planta_ball":
                if(df_filtrado['UnidadesBall'].iloc[indice] not in cidades):
                    cidades[df_filtrado['UnidadesBall'].iloc[indice]] = []
                quality[div] +=1
                cidades[df_filtrado['UnidadesBall'].iloc[indice]].append(df_filtrado['DataInicio'].iloc[indice].strftime('%d/%m/%Y'))
            else: quality[div] +=1
        indice +=1
    
    df_cidades_lista_datas = pd.DataFrame(list(cidades.items()), columns=['Plantas', 'Datas'])
    st.write(get_text("qr_plants_write"))
    st.dataframe(df_cidades_lista_datas)
    
    source = pd.DataFrame({
        "Categoria": quality.keys(),
        "Quantidade": quality.values()
    })

    total = source["Quantidade"].sum()

    base = alt.Chart(source).encode(
        theta=alt.Theta("Quantidade", stack=True)
    )

    donut = base.mark_arc(innerRadius=55, outerRadius=110).encode(
        color=alt.Color("Categoria:N", scale=alt.Scale(scheme='set1')), # Aplica as cores personalizadas
        order=alt.Order("Quantidade", sort="descending"), # Opcional: ordena as fatias
        tooltip=["Categoria", "Quantidade"] # Adiciona tooltip
    )

    text = base.mark_text(radius=130, fontSize=16, fontWeight='bold').encode(
        text=alt.Text("Quantidade"),
        order=alt.Order("Quantidade", sort="descending"),
        color=alt.value("black")
    )

    center_text_data = pd.DataFrame([{"text": f"Total: {total}"}])

    center_text = alt.Chart(center_text_data).mark_text(
        align='center',
        baseline='middle',
        fontSize=20, 
        fontWeight='bold',
        color='black' 
    ).encode(
        text=alt.Text("text")
    )

    chart = (donut + text + center_text).properties(
        title="Quality Reviews Cliente e Planta" 
    )

    col1, col2 = st.columns([3,1])
    with col1:
        st.altair_chart(chart.configure(background='#ffffff00').properties(width=650, height=330), use_container_width=False)
    with col2:
        st.info(get_text("qr_afternoon_chart_info"))

def get_incidentes_por_divisao(df_noc, mes, ano):
    divisoes = st.session_state.dados_carregados.get('divisoes')
    incidentes_anteriores = {}

    for mes_anteriores in range(1, mes+1):
        df_filtrado = filtrar_por_mes(df_noc, 'DataRecebimentoSAC', mes_anteriores, ano)
        indice = 0

        for div in divisoes.keys():
            if(div not in incidentes_anteriores):
                incidentes_anteriores[div] = {}
            if(dict_meses[mes_anteriores] not in incidentes_anteriores[div]):
                incidentes_anteriores[div][dict_meses[mes_anteriores]] = 0
        for cliente in df_filtrado['Clientes']:
            div = categorizar_divisao(cliente)
            if(df_filtrado['Status'].iloc[indice] != 'CANCELADA' and (pd.isna(cliente) == 0) and div != "outros"):
                incidentes_anteriores[div][dict_meses[mes_anteriores]] += 1
            indice += 1

    st.dataframe(incidentes_anteriores, column_order=[coluna for coluna in incidentes_anteriores.keys() if coluna != 'planta_ball' and coluna != 'outros']) #incidentes do mes atual
    col1, col2, col3 = st.columns(3)
    with col1:
        ka = st.selectbox("selecione um key account", options=[coluna for coluna in incidentes_anteriores.keys() if coluna != 'planta_ball' and coluna != 'outros'])
        

    st.write(get_text("evaluate_incidents_write"))
    for mes_anteriores in range(1, mes+1):
        df_filtrado = filtrar_por_mes(df_noc, 'DataRecebimentoSAC', mes_anteriores, ano)
        
        clientes_permitidos = [str(cliente).lower() for cliente in divisoes[ka]]
    
        mascara_filtragem = df_filtrado['Clientes'].str.lower().isin(clientes_permitidos)

        st.write(f"Incidentes - {ka} - {mes_anteriores}/{ano}")
        df_filtrado_2 = df_filtrado[mascara_filtragem]
        df_filtrado_3 = df_filtrado_2[df_filtrado_2["Status"] != "CANCELADA"]
        
        st.dataframe(df_filtrado_3)

    source = incidentes_anteriores[ka]
    df_source = pd.DataFrame(list(source.items()), columns=['Mês', 'Incidentes'])

    month_order_map = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
    }
    df_source['MonthOrder'] = df_source['Mês'].map(month_order_map)
    df_source['Incidentes'] = df_source['Incidentes'].fillna(0)
    
    base_display = alt.Chart(df_source).encode(
        x=alt.X('Incidentes', title='Nº de Incidentes'),
        y=alt.Y('Mês', sort=alt.EncodingSortField(field="MonthOrder", op="min", order='ascending'), axis=alt.Axis(
            labelFontSize=14,
            titleFontSize=16,
            labelColor="#000000", 
            titleColor="#000000"  
        )),
        text='Incidentes'
    ).properties(
        width=290,
        height=260
    )
    
    chart_display = base_display.mark_bar(color="#1f77b4") + base_display.mark_text(align='left', dx=3, color='#000000', fontSize=14)

    base_download = alt.Chart(df_source).encode(
        x=alt.X('Incidentes'),
        y=alt.Y('Mês', sort=alt.EncodingSortField(field="MonthOrder", op="min", order='ascending'), axis=alt.Axis(
            labelFontSize=14,  
            titleFontSize=16,  
            labelColor="#ffffff"    
        )), 
        text='Incidentes'
    ).properties(
        width=290, 
        height=260       
    )

    chart_for_download = base_download.mark_bar(color="#fefefe") + base_download.mark_text(align='left', dx=2, color='#ffffff', fontSize=14)
    chart_for_download = chart_for_download.configure(background='#ffffff00')
    png_buffer = io.BytesIO()
    chart_for_download.save(png_buffer, format='png')

    with col1:
        st.download_button(
            label="⬇️ Baixar Gráfico (PNG)",
            data=png_buffer.getvalue(),
            file_name=f"grafico_incidentes_{ka}.png",
            mime="image/png"
        )
    
    with col2:
        cl1, cl2, cl3 = st.columns([0.5,3,1])
        with cl2:
            st.altair_chart(chart_display.configure(background='#ffffff00'), use_container_width=False)
    with col3:
        st.info(get_text("qr_slide_chart_info"))
        st.info(get_text("filter_info"))

def get_tempo_medio_primeiro_atendimento(df_noc, mes, ano): #parametro julia atendimento
    df_filtrado = filtrar_por_mes(df_noc, 'DataRecebimentoSAC', mes, ano)
    tempos = []
    for _, row in df_filtrado.iterrows():
        try:
            receb = pd.to_datetime(row['DataRecebimentoSAC'])
            abertura = pd.to_datetime(row['DataCriacao'], dayfirst=True)
            if pd.notna(receb) and pd.notna(abertura):
                tempos.append(abs((abertura - receb).days))
                
        except:
            continue
    # st.write(tempos)
    st.write(round(sum(tempos) / len(tempos), 2) if tempos else 0)

def get_time_for_each_level(mes, ano, db, df_noc, coluna_data, tipo_retorno, tempo_resposta_niveis):
    
    df_filtrado = filtrar_por_mes(db, coluna_data, mes, ano)
    df_filtrado_can = df_filtrado[df_filtrado['Status'] != 'CANCELADA']
    indice = 0
    for data in df_filtrado[coluna_data]:
        if(df_filtrado['Status'].iloc[indice] != 'CANCELADA'):
            noc_na_data = df_filtrado['Numero NOC'].iloc[indice]
            if(noc_na_data):
                df_noc['Numero NOC'] = pd.to_numeric(df_noc['Numero NOC'], errors='coerce')
                noc_a_buscar = pd.to_numeric(noc_na_data, errors='coerce')
                df_filtro_noc = df_noc[df_noc['Numero NOC'] == noc_a_buscar]
                if not df_filtro_noc.empty:
                    data_sac = df_filtro_noc['DataRecebimentoSAC'].iloc[0]
                    data_sac = datetime.strptime(str(data_sac), '%d/%m/%Y').date()
                    formatos = ['%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', "%d/%m/%Y %H:%M:%S"]
                    for fmt in formatos:
                        try:
                            data = datetime.strptime(str(data), fmt).date()
                            break
                        except ValueError:
                            pass
                    
                    diferenca = data - data_sac
                    diferenca = diferenca.days
                    tempo_resposta_niveis[tipo_retorno]['acumulado'] += diferenca
                    tempo_resposta_niveis[tipo_retorno]['qtd'] += 1
                
                else:
                    if(str(noc_na_data) not in nocs_nao_cadastradas):
                        nocs_nao_cadastradas.append(str(noc_na_data))
                    
            indice += 1
    
def get_tipos_visitas_rvt_semestre(df_rvt, mes, ano):   
            if(mes==12): 
                init= 6

            elif(mes==6): 
                init=1
            
            lista_dados = []
            soma = {'preventiva':0, 'corretiva':0}
            for mes_anteriores in range(init, mes+1):
                df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes_anteriores, ano) #por que data início e não data de criação do RVT?
                dados_atuais = defaultdict(int)
                for tipo in df_filtrado['Tipo']:
                    dados_atuais['total'] += 1
                    if tipo == 'PREVENTIVA' or tipo == 'ATENDIMENTO REMOTO - PREVENTIVO':
                        dados_atuais['preventiva'] += 1
                        soma['preventiva'] += 1
                    else: 
                        dados_atuais['corretiva'] += 1
                        soma['corretiva'] += 1
                lista_dados.append(dados_atuais)

            # total de visitas, comparar com o semestre anterior
            mes_data = ["Jan", "Fev", "Mar", "Abr", "Maio", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
            dados_preparados = []
            for i, dados in enumerate(lista_dados):
                if(mes==12): 
                    i+=5
                dados_preparados.append({"Mês": f"{mes_data[i]}", "Tipo de Visita": "Corretiva", "Quantidade": dados["corretiva"]})
                dados_preparados.append({"Mês": f"{mes_data[i]}", "Tipo de Visita": "Preventiva", "Quantidade": dados["preventiva"]})

            df_grafico = pd.DataFrame(dados_preparados)

            df_grafico['Mês'] = pd.Categorical(df_grafico['Mês'], categories=mes_data, ordered=True)
            df_grafico = df_grafico.sort_values('Mês')

            st.subheader(f"Preventiva vs Corretiva no {int(mes/6)}º Semestre de {ano}")
            col1, col2, col3 = st.columns(3)
            with col1:
                base = alt.Chart(df_grafico).encode(
                x=alt.X('Mês'),
                y=alt.Y('Quantidade'),
                color=alt.Color('Tipo de Visita',
                                sort='descending',
                                scale=alt.Scale(range=['#90CAF9', '#1976D2']),
                                legend=alt.Legend(title="Tipo de Visita"))
                )
                bars = base.mark_bar().encode(
                    order=alt.Order('Tipo de Visita', sort='ascending')
                )

                text = alt.Chart(df_grafico).mark_text(
                    align='center',
                    baseline='bottom', 
                    dy=-7,
                    color='black'
                ).encode(
                    x=alt.X('Mês'),
                    y=alt.Y('sum(Quantidade):Q', title="Quantidade"),   
                    text=alt.Text('sum(Quantidade)', format='.0f')
                )

 
                chart = (bars + text).properties(
                    width=450,
                    height=300
                )

                st.altair_chart(chart)
            
            if(mes==12): 
                init=1
                mes=6
            elif(mes==6): 
                init=6
                mes=12
                ano = ano-1
            
            lista_dados_anteriores = []
            soma_anteriores = {'preventiva':0, 'corretiva':0}
            for mes_anteriores in range(init, mes+1):
                df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes_anteriores, ano) 
                dados_anteriores = defaultdict(int)
                for tipo in df_filtrado['Tipo']:
                    dados_anteriores['total'] += 1
                    if tipo == 'PREVENTIVA' or tipo == 'ATENDIMENTO REMOTO - PREVENTIVO':
                        dados_anteriores['preventiva'] += 1
                        soma_anteriores['preventiva'] += 1
                    else: 
                        dados_anteriores['corretiva'] += 1
                        soma_anteriores['corretiva'] += 1
                lista_dados_anteriores.append(dados_anteriores)
            
            
            col2.metric("Total de Visitas Preventivas", soma['preventiva'], f"{round((soma['preventiva']*100/soma_anteriores['preventiva'])-100,2) if soma_anteriores['preventiva'] else 0}% (anterior: {soma_anteriores['preventiva']})")
            col3.metric("Total de Visitas Corretivas", soma['corretiva'], f"{round((soma['corretiva']*100/soma_anteriores['corretiva'])-100,2) if soma_anteriores['corretiva'] else 0}% (anterior: {soma_anteriores['corretiva']})", "inverse")
            
def get_rvt_by_person_semestre(df_rvt, mes, ano):
    df_time = st.session_state.dados_carregados.get('df_time')
    if(mes==12): 
        init= 6
    elif(mes==6): 
        init=1
    mes_data = ["Jan", "Fev", "Mar", "Abr", "Maio", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    
    dados_atuais = defaultdict(int)
    for mes_anteriores in range(init, mes+1):
        df_filtrado_mes = filtrar_por_mes(df_rvt, 'DataInicio', mes_anteriores, ano) #por que data início e não data de criação do RVT?
        indice = 0
        # st.write(mes_data[mes_anteriores-1])
        # st.dataframe(df_filtrado_mes)
        for responsavel in df_filtrado_mes['ResponsavelBall']:
            if responsavel != os.getenv("nome_ignorado1") and responsavel != os.getenv("nome_ignorado2"):
                dados_atuais[responsavel] += 1
            indice +=1

    source = dados_atuais
    df_source = pd.DataFrame(list(source.items()), columns=['Nome', 'QTD RVT'])

    df_anonimo = df_source.copy()
    role_mapping = {}
    for index, linha in df_time.iterrows():
        chave = linha['NomeSalesforce']
        role_mapping[chave] = linha['Divisão']
    

    # 2. Contadores para cada tipo de cargo
    counters = {
        'Supervisor': 1,
        'Especialista': 1,
        'Key Account': 1,
        'Analista': 1
    }
    
    new_names = []

    for name in df_anonimo['Nome']:
        role_type = role_mapping.get(name)

        if role_type:
            new_name = f"{role_type} {counters[role_type]}"
            new_names.append(new_name)
            counters[role_type] += 1
        else:
            new_names.append(name)

    df_anonimo['Nome'] = new_names

    col1, col2 = st.columns(2)
    base = alt.Chart(df_anonimo).encode(
        x=alt.X('QTD RVT:Q'),
        y=alt.Y('Nome', 
        axis=alt.Axis(
            labelFontSize=14,  
            titleFontSize=16,   
            labelLimit=500   
        )).sort('-x'), 
        text='QTD RVT'
    ).properties(
        width=800, 
        height=900,
        title=f"RVTs por pessoa no {int(mes/6)}º Semestre de {ano}"
    )

    chart_anonimo = base.mark_bar(color="#26a72c") + base.mark_text(align='left', dx=2, color="#090909", fontSize=14)

    base = alt.Chart(df_source).encode(
        x=alt.X('QTD RVT:Q'),
        y=alt.Y('Nome', 
        axis=alt.Axis(
            labelFontSize=14,  
            titleFontSize=16,   
            labelLimit=500   
        )).sort('-x'), 
        text='QTD RVT'
    ).properties(
        width=800, 
        height=900,
        title=f"RVTs por pessoa no {int(mes/6)}º Semestre de {ano}"
    )

    chart_source = base.mark_bar(color="#26a72c") + base.mark_text(align='left', dx=2, color="#090909", fontSize=14)

    with col1:
        st.altair_chart(chart_anonimo.configure(background="#ffffffff"))
    with col2:
        st.altair_chart(chart_source.configure(background="#ffffffff"))

def get_qr_cliente_ball_semestre(df_rvt, mes, ano):   
    if(mes==12): 
        init= 6

    elif(mes==6): 
        init=1
    
    lista_dados = []
    soma = {'ball':0, 'cliente':0}
    for mes_anteriores in range(init, mes+1):
        df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes_anteriores, ano) #por que data início e não data de criação do RVT?
        dados_atuais = defaultdict(int)
        indice = 0
        for motivo in df_filtrado['Motivo']:
            if motivo == "QUALITY REVIEW":
                if "BALL" in df_filtrado['Clientes'].iloc[indice]:
                    dados_atuais['ball'] += 1
                    soma['ball'] += 1
                else: 
                    dados_atuais['cliente'] += 1
                    soma['cliente'] += 1
            indice += 1
        lista_dados.append(dados_atuais)

    # total de visitas, comparar com o semestre anterior
    mes_data = ["Jan", "Fev", "Mar", "Abr", "Maio", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    dados_preparados = []
    for i, dados in enumerate(lista_dados):
        if(mes==12): 
            i+=5
        dados_preparados.append({"Mês": f"{mes_data[i]}", "QR": "Ball", "Quantidade": dados["ball"]})
        dados_preparados.append({"Mês": f"{mes_data[i]}", "QR": "Cliente", "Quantidade": dados["cliente"]})

    df_grafico = pd.DataFrame(dados_preparados)

    df_grafico['Mês'] = pd.Categorical(df_grafico['Mês'], categories=mes_data, ordered=True)
    df_grafico = df_grafico.sort_values('Mês')

    st.subheader(f"QR em Cliente e Ball no {int(mes/6)}º Semestre de {ano}")
    col1, col2, col3 = st.columns(3)
    with col1:
        base = alt.Chart(df_grafico).encode(
        x=alt.X('Mês'),
        y=alt.Y('Quantidade'),
        color=alt.Color('QR',
                        sort='descending',
                        scale=alt.Scale(range=['#90CAF9', '#1976D2']),
                        legend=alt.Legend(title="QR"))
        )
        bars = base.mark_bar().encode(
            order=alt.Order('QR', sort='ascending')
        )

        text = base.mark_text(
            align='center',
            baseline='bottom',
            dy=-2,  
            color='black'
        ).encode(
            y=alt.Y('sum(Quantidade):Q', title="Quantidade"),  
            text=alt.Text('sum(Quantidade):Q', format='.0f'),
            color=alt.value('black') 
        )
        limit_df = pd.DataFrame({'limit_value': [13.0]})
        limit_line = alt.Chart(limit_df).mark_rule(
            color='red',
            strokeWidth=2,
            strokeDash=[5, 3] 
        ).encode(
            y='limit_value:Q'
        )

        chart = (bars + text + limit_line).properties(
            width=450,
            height=300
        )

        st.altair_chart(chart)
    
    col2.metric("Total de QR Ball", soma['ball'])
    col3.metric("Total de QR Cliente", soma['cliente'])
    
def get_qtd_treinamentos_semestre(df_rvt, mes, ano):
    divisoes = st.session_state.dados_carregados.get('divisoes')
    if(mes==12): 
        init= 6

    elif(mes==6): 
        init=1

    treinamentos = 0
    tipo_treinamento = {'treinamento', 'treinamento cts','treinamento cliente', 'treinamento on-site', 'treinamento fabrica', 'treinamento outros'}
    tipo_treinamentos = defaultdict(int)
    for mes_anteriores in range(init, mes+1):
        df_filtrado = filtrar_por_mes(df_rvt, 'DataInicio', mes_anteriores, ano) #por que data início e não data de criação do RVT?
        indice = 0
        for motivo in df_filtrado['Motivo']:
            if(str(motivo).lower() == 'treinamento'):
                if(str(df_filtrado['Clientes'].iloc[indice]).lower() in divisoes['planta_ball']):
                    tipo_treinamentos['treinamento fabrica'] +=1
                else:
                    tipo_treinamentos['treinamento cliente'] +=1
                treinamentos +=1
            elif(str(motivo).lower() in tipo_treinamento):
                tipo_treinamentos[str(motivo).lower()] += 1
                treinamentos += 1
            indice +=1 
    col1, col2 = st.columns(2)
    col1.metric("Treinamentos", treinamentos)
    with col2:
        st.dataframe(tipo_treinamentos)

def calcular_tempo(data_inicio, data_fim):
        """Calcula a diferença em dias. Retorna '-' se alguma data for inválida."""
        # pd.to_datetime lida com a conversão e com valores nulos (NaT)
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim, dayfirst=True)
        
        if pd.notna(data_inicio) and pd.notna(data_fim):
            return abs((data_fim - data_inicio).days)
        return "-"

def get_tempo_resposta(df_filtro):
    dfs_ressarceball = {
        "Ressarceball Argentina": st.session_state.dados_carregados.get('df_argentina'),
        "Ressarceball Paraguai": st.session_state.dados_carregados.get('df_paraguai'),
        "Ressarceball Chile": st.session_state.dados_carregados.get('df_chile'),
        "Ressarceball Ressarcimento Brasil": st.session_state.dados_carregados.get('df_r_brasil'),
        "Ressarceball Devolução Brasil": st.session_state.dados_carregados.get('df_d_brasil')
    }

    lista_tempo_resposta = []

    # .iterrows() permite acessar o índice e os dados de cada linha.
    for _, linha_sup in df_filtro.iterrows():
        noc = linha_sup['Numero NOC']
        data_recebimento = linha_sup['DataRecebimentoSAC']
        encontrado = False

        # Procura a NOC em cada um dos DataFrames de "ressarceball"
        for local, df_local in dfs_ressarceball.items():
            df_filtro_noc = df_local[df_local['Numero NOC'] == noc]

            if not df_filtro_noc.empty:
                # se houver mais de uma correspondência, pega a linha com o maior 'Id'.
                linha_maior_id = df_filtro_noc.loc[df_filtro_noc['ID'].idxmax()]

                # st.dataframe(df_filtro_noc)

                data_final = linha_maior_id['StatusFinal']
                tempo = calcular_tempo(data_recebimento, data_final)
                if(tempo != "-"):
                    lista_tempo_resposta.append({
                        "Numero NOC": noc,
                        "Local": "Concluída",
                        "Tempo de Resposta (dias)": tempo
                    })
                else:
                    lista_tempo_resposta.append({
                        "Numero NOC": noc,
                        "Local": local,
                        "Tempo de Resposta (dias)": tempo
                    })
                
                encontrado = True
                break  

        # Se, após procurar em todos os DFs, a NOC não foi encontrada
        if not encontrado:
            data_final = linha_sup['DataAprovacao']
            tempo = calcular_tempo(data_recebimento, data_final)
            if(tempo != "-"):
                lista_tempo_resposta.append({
                    "Numero NOC": noc,
                    "Local": "Concluída",
                    "Tempo de Resposta (dias)": tempo
                })
            else:
                lista_tempo_resposta.append({
                    "Numero NOC": noc,
                    "Local": "Salesforce - esperando aprovação",
                    "Tempo de Resposta (dias)": tempo
                })

    # Cria o DataFrame final a partir da lista de dicionários.
    df_nocs_tempo_resposta = pd.DataFrame(
        lista_tempo_resposta,
        columns=["Numero NOC", "Local", "Tempo de Resposta (dias)"]
    )

    # Exibe o DataFrame final e consolidado
    st.info(get_text("ressarceball_time_info"))
    st.dataframe(df_nocs_tempo_resposta, hide_index=True)

    tempos = pd.to_numeric(df_nocs_tempo_resposta['Tempo de Resposta (dias)'], errors='coerce')
    media_dias = round(tempos.mean(), 1)

    if(media_dias > 0): st.metric("Média de Dias", media_dias)

def get_mapa():
    divisoes_pesquisa = {}
    complaints_data = divisoes_pesquisa
    # Botão para limpar o estado e recomeçar o processo
    # if st.sidebar.button("🧹 Limpar Cache e Recomeçar"):
    #     st.session_state.geocoded_df = pd.DataFrame(columns=["City", "Complaints", "lat", "lon", "Full Address"])
    #     st.session_state.ambiguous_city = None
    #     st.session_state.processed_cities = []
    #     st.rerun()

    # --- 2. Preparação dos Dados de Entrada ---
    # Limpa e agrega os dados: soma contagens para cidades com o mesmo nome (ignorando maiúsculas/minúsculas)
    aggregated_data = {}
    for city, count in complaints_data.items():
        if isinstance(city, str) and city.lower() != 'nan':
            # Normaliza o nome da cidade (primeira letra maiúscula)
            cleaned_city = city.strip().title()
            aggregated_data[cleaned_city] = aggregated_data.get(cleaned_city, 0) + count


    # --- 3. Processo de Geocodificação (Controlado por Estado) ---
    st.header("1. Geocodificação das Cidades")

    # Se uma cidade ambígua está aguardando resolução, mostre as opções
    if st.session_state.ambiguous_city:
        amb_info = st.session_state.ambiguous_city
        st.warning(f"⚠️ A cidade '{amb_info['name']}' tem múltiplos resultados. Por favor, escolha o correto:")
        
        # Formata as opções para serem mais legíveis no selectbox
        location_options = [loc.address for loc in amb_info['options']]
        
        selected_address = st.selectbox(
            f"Opções para {amb_info['name']}",
            options=location_options,
            index=0,
            key=f"select_{amb_info['name']}"
        )

        if st.button("Confirmar e Continuar", key="confirm_button"):
            # Encontra o objeto location completo correspondente à seleção
            selected_location = next((loc for loc in amb_info['options'] if loc.address == selected_address), None)
            
            if selected_location:
                new_row = {
                    "City": amb_info['name'],
                    "Complaints": amb_info['complaints'],
                    "lat": selected_location.latitude,
                    "lon": selected_location.longitude,
                    "Full Address": selected_location.address
                }
                # Adiciona a nova linha ao DataFrame no session_state
                st.session_state.geocoded_df = pd.concat(
                    [st.session_state.geocoded_df, pd.DataFrame([new_row])], 
                    ignore_index=True
                )
            
            # Limpa o estado de ambiguidade e reinicia o script para continuar o loop
            st.session_state.ambiguous_city = None
            st.rerun()

    # Se não houver cidade ambígua, continue o processo de geocodificação
    else:
        if not aggregated_data:
            st.warning("Sem dados válidos para geocodificar.")
        else:
            # Inicializa o geolocator
            geolocator = Nominatim(user_agent=f"brazil_mapper_app_{time.time()}")
            geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, error_wait_seconds=5)

            total_cities_to_process = len([c for c in aggregated_data if c not in st.session_state.processed_cities])
            if total_cities_to_process > 0:
                progress_bar = st.progress(0, text="Iniciando geocodificação...")
                status_text = st.empty()
                
                processed_count = 0
                for city, complaints in aggregated_data.items():
                    # Pula cidades que já foram processadas nesta sessão
                    if city in st.session_state.processed_cities:
                        continue

                    try:
                        status_text.info(f"Procurando: '{city}'...")
                        st.session_state.processed_cities.append(city) # Marca como tentada
                        
                        locations = geocode(query={'city': city}, exactly_one=False, limit=5, timeout=10)

                        if not locations:
                            status_text.warning(f"❌ Não foi possível encontrar a cidade: '{city}'.")
                        
                        elif len(locations) > 1:
                            status_text.warning(f"Ambiguidade encontrada para '{city}'. Aguardando sua seleção...")
                            st.session_state.ambiguous_city = {'name': city, 'complaints': complaints, 'options': locations}
                            st.rerun() # Reinicia para mostrar o selectbox

                        else: # Exatamente um resultado encontrado
                            location = locations[0]
                            new_row = {
                                "City": city,
                                "Complaints": complaints,
                                "lat": location.latitude,
                                "lon": location.longitude,
                                "Full Address": location.address
                            }
                            st.session_state.geocoded_df = pd.concat(
                                [st.session_state.geocoded_df, pd.DataFrame([new_row])], 
                                ignore_index=True
                            )
                            status_text.success(f"✔️ {city} encontrada!")

                    except Exception as e:
                        st.error(f"Erro ao processar '{city}': {e}")
                    
                    finally:
                        processed_count += 1
                        progress_text = f"Processando... {processed_count}/{total_cities_to_process}"
                        progress_bar.progress(processed_count / total_cities_to_process, text=progress_text)
                        time.sleep(1) # Respeita o RateLimiter

                status_text.success("Geocodificação concluída!")
            else:
                st.info("Todas as cidades já foram processadas.")


    # --- 4. Exibição dos Resultados e do Mapa ---
    df_final = st.session_state.geocoded_df

    if not df_final.empty:
        st.header("2. Resultados da Geocodificação")
        st.dataframe(df_final)

        st.header("3. Mapa de Reclamações")
        fig = px.scatter_mapbox(
            df_final,
            lat="lat",
            lon="lon",
            color="Complaints",
            size="Complaints",
            hover_name="City",
            hover_data={"Complaints": True, "Full Address": True, "lat": False, "lon": False},
            color_continuous_scale=px.colors.sequential.Plasma_r,
            size_max=30,
            zoom=3.5,
            center={"lat": -14.2350, "lon": -51.9253},
            title="Número de Reclamações por Localização"
        )

        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando dados geocodificados para gerar o mapa.")

def menu_mensal():
        st.write("Selecione o mês e ano desejado:")
        periodo = []
        col1, col2 = st.columns(2)
        with col1:
            mes = st.number_input("Insira o mês (número)",min_value=1, max_value=12, step=1)
            periodo.append(mes)
        with col2:
            ano = st.number_input("Insira o ano",min_value=2023, step=1)
            periodo.append(ano)
        
        return periodo
