📄 PARTE 1 — VISÃO GERAL DO SISTEMA
1. Nome do sistema

Plataforma de Monitoramento e Análise de Tipsters do YouTube

2. Objetivo

Construir uma plataforma web autenticada que:

monitora canais do YouTube automaticamente
analisa vídeos novos periodicamente
extrai jogos mencionados
identifica ideias/opiniões dos tipsters
organiza essas ideias por jogo e por dia
permite registrar resultados reais
calcula assertividade por tipster, mercado e tipo de ideia
mantém histórico completo de análise de vídeos (inclusive quando não há jogos ou entradas)
3. Problema que resolve

Hoje:

conteúdo de tipsters se perde em vídeos
não existe histórico estruturado
não há como comparar performance
não há rastreabilidade de ideias

O sistema resolve isso transformando fala em:

dados estruturados
histórico consultável
inteligência comparativa
4. Princípio central do sistema

O sistema deve modelar separadamente:

1. O que foi dito
2. Em que contexto (jogo)
3. O que isso significa (ideia)
4. Se é acionável ou não
5. O nível de confiança
6. O resultado posterior
5. Unidade fundamental
Idea (Tip Signal)

Uma idea representa uma leitura do tipster sobre um jogo.

Pode ser:

entrada possível
entrada forte
alerta
cautela
ausência de valor
recomendação de evitar
leitura de tendência
condição de entrada
6. Tipos de ideias
idea_type
possible_entry
strong_entry
caution
no_value
avoid_game
watch_live
trend_read
risk_alert
condition_based_entry
contextual_note
7. Tipos de mercado
market_type
over_0_5
over_1_5
over_2_5
under_2_5
btts_yes
btts_no
home_win
away_win
draw_no_bet
asian_handicap
corners
cards
player_props
lay
back
no_specific_market
8. Classificação de vídeos (IMPORTANTE)

Nem todo vídeo gera dados úteis.

content_scope
daily_games
future_games
general_analysis
methodology
bankroll_management
trading_education
promotional
mixed
unknown
analysis_status
pending
processing
analyzed_with_matches
analyzed_without_matches
analyzed_without_actionable_ideas
irrelevant
failed
9. Fluxo geral do sistema
1. Admin cadastra canal
2. Sistema monitora YouTube
3. Detecta vídeos novos
4. Salva vídeo
5. Processa vídeo
6. Classifica conteúdo
7. Detecta jogos
8. Extrai ideias
9. Registra análise do vídeo
10. Exibe na plataforma
11. Usuário registra resultado
12. Sistema calcula assertividade
10. Resultado esperado

O sistema permitirá:

ver jogos do dia com ideias de vários tipsters
comparar opiniões
registrar resultados
avaliar desempenho dos tipsters
consultar histórico completo de vídeos analisados

📄 PARTE 2 — ARQUITETURA E MÓDULOS DO SISTEMA
11. Visão geral da arquitetura

O sistema deve ser dividido em módulos independentes, com processamento assíncrono para vídeos.

Arquitetura recomendada:

Frontend (React / Next.js)
        ↓
API Backend (FastAPI)
        ↓
Banco de Dados (PostgreSQL)
        ↓
Workers Assíncronos (Celery / RQ + Redis)
        ↓
Serviços de IA (LLM / Transcrição)
12. Princípios arquiteturais
processamento assíncrono de vídeos
separação entre ingestão, processamento e exibição
auditabilidade completa
human-in-the-loop (revisão)
versionamento de dados
tolerância a falhas
escalabilidade por canal
13. Módulos do sistema
13.1 Módulo de Autenticação

Responsável por:

login
logout
registro
recuperação de senha
controle de sessão

Perfis:

admin
revisor
usuário
13.2 Módulo de Administração de Canais

Permite:

cadastrar canal do YouTube
editar canal
ativar/desativar monitoramento
visualizar status do canal
ver último processamento

Campos principais:

nome do canal
URL
tipster associado
status
frequência de monitoramento
13.3 Módulo de Monitoramento de Vídeos

Responsável por:

verificar vídeos novos via YouTube
evitar duplicação
registrar vídeos encontrados
disparar processamento

Execução:

job periódico (cron/scheduler)
13.4 Módulo de Ingestão de Vídeos

Para cada vídeo:

salvar metadados
armazenar URL
registrar data de publicação
colocar na fila de processamento
13.5 Módulo de Transcrição

Responsável por:

obter transcript do vídeo
normalizar texto
remover ruído
salvar transcript bruto e limpo
13.6 Módulo de Segmentação

Divide o conteúdo em:

blocos por jogo
blocos por mudança de assunto
blocos por mudança de ideia

Regras:

detectar mudança de times
detectar mudança de mercado
detectar mudança de intenção
13.7 Módulo de Extração de Ideias (NLP)

Responsável por:

identificar jogos mencionados
identificar ideias do tipster
classificar tipo de ideia
identificar mercado
extrair crença, medo, cautela
identificar condições
extrair justificativa

Saída:
→ JSON estruturado de ideias

13.8 Módulo de Classificação de Vídeo

Define:

content_scope
analysis_status
quantidade de jogos
quantidade de ideias
13.9 Módulo de Revisão Humana (HITL)

Responsável por:

revisar extrações ambíguas
corrigir dados
validar ideias
dividir/mesclar ideias

Critérios de envio para revisão:

baixa confiança
múltiplos mercados
ideia implícita
inconsistência de dados
13.10 Módulo de Armazenamento

Salva:

vídeos
análises
jogos
ideias
revisões
resultados
auditoria
13.11 Módulo de Registro de Resultados

Permite:

registrar placar final
registrar eventos relevantes
atualizar status do jogo
validar ideias automaticamente
13.12 Módulo de Avaliação

Calcula:

acerto direto
acerto condicional
assertividade por mercado
assertividade por tipo de ideia
calibração de confiança
13.13 Módulo de Dashboard

Exibe:

jogos do dia
ideias por tipster
possíveis entradas
convergência entre tipsters
estatísticas gerais
13.14 Módulo de Página do Tipster

Exibe:

perfil do tipster
histórico de vídeos
ideias geradas
estatísticas
assertividade
13.15 Módulo de Página do Vídeo

Exibe:

vídeo analisado
URL do YouTube
status da análise
jogos detectados
ideias extraídas
resumo da análise
14. Comunicação entre módulos

Fluxo interno:

monitor → ingestão → transcrição → segmentação → extração → classificação → armazenamento → revisão → avaliação → dashboard
15. Processamento assíncrono

Todos os passos pesados devem rodar em background:

transcrição
NLP
classificação
avaliação

Fila recomendada:

Redis + Celery
16. Tolerância a falhas

O sistema deve:

marcar vídeo como failed
permitir reprocessamento
registrar erro
não travar pipeline
17. Auditabilidade

Cada ação deve gerar evento:

vídeo processado
ideia criada
ideia editada
revisão realizada
resultado registrado
18. Versionamento

Cada extração deve guardar:

versão do modelo
versão do prompt
versão do schema
timestamp


📄 PARTE 3 — MODELO DE DADOS COMPLETO
19. Visão geral do modelo de dados

O sistema precisa suportar quatro camadas de informação:

cadastro e autenticação
monitoramento de canais e vídeos
extração e revisão de ideias
resultados, avaliação e auditoria

O banco principal pode ser relacional, com PostgreSQL.

20. Tabelas de autenticação e usuários
20.1 users

Armazena os usuários da plataforma.

Campos sugeridos:

id
name
email
password_hash
is_active
created_at
updated_at
last_login_at
20.2 roles

Perfis de acesso.

Campos:

id
name

Valores esperados:

admin
reviewer
user
20.3 user_roles

Relacionamento entre usuários e perfis.

Campos:

id
user_id
role_id
21. Tabelas de tipsters e canais
21.1 tipsters

Cadastro lógico do criador/analisador.

Campos:

id
name
display_name
bio
status
notes
created_at
updated_at
21.2 youtube_channels

Cadastro do canal monitorado.

Campos:

id
tipster_id
channel_name
channel_url
channel_external_id
is_active
monitoring_frequency_minutes
last_checked_at
last_video_published_at
last_video_analyzed_at
last_successful_analysis_at
last_failed_analysis_at
last_irrelevant_video_at
monitoring_status
created_at
updated_at
monitoring_status

Sugestão:

active
paused
error
disabled
22. Tabelas de vídeos
22.1 videos

Metadados do vídeo do YouTube.

Campos:

id
channel_id
youtube_video_id
youtube_url
title
description
thumbnail_url
published_at
fetched_at
duration_seconds
status
created_at
updated_at
status

Sugestão:

discovered
queued
processing
analyzed
failed
22.2 video_analyses

Resultado analítico do vídeo.

Essa tabela é obrigatória, porque um vídeo pode:

ter jogos
não ter jogos
ter jogos sem entrada
ser irrelevante

Campos:

id
video_id
analysis_url_slug
analyzed_at
analysis_status
content_scope
summary_text
games_detected_count
ideas_detected_count
actionable_ideas_count
warnings_count
no_value_count
review_status
reviewer_user_id
reviewed_at
model_version
prompt_version
schema_version
raw_output_json
normalized_output_json
created_at
updated_at
review_status
pending
reviewed
partially_reviewed
rejected
23. Tabelas de transcrição
23.1 video_transcripts

Armazena transcript do vídeo.

Campos:

id
video_id
transcript_source
language_code
raw_transcript_text
normalized_transcript_text
has_timestamps
created_at
updated_at
23.2 transcript_segments

Trechos segmentados da transcrição.

Campos:

id
video_id
transcript_id
start_seconds
end_seconds
raw_text
normalized_text
segment_type
created_at
segment_type
intro
match_analysis
methodology
promotional
closing
unknown
24. Tabelas esportivas
24.1 competitions

Campos:

id
name
country
season
created_at
24.2 teams

Campos:

id
name
country
created_at
24.3 team_aliases

Ajuda na reconciliação de nomes vindos da transcrição.

Campos:

id
team_id
alias
source
created_at
24.4 games

Jogos identificados ou cadastrados.

Campos:

id
competition_id
home_team_id
away_team_id
scheduled_at
round_label
status
created_at
updated_at
status
scheduled
finished
canceled
unknown
24.5 game_aliases

Opcional, para resolver nomes de jogos detectados em formatos diversos.

Campos:

id
game_id
alias
source
created_at
25. Tabela central de ideias
25.1 game_ideas

Tabela principal do sistema.

Cada linha representa uma ideia/opinião/alerta extraído de um tipster sobre um jogo.

Campos:

id
game_id
tipster_id
video_id
video_analysis_id
segment_id
source_timestamp_start
source_timestamp_end
idea_type
market_type
selection_label
sentiment_direction
confidence_band
confidence_expression_text
belief_text
fear_text
entry_text
avoid_text
rationale_text
condition_text
source_excerpt
is_actionable
needs_review
extraction_confidence
review_status
created_at
updated_at
sentiment_direction
favorable
unfavorable
neutral
conditional
review_status
pending
approved
corrected
rejected
26. Tabelas auxiliares de ideias
26.1 idea_conditions

Para registrar condições estruturadas.

Campos:

id
idea_id
condition_type
condition_text
is_inferred
created_at
condition_type
lineup
early_goal
live_entry
odds_movement
tactical_setup
unknown
26.2 idea_reasons

Razões/justificativas categorizadas.

Campos:

id
idea_id
reason_category
reason_text
created_at
reason_category
form
defense
attack
motivation
odds
lineup
context
home_advantage
fatigue
market_value
unknown
26.3 idea_labels

Permite multi-rótulo por ideia.

Campos:

id
idea_id
label

Valores esperados:

explicit_prediction
implicit_prediction
caution
contextual_comment
risk_alert
no_value
watch_live
27. Tabelas de revisão humana
27.1 idea_reviews

Histórico de revisão de ideias.

Campos:

id
idea_id
reviewer_user_id
action_type
previous_data_json
new_data_json
review_notes
created_at
action_type
approve
edit
reject
split
merge
reassign_game
27.2 video_analysis_reviews

Revisão no nível do vídeo.

Campos:

id
video_analysis_id
reviewer_user_id
action_type
review_notes
created_at
28. Tabelas de resultado
28.1 game_results

Resultado real do jogo.

Campos:

id
game_id
home_score
away_score
both_teams_scored
total_goals
corners_total
cards_total
result_source
is_manual
created_by_user_id
created_at
updated_at
28.2 idea_evaluations

Avaliação de acerto/erro da ideia.

Campos:

id
idea_id
evaluation_type
evaluation_status
is_hit
is_partial_hit
manual_required
evaluation_notes
evaluated_at
evaluated_by_user_id
created_at
updated_at
evaluation_type
automatic_binary
automatic_conditional
manual_review
non_binary_insight
evaluation_status
pending
evaluated
requires_manual_review
skipped
29. Tabelas de auditoria e eventos
29.1 audit_events

Ledger append-only do sistema.

Campos:

id
entity_type
entity_id
event_type
actor_user_id
event_payload_json
created_at
entity_type
channel
video
video_analysis
transcript
idea
result
evaluation
user
event_type

Exemplos:

created
updated
deleted
processed
failed
reviewed
evaluated
reprocessed
29.2 processing_jobs

Controle opcional de jobs.

Campos:

id
job_type
entity_type
entity_id
status
payload_json
started_at
finished_at
error_message
created_at
30. Relacionamentos principais
Relações centrais
um tipster pode ter um ou mais youtube_channels
um youtube_channel possui muitos videos
um video possui uma ou mais video_analyses
um video possui um video_transcript
um video_transcript possui muitos transcript_segments
um video_analysis pode gerar muitos game_ideas
um game pode ter muitas game_ideas
uma game_idea pode ter muitas idea_conditions
uma game_idea pode ter muitas idea_reasons
uma game_idea pode ter muitas idea_reviews
um game possui zero ou um game_result
uma game_idea possui zero ou uma idea_evaluation
31. Índices recomendados

Criar índices para:

videos(channel_id, published_at)
youtube_channels(last_checked_at)
video_analyses(video_id, analyzed_at)
games(scheduled_at)
game_ideas(game_id, tipster_id)
game_ideas(video_id)
idea_evaluations(idea_id)
audit_events(entity_type, entity_id, created_at)
32. Regras de integridade importantes
um vídeo não pode existir duplicado por youtube_video_id
uma análise deve referenciar vídeo válido
uma ideia deve referenciar um vídeo e um tipster válidos
uma avaliação só pode existir para ideia existente
exclusão física deve ser evitada em registros analíticos; preferir status lógico

📄 PARTE 4 — REQUISITOS FUNCIONAIS, REGRAS DE NEGÓCIO E FLUXOS OPERACIONAIS
33. Requisitos funcionais
RF01 — Autenticação

O sistema deve permitir login com email e senha.

RF02 — Perfis de acesso

O sistema deve suportar perfis de acesso distintos:

admin
reviewer
user
RF03 — Recuperação de senha

O sistema deve permitir recuperação de senha.

RF04 — Cadastro de tipsters

O sistema deve permitir cadastrar, editar e inativar tipsters.

RF05 — Cadastro de canais do YouTube

O sistema deve permitir cadastrar, editar, ativar e desativar canais do YouTube.

RF06 — Monitoramento periódico

O sistema deve verificar periodicamente vídeos novos dos canais ativos.

RF07 — Registro de vídeos

O sistema deve registrar metadados de cada vídeo encontrado.

RF08 — Evitar duplicação

O sistema não deve cadastrar o mesmo vídeo mais de uma vez.

RF09 — Transcrição

O sistema deve obter e armazenar a transcrição do vídeo.

RF10 — Normalização

O sistema deve gerar uma versão normalizada da transcrição.

RF11 — Segmentação

O sistema deve segmentar a transcrição em blocos relevantes.

RF12 — Classificação do vídeo

O sistema deve classificar o vídeo por escopo e status de análise.

RF13 — Detecção de jogos

O sistema deve identificar jogos mencionados no vídeo quando existirem.

RF14 — Extração de ideias

O sistema deve extrair ideias por jogo a partir da fala do tipster.

RF15 — Classificação das ideias

O sistema deve classificar cada ideia por tipo, mercado, direção e acionabilidade.

RF16 — Extração de crença e medo

O sistema deve registrar o que o tipster acredita, teme, evita ou sugere.

RF17 — Registro de condições

O sistema deve registrar condições explícitas ou inferidas associadas à ideia.

RF18 — Registro de justificativas

O sistema deve registrar justificativas/racionalidades associadas à ideia.

RF19 — Registro da análise do vídeo

O sistema deve registrar o resultado analítico do vídeo mesmo quando não houver jogos ou ideias acionáveis.

RF20 — Página diária de jogos

O sistema deve exibir uma página diária com os jogos e as ideias extraídas por tipster.

RF21 — Página do jogo

O sistema deve exibir uma página detalhada do jogo com todas as ideias relacionadas.

RF22 — Página do tipster

O sistema deve exibir uma página do tipster com histórico de vídeos, ideias e métricas.

RF23 — Página da análise do vídeo

O sistema deve exibir uma página interna com o resumo da análise do vídeo.

RF24 — URL do vídeo e URL da análise

O sistema deve mostrar a URL original do YouTube e a URL interna da análise.

RF25 — Último dia de análise do canal

O sistema deve registrar e exibir a data da última análise do canal.

RF26 — Revisão humana

O sistema deve permitir revisar, corrigir, rejeitar, dividir e mesclar ideias.

RF27 — Reprocessamento

O sistema deve permitir reprocessar vídeos e análises.

RF28 — Registro de resultado

O sistema deve permitir registrar resultado real do jogo.

RF29 — Avaliação de ideias

O sistema deve avaliar ideias automaticamente quando possível.

RF30 — Avaliação manual

O sistema deve permitir avaliação manual para ideias não binárias ou ambíguas.

RF31 — Dashboard geral

O sistema deve exibir dashboard consolidado com jogos, ideias e métricas.

RF32 — Dashboard por tipster

O sistema deve exibir estatísticas e assertividade por tipster.

RF33 — Auditoria

O sistema deve registrar eventos relevantes em trilha de auditoria.

RF34 — Logs de falha

O sistema deve registrar falhas de processamento.

RF35 — Histórico completo

O sistema deve manter histórico de vídeos analisados, mesmo quando irrelevantes ou sem saída útil.

34. Requisitos não funcionais
RNF01

As senhas devem ser armazenadas com hash seguro.

RNF02

O sistema deve exigir autenticação para acesso às áreas internas.

RNF03

O processamento de vídeos deve ser assíncrono.

RNF04

O sistema deve suportar múltiplos canais e múltiplos vídeos por dia.

RNF05

O sistema deve manter trilha de auditoria append-only.

RNF06

O sistema deve permitir evolução de schema com versionamento.

RNF07

O sistema deve ser resiliente a falhas parciais no pipeline.

RNF08

A interface deve ser responsiva.

RNF09

O sistema deve registrar timestamps em UTC.

RNF10

O sistema deve permitir reprocessamento sem perder histórico anterior.

35. Regras de negócio
RN01 — Nem todo vídeo gera jogos

Um vídeo pode ser analisado e não gerar nenhum jogo identificado.

RN02 — Nem todo vídeo gera ideias acionáveis

Um vídeo pode conter jogos, mas não gerar entradas claras.

RN03 — Vídeo irrelevante continua no histórico

Vídeos classificados como irrelevantes ainda devem ficar visíveis no histórico do tipster/canal.

RN04 — Ideia não é igual a aposta fechada

Uma ideia pode representar:

entrada possível
tendência
medo
cautela
ausência de valor
alerta
RN05 — Nem toda ideia é binária

Ideias como “não vejo valor” ou “cuidado com reservas” podem não ter avaliação automática.

RN06 — Revisão humana é parte do sistema

Casos ambíguos devem ir para revisão.

RN07 — Uma fala pode gerar várias ideias

Um mesmo trecho pode produzir mais de uma ideia.

RN08 — Uma ideia pode ter múltiplos rótulos

Exemplo:

caution
implicit_prediction
contextual_note
RN09 — O sistema não deve transformar tudo em entrada

Comentários vagos devem poder ser salvos como contexto, sem forçar tip acionável.

RN10 — A análise do vídeo é uma entidade própria

Cada vídeo deve ter um registro de análise, independentemente de ter ou não gerado jogos/ideias.

RN11 — A página do tipster deve refletir histórico real

Deve mostrar vídeos com ou sem resultados úteis.

RN12 — Resultado manual é aceitável no MVP

No MVP, o placar pode ser lançado manualmente.

RN13 — Avaliação automática só quando houver critério claro

Exemplo:

over 1.5
ambas marcam
vitória mandante
RN14 — Alterações humanas devem ser auditáveis

Toda revisão deve gerar evento de auditoria.

RN15 — Reprocessamento não deve sobrescrever silenciosamente

Deve preservar rastreabilidade entre versões.

36. Regras de classificação de vídeos
36.1 content_scope
daily_games

Quando o vídeo foca em jogos próximos/do dia.

future_games

Quando o vídeo fala de jogos futuros, rodada posterior, prévia geral.

general_analysis

Quando fala de futebol/apostas sem foco específico em uma grade do dia.

methodology

Quando o vídeo discute método, leitura, postura, disciplina.

bankroll_management

Quando o foco é banca, gestão, controle emocional.

trading_education

Quando o foco é explicar trading/mercado.

promotional

Quando é majoritariamente propaganda.

mixed

Quando mistura mais de um tipo.

unknown

Quando o sistema não conseguiu classificar.

36.2 analysis_status
pending

Vídeo aguardando processamento.

processing

Vídeo em processamento.

analyzed_with_matches

Vídeo com jogos detectados.

analyzed_without_matches

Vídeo analisado sem jogos detectados.

analyzed_without_actionable_ideas

Vídeo com análise mas sem ideias acionáveis.

irrelevant

Vídeo fora de escopo útil.

failed

Falha de processamento.

37. Regras de classificação de ideias
37.1 idea_type
possible_entry

Entrada possível, mas sem convicção máxima.

strong_entry

Entrada mais forte/afirmativa.

caution

Aviso de atenção.

no_value

Percepção de ausência de valor.

avoid_game

Recomendação de evitar o jogo.

watch_live

Recomendação de observar ao vivo.

trend_read

Leitura de tendência sem entrada fechada.

risk_alert

Alerta de risco.

condition_based_entry

Entrada dependente de condição.

contextual_note

Comentário contextual útil, não necessariamente acionável.

38. Critérios operacionais para extração
38.1 O que deve ser extraído como ideia

Extrair quando houver ao menos um dos seguintes:

direção de mercado
opinião acionável
alerta relevante
leitura de tendência
ausência explícita de valor
condição operacional
38.2 O que não deve virar ideia

Não transformar em ideia:

propaganda
CTA
auto promoção
saudação
encerramento
ruído/transição sem conteúdo analítico
39. Regras de envio para revisão humana

Enviar para revisão quando houver:

extraction_confidence < 0.80
múltiplos mercados candidatos
múltiplos jogos candidatos
ideia implícita
condição complexa
entidades inconsistentes
conteúdo muito ambíguo
conflito entre classificação e texto
40. Fluxo operacional — cadastro de canal
Admin acessa painel
Cadastra tipster
Cadastra canal do YouTube
Define frequência de monitoramento
Sistema salva e inicia monitoramento
41. Fluxo operacional — descoberta de vídeos
Job periódico roda
Busca vídeos novos no canal
Compara com youtube_video_id
Salva apenas novos
Atualiza last_checked_at
Enfileira processamento
42. Fluxo operacional — processamento de vídeo
Worker recebe vídeo
Marca status como processing
Obtém transcript
Normaliza transcript
Segmenta blocos
Classifica conteúdo do vídeo
Detecta jogos
Extrai ideias
Cria video_analysis
Cria game_ideas
Envia ambiguidades para revisão
Atualiza status final
43. Fluxo operacional — revisão humana
Revisor abre fila
Escolhe vídeo/ideia pendente
Visualiza trecho, jogo e estrutura extraída
Aprova, edita, rejeita, divide ou mescla
Sistema salva revisão e gera auditoria
44. Fluxo operacional — registro de resultado
Usuário acessa jogo
Informa placar e dados relevantes
Sistema salva game_result
Motor de avaliação roda
Atualiza idea_evaluations
45. Fluxo operacional — páginas do produto
45.1 Página diária
lista jogos por data
mostra tipsters que falaram
mostra ideias por jogo
45.2 Página do jogo
detalha jogo
exibe todas as ideias
exibe resultado e avaliações
45.3 Página do tipster
exibe perfil
mostra métricas
lista vídeos
mostra URL do vídeo
mostra URL da análise
mostra o que foi analisado
45.4 Página do vídeo/análise
título
URL do YouTube
data do vídeo
data da análise
status
escopo
resumo
jogos detectados
ideias detectadas
trechos relevantes
46. Métricas principais do produto
Gerais
vídeos analisados
vídeos com jogos
vídeos sem jogos
vídeos irrelevantes
ideias extraídas
ideias acionáveis
Por tipster
total de vídeos
total de jogos
total de ideias
total de entradas possíveis
total de alertas
taxa de acerto
taxa por mercado
taxa por tipo de ideia
Por jogo/dia
número de tipsters que falaram
número de ideias convergentes
mercados mais citados

📄 PARTE 5 — PÁGINAS, UX, DASHBOARDS, JSON OFICIAL DE EXTRAÇÃO E CRITÉRIOS DE AVALIAÇÃO
47. Páginas do sistema
47.1 Página de login

Objetivo:

autenticar acesso à plataforma

Campos:

email
senha

Ações:

entrar
recuperar senha
47.2 Dashboard inicial

Objetivo:

mostrar visão geral da operação e do dia

Blocos sugeridos:

total de canais ativos
total de vídeos analisados hoje
total de vídeos pendentes
total de vídeos com falha
jogos do dia
ideias acionáveis do dia
tipsters mais ativos
mercados mais citados
47.3 Página de administração de canais

Objetivo:

gerenciar canais monitorados

Campos e colunas:

nome do tipster
nome do canal
URL do canal
status do monitoramento
frequência de verificação
último check
último vídeo analisado
ações

Ações:

cadastrar canal
editar
pausar
ativar
reprocessar últimos vídeos
47.4 Página de tipsters

Objetivo:

listar todos os tipsters cadastrados

Colunas:

nome
canal principal
status
vídeos analisados
ideias registradas
assertividade geral
última análise
ação de visualizar
47.5 Página do tipster

Objetivo:

concentrar o histórico analítico completo do criador
Bloco 1 — resumo do tipster

Campos:

nome
nome do canal
URL do canal
status
data do cadastro
último check do canal
último vídeo publicado
último vídeo analisado
última análise bem-sucedida
última falha
total de vídeos analisados
total de vídeos irrelevantes
total de jogos detectados
total de ideias registradas
total de ideias acionáveis
assertividade geral
assertividade por mercado
mercados mais frequentes
Bloco 2 — lista de vídeos analisados

Cada linha deve mostrar:

data de publicação
data da análise
título do vídeo
URL do YouTube
URL interna da análise
content_scope
analysis_status
jogos detectados
ideias detectadas
ideias acionáveis
revisado?
ação ver análise
Bloco 3 — indicadores
vídeos com jogos
vídeos sem jogos
vídeos sem ideias
vídeos irrelevantes
taxa de aproveitamento
total de alertas
total de “no value”
total de “watch live”
total de “possible entry”
Bloco 4 — performance
taxa de acerto global
taxa por mercado
taxa por tipo de ideia
taxa por faixa de confiança
volume de ideias por semana/mês
47.6 Página diária de jogos

Objetivo:

mostrar os jogos de uma data e tudo o que cada tipster falou

Filtros:

data
competição
tipster
mercado
tipo de ideia

Para cada jogo exibir:

horário
competição
mandante x visitante
resultado, se houver
tipsters que falaram
ideias extraídas

Cada bloco de ideia deve mostrar:

nome do tipster
idea_type
market_type
belief_text
fear_text
entry_text
avoid_text
condition_text
confidence_band
link para vídeo
link para análise
status de acerto/erro, se já avaliado
47.7 Página do jogo

Objetivo:

detalhar tudo que foi dito sobre um jogo específico

Seções:

dados do jogo
resultado real
ideias por tipster
trechos da fala
justificativas
condições
avaliações
histórico de revisões
47.8 Página da análise do vídeo

Objetivo:

mostrar o resultado completo do processamento do vídeo

Campos:

título do vídeo
tipster
URL do YouTube
data de publicação
data da análise
analysis_status
content_scope
resumo da análise
transcript bruto/normalizado
jogos detectados
ideias detectadas
trechos analisados
revisões realizadas
versão do modelo/prompt/schema

Essa página deve responder:

o que foi analisado
o que foi encontrado
o que não foi encontrado
se exigiu revisão
47.9 Tela de revisão humana

Objetivo:

permitir corrigir estrutura extraída rapidamente

Exibir lado a lado:

vídeo/timestamp
trecho bruto
trecho normalizado
jogo detectado
ideia proposta
condições
justificativas
confiança
labels

Ações:

aprovar
editar
rejeitar
dividir
mesclar
reatribuir jogo
marcar como contextual apenas
48. UX — princípios de interface

A interface deve seguir estes princípios:

mostrar sempre a evidência textual que gerou a estrutura
permitir correção rápida
não esconder vídeos “sem saída útil”
distinguir vídeo, análise, jogo e ideia
mostrar status de processamento e revisão
destacar o que é automático e o que foi corrigido manualmente
49. Dashboard geral

Objetivo:

visão executiva e operacional

Widgets sugeridos:

vídeos processados hoje
vídeos pendentes
falhas recentes
jogos do dia com mais ideias
possíveis entradas do dia
tipsters mais ativos
mercados mais citados
convergência por jogo
taxa geral de acerto
vídeos sem jogos
vídeos sem ideias acionáveis
50. Dashboard de possíveis entradas

Objetivo:

listar oportunidades agregadas do dia

Cada linha pode representar:

jogo
mercado
número de tipsters que sugeriram algo parecido
tipsters envolvidos
nível de confiança agregado
divergências
resultado posterior

Importante:
O dashboard não deve inventar entrada própria.
Ele apenas agrega o que os tipsters disseram.

51. Dashboard de tipsters

Objetivo:

comparar criadores

Indicadores:

total de vídeos
total de jogos
total de ideias
taxa de acerto
taxa por mercado
taxa por tipo de ideia
taxa por faixa de confiança
quantidade de “no value”
quantidade de “risk_alert”
quantidade de “watch_live”
média de ideias por vídeo
52. JSON oficial de extração — v1

Este JSON é o contrato mínimo que o motor de extração deve devolver por vídeo.

{
  "video_analysis": {
    "content_scope": "daily_games | future_games | general_analysis | methodology | bankroll_management | trading_education | promotional | mixed | unknown",
    "analysis_status": "analyzed_with_matches | analyzed_without_matches | analyzed_without_actionable_ideas | irrelevant | failed",
    "summary_text": "",
    "games_detected_count": 0,
    "ideas_detected_count": 0,
    "actionable_ideas_count": 0,
    "warnings_count": 0,
    "no_value_count": 0
  },
  "games": [
    {
      "match_ref": {
        "home": "",
        "away": "",
        "competition": "",
        "scheduled_date": ""
      },
      "ideas": [
        {
          "idea_type": "possible_entry | strong_entry | caution | no_value | avoid_game | watch_live | trend_read | risk_alert | condition_based_entry | contextual_note",
          "market_type": "over_0_5 | over_1_5 | over_2_5 | under_2_5 | btts_yes | btts_no | home_win | away_win | draw_no_bet | asian_handicap | corners | cards | player_props | lay | back | no_specific_market",
          "selection_label": "",
          "sentiment_direction": "favorable | unfavorable | neutral | conditional",
          "confidence_band": "high | medium | low",
          "confidence_expression_text": "",
          "belief_text": "",
          "fear_text": "",
          "entry_text": "",
          "avoid_text": "",
          "rationale_text": "",
          "condition_text": "",
          "source_excerpt": "",
          "source_timestamp_start": 0,
          "source_timestamp_end": 0,
          "is_actionable": true,
          "needs_review": false,
          "extraction_confidence": 0.0,
          "labels": [
            "explicit_prediction",
            "implicit_prediction",
            "caution",
            "contextual_comment",
            "risk_alert",
            "no_value",
            "watch_live"
          ],
          "reasons": [
            {
              "category": "form | defense | attack | motivation | odds | lineup | context | home_advantage | fatigue | market_value | unknown",
              "text": ""
            }
          ],
          "conditions": [
            {
              "condition_type": "lineup | early_goal | live_entry | odds_movement | tactical_setup | unknown",
              "text": "",
              "is_inferred": false
            }
          ]
        }
      ]
    }
  ]
}
53. Regras do JSON v1
um vídeo pode retornar zero jogos
um jogo pode retornar zero ideias
um vídeo irrelevante ainda deve gerar video_analysis
belief_text, fear_text, entry_text e avoid_text podem estar vazios
labels é multi-rótulo
is_actionable deve ser falso quando a ideia for apenas contextual
needs_review deve ser verdadeiro em casos ambíguos
54. Critérios de avaliação das ideias

O sistema precisa tratar avaliação por categoria.

54.1 Ideias com avaliação automática binária

Exemplos:

over 1.5
ambas marcam
home_win
away_win

Nesses casos:

comparar com game_results
marcar hit/miss automaticamente
54.2 Ideias condicionais

Exemplos:

“se sair gol cedo, over cresce”
“se vier time reserva, cuidado”

Nesses casos:

avaliação pode exigir revisão manual
ou lógica adicional no futuro
54.3 Ideias não binárias

Exemplos:

“não vejo valor”
“jogo perigoso”
“time está voando”

Nesses casos:

marcar como manual_review ou non_binary_insight
55. Tipos de avaliação
evaluation_type
automatic_binary
automatic_conditional
manual_review
non_binary_insight
evaluation_status
pending
evaluated
requires_manual_review
skipped
56. Regras para “acertou ou não”
Acerto objetivo

Quando o mercado associado bateu.

Erro objetivo

Quando o mercado associado não bateu.

Acerto parcial

Quando a leitura tinha valor parcial, mas não foi totalmente validada.

Sem avaliação automática

Quando a ideia é subjetiva, contextual ou condicional complexa.

57. Assertividade do tipster

A página do tipster deve mostrar múltiplas métricas:

57.1 Assertividade objetiva

Taxa de acerto em ideias avaliáveis automaticamente.

57.2 Assertividade por mercado

Exemplo:

over 1.5
btts
home win
57.3 Assertividade por tipo de ideia

Exemplo:

possible_entry
strong_entry
caution
57.4 Volume analítico
vídeos analisados
jogos detectados
ideias registradas
57.5 Perfil discursivo
quantas ideias são entrada
quantas são medo
quantas são “sem valor”
quantas são watch live
58. Regras para “último dia de análise do canal”

Na página do canal/tipster, o sistema deve exibir:

último dia em que um vídeo do canal foi processado
último dia em que um vídeo gerou análise útil
último dia em que houve falha
último check do monitoramento

Esses dados vêm principalmente de:

youtube_channels.last_checked_at
youtube_channels.last_video_analyzed_at
youtube_channels.last_successful_analysis_at
youtube_channels.last_failed_analysis_at
59. Regras para vídeos sem conteúdo útil

Mesmo que um vídeo:

não tenha jogos
não tenha ideias
seja promocional
seja metodológico

ele ainda deve:

aparecer na página do tipster
ter sua própria página de análise
mostrar o que foi classificado
ficar auditável
60. Critérios mínimos para o MVP

Entram no MVP:

login
cadastro de tipsters e canais
monitoramento periódico
registro de vídeos
transcrição
classificação de vídeo
detecção básica de jogos
extração de ideias
revisão humana
página diária de jogos
página do tipster
página da análise do vídeo
registro manual de resultado
avaliação automática simples
dashboard inicial

Não entram no MVP:

integração automática com APIs esportivas complexas
avaliação avançada de condicionais
prosódia/áudio avançado
agrupamento semântico sofisticado entre tipsters
recomendação automática própria do sistema

📄 PARTE 6 — ARQUITETURA TÉCNICA, ESTRUTURA DO PROJETO, APIS E PLANO DE IMPLEMENTAÇÃO

Esta parte é a que você vai literalmente usar com o Claude para gerar o sistema e subir no Git.

61. Stack tecnológica recomendada
Backend
Python
FastAPI
Frontend
Next.js (React)
Banco de dados
PostgreSQL
Filas / processamento assíncrono
Redis
Celery (ou RQ)
Autenticação
JWT + refresh token
Infraestrutura
Docker
Docker Compose
Nginx (opcional)
IA / NLP
LLM (OpenAI / Claude)
Serviço de transcrição (Whisper ou similar)
62. Arquitetura em camadas
Frontend (Next.js)
        ↓
API Gateway (FastAPI)
        ↓
Services Layer
        ↓
Database (PostgreSQL)
        ↓
Workers (Celery + Redis)
        ↓
External APIs (YouTube, Transcription, LLM)
63. Separação de módulos no backend
Estrutura recomendada
/backend
  /app
    /api
    /core
    /models
    /schemas
    /services
    /workers
    /repositories
    /utils
  main.py
63.1 /api

Endpoints HTTP

Exemplo:

auth
channels
videos
tipsters
games
ideas
dashboards
63.2 /core

Configurações globais:

settings
auth
security
database connection
63.3 /models

Modelos ORM (SQLAlchemy)

63.4 /schemas

Schemas Pydantic (entrada/saída da API)

63.5 /services

Lógica de negócio

Exemplo:

youtube_service
transcript_service
extraction_service
evaluation_service
channel_monitor_service
63.6 /workers

Tasks assíncronas

Exemplo:

process_video_task
transcript_task
extract_ideas_task
63.7 /repositories

Acesso ao banco

63.8 /utils

Funções auxiliares

64. Estrutura do frontend
/frontend
  /app
    /login
    /dashboard
    /tipsters
    /tipster/[id]
    /videos
    /video/[id]
    /games
    /game/[id]
  /components
  /services
  /hooks
65. Principais APIs (FastAPI)
65.1 Autenticação
POST /auth/login
retorna token
POST /auth/register
POST /auth/refresh
65.2 Tipsters
GET /tipsters

Lista todos

GET /tipsters/{id}

Detalhes + métricas

65.3 Canais
POST /channels

Cadastrar canal

GET /channels

Listar

PATCH /channels/{id}

Editar

65.4 Vídeos
GET /videos

Listar vídeos

GET /videos/{id}

Detalhes

65.5 Análise de vídeo
GET /video-analyses/{id}

Página da análise

65.6 Jogos
GET /games?date=YYYY-MM-DD

Página diária

GET /games/{id}

Detalhes do jogo

65.7 Ideias
GET /ideas?game_id=

Listar ideias do jogo

65.8 Resultados
POST /game-results

Cadastrar resultado

65.9 Dashboard
GET /dashboard

Resumo geral

66. Workers (tarefas assíncronas)
66.1 monitor_channels_task
roda periodicamente
busca vídeos novos
66.2 process_video_task(video_id)

Pipeline principal:

1. obter transcript
2. normalizar texto
3. segmentar
4. extrair ideias (LLM)
5. classificar vídeo
6. salvar análise
7. salvar ideias
8. enviar para revisão se necessário
66.3 evaluate_ideas_task(game_id)
roda após resultado
avalia ideias automaticamente
67. Integrações externas
YouTube API

Para:

listar vídeos
obter metadata
Transcrição
Whisper ou API externa
LLM (Claude/OpenAI)

Para:

extrair JSON de ideias
68. Prompt base para extração (ESSENCIAL PARA CLAUDE)

Esse prompt é o coração do sistema.

Instrução principal

O modelo deve:

ler transcrição
identificar jogos
extrair ideias
classificar ideias
devolver JSON no formato especificado
Prompt base simplificado
Você é um sistema de análise de vídeos de apostas esportivas.

Sua tarefa é:
1. identificar jogos mencionados
2. extrair ideias/opiniões do tipster
3. classificar essas ideias
4. devolver em JSON estruturado

Regras:
- não inventar jogos
- não inventar mercados
- não forçar ideias quando não existirem
- separar crença, medo, entrada e cautela
- marcar ideias não acionáveis como contextual_note
- marcar needs_review quando houver ambiguidade

Formato de saída:
[JSON v1 definido]

(O Claude deve usar exatamente o JSON definido na Parte 5)

69. Plano de implementação (passo a passo)
Fase 1 — Base do sistema
autenticação
cadastro de tipsters
cadastro de canais
banco de dados
APIs básicas
Fase 2 — Monitoramento
integração com YouTube
job de monitoramento
ingestão de vídeos
Fase 3 — Processamento
transcrição
armazenamento
worker de processamento
Fase 4 — Extração
integração com LLM
retorno JSON
salvar análise e ideias
Fase 5 — Interface
página de tipster
página de vídeo
página diária de jogos
Fase 6 — Avaliação
registro manual de resultado
avaliação automática simples
Fase 7 — Dashboard
visão geral
métricas por tipster
70. Estrutura inicial para Git
project-root/
  backend/
  frontend/
  docker-compose.yml
  README.md
README.md deve conter:
descrição do projeto
stack
como rodar localmente
variáveis de ambiente
comandos principais
71. Variáveis de ambiente

Exemplo:

DATABASE_URL=
REDIS_URL=
JWT_SECRET=
YOUTUBE_API_KEY=
OPENAI_API_KEY=
72. Segurança
senha com bcrypt
tokens com expiração
validação de entrada
proteção de rotas
73. Escalabilidade futura
adicionar novos canais facilmente
suportar múltiplos idiomas
melhorar NLP
adicionar automação de resultados
clustering de ideias
🚀 CONCLUSÃO FINAL

Agora você tem:

✔ visão de produto
✔ regras de negócio
✔ modelo de dados
✔ arquitetura
✔ APIs
✔ JSON de extração
✔ fluxo completo
✔ plano de implementação

PARTE 7 — PROMPT MESTRE PARA O CLAUDE GERAR O PROJETO COMPLETO

Abaixo está um prompt já estruturado para você colar no Claude e pedir a implementação completa do sistema, pronta para Git.

74. Prompt mestre para o Claude
Você é um arquiteto de software sênior e desenvolvedor full stack especialista em Python, FastAPI, PostgreSQL, Next.js, Redis, Celery e sistemas com pipelines assíncronos.

Sua tarefa é construir um projeto completo, pronto para Git, baseado na especificação abaixo.

IMPORTANTE:
- gere código real
- gere estrutura de projeto organizada
- use boas práticas
- use arquitetura limpa e modular
- não entregue pseudocódigo
- não simplifique demais a modelagem
- preserve auditabilidade, revisão humana e processamento assíncrono
- o sistema deve estar pronto para evoluir em produção
- se necessário, entregue em etapas, mas sempre com código consistente e integrável
- sempre gere arquivos completos
- sempre respeite a especificação funcional e de dados
- backend em FastAPI
- frontend em Next.js
- banco em PostgreSQL
- filas com Redis + Celery
- autenticação com JWT
- Docker e docker-compose
- estrutura pronta para subir no Git

OBJETIVO DO SISTEMA:
Construir uma plataforma web autenticada que monitora canais do YouTube, analisa vídeos novos periodicamente, extrai jogos mencionados e ideias/opiniões dos tipsters, organiza essas ideias por jogo e por dia, permite registrar resultados e calcula métricas por tipster.

O sistema também deve manter histórico completo de vídeos analisados, inclusive quando não houver jogos, quando não houver ideias acionáveis, ou quando o vídeo for irrelevante.

### VISÃO FUNCIONAL

O sistema deve permitir:
- cadastro de usuários com autenticação
- perfis admin, reviewer e user
- cadastro de tipsters
- cadastro de canais do YouTube
- monitoramento periódico de vídeos novos
- processamento assíncrono dos vídeos
- obtenção de transcrição
- classificação do vídeo por escopo
- identificação de jogos
- extração de ideias por jogo
- revisão humana das extrações
- página diária de jogos
- página do tipster
- página da análise do vídeo
- registro manual de resultados
- avaliação automática simples das ideias objetivas
- dashboards operacionais e analíticos
- audit trail append-only

### PRINCÍPIO DE MODELAGEM

O sistema deve modelar separadamente:
1. o vídeo
2. a análise do vídeo
3. o jogo
4. a ideia extraída
5. as condições da ideia
6. as justificativas da ideia
7. o resultado do jogo
8. a avaliação da ideia

### CLASSIFICAÇÃO DE VÍDEOS

content_scope:
- daily_games
- future_games
- general_analysis
- methodology
- bankroll_management
- trading_education
- promotional
- mixed
- unknown

analysis_status:
- pending
- processing
- analyzed_with_matches
- analyzed_without_matches
- analyzed_without_actionable_ideas
- irrelevant
- failed

### TIPOS DE IDEIA

idea_type:
- possible_entry
- strong_entry
- caution
- no_value
- avoid_game
- watch_live
- trend_read
- risk_alert
- condition_based_entry
- contextual_note

market_type:
- over_0_5
- over_1_5
- over_2_5
- under_2_5
- btts_yes
- btts_no
- home_win
- away_win
- draw_no_bet
- asian_handicap
- corners
- cards
- player_props
- lay
- back
- no_specific_market

sentiment_direction:
- favorable
- unfavorable
- neutral
- conditional

### TABELAS PRINCIPAIS

Implemente modelos e migrations para as seguintes tabelas:

users
roles
user_roles
tipsters
youtube_channels
videos
video_analyses
video_transcripts
transcript_segments
competitions
teams
team_aliases
games
game_aliases
game_ideas
idea_conditions
idea_reasons
idea_labels
idea_reviews
video_analysis_reviews
game_results
idea_evaluations
audit_events
processing_jobs

### CAMPOS IMPORTANTES

#### youtube_channels
- id
- tipster_id
- channel_name
- channel_url
- channel_external_id
- is_active
- monitoring_frequency_minutes
- last_checked_at
- last_video_published_at
- last_video_analyzed_at
- last_successful_analysis_at
- last_failed_analysis_at
- last_irrelevant_video_at
- monitoring_status
- created_at
- updated_at

#### videos
- id
- channel_id
- youtube_video_id
- youtube_url
- title
- description
- thumbnail_url
- published_at
- fetched_at
- duration_seconds
- status
- created_at
- updated_at

#### video_analyses
- id
- video_id
- analysis_url_slug
- analyzed_at
- analysis_status
- content_scope
- summary_text
- games_detected_count
- ideas_detected_count
- actionable_ideas_count
- warnings_count
- no_value_count
- review_status
- reviewer_user_id
- reviewed_at
- model_version
- prompt_version
- schema_version
- raw_output_json
- normalized_output_json
- created_at
- updated_at

#### game_ideas
- id
- game_id
- tipster_id
- video_id
- video_analysis_id
- segment_id
- source_timestamp_start
- source_timestamp_end
- idea_type
- market_type
- selection_label
- sentiment_direction
- confidence_band
- confidence_expression_text
- belief_text
- fear_text
- entry_text
- avoid_text
- rationale_text
- condition_text
- source_excerpt
- is_actionable
- needs_review
- extraction_confidence
- review_status
- created_at
- updated_at

### JSON OFICIAL DE EXTRAÇÃO

O serviço de extração deve trabalhar com este contrato:

{
  "video_analysis": {
    "content_scope": "daily_games | future_games | general_analysis | methodology | bankroll_management | trading_education | promotional | mixed | unknown",
    "analysis_status": "analyzed_with_matches | analyzed_without_matches | analyzed_without_actionable_ideas | irrelevant | failed",
    "summary_text": "",
    "games_detected_count": 0,
    "ideas_detected_count": 0,
    "actionable_ideas_count": 0,
    "warnings_count": 0,
    "no_value_count": 0
  },
  "games": [
    {
      "match_ref": {
        "home": "",
        "away": "",
        "competition": "",
        "scheduled_date": ""
      },
      "ideas": [
        {
          "idea_type": "possible_entry | strong_entry | caution | no_value | avoid_game | watch_live | trend_read | risk_alert | condition_based_entry | contextual_note",
          "market_type": "over_0_5 | over_1_5 | over_2_5 | under_2_5 | btts_yes | btts_no | home_win | away_win | draw_no_bet | asian_handicap | corners | cards | player_props | lay | back | no_specific_market",
          "selection_label": "",
          "sentiment_direction": "favorable | unfavorable | neutral | conditional",
          "confidence_band": "high | medium | low",
          "confidence_expression_text": "",
          "belief_text": "",
          "fear_text": "",
          "entry_text": "",
          "avoid_text": "",
          "rationale_text": "",
          "condition_text": "",
          "source_excerpt": "",
          "source_timestamp_start": 0,
          "source_timestamp_end": 0,
          "is_actionable": true,
          "needs_review": false,
          "extraction_confidence": 0.0,
          "labels": [
            "explicit_prediction",
            "implicit_prediction",
            "caution",
            "contextual_comment",
            "risk_alert",
            "no_value",
            "watch_live"
          ],
          "reasons": [
            {
              "category": "form | defense | attack | motivation | odds | lineup | context | home_advantage | fatigue | market_value | unknown",
              "text": ""
            }
          ],
          "conditions": [
            {
              "condition_type": "lineup | early_goal | live_entry | odds_movement | tactical_setup | unknown",
              "text": "",
              "is_inferred": false
            }
          ]
        }
      ]
    }
  ]
}

### REGRAS DE NEGÓCIO IMPORTANTES

- nem todo vídeo terá jogos
- nem todo vídeo terá ideias acionáveis
- vídeos irrelevantes devem continuar aparecendo no histórico
- a análise do vídeo é uma entidade própria
- a página do tipster deve listar todos os vídeos analisados
- a página do tipster deve mostrar a URL do vídeo e a URL da análise interna
- o canal deve armazenar o último dia de análise
- revisão humana é obrigatória em casos ambíguos
- alterações humanas devem ser auditáveis
- reprocessamento não deve sobrescrever silenciosamente o histórico

### REGRAS DE REVISÃO HUMANA

Enviar para revisão quando:
- extraction_confidence < 0.80
- ideia implícita
- múltiplos mercados
- múltiplos jogos candidatos
- condição complexa
- conflito de entidades
- conflito entre texto e classificação

### PÁGINAS OBRIGATÓRIAS DO FRONTEND

1. Login
2. Dashboard inicial
3. Administração de canais
4. Lista de tipsters
5. Página do tipster
6. Página diária de jogos
7. Página do jogo
8. Página da análise do vídeo
9. Tela de revisão humana

### A PÁGINA DO TIPSTER DEVE MOSTRAR

- nome do tipster
- canal
- URL do canal
- status
- último check
- último vídeo publicado
- último vídeo analisado
- última análise bem-sucedida
- última falha
- total de vídeos analisados
- total de vídeos irrelevantes
- total de jogos detectados
- total de ideias registradas
- total de ideias acionáveis
- assertividade geral
- assertividade por mercado
- lista de vídeos analisados
- URL do vídeo
- URL da análise
- o que foi analisado em cada vídeo

### A PÁGINA DA ANÁLISE DO VÍDEO DEVE MOSTRAR

- título do vídeo
- tipster
- URL do YouTube
- data de publicação
- data de análise
- analysis_status
- content_scope
- resumo da análise
- jogos detectados
- ideias detectadas
- ideias acionáveis
- transcript bruto ou trechos relevantes
- revisões realizadas
- versão do modelo
- versão do prompt
- versão do schema

### A PÁGINA DIÁRIA DE JOGOS DEVE MOSTRAR

Para cada jogo:
- competição
- horário
- mandante x visitante
- tipsters que falaram do jogo
- ideias por tipster
- belief_text
- fear_text
- entry_text
- avoid_text
- market_type
- idea_type
- confidence_band
- links para vídeo e análise
- status da avaliação

### REQUISITOS TÉCNICOS

- usar FastAPI no backend
- usar SQLAlchemy
- usar Alembic para migrations
- usar Pydantic
- usar Next.js no frontend
- usar PostgreSQL
- usar Redis + Celery
- usar Docker e docker-compose
- implementar autenticação JWT
- implementar seed inicial com roles
- implementar estrutura de logs
- implementar audit_events
- preparar projeto para produção
- criar README detalhado
- organizar o projeto em backend e frontend

### ESTRUTURA DE PROJETO ESPERADA

project-root/
  backend/
  frontend/
  docker-compose.yml
  README.md

### BACKEND ESPERADO

/backend
  /app
    /api
    /core
    /models
    /schemas
    /services
    /workers
    /repositories
    /utils
  main.py

### FRONTEND ESPERADO

/frontend
  /app
    /login
    /dashboard
    /tipsters
    /tipster/[id]
    /videos
    /video/[id]
    /games
    /game/[id]
  /components
  /services
  /hooks

### APIs MÍNIMAS

POST /auth/login
POST /auth/register
POST /auth/refresh

GET /tipsters
GET /tipsters/{id}

POST /channels
GET /channels
PATCH /channels/{id}

GET /videos
GET /videos/{id}

GET /video-analyses/{id}

GET /games?date=YYYY-MM-DD
GET /games/{id}

GET /ideas?game_id=

POST /game-results

GET /dashboard

### FASES DE IMPLEMENTAÇÃO

Fase 1:
- estrutura do projeto
- autenticação
- banco
- models
- migrations
- seed de roles

Fase 2:
- tipsters
- canais
- vídeos
- APIs CRUD principais

Fase 3:
- monitoramento de canais
- workers
- ingestão de vídeos

Fase 4:
- transcrição
- extração JSON
- gravação de análises e ideias

Fase 5:
- páginas do frontend
- dashboards
- tela de revisão

Fase 6:
- registro de resultados
- avaliação
- auditoria

### O QUE ESPERO COMO SAÍDA

Quero que você gere:

1. estrutura completa de pastas
2. backend funcional
3. frontend funcional
4. models e migrations
5. endpoints principais
6. workers e tasks
7. schemas Pydantic
8. serviço de monitoramento
9. serviço de extração
10. páginas do frontend
11. docker-compose
12. README
13. arquivos prontos para Git

### MUITO IMPORTANTE

- não resuma
- não descreva apenas
- gere os arquivos
- gere código completo
- respeite a especificação
- se a resposta ficar grande, entregue em múltiplas partes, mas mantendo consistência
- comece pela estrutura do projeto e backend base
75. Prompt complementar para a etapa de extração

Esse prompt pode ser usado pelo Claude para gerar o serviço de extração ou para você usar depois dentro do sistema.

Você é um extrator estruturado de ideias de vídeos de tipsters esportivos.

Receberá a transcrição de um vídeo do YouTube sobre futebol, apostas ou trading esportivo.

Sua tarefa:
1. identificar se o vídeo fala de jogos do dia, jogos futuros, metodologia ou outro escopo
2. identificar jogos mencionados
3. extrair ideias do tipster por jogo
4. separar:
   - belief_text
   - fear_text
   - entry_text
   - avoid_text
   - rationale_text
   - condition_text
5. classificar cada ideia
6. devolver SOMENTE JSON válido no formato especificado

Regras:
- não invente jogos
- não invente mercados
- não force ideia quando não existir
- se o vídeo não tiver jogos, retorne games vazios
- se o vídeo for irrelevante, marque analysis_status adequadamente
- use needs_review=true quando houver ambiguidade
- comentários sem acionabilidade devem virar contextual_note
- frases como “não vejo valor”, “cuidado”, “time reserva”, “jogo perigoso” devem ser preservadas como sinais analíticos

Saída:
retorne apenas JSON
76. Ordem ideal para pedir ao Claude

Para reduzir erro e evitar respostas muito bagunçadas, peça em etapas.

Etapa 1

Peça:

estrutura do projeto
backend base
models
migrations
autenticação
Etapa 2

Peça:

CRUD de tipsters, canais, vídeos, análises
workers
monitoramento
Etapa 3

Peça:

serviço de extração
integração do JSON
revisão humana
avaliação
Etapa 4

Peça:

frontend
páginas
dashboards
refinamento visual
77. Ordem ideal para subir no Git
Primeiro commit
estrutura inicial
docker-compose
backend base
frontend base
Segundo commit
banco + migrations + auth
Terceiro commit
tipsters + canais + vídeos
Quarto commit
workers + monitoramento + transcrição
Quinto commit
extração + análises + ideias
Sexto commit
revisão + resultados + avaliação
Sétimo commit
dashboards + páginas finais
78. Critérios de aceite do MVP

O MVP será considerado pronto quando permitir:

login funcional
cadastro de tipster
cadastro de canal
descoberta de vídeos
criação de registro de vídeo
criação de análise do vídeo
extração de ao menos ideias simples
exibição da página do tipster
exibição da página da análise do vídeo
exibição da página diária de jogos
lançamento manual de resultado
avaliação automática simples
trilha básica de auditoria
79. Itens que o Claude deve evitar

Peça para ele evitar:

criar sistema excessivamente genérico
simplificar o banco demais
esconder histórico
tratar todo comentário como entrada
remover vídeos sem jogos
ignorar video_analyses
misturar vídeo com ideia
misturar confiança do modelo com confiança do tipster
sobrescrever revisões sem auditoria
80. Recomendação final de uso

O melhor uso agora é:

pegar a Parte 1 a Parte 7
colar tudo em um documento
mandar para o Claude com o prompt mestre
pedir entrega em etapas
revisar cada etapa antes da próxima
Fechamento

Agora você tem o pacote completo de especificação para desenvolvimento:

visão do produto
arquitetura
modelo de dados
regras de negócio
páginas
dashboards
JSON oficial
APIs
stack
prompt mestre para geração
