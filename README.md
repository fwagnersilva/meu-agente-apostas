# Tipster Monitor — Plataforma de Análise de Tipsters do YouTube

> Monitora canais do YouTube, transcreve vídeos, extrai ideias de tipsters com IA e organiza tudo em um painel analítico com histórico completo, revisão humana e avaliação de assertividade.

---

## Índice

1. [Objetivo](#objetivo)
2. [Problema que resolve](#problema-que-resolve)
3. [Princípio central](#princípio-central)
4. [Requisitos funcionais (resumo)](#requisitos-funcionais-resumo)
5. [Regras de negócio essenciais](#regras-de-negócio-essenciais)
6. [Arquitetura](#arquitetura)
7. [Stack tecnológica](#stack-tecnológica)
8. [Estrutura do projeto](#estrutura-do-projeto)
9. [Como rodar localmente](#como-rodar-localmente)
10. [Variáveis de ambiente](#variáveis-de-ambiente)
11. [Banco de dados](#banco-de-dados)
12. [API — endpoints principais](#api--endpoints-principais)
13. [Plano de implementação por fases](#plano-de-implementação-por-fases)
14. [Critérios do MVP](#critérios-do-mvp)

---

## Objetivo

Construir uma **plataforma web autenticada** que:

- Monitora canais do YouTube automaticamente
- Analisa vídeos novos periodicamente via IA (LLM)
- Extrai jogos mencionados pelos tipsters
- Identifica e classifica ideias/opiniões por jogo
- Organiza as ideias por jogo e por dia
- Permite registrar resultados reais
- Calcula assertividade por tipster, mercado e tipo de ideia
- Mantém **histórico completo** de todos os vídeos, inclusive irrelevantes ou sem ideias acionáveis

---

## Problema que resolve

Hoje o conteúdo de tipsters esportivos se perde em vídeos longos. Não há:
- Histórico estruturado de análises
- Forma de comparar performance entre tipsters
- Rastreabilidade das ideias ditas

O sistema resolve isso transformando **fala em dados estruturados, histórico consultável e inteligência comparativa**.

---

## Princípio central

O sistema modela separadamente:

| Camada | O que representa |
|--------|-----------------|
| **Vídeo** | Metadados do vídeo no YouTube |
| **Análise do vídeo** | Resultado analítico do processamento (sempre gerada, mesmo sem jogos) |
| **Jogo** | Partida identificada na transcrição |
| **Ideia** | Opinião/leitura do tipster sobre um mercado de um jogo |
| **Condições da ideia** | Condições explícitas ou inferidas ligadas à ideia |
| **Justificativas** | Razões categorizadas da ideia |
| **Resultado** | Placar real do jogo |
| **Avaliação** | Acerto ou erro da ideia após resultado |

---

## Requisitos funcionais (resumo)

| Código | Requisito |
|--------|-----------|
| RF01–03 | Autenticação: login, perfis (admin/reviewer/user), recuperação de senha |
| RF04–05 | Cadastro de tipsters e canais do YouTube |
| RF06–08 | Monitoramento periódico de vídeos, ingestão, deduplicação |
| RF09–11 | Transcrição, normalização e segmentação do conteúdo |
| RF12–18 | Classificação do vídeo, detecção de jogos, extração de ideias com IA |
| RF19 | Registro de análise **sempre** criado, mesmo sem jogos ou ideias |
| RF20–24 | Páginas: diária de jogos, jogo, tipster, análise do vídeo |
| RF26–27 | Revisão humana e reprocessamento |
| RF28–30 | Registro de resultado, avaliação automática e manual |
| RF31–35 | Dashboards, auditoria, logs de falha, histórico completo |

---

## Regras de negócio essenciais

| Código | Regra |
|--------|-------|
| **RN01** | Nem todo vídeo gera jogos |
| **RN02** | Nem todo vídeo gera ideias acionáveis |
| **RN03** | Vídeos irrelevantes continuam visíveis no histórico do tipster |
| **RN04** | Uma ideia pode ser: entrada, tendência, medo, cautela, ausência de valor, alerta |
| **RN05** | Nem toda ideia tem avaliação automática |
| **RN06** | Revisão humana é parte obrigatória para casos ambíguos |
| **RN10** | A análise do vídeo é uma entidade própria — sempre criada |
| **RN12** | Resultado manual é aceitável no MVP |
| **RN14** | Toda alteração humana gera evento de auditoria |
| **RN15** | Reprocessamento não sobrescreve histórico silenciosamente |

### Tipos de ideia (`idea_type`)

```
possible_entry | strong_entry | caution | no_value | avoid_game
watch_live | trend_read | risk_alert | condition_based_entry | contextual_note
```

### Tipos de mercado (`market_type`)

```
over_0_5 | over_1_5 | over_2_5 | under_2_5 | btts_yes | btts_no
home_win | away_win | draw_no_bet | asian_handicap
corners | cards | player_props | lay | back | no_specific_market
```

### Status de análise do vídeo (`analysis_status`)

```
pending | processing | analyzed_with_matches | analyzed_without_matches
analyzed_without_actionable_ideas | irrelevant | failed
```

### Critério de envio para revisão humana

Ideia vai para revisão quando:
- `extraction_confidence < 0.80`
- Ideia implícita ou com múltiplos mercados candidatos
- Condição complexa ou conflito de entidades

---

## Arquitetura

```
Frontend (Next.js)
       ↓
API Gateway (FastAPI)
       ↓
Services Layer (Python)
       ↓
Database (PostgreSQL)
       ↕
Workers (Celery + Redis)
       ↓
External APIs (YouTube, Whisper, LLM)
```

**Princípios:**
- Processamento de vídeos 100% assíncrono (workers)
- Separação entre ingestão, processamento e exibição
- Auditabilidade completa (append-only)
- Human-in-the-loop (revisão humana)
- Versionamento de modelo/prompt/schema por extração
- Tolerância a falhas (falha em um vídeo não trava o pipeline)

---

## Stack tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic |
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS |
| Banco de dados | PostgreSQL 16 |
| Filas | Redis 7 + Celery |
| Autenticação | JWT (access + refresh token), bcrypt |
| IA / NLP | Claude (Anthropic) ou OpenAI GPT |
| Transcrição | YouTube Transcript API ou Whisper |
| Infraestrutura | Docker, Docker Compose |

---

## Estrutura do projeto

```
meu-agente-apostas/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Endpoints HTTP (auth, tipsters, channels, ...)
│   │   ├── core/               # Config, database, security, dependencies
│   │   ├── models/             # Modelos SQLAlchemy (24 tabelas)
│   │   ├── schemas/            # Schemas Pydantic (request/response)
│   │   ├── services/           # Lógica de negócio
│   │   ├── workers/            # Tasks Celery assíncronas
│   │   ├── repositories/       # Acesso ao banco (queries)
│   │   └── utils/              # Utilitários (seed, helpers)
│   ├── alembic/                # Migrations do banco
│   ├── main.py                 # Entrypoint FastAPI
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                    # Páginas Next.js (App Router)
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── tipsters/
│   │   ├── games/
│   │   └── videos/
│   ├── components/             # Componentes reutilizáveis
│   ├── services/               # Cliente HTTP (axios)
│   ├── stores/                 # Estado global (zustand)
│   ├── hooks/                  # Custom hooks
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Como rodar localmente

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### 1. Clone o repositório

```bash
git clone https://github.com/fwagnersilva/meu-agente-apostas.git
cd meu-agente-apostas
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas chaves (YouTube API, OpenAI/Anthropic, etc.)
```

### 3. Suba todos os serviços

```bash
docker-compose up -d
```

### 4. Execute as migrations

```bash
docker-compose exec backend alembic upgrade head
```

> O seed de roles e usuário admin roda automaticamente na inicialização do backend.

### 5. Acesse

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API (docs) | http://localhost:8000/docs |
| API (redoc) | http://localhost:8000/redoc |

### Credenciais padrão (seed)

```
Email: admin@tipster.local
Senha: admin1234
```

> **Troque a senha imediatamente após o primeiro login em produção.**

---

## Variáveis de ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `DATABASE_URL` | URL de conexão PostgreSQL (asyncpg) | Sim |
| `REDIS_URL` | URL do Redis | Sim |
| `JWT_SECRET` | Chave secreta para assinar tokens JWT | Sim |
| `YOUTUBE_API_KEY` | Chave da YouTube Data API v3 | Fase 2 |
| `OPENAI_API_KEY` | Chave da OpenAI (GPT) | Fase 4 |
| `ANTHROPIC_API_KEY` | Chave da Anthropic (Claude) | Fase 4 |
| `CORS_ORIGINS` | Origens permitidas pelo CORS | Sim |
| `NEXT_PUBLIC_API_URL` | URL da API (para o frontend) | Sim |

---

## Banco de dados

### Tabelas principais

| Tabela | Descrição |
|--------|-----------|
| `users`, `roles`, `user_roles` | Autenticação e perfis |
| `tipsters` | Cadastro lógico dos criadores |
| `youtube_channels` | Canais monitorados |
| `videos` | Metadados dos vídeos |
| `video_analyses` | **Resultado analítico** (sempre criado, mesmo sem jogos) |
| `video_transcripts`, `transcript_segments` | Transcrição e segmentos |
| `competitions`, `teams`, `team_aliases` | Entidades esportivas |
| `games`, `game_aliases` | Jogos identificados |
| `game_ideas` | **Tabela central** — ideias dos tipsters por jogo |
| `idea_conditions`, `idea_reasons`, `idea_labels` | Detalhes das ideias |
| `idea_reviews`, `video_analysis_reviews` | Revisões humanas |
| `game_results` | Resultado real dos jogos |
| `idea_evaluations` | Avaliação de acerto/erro |
| `audit_events` | Ledger append-only de toda ação |
| `processing_jobs` | Controle de jobs assíncronos |

### Executar migrations

```bash
# Subir todas as migrations
docker-compose exec backend alembic upgrade head

# Criar nova migration (após alterar modelos)
docker-compose exec backend alembic revision --autogenerate -m "descricao"

# Reverter última migration
docker-compose exec backend alembic downgrade -1
```

---

## API — endpoints principais

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/auth/login` | Login com email e senha |
| POST | `/api/v1/auth/register` | Criar novo usuário |
| POST | `/api/v1/auth/refresh` | Renovar access token |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado |

### Tipsters e Canais *(Fase 2)*

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/tipsters` | Listar tipsters |
| GET | `/api/v1/tipsters/{id}` | Detalhes + métricas |
| POST | `/api/v1/tipsters` | Criar tipster (admin) |
| PATCH | `/api/v1/tipsters/{id}` | Editar tipster (admin) |
| DELETE | `/api/v1/tipsters/{id}` | Inativar tipster (admin) |
| POST | `/api/v1/channels` | Cadastrar canal |
| GET | `/api/v1/channels` | Listar canais |
| PATCH | `/api/v1/channels/{id}` | Editar canal |
| POST | `/api/v1/channels/{id}/pause` | Pausar monitoramento |
| POST | `/api/v1/channels/{id}/activate` | Ativar monitoramento |
| POST | `/api/v1/channels/{id}/trigger-monitor` | Disparar check manual |

### Vídeos e Análises *(Fase 4)*

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/videos` | Listar vídeos |
| GET | `/api/v1/videos/{id}` | Detalhes do vídeo |
| GET | `/api/v1/video-analyses/{id}` | Análise completa do vídeo (com transcript e segmentos) |
| GET | `/api/v1/video-analyses/by-slug/{slug}` | Análise por slug de URL |
| GET | `/api/v1/video-analyses/by-video/{video_id}` | Todas as análises de um vídeo |

### Jogos e Ideias *(Fase 4)*

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/games?date=YYYY-MM-DD` | Jogos do dia com ideias |
| GET | `/api/v1/games/{id}` | Detalhes do jogo |
| GET | `/api/v1/ideas?game_id=` | Ideias de um jogo |

### Resultados e Dashboard *(Fase 6–7)*

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/game-results` | Registrar resultado |
| GET | `/api/v1/dashboard` | Resumo geral |

---

## Plano de implementação por fases

| Fase | Conteúdo | Status |
|------|----------|--------|
| **Fase 1** | Estrutura do projeto, autenticação JWT, banco de dados, modelos, migrations, seed | ✅ Concluída |
| **Fase 2** | CRUD de tipsters e canais, monitoramento periódico via YouTube API | ✅ Concluída |
| **Fase 3** | Pipeline de processamento: transcrição, normalização, segmentação | ✅ Concluída |
| **Fase 4** | Extração de ideias via LLM, APIs de vídeos/jogos/ideias, revisão humana | ✅ Concluída |
| **Fase 5** | Frontend completo: login, dashboard, tipsters, jogos, vídeos, revisão | ✅ Concluída |
| **Fase 6** | Registro de resultados, avaliação automática, auditoria | ✅ Concluída |
| **Fase 7** | Dashboards analíticos, comparativo de tipsters, métricas avançadas | ✅ Concluída |

---

## Critérios do MVP

O MVP está pronto quando permitir:

- [x] Login funcional
- [ ] Cadastro de tipster e canal
- [ ] Descoberta periódica de vídeos
- [ ] Transcrição e extração básica de ideias
- [ ] Análise do vídeo sempre registrada (mesmo sem jogos)
- [ ] Revisão humana de ideias ambíguas
- [ ] Página diária de jogos
- [ ] Página do tipster com histórico completo
- [ ] Página da análise do vídeo
- [ ] Registro manual de resultado
- [ ] Avaliação automática simples (over 1.5, btts, home_win...)
- [ ] Trilha de auditoria básica

**Fora do MVP:** integração automática com APIs esportivas, avaliação avançada de condicionais, prosódia/áudio avançado, clustering semântico de ideias, recomendação automática própria.

---

## Issues no GitHub

O desenvolvimento é rastreado via [GitHub Issues](https://github.com/fwagnersilva/meu-agente-apostas/issues), organizadas por fase com labels `fase-1` a `fase-7`, `backend`, `frontend`, `banco-de-dados` e `ia-nlp`.
