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

# Features
bins   = [0, 15, 30, 45, 50, 60, 75, 90, 999]
labels = ['1-15', '16-30', '31-45', '45+ (acresc)', '46-60', '61-75', '76-90', '90+ (acresc)']
df['faixa_minuto'] = pd.cut(df['minuto'], bins=bins, labels=labels)
df.loc[(df['minuto'] >= 90) & (df['acrescimo']), 'faixa_minuto'] = '90+ (acresc)'
df.loc[(df['minuto'] == 45) & (df['acrescimo']), 'faixa_minuto'] = '45+ (acresc)'
df['mes'] = df['data'].dt.month

st.sidebar.header('Filtros')

# times
times = sorted(df['clube'].unique())

time_selecionado = st.sidebar.selectbox('Time', ['Todos'] + times)

time_comparacao = st.sidebar.selectbox(
    'Comparar com (opcional)',
    ['Nenhum'] + [t for t in times if t != time_selecionado]
)

# marcador (só aplica se NÃO estiver comparando)
marcadores = sorted(df['atleta'].unique())
marcador_selecionado = st.sidebar.selectbox('Marcador', ['Todos'] + marcadores)

# rodada
rodada_min = int(df['rodata'].min())
rodada_max = int(df['rodata'].max())
rodada_range = st.sidebar.slider('Rodada', rodada_min, rodada_max, (rodada_min, rodada_max))

# Base filtrada por rodada
df_base = df[
    (df['rodata'] >= rodada_range[0]) &
    (df['rodata'] <= rodada_range[1])
]

# separação dos times
if time_selecionado != 'Todos':
    df_time1 = df_base[df_base['clube'] == time_selecionado]
else:
    df_time1 = df_base

if time_comparacao != 'Nenhum':
    df_time2 = df_base[df_base['clube'] == time_comparacao]
else:
    df_time2 = None

# regra B: marcador só vale quando NÃO há comparação
if df_time2 is None and marcador_selecionado != 'Todos':
    df_time1 = df_time1[df_time1['atleta'] == marcador_selecionado]

st.metric(
    'Total de Gols',
    len(df_time1) if df_time2 is None else len(df_time1) + len(df_time2)
)

# GRAFICO 1
st.subheader('Gols por Faixa de Minuto')

labels_graf = labels

g1 = df_time1['faixa_minuto'].value_counts().reindex(labels_graf, fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(g1.index, g1.values, color='#C8102E', label=time_selecionado)

if df_time2 is not None:
    g2 = df_time2['faixa_minuto'].value_counts().reindex(labels_graf, fill_value=0)
    ax.bar(g2.index, g2.values, color='#1A1A1A', alpha=0.7, label=time_comparacao)

ax.set_title('Distribuicao de Gols por Faixa de Minuto')
ax.set_xlabel('Faixa de Minuto')
ax.set_ylabel('Quantidade de Gols')
ax.legend()
ax.set_facecolor('#FAFAFA')
ax.grid(axis='y', color='#DDDDDD')
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
st.pyplot(fig)

st.caption("Mostra em quais períodos do jogo os gols acontecem com mais frequência, destacando início, meio e fim das partidas.")


# GRAFICO 2
st.subheader('Gols por Rodada')

rodadas = range(rodada_min, rodada_max + 1)

r1 = df_time1.groupby('rodata').size().reindex(rodadas, fill_value=0)

fig, ax = plt.subplots(figsize=(10, 4))

ax.plot(
    r1.index,
    r1.values,
    marker='o',
    color='#1A1A1A',
    markerfacecolor='#C8102E',
    markeredgecolor='#C8102E',
    linewidth=2,
    label=time_selecionado
)

if df_time2 is not None:
    r2 = df_time2.groupby('rodata').size().reindex(rodadas, fill_value=0)

    ax.plot(
        r2.index,
        r2.values,
        marker='o',
        color='#C8102E',
        markerfacecolor='#1A1A1A',
        markeredgecolor='#1A1A1A',
        linewidth=2,
        alpha=0.8,
        label=time_comparacao
    )

ax.set_xlabel('Rodada')
ax.set_ylabel('Quantidade de Gols')
ax.set_title('Evolucao de Gols por Rodada', color='#1A1A1A', fontweight='bold')

ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(True, color='#DDDDDD')
ax.set_facecolor('#FAFAFA')

ax.legend()
st.pyplot(fig)

st.caption("Mostra a evolução do desempenho ofensivo ao longo das rodadas do campeonato, permitindo identificar consistência ou oscilações.")


# GRAFICO 3
st.subheader('Tipo de Gol')

tipo_contagem = df_time1['tipo_de_gol'].value_counts()

def fmt_autopct(pct, valores):
    total = sum(valores)
    qtd = int(round(pct * total / 100.0))
    return f'{qtd}\n({pct:.1f}%)'

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(
    tipo_contagem.values,
    labels=tipo_contagem.index,
    autopct=lambda pct: fmt_autopct(pct, tipo_contagem.values),
    colors=['#C8102E', '#1A1A1A', '#BDBDBD'][:len(tipo_contagem)],
    textprops={'color': 'white', 'fontweight': 'bold'}
)

ax.legend(tipo_contagem.index, loc='center left', bbox_to_anchor=(1, 0.5))
ax.set_title('Proporcao de Tipos de Gol')
st.pyplot(fig)

st.caption("Apresenta a distribuição dos tipos de gols (normal, pênalti ou contra), mostrando padrões de finalização.")


# GRAFICO 4
st.subheader('Gols Casa e Fora')

c1 = df_time1['casa_ou_fora'].value_counts().reindex(['Casa','Fora'], fill_value=0)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(['Casa','Fora'], c1.values, color='#C8102E', label=time_selecionado)

if df_time2 is not None:
    c2 = df_time2['casa_ou_fora'].value_counts().reindex(['Casa','Fora'], fill_value=0)
    ax.bar(['Casa','Fora'], c2.values, color='#1A1A1A', alpha=0.7, label=time_comparacao)

ax.set_title('Gols Casa e Fora')
ax.set_ylabel('Quantidade de Gols')
ax.legend()
ax.grid(axis='y', color='#DDDDDD')
ax.set_facecolor('#FAFAFA')
st.pyplot(fig)

st.caption("Compara o desempenho ofensivo dentro e fora de casa, ajudando a identificar vantagem de mando de campo.")


# GRAFICO 5
st.subheader('Gols por Mes')

meses_nome = {4:'Abr',5:'Mai',6:'Jun',7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
meses = range(4, 13)

m1 = df_time1['mes'].value_counts().reindex(meses, fill_value=0).sort_index()
m1.index = m1.index.map(meses_nome)

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(m1.index, m1.values, color='#C8102E', label=time_selecionado)

if df_time2 is not None:
    m2 = df_time2['mes'].value_counts().reindex(meses, fill_value=0).sort_index()
    m2.index = m2.index.map(meses_nome)
    ax.bar(m2.index, m2.values, color='#1A1A1A', alpha=0.7, label=time_comparacao)

ax.set_title('Gols por Mes')
ax.set_xlabel('Mes')
ax.set_ylabel('Quantidade de Gols')
ax.legend()
ax.grid(axis='y', color='#DDDDDD')
ax.set_facecolor('#FAFAFA')
st.pyplot(fig)

st.caption("Mostra a evolução mensal dos gols ao longo do campeonato, destacando fases de maior ou menor desempenho.")