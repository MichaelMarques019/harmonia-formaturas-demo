<div align="center">

# 🎓 Harmonia Formaturas & Buffet
### Sistema completo de gerenciamento e entrega de álbuns digitais

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)

**Sistema web desenvolvido do zero — do banco de dados ao deploy em produção.**

[🔗 Ver ao vivo](https://harmonia-formaturas.onrender.com) · [💼 Portfólio](https://michael-douglas.netlify.app) · [👤 LinkedIn](https://www.linkedin.com/in/michael-marques019/)

</div>

---

## 📋 Sobre o projeto

Sistema criado para **empresas de formatura e buffet** gerenciarem a entrega de álbuns digitais aos formandos. O cliente recebe um link com login e senha, acessa seus álbuns e tem **7 dias** para baixar antes do prazo expirar.

O sistema conta com **3 níveis de acesso** — cliente, vendedor e administrador — cada um com sua área específica e funcionalidades dedicadas.

---

## ✨ Funcionalidades por área

### 👤 Área do Cliente
- Login seguro com prazo de 7 dias configurável
- **Countdown em tempo real** (dias, horas, minutos e segundos)
- Download direto do servidor ou via Google Drive
- Botão de Visualizar separado do Baixar (rastreamento independente)
- Caixa de confirmação antes do download com checklist de segurança
- Tela de sucesso pós-download com dicas de onde salvar
- **Avaliação do serviço** com nota (1–5 estrelas) e comentário
- Cadastro de e-mail para lembretes automáticos
- Histórico de acessos (data e hora de cada visualização e download)
- Botão flutuante de suporte via WhatsApp
- **Multi-idioma** (Português · English · Español)
- **Modo claro / escuro** com preferência salva no navegador
- **PWA** — instalável como app na tela inicial do celular

### 🛠️ Painel Administrativo
- **Dashboard** com gráficos de atividade dos últimos 7 dias
- Gráfico de rosca: baixaram × aguardando × expirados
- **Busca rápida** de clientes por nome
- **Filtros** por status: Todos / Baixou / Pendente / Expirado
- **Tags** coloridas nos clientes (VIP, Indicação, Pendente pagamento...)
- **Calendário de expirações** — próximos 30 dias com alertas visuais
- **Ranking mensal de vendedores** com valor total vendido
- Envio de notificação via WhatsApp (mensagem pré-formatada)
- **Envio em lote** — lista todos pendentes com botão WhatsApp por cliente
- **Lembrete automático** — botão ⏰ aparece quando faltam ≤ 3 dias
- E-mail automático de boas-vindas ao criar cliente (Flask-Mail + Gmail)
- **Renovação de prazo** com um clique
- Upload de arquivo direto pelo site (até 15 GB) + link Drive como alternativa
- **Backup do banco** em um clique com download do arquivo `.db`
- **Banner de alerta de backup** — avisa quando passa de 7 dias sem backup
- **Central de notificações** — clientes expirando hoje, visualizaram mas não baixaram
- **Gerenciamento de disco** — lista arquivos, tamanho total, remove órfãos
- **Log de atividades** — histórico completo de tudo que aconteceu no sistema
- **Log de tentativas de login** — IPs suspeitos com 5+ falhas
- **Avaliações dos clientes** — média geral e comentários
- **Modo manutenção** — toggle que exibe tela de manutenção sem derrubar o site
- **Template de WhatsApp editável** pelo painel sem mexer no código
- **Configurações globais** — prazo, número de suporte, timeout de sessão

### 🧑‍💼 Módulo do Vendedor
- Login individual por vendedor com escolas restritas por configuração
- **Modo apresentação** — tela cheia sem menu para mostrar ao cliente
- **Galeria integrada** — embed do Google Drive na página
- **Registro de atendimentos** — nome, telefone, endereço, status, valor e observação
- Status por atendimento: Com interesse / Vendido / Não quis
- **Agenda de visitas** — próximas e passadas com data e hora
- **Histórico completo** com resumo de vendas e valor total
- Resumo do mês na tela inicial (visitas, vendidos, valor em R$)
- Botão para enviar link do site ao cliente via WhatsApp na hora da visita

---

## 🛠️ Tecnologias utilizadas

| Categoria | Tecnologia |
|-----------|-----------|
| **Linguagem** | Python 3.11 |
| **Framework** | Flask 3.0 |
| **ORM** | SQLAlchemy 2.0 |
| **Banco de dados** | SQLite (produção com disco persistente) |
| **Autenticação** | Werkzeug Security (hash de senhas) |
| **E-mail** | Flask-Mail + Gmail SMTP |
| **Templates** | Jinja2 |
| **Frontend** | HTML5 + CSS3 + JavaScript puro |
| **Deploy** | Render (Gunicorn) |
| **PWA** | Web App Manifest + Service Worker |
| **Design** | CSS Variables, dark/light mode, responsivo |

---

## 📁 Estrutura do projeto

```
harmonia/
├── app.py                      # Aplicação principal (~1500 linhas, 25+ rotas)
├── requirements.txt            # Dependências Python
├── Procfile                    # Configuração do servidor Gunicorn
├── render.yaml                 # Infraestrutura como código (Render)
├── .gitignore                  # Arquivos ignorados pelo Git
│
├── static/
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service Worker
│
└── templates/                  # 35 templates Jinja2
    ├── base.html               # Layout base (nav, estilos, dark mode, i18n)
    ├── index.html              # Landing page pública
    ├── login.html              # Login do cliente
    ├── area_cliente.html       # Área do formando
    ├── cliente_email.html      # Cadastro de e-mail para lembretes
    │
    ├── admin_login.html
    ├── admin_painel.html       # Painel principal com dashboard e gráficos
    ├── admin_configuracoes.html
    ├── admin_notificacoes.html
    ├── admin_novo_cliente.html
    ├── admin_editar_cliente.html
    ├── admin_novo_album.html
    ├── admin_editar_album.html
    ├── admin_nova_escola.html
    ├── admin_lembrete.html
    ├── admin_whatsapp.html
    ├── admin_lote_whatsapp.html
    ├── admin_avaliacoes.html
    ├── admin_login_falhas.html
    ├── admin_arquivos.html
    │
    ├── vendedor_login.html
    ├── vendedor_painel.html
    ├── vendedor_escola.html
    ├── vendedor_album.html
    ├── vendedor_apresentar.html # Modo tela cheia
    ├── vendedor_galeria.html
    ├── vendedor_agenda.html
    ├── vendedor_historico.html
    │
    ├── manutencao.html         # Tela de manutenção
    └── erro.html               # Páginas de erro 404 / 500
```

---

## ⚙️ Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/harmonia-formaturas-demo
cd harmonia-formaturas-demo

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o servidor
python app.py
```

Acesse: **http://127.0.0.1:5000**

**Credenciais de demonstração:**
- Admin: `/admin/login` → senha `harmonia@admin2024`
- Vendedor: `/vendedor/login` → crie um na área admin

---

## 🔑 Variáveis de ambiente (produção)

Configure no painel do Render antes do deploy:

| Variável | Descrição | Obrigatório |
|---|---|---|
| `SECRET_KEY` | Chave secreta do Flask (gere uma aleatória longa) | ✅ |
| `ADMIN_PASSWORD` | Senha do painel administrativo | ✅ |
| `SITE_URL` | URL pública do site (ex: `https://harmonia.onrender.com`) | ✅ |
| `MAIL_USERNAME` | Gmail para envio de e-mails | ⚪ Opcional |
| `MAIL_PASSWORD` | Senha de app do Gmail | ⚪ Opcional |
| `SUPORTE_WHATSAPP` | Número do WhatsApp de suporte (55+DDD+número) | ⚪ Opcional |

---

## 🚀 Deploy no Render

1. Fork ou clone este repositório para o seu GitHub
2. Crie uma conta em [render.com](https://render.com)
3. New → Web Service → conecte o repositório
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Starter ($7/mês) — necessário para disco persistente
5. Adicione as variáveis de ambiente
6. Deploy!

---

## 📸 Screenshots

> *Em breve — adicionar prints do sistema funcionando*

---

## 👨‍💻 Desenvolvedor

<div align="center">

**Michael Douglas Marques dos Santos**

18 anos · Análise e Desenvolvimento de Sistemas (1° semestre)
CEUNSP — Salto, São Paulo

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/michael-marques019/)
[![Portfólio](https://img.shields.io/badge/Portfólio-FF2D55?style=for-the-badge&logo=firefox&logoColor=white)](https://michael-douglas.netlify.app)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MichaelMarques019)

</div>

---

<div align="center">
<sub>Desenvolvido com 💻 e muita dedicação · 2025</sub>
</div>
