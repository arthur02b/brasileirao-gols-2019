import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import streamlit as st

df = pd.read_csv('gols_brasileirao_2019.csv')

st.set_page_config(page_title='Gols Brasileirão 2019', layout='wide')
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

st.metric('Total de Gols', len(df_filtrado))

# Grafico 1 - Gols por faixa de minuto
st.subheader('Gols por Faixa de Minuto')

labels_graf = ['1-15', '16-30', '31-45', '45+', '46-60', '61-75', '76-90', '90+']
gols_faixa = df_filtrado['faixa_minuto'].value_counts().reindex(labels_graf, fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(gols_faixa.index, gols_faixa.values, color='#C8102E')
ax.bar_label(bars, color='#1A1A1A', fontweight='bold')
ax.set_xlabel('Faixa de Minuto')
ax.set_ylabel('Quantidade de Gols')
ax.set_title('Distribuicao de Gols por Faixa de Minuto', color='#1A1A1A', fontweight='bold')
ax.set_ylim(0, gols_faixa.values.max() * 1.15)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(axis='y', color='#DDDDDD')
ax.set_facecolor('#FAFAFA')
st.pyplot(fig)

# Grafico 2 - Gols por rodada
st.subheader('Gols por Rodada')

todas_rodadas = range(rodada_min, rodada_max + 1)
gols_rodada = df_filtrado.groupby('rodata').size().reindex(todas_rodadas, fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(gols_rodada.index, gols_rodada.values, marker='o', color='#1A1A1A',
        markerfacecolor='#C8102E', markeredgecolor='#C8102E', linewidth=2)
ax.set_xlabel('Rodada')
ax.set_ylabel('Quantidade de Gols')
ax.set_title('Evolucao de Gols por Rodada', color='#1A1A1A', fontweight='bold')
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(True, color='#DDDDDD')
ax.set_facecolor('#FAFAFA')
st.pyplot(fig)

# Grafico 3 - Tipo de gol
st.subheader('Tipo de Gol')

tipo_contagem = df_filtrado['tipo_de_gol'].value_counts()

def fmt_autopct(pct, valores):
    total = sum(valores)
    qtd = int(round(pct * total / 100.0))
    return f'{qtd}\n({pct:.1f}%)'

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(tipo_contagem.values, labels=tipo_contagem.index,
       autopct=lambda pct: fmt_autopct(pct, tipo_contagem.values),
       colors=['#C8102E', '#1A1A1A', '#BDBDBD'],
       textprops={'color': 'white', 'fontweight': 'bold'})
ax.set_title('Proporcao de Tipos de Gol', color='#1A1A1A', fontweight='bold')
st.pyplot(fig)

# Grafico 4 - Casa vs fora
st.subheader('Gols Casa e Fora')

casa_fora = df_filtrado['casa_ou_fora'].value_counts().reindex(['Casa', 'Fora'], fill_value=0)

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(casa_fora.index, casa_fora.values, color=['#C8102E', '#1A1A1A'])
ax.bar_label(bars, color='#1A1A1A', fontweight='bold')
ax.set_xlabel('Local')
ax.set_ylabel('Quantidade de Gols')
ax.set_title('Gols Marcados em Casa vs Fora', color='#1A1A1A', fontweight='bold')
ax.set_ylim(0, casa_fora.values.max() * 1.15)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(axis='y', color='#DDDDDD')
ax.set_facecolor('#FAFAFA')
st.pyplot(fig)

# Grafico 5 - Gols por mes
st.subheader('Gols por Mes')

meses_nome = {4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
              9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

todos_meses = range(4, 13)
gols_mes = df_filtrado['mes'].value_counts().reindex(todos_meses, fill_value=0).sort_index()
gols_mes.index = gols_mes.index.map(meses_nome)

fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(gols_mes.index, gols_mes.values, color='#C8102E')
ax.bar_label(bars, color='#1A1A1A', fontweight='bold')
ax.set_xlabel('Mes')
ax.set_ylabel('Quantidade de Gols')
ax.set_title('Gols Marcados por Mes do Campeonato', color='#1A1A1A', fontweight='bold')
ax.set_ylim(0, gols_mes.values.max() * 1.15)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(axis='y', color='#DDDDDD')
ax.set_facecolor('#FAFAFA')
st.pyplot(fig)