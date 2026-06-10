import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

df = pd.read_csv('gols_brasileirao_2019.csv')

st.set_page_config(page_title='Gols Brasileirao 2019', layout='wide')
st.title('Análise de Gols - Brasileirão Série A 2019')

# Limpeza
print('Nulos antes:', df.isnull().sum().sum())
print('Duplicatas:', df.duplicated().sum())
df = df.drop_duplicates()
df = df.drop(columns=['rodata_y'])
df = df.rename(columns={'rodata_x': 'rodata'})
df['tipo_de_gol'] = df['tipo_de_gol'].fillna('Normal')
df['acrescimo'] = df['minuto'].astype(str).str.contains(r'\+')
df['minuto'] = df['minuto'].astype(str).str.extract(r'(\d+)').astype(float)
df = df.dropna(subset=['minuto'])
df['minuto'] = df['minuto'].astype(int)
df['data'] = pd.to_datetime(df['data'], dayfirst=True)
print('Nulos depois:', df.isnull().sum().sum())

# Engenharia de features
bins   = [0, 15, 30, 45, 50, 60, 75, 90, 999]
labels = ['1-15', '16-30', '31-45', '45+', '46-60', '61-75', '76-90', '90+']
df['faixa_minuto'] = pd.cut(df['minuto'], bins=bins, labels=labels)
df.loc[(df['minuto'] >= 90) & (df['acrescimo']), 'faixa_minuto'] = '90+'
df.loc[(df['minuto'] == 45) & (df['acrescimo']), 'faixa_minuto'] = '45+'
df['periodo'] = df['minuto'].apply(lambda x: '1 Tempo' if x <= 45 else '2 Tempo')
df['gol_decisivo'] = df['minuto'] > 80
df['mes'] = df['data'].dt.month
df['gol_contra'] = df['tipo_de_gol'] == 'Gol Contra'

#sidebar
st.sidebar.header('Filtros')

times = sorted(df['clube'].unique())
time_selecionado = st.sidebar.selectbox('Time', ['Todos'] + times)

marcadores = sorted(df['atleta'].unique())
marcador_selecionado = st.sidebar.selectbox('Marcador', ['Todos'] + marcadores)

rodada_min = int(df['rodata'].min())
rodada_max = int(df['rodata'].max())
rodada_range = st.sidebar.slider('Rodada', rodada_min, rodada_max, (rodada_min, rodada_max))

# Aplicando filtros
df_filtrado = df.copy()

if time_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['clube'] == time_selecionado]

if marcador_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['atleta'] == marcador_selecionado]

df_filtrado = df_filtrado[
    (df_filtrado['rodata'] >= rodada_range[0]) &
    (df_filtrado['rodata'] <= rodada_range[1])
]

# Grafico 1 - Gols por faixa de minuto
st.subheader('Gols por Faixa de Minuto')

labels_graf = ['1-15', '16-30', '31-45', '45+', '46-60', '61-75', '76-90', '90+']
gols_faixa = df_filtrado['faixa_minuto'].value_counts().reindex(labels_graf)

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(gols_faixa.index, gols_faixa.values, color='green')
ax.set_xlabel('Faixa de Minuto')
ax.set_ylabel('Quantidade de Gols')
ax.set_title('Distribuicao de Gols por Faixa de Minuto')
ax.grid(axis='y')
st.pyplot(fig)
