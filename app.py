import pandas as pd
import streamlit as st
import altair as alt
from streamlit_option_menu import option_menu
from st_click_detector import click_detector
from dotenv import load_dotenv
import os
import json


load_dotenv()

from service.functions import menu_mensal, filtrar_por_mes, filtrar_por_ytd, get_incidentes_por_divisao, get_qr_cliente_ball_semestre, get_qtd_quality, get_qtd_treinamentos, get_qtd_treinamentos_semestre, get_rvt_by_person_semestre, get_tempo_medio_primeiro_atendimento, get_tempo_resposta, get_time_for_each_level, get_tipos_visitas_rvt, get_tipos_visitas_rvt_semestre, get_visitas_por_divisao, get_mapa, nocs_nao_cadastradas, load_translation, get_text, get_flow, get_tempo_rvt, get_incidentes_nps
from service.connections import processar_arquivos_carregados


def check_password():
    with st.form("password_form"):
        password = st.text_input(get_text("password_label"), type="password")
        submitted = st.form_submit_button(get_text("enter_button"))

        if submitted and password == os.getenv("APP_PASSWORD_G"):
            st.session_state["password_correct_g"] = True
            st.rerun()
        elif submitted and password == os.getenv("APP_PASSWORD_C"):
            st.session_state["password_correct_c"] = True
            st.rerun()
        elif submitted:
            st.session_state["password_correct_g"] = False
            st.session_state["password_correct_c"] = False
            st.error(get_text("wrong_password_error"))

if st.session_state.get("password_correct_g", False):
    login_inicio_g = 1
    login_inicio_c = 0

elif st.session_state.get("password_correct_c", False):
    login_inicio_c = 1
    login_inicio_g = 0

else:
    login_inicio_g = 0
    login_inicio_c = 0
    st.set_page_config(
        page_title="Quality Review",
        page_icon="📚", 
        layout='centered'
    )
    st.title(get_text("login_title"))
    st.warning(get_text("login_warning"))
    check_password()

if(login_inicio_c or login_inicio_g):
    st.set_page_config(
        page_title="Quality Review",
        page_icon="📚",
        layout="wide" 
    )

    if 'dados_carregados' not in st.session_state:
        st.header("1. Carregar Arquivos")
        
        uploaded_files = st.file_uploader(
            "Navegue até a pasta \\16 - SERVIÇO AO CLIENTE\\32. Conexoes, e selecione todos os arquivos",
            type=['xlsx'],
            accept_multiple_files=True
        )
        
        if uploaded_files and len(uploaded_files) == 4:
            dados = processar_arquivos_carregados(uploaded_files)
            
            if dados:
                st.session_state.dados_carregados = dados
                st.success("Arquivos carregados e processados com sucesso!")
                st.rerun() 

    if 'dados_carregados' in st.session_state:
        
        df_noc = st.session_state.dados_carregados.get('df_noc')
        df_rvt = st.session_state.dados_carregados.get('df_rvt')
        df_consulta = st.session_state.dados_carregados.get('df_consulta')
        df_d_brasil = st.session_state.dados_carregados.get('df_d_brasil')
        df_r_brasil = st.session_state.dados_carregados.get('df_r_brasil')
        df_argentina = st.session_state.dados_carregados.get('df_argentina')
        df_chile = st.session_state.dados_carregados.get('df_chile')
        df_paraguai = st.session_state.dados_carregados.get('df_paraguai')
        df_time = st.session_state.dados_carregados.get('df_time')
        divisoes = st.session_state.dados_carregados.get('divisoes')
        df_cop = st.session_state.dados_carregados.get('df_cop')
        df_riscos = st.session_state.dados_carregados.get('riscos')
        df_melhorias = st.session_state.dados_carregados.get('melhorias') 
       
        divisoes_pesquisa = {}
        
        dfs_ressarceball = {
            "Ressarceball Argentina": st.session_state.dados_carregados.get('df_argentina'),
            "Ressarceball Paraguai": st.session_state.dados_carregados.get('df_paraguai'),
            "Ressarceball Chile": st.session_state.dados_carregados.get('df_chile'),
            "Ressarceball Ressarcimento Brasil": st.session_state.dados_carregados.get('df_r_brasil'),
            "Ressarceball Devolução Brasil": st.session_state.dados_carregados.get('df_d_brasil')
        }

        dfs_salesforce = {
            "NOCs Salesforce": st.session_state.dados_carregados.get('df_noc'),
            "RVTs Salesforce": st.session_state.dados_carregados.get('df_rvt')
        }

        with st.sidebar:
            st.header("Configurações")
            
            is_spanish = st.toggle(
                "Idioma: 🇧🇷 / 🇪🇸", 
                help="Alterne para mudar o idioma. Desligado = Português, Ligado = Español"
            )
            
            if is_spanish:
                st.session_state.language = "es"
            else:
                st.session_state.language = "pt"

        st.title(get_text("main_title"))
        st.write(get_text("app_intro"))

        logo = str(os.getenv("logo"))
        st.logo(logo)

        if(login_inicio_g):
            with st.sidebar:
                menu_options_g = [
                    get_text("salesforce_section_title"), 
                    get_text("ressarceball_section_title"), 
                    get_text("noc_rvt_relation_section_title"), 
                    get_text("search_noc_section_title"),
                    get_text("search_rvt_section_title"), 
                    get_text("rvt_time"),
                    get_text("response_time"),
                    get_text("riscos_melhorias"),
                    get_text("NPS"),
                    
                    get_text("where_weve_been_section_title"),  
                    get_text("cts_managers_section_title"), 
                    get_text("chat_section_title")
                ]
                selecao_side_bar = option_menu(get_text("sidebar_menu_title"), menu_options_g, 
                    icons=['cloud', 'coin', 'search', 'search', 'search', 'clock', 'clock', 'hammer', 'person', 'person', 'map', 'eye', 'chat'], menu_icon="cast", default_index=0,
                    styles={"nav-link-selected": {"background-color": "#093DC1"}})
        
        elif (login_inicio_c):
            with st.sidebar:
                menu_options_c = [
                    get_text("salesforce_section_title"), 
                    get_text("ressarceball_section_title"), 
                    get_text("noc_rvt_relation_section_title"), 
                    get_text("search_noc_section_title"), 
                    get_text("search_rvt_section_title"),
                    get_text("rvt_time"),
                    get_text("response_time"),
                    get_text("riscos_melhorias"), 
                    get_text("NPS"),
                    
                    get_text("where_weve_been_section_title"), 
                    get_text("chat_section_title")
                ]
                selecao_side_bar = option_menu(get_text("sidebar_menu_title"), menu_options_c, 
                    icons=['cloud', 'coin', 'search', 'search', 'search', 'clock', 'clock', 'hammer', 'person', 'person', 'map', 'chat'], menu_icon="cast", default_index=0,
                    styles={"nav-link-selected": {"background-color": "#093DC1"}})
                
        if selecao_side_bar == get_text("salesforce_section_title"):
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]

            with st.container(border=True):
                st.subheader(get_text("rvt_classification_subheader", mes=mes, ano=ano))
                get_visitas_por_divisao(df_rvt, mes, ano)

            with st.container(border=True):
                st.subheader(get_text("preventive_corrective_subheader", mes=mes, ano=ano))
                get_tipos_visitas_rvt(df_rvt, mes, ano)
            
            with st.container(border=True):
                st.subheader(get_text("training_subheader", mes=mes, ano=ano))
                get_qtd_treinamentos(df_rvt, mes, ano)

            with st.container(border=True):
                st.subheader(get_text("quality_reviews_subheader", mes=mes, ano=ano))
                get_qtd_quality(df_rvt, mes, ano)

            with st.container(border=True):
                st.subheader(get_text("incidents_subheader", mes=mes, ano=ano))
                get_incidentes_por_divisao(df_noc, mes, ano)

            # with st.container(border=True):
            #     st.subheader(f"Tempo médio de primeiro atendimento em dias -{mes}/{ano}")
            #     col1, col2 = st.columns(2)
            #     with col1:
            #         get_tempo_medio_primeiro_atendimento(df_noc, mes, ano)
            #     with col2:
            #         st.info("A Data de Recebimento SAC não contém a hora exata de recebimento, apenas o dia, então existe uma margem de erro neste tempo")
            
        elif selecao_side_bar == get_text("ressarceball_section_title"):
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]
            
            # investigação, devolução, bonificação, carta de crédito
            st.subheader(get_text("ressarceball_title"))
            if(nocs_nao_cadastradas): st.info(get_text("nocs_not_registered_info", nocs_nao_cadastradas=nocs_nao_cadastradas))
            tempo_resposta_niveis_br = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}

            get_time_for_each_level(mes, ano, df_r_brasil, df_noc, 'Data da Ultima Modificação - Ressarcimento - Tipo de Ressarcimento', 'Investigação', tempo_resposta_niveis_br)
            get_time_for_each_level(mes, ano, df_r_brasil, df_noc, 'Data da Ultima Modificação - Bonificações Alocadas', 'Bonificação', tempo_resposta_niveis_br)
            get_time_for_each_level(mes, ano, df_r_brasil, df_noc, 'Emissão Gerente CTS em', 'Carta de Crédito', tempo_resposta_niveis_br)

            get_time_for_each_level(mes, ano, df_d_brasil, df_noc, 'Data de Ultima Modificação - Solicitação de Devolução', 'Investigação', tempo_resposta_niveis_br)
            get_time_for_each_level(mes, ano, df_d_brasil, df_noc, 'Data de Ultima Modificação - Aprovação dos Registros', 'Devolução', tempo_resposta_niveis_br)

            # st.write("RessarceBall Brasil")

            tempo_resposta_niveis_arg = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}

            get_time_for_each_level(mes, ano, df_argentina, df_noc, 'DataCriacao', 'Investigação', tempo_resposta_niveis_arg)
            get_time_for_each_level(mes, ano, df_argentina, df_noc, 'DataFinal - Devolução', 'Devolução', tempo_resposta_niveis_arg) 
            get_time_for_each_level(mes, ano, df_argentina, df_noc, 'DataFinal - Ressarcimento', 'Carta de Crédito', tempo_resposta_niveis_arg)

            tempo_resposta_niveis_chi = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}

            get_time_for_each_level(mes, ano, df_chile, df_noc, 'DataCriacao', 'Investigação', tempo_resposta_niveis_chi)
            get_time_for_each_level(mes, ano, df_chile, df_noc, 'DataFinal - Devolução', 'Devolução', tempo_resposta_niveis_chi) 
            get_time_for_each_level(mes, ano, df_chile, df_noc, 'DataFinal - Ressarcimento', 'Carta de Crédito', tempo_resposta_niveis_chi) 

            tempo_resposta_niveis_py = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}

            get_time_for_each_level(mes, ano, df_paraguai, df_noc, 'Solicitación criada en', 'Investigação', tempo_resposta_niveis_py)
            get_time_for_each_level(mes, ano, df_paraguai, df_noc, 'DataFinal - Devolução', 'Devolução', tempo_resposta_niveis_py)
            get_time_for_each_level(mes, ano, df_paraguai, df_noc, 'DataFinal - Ressarcimento', 'Carta de Crédito', tempo_resposta_niveis_py)

            options = ["Brasil", "Paraguai", "Chile", "Argentina"]
            select_rb = st.segmented_control(
                "País RessarceBall", options, selection_mode="multi"
            )

            resultados = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}
            retorno = ['Investigação', 'Devolução', 'Bonificação', 'Carta de Crédito']

            for pais in select_rb:
                if(pais == "Brasil"): 
                    tempo_resposta = tempo_resposta_niveis_br
                elif(pais == "Argentina"): 
                    tempo_resposta = tempo_resposta_niveis_arg
                elif(pais == "Chile"): 
                    tempo_resposta = tempo_resposta_niveis_chi
                elif(pais == "Paraguai"): 
                    tempo_resposta = tempo_resposta_niveis_py
                
                for chave, item in tempo_resposta.items():
                    resultados[chave]['acumulado'] += tempo_resposta[chave]['acumulado']
                    resultados[chave]['qtd'] += tempo_resposta[chave]['qtd']  

            valores = []
            for chave in resultados.keys():
                if(resultados[chave]['qtd'] == 0): 
                    valores.append(0)
                else:
                    valores.append(round(resultados[chave]['acumulado']/resultados[chave]['qtd']))
        
            df_dados_grafico = pd.DataFrame({
                'tipo': retorno,
                'média de dias': valores
            })

            tipos = alt.Chart(df_dados_grafico).encode(
                x=alt.X('tipo', axis=alt.Axis(
                            labelFontSize=14,  
                            titleFontSize=16,  
                            labelColor="#000000"    
                        )),
                y=alt.Y('média de dias')
            )

            chart = tipos.mark_bar() + tipos.mark_text(align='center', baseline='bottom', dy=-5, color="#000000", fontSize=15, fontWeight='bold').encode(text=alt.Text('média de dias'))

            st.altair_chart(chart.properties(height=450, width=700), use_container_width=False)

            source = pd.DataFrame({
                "Categoria": retorno,
                "Quantidade": valores
            })

            total_media = sum(valores)/len(valores) if valores else 0

            base = alt.Chart(source).encode(
                theta=alt.Theta("Quantidade", stack=True)
            )

            donut = base.mark_arc(innerRadius=55, outerRadius=120).encode(
                color=alt.Color("Categoria:N", scale=alt.Scale(scheme='set1')), 
                order=alt.Order("Quantidade", sort="descending"), 
                tooltip=["Categoria", "Quantidade"] 
            )

            text = base.mark_text(radius=130, fontSize=16, fontWeight='bold').encode(
                text=alt.Text("Quantidade"),
                order=alt.Order("Quantidade", sort="descending"),
                color=alt.value("black")
            )

            center_text_data = pd.DataFrame([{"text": f"Média: {round(total_media,1)}"}])

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
                title="Média de Conclusão por Etapa em Dias" 
            )

            st.altair_chart(chart.configure(background='#ffffff00').properties(width=600, height=330), use_container_width=False)

        elif selecao_side_bar == get_text("noc_rvt_relation_section_title"):
            st.subheader(get_text("noc_rvt_relation_subheader"))
            st.write(get_text("noc_rvt_relation_write"))

            st.dataframe(df_consulta)
            
            #buscar noc ou rvt na tabela de relação
            with st.container(border=True):
                options = ["NOC", "RVT"]
                select_rn = st.segmented_control(
                    get_text("search_relation_label"), options, selection_mode="single"
                )
                if(select_rn):
                    if select_rn == "NOC": 
                        buscaNOC = st.text_input(get_text("type_noc_number_label"), placeholder=get_text("noc_placeholder"))
                        if(buscaNOC):
                            linhas_noc = df_consulta.loc[df_consulta["Numero NOC"] == int(buscaNOC)]
                            if(linhas_noc.empty):
                                st.write(get_text("noc_has_no_rvt_write"))
                                #buscar na tabela de noc
                                linhas_noc = df_noc.loc[df_noc["Numero NOC"] == int(buscaNOC)]
                                if(linhas_noc.empty):
                                    st.write(get_text("noc_not_registered_write"))
                                else:
                                    st.dataframe(linhas_noc)
                            else:
                                st.write(get_text("noc_found_write"))
                                manter_col = ["NR (Relação NOC e RVT)", "Data Criação NR", "Numero NOC", "NOC.DataRecebimentoSAC", "NOC.DataCriacao", "Numero RVT", "Data Criação RVT"]
                                st.dataframe(linhas_noc.drop(columns=[col for col in df_consulta if col not in manter_col]))

                    else: 
                        buscaRVT = st.text_input(get_text("type_rvt_number_label"), placeholder=get_text("rvt_placeholder"))
                        if(buscaRVT):
                            linhas_rvt = df_consulta.loc[df_consulta["Numero RVT"] == buscaRVT]
                            if(linhas_rvt.empty):
                                st.write(get_text("rvt_has_no_noc_write"))
                                #buscar na tabela de noc
                                linhas_rvt = df_rvt.loc[df_rvt["Numero RVT"] == buscaRVT]
                                if(linhas_rvt.empty):
                                    st.write(get_text("rvt_not_registered_write"))
                                else:
                                    st.dataframe(linhas_rvt)
                            else:
                                st.write(get_text("rvt_found_write"))
                                manter_col = ["NR (Relação NOC e RVT)", "Data Criação NR", "Numero NOC", "NOC.DataRecebimentoSAC", "NOC.DataCriacao", "Numero RVT", "Data Criação RVT"]
                                st.dataframe(linhas_rvt.drop(columns=[col for col in df_consulta if col not in manter_col]))

        elif selecao_side_bar == get_text("search_noc_section_title"):
            with st.container(border=True):
                    st.subheader(get_text("search_noc_subheader"))
                    noc_pesquisada = st.text_input(get_text("noc_search_input_label"), placeholder=get_text("noc_search_input_placeholder"))
                    if(noc_pesquisada):
                        for local, df_local in dfs_ressarceball.items():
                            df_filtro_noc = df_local[df_local['Numero NOC'].astype(int) == int(noc_pesquisada)]

                            if not df_filtro_noc.empty:
                                st.write(local)
                                df_sorted = df_filtro_noc.sort_values(by='ID', ascending=False)
                                st.dataframe(df_sorted)
                                get_flow(local, int(noc_pesquisada), df_sorted.iloc[0])

                        for local, df_local in dfs_salesforce.items():
                            if local == 'NOCs Salesforce':
                                df_filtro_noc = df_local[df_local['Numero NOC'].astype(int) == int(noc_pesquisada)]
                            
                                if not df_filtro_noc.empty:
                                    st.write(local)
                                    st.dataframe(df_filtro_noc)

        elif selecao_side_bar == get_text("search_rvt_section_title"):
            buscaRVT = st.text_input(get_text("type_rvt_number_label"), placeholder=get_text("rvt_placeholder"))
            if(buscaRVT):
                linhas_rvt = df_rvt.loc[df_rvt["Numero RVT"] == buscaRVT]
                if(linhas_rvt.empty):
                    st.write(get_text("rvt_not_registered_write"))
                else:
                    st.dataframe(linhas_rvt)

        elif selecao_side_bar == get_text("rvt_time"):
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]
            df_time_filtrado = df_time[df_time['Divisão'] == 'Analista']
            df_time_filtrado_2 = df_time[df_time['Divisão'] == 'Supervisor']
            df_time_filtrado_3 =  pd.concat([df_time_filtrado, df_time_filtrado_2], axis=0)   

            nomes = list(set(df_time_filtrado_3['NomeSalesforce']))
            analista = st.selectbox("Selecione o Supervisor ou Analista:", options=nomes)
            df_rvt_filtrado_mes = filtrar_por_mes(df_rvt, "DataInicio", mes, ano)
            df_rvt_filtrado_tipo = df_rvt_filtrado_mes[df_rvt_filtrado_mes["Tipo"].astype(str).str.contains("CORRETIVA")]
            df_rvt_nome_analista = df_rvt_filtrado_tipo[df_rvt_filtrado_tipo['ResponsavelBall'] == analista]
            
            st.dataframe(df_rvt_nome_analista, hide_index=True)

            get_tempo_rvt(df_rvt_nome_analista)
            
        elif selecao_side_bar == get_text("response_time"):
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]
            tab1, tab2, tab3 = st.tabs(["📗Supervisores", "📘 Especialistas", "📙 Key Accounts"])
            with tab1:
                df_time_filtrado = df_time[df_time['Divisão'] == 'Supervisor']
                options = list(set(df_time_filtrado['RegiãoSupervisor']))
                
                selection = st.segmented_control(
                    "Supervisores", options, selection_mode='single'
                )
            
                df_filtrado = filtrar_por_mes(df_noc, 'DataRecebimentoSAC', mes, ano)
                df_filtrado_status = df_filtrado[df_filtrado['Status']!= 'CANCELADA']
                df_filtrado_status2 = df_filtrado_status[df_filtrado_status['Status']!='PREENCHIMENTO DE DADOS DA NOC']
                df_filtrado_tipo = df_filtrado_status2[df_filtrado_status2['Tipo de NOC'] == 'EXTERNA']
                df_filtrado_aprovacao = df_filtrado_tipo[df_filtrado_tipo["AprovacaoInvestigacao"] == "APROVADA"]
                

                if(selection):
                    df_selecao = df_time_filtrado[df_time_filtrado['RegiãoSupervisor'] == selection]
                    filtro_sup = str(df_selecao['FiltroSalesforce'].iloc[0])
                    nome = str(df_selecao['NomeSalesforce'].iloc[0])
                    imagem1 = str(df_selecao['ImagemPessoaDB'].iloc[0])
                    imagem2 = str(df_selecao['ImagemRegiaoDB'].iloc[0])
                    

                    with st.container(border=True):
                        col1, col2 = st.columns([0.2, 0.8], vertical_alignment="center")
                        with col1:
                            
                            cl1,cl2,cl3 = st.columns([1,3,1])
                            with cl2:
                                st.image(imagem1, nome)
                            
                            st.image(imagem2)
                        df_filtro_sup = df_filtrado_aprovacao[df_filtrado_aprovacao['Supervisores'] == filtro_sup] 
                        with col2:
                            st.info(get_text("month_info_text", mes=mes, ano=ano, nome=nome, role="supervisor"))
                            st.dataframe(df_filtro_sup)

                    with st.container(border=True):
                        st.subheader(get_text("response_time_subheader", mes=mes, ano=ano))
                        get_tempo_resposta(df_filtro_sup)

                    with st.container(border=True):
                        st.subheader(get_text("ytd_response_time_subheader"))
                        df_filtrado_ytd = filtrar_por_ytd(df_noc, 'DataRecebimentoSAC', mes, ano)
                        df_filtrado_status_ytd = df_filtrado_ytd[df_filtrado_ytd['Status']!= 'CANCELADA']
                        df_filtrado_status2_ytd = df_filtrado_status_ytd[df_filtrado_status_ytd['Status']!='PREENCHIMENTO DE DADOS DA NOC']
                        df_filtrado_tipo_ytd = df_filtrado_status2_ytd[df_filtrado_status2_ytd['Tipo de NOC'] == 'EXTERNA']
                        df_filtrado_aprovacao_ytd = df_filtrado_tipo_ytd[df_filtrado_tipo_ytd["AprovacaoInvestigacao"] == "APROVADA"]
                        df_filtro_sup_ytd = df_filtrado_aprovacao_ytd[df_filtrado_aprovacao_ytd['Supervisores'] == filtro_sup]
                        st.info(get_text("ytd_info_text", mes=mes, ano=ano, nome=nome, role="supervisor"))
                        st.dataframe(df_filtro_sup_ytd)
                        get_tempo_resposta(df_filtro_sup_ytd)                       
            with tab2:
                df_time_filtrado = df_time[df_time['Divisão'] == 'Especialista']
                options = list(set(df_time_filtrado['RegiãoEspecialista']))
                selection = st.segmented_control(
                    "Especialistas", options, selection_mode='single'
                )

                df_filtrado = filtrar_por_mes(df_noc, 'DataRecebimentoSAC', mes, ano)
                df_filtrado_status = df_filtrado[df_filtrado['Status']!= 'CANCELADA']
                df_filtrado_status2 = df_filtrado_status[df_filtrado_status['Status']!='PREENCHIMENTO DE DADOS DA NOC']
                df_filtrado_tipo = df_filtrado_status2[df_filtrado_status2['Tipo de NOC'] == 'EXTERNA']
                df_filtrado_aprovacao = df_filtrado_tipo[df_filtrado_tipo["AprovacaoInvestigacao"] == "APROVADA"]
                
                if(selection):
                    df_selecao = df_time_filtrado[df_time_filtrado['RegiãoEspecialista'] == selection]
                    filtro_sup = str(df_selecao['FiltroSalesforce'].iloc[0])
                    nome = str(df_selecao['NomeSalesforce'].iloc[0])
                    imagem1 = str(df_selecao['ImagemPessoaDB'].iloc[0])
                    imagem2 = str(df_selecao['ImagemRegiaoDB'].iloc[0])

                    with st.container(border=True):
                        col1, col2 = st.columns([0.2, 0.8], vertical_alignment="center")
                        with col1:
                            
                            cl1,cl2,cl3 = st.columns([1,3,1])
                            with cl2:
                                st.image(imagem1, nome)
                            
                            st.image(imagem2)
                        with col2:
                            st.info(get_text("month_info_text", mes=mes, ano=ano, nome=nome, role="especialista"))
                            df_filtro_sup = df_filtrado_aprovacao[df_filtrado_aprovacao['Supervisores'] == filtro_sup] 
                            st.dataframe(df_filtro_sup)

                    with st.container(border=True):
                        st.subheader(get_text("response_time_subheader", mes=mes, ano=ano))
                        get_tempo_resposta(df_filtro_sup)

                    with st.container(border=True):
                        st.subheader(get_text("ytd_response_time_subheader"))
                        df_filtrado_ytd = filtrar_por_ytd(df_noc, 'DataRecebimentoSAC', mes, ano)
                        df_filtrado_status_ytd = df_filtrado_ytd[df_filtrado_ytd['Status']!= 'CANCELADA']
                        df_filtrado_status2_ytd = df_filtrado_status_ytd[df_filtrado_status_ytd['Status']!='PREENCHIMENTO DE DADOS DA NOC']
                        df_filtrado_tipo_ytd = df_filtrado_status2_ytd[df_filtrado_status2_ytd['Tipo de NOC'] == 'EXTERNA']
                        df_filtrado_aprovacao_ytd = df_filtrado_tipo_ytd[df_filtrado_tipo_ytd["AprovacaoInvestigacao"] == "APROVADA"]
                        df_filtro_sup_ytd = df_filtrado_aprovacao_ytd[df_filtrado_aprovacao_ytd['Supervisores'] == filtro_sup]
                        st.info(get_text("ytd_info_text", mes=mes, ano=ano, nome=nome, role="especialista"))
                        st.dataframe(df_filtro_sup_ytd)
                        get_tempo_resposta(df_filtro_sup_ytd)
            with tab3:  
                options = [div for div in divisoes.keys() if div not in ['planta_ball','outros', 'argentina', 'chile', 'paraguai', 'bolivia', 'peru', 'copacker']]
                df_time_filtrado = df_time[df_time['Divisão'] == 'Key Account']
                selection = st.segmented_control(
                    "Key Accounts", options, selection_mode="single"
                )
                
                st.write(get_text("key_accounts_clients_write"))
                df_filtrado = filtrar_por_mes(df_noc, 'DataRecebimentoSAC', mes, ano)
                df_filtrado_status = df_filtrado[df_filtrado['Status']!= 'CANCELADA']
                df_filtrado_status2 = df_filtrado_status[df_filtrado_status['Status']!='PREENCHIMENTO DE DADOS DA NOC']
                df_filtrado_tipo = df_filtrado_status2[df_filtrado_status2['Tipo de NOC'] == 'EXTERNA']
                df_filtrado_aprovacao = df_filtrado_tipo[df_filtrado_tipo["AprovacaoInvestigacao"] == "APROVADA"]
                
                
                if(selection):
                    df_selecao = df_time_filtrado[df_time_filtrado['KA'] == selection]
                    # filtro_sup = str(df_selecao['FiltroSalesforce'].iloc[0])
                    nome = str(df_selecao['NomeSalesforce'].iloc[0])
                    imagem1 = str(df_selecao['ImagemPessoaDB'].iloc[0])
                    imagem2 = str(df_selecao['ImagemRegiaoDB'].iloc[0])
                    
                    with st.container(border=True):
                        col1, col2 = st.columns([0.2, 0.8], vertical_alignment="center")

                        with col1:
                            cl1,cl2,cl3 = st.columns([1,3,1])
                            with cl2:
                                st.image(imagem1, nome)
                            
                            st.image(imagem2)
                        #por cliente
                        lista_em_maiusculo = [cliente.upper() for cliente in divisoes[selection]]
                        df_filtro_ka = df_filtrado_aprovacao[df_filtrado_aprovacao['Clientes'].isin(lista_em_maiusculo)]
                        st.dataframe(df_filtro_ka.drop_duplicates(subset=['CodigoCliente']), column_order=["CodigoCliente", "Clientes", "Termo_pesquisa"])
                        with col2:
                            st.info(get_text("month_info_text", mes=mes, ano=ano, nome=nome, role="ka"))
                            st.dataframe(df_filtro_ka)
                    
                    with st.container(border=True):
                        st.subheader(f"Tempo de resposta - {mes}/{ano}")
                        get_tempo_resposta(df_filtro_ka)

                    with st.container(border=True):
                        st.subheader("Tempo de resposta - YTD")
                        df_filtrado_ytd = filtrar_por_ytd(df_noc, 'DataRecebimentoSAC', mes, ano)
                        df_filtrado_status_ytd = df_filtrado_ytd[df_filtrado_ytd['Status']!= 'CANCELADA']
                        df_filtrado_status2_ytd = df_filtrado_status_ytd[df_filtrado_status_ytd['Status']!='PREENCHIMENTO DE DADOS DA NOC']
                        df_filtrado_tipo_ytd = df_filtrado_status2_ytd[df_filtrado_status2_ytd['Tipo de NOC'] == 'EXTERNA']
                        df_filtrado_aprovacao_ytd = df_filtrado_tipo_ytd[df_filtrado_tipo_ytd["AprovacaoInvestigacao"] == "APROVADA"]
                        df_filtro_ka_ytd = df_filtrado_aprovacao_ytd[df_filtrado_aprovacao_ytd['Clientes'].isin(lista_em_maiusculo)]
                        st.info(get_text("ytd_info_text", mes=mes, ano=ano, nome=nome, role="ka"))
                        st.dataframe(df_filtro_ka_ytd)
                        st.dataframe(df_filtro_ka_ytd.drop_duplicates(subset=['CodigoCliente']), column_order=["CodigoCliente", "Clientes", "Termo_pesquisa"])    
                        get_tempo_resposta(df_filtro_ka_ytd)

        elif selecao_side_bar == get_text("riscos_melhorias"):
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]
            tab1, tab2 = st.tabs(["⛑️Riscos de Segurança", "🔨Oportunidades de Melhoria"])
            with tab1:
                df_filtrado_riscos = filtrar_por_mes(df_riscos, "DataCriacao", mes, ano)
                st.dataframe(df_filtrado_riscos, hide_index=True)
            with tab2:    
                df_filtrado_melhorias = filtrar_por_mes(df_melhorias, "DataCriacao", mes, ano)
                st.dataframe(df_filtrado_melhorias, hide_index=True)

        elif selecao_side_bar == get_text("NPS"):
            
            st.subheader("Perfil por Key Account")
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]

            #selecionar ka

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                with st.container(border=True):
                    st.write("Incidentes YTD")
                    get_incidentes_nps(df_noc, mes, ano)
            with col2:
                with st.container(border=True):
                    st.write("Latas e Tampas")
            with col3:
                with st.container(border=True):
                    st.write("Parecer")
            with col4:
                with st.container(border=True):
                    st.write("Tratativa Final")
            
            #devolucao ressarcimento e cartas de credito para latas e tampas

            cl1, cl2, cl3 = st.columns(3)
            with cl1:
                with st.container(border=True):
                    st.write("TOP 10 Defeitos")
            with cl2:
                with st.container(border=True):
                    st.write("Incidentes por Fabricante")
            with cl3:
                with st.container(border=True):
                    st.write("Número de Incidentes Abertos por Planta")
    
        elif selecao_side_bar == get_text("where_weve_been_section_title"):
            
            st.info(get_text("where_weve_been_info"))

            for linha in df_rvt["CidadeCliente"]:
                if pd.isna(linha):
                    continue
                if linha not in divisoes_pesquisa:
                    divisoes_pesquisa[linha] = 0
                divisoes_pesquisa[linha]+= 1

            # if 'geocoded_df' not in st.session_state:
            #     st.session_state.geocoded_df = pd.DataFrame(columns=["City", "Complaints", "lat", "lon", "Full Address"])

            # if 'ambiguous_city' not in st.session_state:
            #     st.session_state.ambiguous_city = None

            # if 'processed_cities' not in st.session_state:
            #     st.session_state.processed_cities = []
                
            # get_mapa(divisoes_pesquisa)
            visitas = str(os.getenv("visitas"))
            st.image(visitas)

        elif selecao_side_bar == get_text("cts_managers_section_title"):
            
            st.write(get_text("select_month_year_write"))
            periodo = menu_mensal()
            mes = periodo[0]
            ano = periodo[1]
            
            # with st.container(border=True):
            #     get_tipos_visitas_rvt_semestre(df_rvt, mes, ano)
            with st.container(border=True):
                get_rvt_by_person_semestre(df_rvt, mes, ano)
            # with st.container(border=True):
            #     get_qr_cliente_ball_semestre(df_rvt, mes, ano)
            # with st.container(border=True):
            #     get_qtd_treinamentos_semestre(df_rvt, mes, ano)
            # with st.container(border=True):
            #     st.subheader("RessarceBall")

            #     if(mes==12): 
            #         init= 7

            #     elif(mes==6): 
            #         init=1
                
            #     tempo_resposta_niveis_br = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}
            #     tempo_resposta_niveis_arg = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}
            #     tempo_resposta_niveis_chi = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}
            #     tempo_resposta_niveis_py = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}

            #     for mes_anteriores in range(init, mes+1):
            #         get_time_for_each_level(mes_anteriores, ano, df_r_brasil, df_noc, 'Data da Ultima Modificação - Ressarcimento - Tipo de Ressarcimento', 'Investigação', tempo_resposta_niveis_br)
            #         get_time_for_each_level(mes_anteriores, ano, df_r_brasil, df_noc, 'Data da Ultima Modificação - Bonificações Alocadas', 'Bonificação', tempo_resposta_niveis_br)
            #         get_time_for_each_level(mes_anteriores, ano, df_r_brasil, df_noc, 'Emissão Gerente CTS em', 'Carta de Crédito', tempo_resposta_niveis_br)

            #         get_time_for_each_level(mes_anteriores, ano, df_d_brasil, df_noc, 'Data de Ultima Modificação - Solicitação de Devolução', 'Investigação', tempo_resposta_niveis_br)
            #         get_time_for_each_level(mes_anteriores, ano, df_d_brasil, df_noc, 'Data de Ultima Modificação - Aprovação dos Registros', 'Devolução', tempo_resposta_niveis_br)


            #         get_time_for_each_level(mes_anteriores, ano, df_argentina, df_noc, 'DataCriacao', 'Investigação', tempo_resposta_niveis_arg)
            #         get_time_for_each_level(mes_anteriores, ano, df_argentina, df_noc, 'DataFinal - Devolução', 'Devolução', tempo_resposta_niveis_arg) 
            #         get_time_for_each_level(mes_anteriores, ano, df_argentina, df_noc, 'DataFinal - Ressarcimento', 'Carta de Crédito', tempo_resposta_niveis_arg)


            #         get_time_for_each_level(mes_anteriores, ano, df_chile, df_noc, 'DataCriacao', 'Investigação', tempo_resposta_niveis_chi)
            #         get_time_for_each_level(mes_anteriores, ano, df_chile, df_noc, 'DataFinal - Devolução', 'Devolução', tempo_resposta_niveis_chi) 
            #         get_time_for_each_level(mes_anteriores, ano, df_chile, df_noc, 'DataFinal - Ressarcimento', 'Carta de Crédito', tempo_resposta_niveis_chi) 


            #         get_time_for_each_level(mes_anteriores, ano, df_paraguai, df_noc, 'Solicitación criada en', 'Investigação', tempo_resposta_niveis_py)
            #         get_time_for_each_level(mes_anteriores, ano, df_paraguai, df_noc, 'DataFinal - Devolução', 'Devolução', tempo_resposta_niveis_py)
            #         get_time_for_each_level(mes_anteriores, ano, df_paraguai, df_noc, 'DataFinal - Ressarcimento', 'Carta de Crédito', tempo_resposta_niveis_py)

            #     options = ["Brasil", "Paraguai", "Chile", "Argentina"]
            #     select_rb_s = ""
            #     select_rb_s = st.segmented_control(
            #         "País RessarceBall", options, selection_mode="multi"
            #     )

            #     resultados = {'Investigação':{'acumulado':0, 'qtd':0}, 'Devolução': {'acumulado':0, 'qtd':0}, 'Bonificação': {'acumulado':0, 'qtd':0}, 'Carta de Crédito': {'acumulado':0, 'qtd':0}}
            #     retorno = ['Investigação', 'Devolução', 'Bonificação', 'Carta de Crédito']

            #     for pais in select_rb_s:
            #         if(pais == "Brasil"): 
            #             tempo_resposta = tempo_resposta_niveis_br
            #             st.write("dados Brasil")
            #             st.dataframe(tempo_resposta_niveis_br)
            #             # st.dataframe(df_d_brasil)
            #             # st.dataframe(df_r_brasil)
            #         elif(pais == "Argentina"): 
            #             tempo_resposta = tempo_resposta_niveis_arg
            #             st.write("dados Argentina")
            #             st.dataframe(tempo_resposta_niveis_arg)
            #             # st.dataframe(df_argentina)
            #         elif(pais == "Chile"): 
            #             tempo_resposta = tempo_resposta_niveis_chi
            #             st.write("dados Chile")
            #             st.dataframe(tempo_resposta_niveis_chi)
            #             # st.dataframe(df_chile)
            #         elif(pais == "Paraguai"): 
            #             tempo_resposta = tempo_resposta_niveis_py
            #             st.write("dados Paraguai")
            #             st.dataframe(tempo_resposta_niveis_py)
            #             # st.dataframe(df_paraguai)
            #         else:
            #             st.write("selecione um ou mais países")
            #         for chave, item in tempo_resposta.items():
            #             resultados[chave]['acumulado'] += tempo_resposta[chave]['acumulado']
            #             resultados[chave]['qtd'] += tempo_resposta[chave]['qtd']  

            #     valores = []
            #     for chave in resultados.keys():
            #         if(resultados[chave]['qtd'] == 0): 
            #             valores.append(0)
            #         else:
            #             valores.append(round(resultados[chave]['acumulado']/resultados[chave]['qtd']))
            
            #     df_dados_grafico = pd.DataFrame({
            #         'tipo': retorno,
            #         'média de dias': valores
            #     })

            #     tipos = alt.Chart(df_dados_grafico).encode(
            #         x=alt.X('tipo', axis=alt.Axis(
            #                     labelFontSize=14,  
            #                     titleFontSize=16,  
            #                     labelColor="#000000"    
            #                 )),
            #         y=alt.Y('média de dias')
            #     )

            #     chart = tipos.mark_bar() + tipos.mark_text(align='center', baseline='bottom', dy=-2, color="#000000", fontSize=15, fontWeight='bold').encode(text=alt.Text('média de dias') )

            #     st.altair_chart(chart.properties(height=450, width=700), use_container_width=False)

        elif selecao_side_bar == get_text("chat_section_title"):
            st.write("Em breve...")
            # latinha = str(os.getenv("latinha"))
            # st.image(image=latinha)
            

    else:
        st.warning(get_text("upload_warning"))

