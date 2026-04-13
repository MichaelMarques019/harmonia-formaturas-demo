# ═══════════════════════════════════════════════════════════════════
# HARMONIA FORMATURAS & BUFFET — Sistema de Álbuns Digitais
# ═══════════════════════════════════════════════════════════════════
#
# Desenvolvido por: Michael Douglas Marques dos Santos
# Curso: ADS 1° semestre — CEUNSP Salto, SP
# GitHub: https://github.com/MichaelMarques019
# LinkedIn: https://www.linkedin.com/in/michael-marques019/
#
# VERSÃO DEMO — Para uso em produção configure as variáveis de ambiente:
#   SECRET_KEY, ADMIN_PASSWORD, SITE_URL, MAIL_USERNAME, MAIL_PASSWORD
#
# Como rodar localmente:
#   pip install -r requirements.txt
#   python app.py
#   Acesse: http://127.0.0.1:5000
#   Admin: /admin/login  →  senha: harmonia@admin2024
# ═══════════════════════════════════════════════════════════════════

import os, json, shutil, uuid
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote as url_quote

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file, g)
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ── Core config ──────────────────────────────
app.config['SECRET_KEY']                    = os.environ.get('SECRET_KEY', 'harmonia-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI']       = 'sqlite:///harmonia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
app.config['ADMIN_PASSWORD']                = os.environ.get('ADMIN_PASSWORD', 'harmonia@admin2024')
app.config['DIAS_EXPIRACAO']                = 7
app.config['SITE_URL']                      = os.environ.get('SITE_URL', 'http://127.0.0.1:5000')
app.config['SUPORTE_WHATSAPP']              = os.environ.get('SUPORTE_WHATSAPP', '5519999998888')
app.config['SESSION_TIMEOUT_MINUTES']       = 60   # inatividade em minutos

# ── Upload ────────────────────────────────────
app.config['UPLOAD_FOLDER']      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'zip','rar','7z','pdf','jpg','jpeg','png','mp4','mov'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ── E-mail (Flask-Mail via Gmail) ─────────────
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', '')

# ── Web Push VAPID keys ───────────────────────
app.config['VAPID_PUBLIC_KEY']  = os.environ.get('VAPID_PUBLIC_KEY', '')
app.config['VAPID_PRIVATE_KEY'] = os.environ.get('VAPID_PRIVATE_KEY', '')
app.config['VAPID_CLAIMS']      = {'sub': 'mailto:' + os.environ.get('MAIL_USERNAME', 'harmonia@gmail.com')}

# ── Default WhatsApp message template ────────
app.config['MSG_TEMPLATE'] = (
    "Olá, {primeiro}! 🎓\n\n"
    "Seus álbuns digitais da *Harmonia Formaturas & Buffet* estão prontos!\n\n"
    "📸 *{titulo}*\n\n"
    "🌐 Acesse: {site_url}\n"
    "👤 Usuário: {login}\n"
    "🔑 Senha: {senha}\n\n"
    "⚠️ *Atenção:* o link expira em *{expira}* ({dias} dia{s} restante{s2}). "
    "Faça o download e salve em local seguro!\n\n"
    "Qualquer dúvida estamos à disposição. 💛\n\n"
    "_Harmonia Formaturas & Buffet_"
)

db   = SQLAlchemy(app)
mail = Mail(app)


# ══════════════════════════════════════════════
#  TRANSLATIONS (i18n simples sem dependência)
# ══════════════════════════════════════════════
TRANSLATIONS = {
    'pt': {
        'login_title': 'Área do Formando',
        'login_sub': 'Acesse seus álbuns digitais',
        'login_user': 'Usuário', 'login_pass': 'Senha',
        'login_btn': 'Entrar', 'login_wrong': 'Usuário ou senha incorretos.',
        'hello': 'Olá', 'my_albums': 'Meus álbuns',
        'notice_expire': 'Seus arquivos ficam disponíveis por',
        'notice_days': 'dias após o envio.',
        'notice_warn': 'Após esse prazo o acesso expira permanentemente. Guarde seus arquivos em local seguro.',
        'btn_view': 'Visualizar', 'btn_download': 'Baixar álbum',
        'btn_redownload': 'Baixar novamente', 'btn_expired': 'Acesso expirado',
        'btn_waiting': 'Aguardando arquivo', 'btn_logout': 'Sair da conta',
        'downloaded': 'Baixado', 'viewed': 'Visualizado', 'expires_in': 'dias',
        'confirm_title': 'Antes de baixar:', 'confirm_btn': 'Confirmar e baixar',
        'confirm_cancel': 'Cancelar', 'confirm_text': 'Salve o arquivo em local seguro.',
        'success_title': 'Download iniciado!', 'success_sub': 'Lembre-se de salvar em local seguro:',
        'check1': 'HD externo ou pendrive', 'check2': 'Google Drive pessoal ou iCloud',
        'check3': 'Computador e celular',
        'rate_title': 'Avalie sua experiência',
        'rate_sub': 'Sua opinião é muito importante para nós!',
        'rate_comment': 'Comentário (opcional)',
        'rate_btn': 'Enviar avaliação', 'rate_thanks': 'Obrigado pela avaliação!',
        'history_title': 'Histórico de acessos',
        'history_empty': 'Nenhum acesso registrado ainda.',
        'support': 'Precisa de ajuda? Fale conosco',
        'lang_label': 'Idioma',
    },
    'en': {
        'login_title': 'Student Area',
        'login_sub': 'Access your digital albums',
        'login_user': 'Username', 'login_pass': 'Password',
        'login_btn': 'Sign in', 'login_wrong': 'Incorrect username or password.',
        'hello': 'Hello', 'my_albums': 'My albums',
        'notice_expire': 'Your files are available for',
        'notice_days': 'days after delivery.',
        'notice_warn': 'After this period access expires permanently. Store your files in a safe location.',
        'btn_view': 'View', 'btn_download': 'Download album',
        'btn_redownload': 'Download again', 'btn_expired': 'Access expired',
        'btn_waiting': 'Awaiting file', 'btn_logout': 'Sign out',
        'downloaded': 'Downloaded', 'viewed': 'Viewed', 'expires_in': 'days',
        'confirm_title': 'Before downloading:', 'confirm_btn': 'Confirm & download',
        'confirm_cancel': 'Cancel', 'confirm_text': 'Save the file to a safe location.',
        'success_title': 'Download started!', 'success_sub': 'Remember to save in a safe location:',
        'check1': 'External HD or USB drive', 'check2': 'Google Drive or iCloud',
        'check3': 'Computer and phone',
        'rate_title': 'Rate your experience',
        'rate_sub': 'Your feedback means a lot to us!',
        'rate_comment': 'Comment (optional)',
        'rate_btn': 'Submit review', 'rate_thanks': 'Thanks for your review!',
        'history_title': 'Access history',
        'history_empty': 'No access records yet.',
        'support': 'Need help? Chat with us',
        'lang_label': 'Language',
    },
    'es': {
        'login_title': 'Área del Graduado',
        'login_sub': 'Accede a tus álbumes digitales',
        'login_user': 'Usuario', 'login_pass': 'Contraseña',
        'login_btn': 'Entrar', 'login_wrong': 'Usuario o contraseña incorrectos.',
        'hello': 'Hola', 'my_albums': 'Mis álbumes',
        'notice_expire': 'Tus archivos están disponibles por',
        'notice_days': 'días tras el envío.',
        'notice_warn': 'Después de ese plazo el acceso expira permanentemente. Guarda tus archivos en un lugar seguro.',
        'btn_view': 'Ver', 'btn_download': 'Descargar álbum',
        'btn_redownload': 'Descargar de nuevo', 'btn_expired': 'Acceso expirado',
        'btn_waiting': 'Esperando archivo', 'btn_logout': 'Cerrar sesión',
        'downloaded': 'Descargado', 'viewed': 'Visto', 'expires_in': 'días',
        'confirm_title': 'Antes de descargar:', 'confirm_btn': 'Confirmar y descargar',
        'confirm_cancel': 'Cancelar', 'confirm_text': 'Guarda el archivo en un lugar seguro.',
        'success_title': '¡Descarga iniciada!', 'success_sub': 'Recuerda guardar en un lugar seguro:',
        'check1': 'Disco externo o USB', 'check2': 'Google Drive o iCloud',
        'check3': 'Computadora y teléfono',
        'rate_title': 'Califica tu experiencia',
        'rate_sub': '¡Tu opinión es muy importante para nosotros!',
        'rate_comment': 'Comentario (opcional)',
        'rate_btn': 'Enviar calificación', 'rate_thanks': '¡Gracias por tu calificación!',
        'history_title': 'Historial de accesos',
        'history_empty': 'Aún no hay registros de acceso.',
        'support': '¿Necesitas ayuda? Chatea con nosotros',
        'lang_label': 'Idioma',
    }
}

def t(key):
    lang = session.get('lang', 'pt')
    return TRANSLATIONS.get(lang, TRANSLATIONS['pt']).get(key, key)

app.jinja_env.globals['t'] = t
app.jinja_env.globals['TRANSLATIONS'] = TRANSLATIONS


# ══════════════════════════════════════════════
#  MODELS
# ══════════════════════════════════════════════
class Escola(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(200), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    albums    = db.relationship('Album', backref='escola', lazy=True, cascade='all,delete')


class Album(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    escola_id    = db.Column(db.Integer, db.ForeignKey('escola.id'), nullable=False)
    titulo       = db.Column(db.String(200), nullable=False)
    descricao    = db.Column(db.String(400))
    drive_url    = db.Column(db.String(500))
    nome_arquivo = db.Column(db.String(300))
    tamanho_fmt  = db.Column(db.String(30))
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)
    clientes     = db.relationship('ClienteAlbum', backref='album', lazy=True, cascade='all,delete')
    vendas       = db.relationship('VendaAnotacao', backref='album', lazy=True, cascade='all,delete')


class Cliente(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(120), nullable=False)
    evento     = db.Column(db.String(120))
    login      = db.Column(db.String(60), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    telefone   = db.Column(db.String(30))
    email      = db.Column(db.String(120))          # e-mail para lembretes
    push_sub   = db.Column(db.Text)                 # JSON da subscrição Web Push
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)
    acessos    = db.relationship('ClienteAlbum', backref='cliente', lazy=True, cascade='all,delete')
    avaliacoes = db.relationship('Avaliacao', backref='cliente', lazy=True, cascade='all,delete')

    def set_senha(self, s):   self.senha_hash = generate_password_hash(s)
    def check_senha(self, s): return check_password_hash(self.senha_hash, s)


class ClienteAlbum(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    cliente_id      = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    album_id        = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    expira_em       = db.Column(db.DateTime)
    visualizado     = db.Column(db.Boolean, default=False)
    dt_visualizacao = db.Column(db.DateTime)
    baixado         = db.Column(db.Boolean, default=False)
    dt_download     = db.Column(db.DateTime)
    qtd_acessos     = db.Column(db.Integer, default=0)
    historico       = db.Column(db.Text, default='[]')  # JSON list de {dt, acao}

    avaliacoes = db.relationship('Avaliacao', backref='acesso', lazy=True, cascade='all,delete')

    @property
    def expirado(self):
        return self.expira_em and datetime.utcnow() > self.expira_em

    @property
    def dias_restantes(self):
        if self.expirado: return 0
        return max(0, (self.expira_em - datetime.utcnow()).days)

    @property
    def segundos_restantes(self):
        if self.expirado: return 0
        return max(0, int((self.expira_em - datetime.utcnow()).total_seconds()))

    @property
    def pct_prazo(self):
        t = app.config['DIAS_EXPIRACAO']
        return max(0, min(100, int((self.dias_restantes / t) * 100)))

    def add_historico(self, acao):
        try:    hist = json.loads(self.historico or '[]')
        except: hist = []
        hist.insert(0, {'dt': datetime.utcnow().strftime('%d/%m/%Y %H:%M'), 'acao': acao})
        self.historico = json.dumps(hist[:50])   # mantém últimos 50

    def get_historico(self):
        try:    return json.loads(self.historico or '[]')
        except: return []


class Avaliacao(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    nota       = db.Column(db.Integer)          # 1-5
    comentario = db.Column(db.String(500))
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)


class Vendedor(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    nome            = db.Column(db.String(120), nullable=False)
    login           = db.Column(db.String(60), unique=True, nullable=False)
    senha_hash      = db.Column(db.String(256), nullable=False)
    ativo           = db.Column(db.Boolean, default=True)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)
    escolas_ids     = db.Column(db.Text, default='[]')
    meta_mes        = db.Column(db.Integer, default=0)   # meta de vendas/mês
    anotacoes       = db.relationship('VendaAnotacao', backref='vendedor', lazy=True, cascade='all,delete')

    def set_senha(self, s):   self.senha_hash = generate_password_hash(s)
    def check_senha(self, s): return check_password_hash(self.senha_hash, s)

    def get_escolas_ids(self):
        try:    return json.loads(self.escolas_ids or '[]')
        except: return []

    def set_escolas_ids(self, ids):
        self.escolas_ids = json.dumps(ids)

    def pode_ver_escola(self, escola_id):
        ids = self.get_escolas_ids()
        return not ids or escola_id in ids

    @property
    def total_vendas_mes(self):
        inicio = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        return VendaAnotacao.query.filter(
            VendaAnotacao.vendedor_id == self.id,
            VendaAnotacao.criado_em  >= inicio
        ).count()


class VendaAnotacao(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    vendedor_id     = db.Column(db.Integer, db.ForeignKey('vendedor.id'), nullable=False)
    album_id        = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    nome_cliente    = db.Column(db.String(120))
    telefone        = db.Column(db.String(30))
    status          = db.Column(db.String(30), default='interesse')
    obs             = db.Column(db.String(400))
    endereco        = db.Column(db.String(200))
    valor_venda     = db.Column(db.Float)
    visita_agendada = db.Column(db.DateTime)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)


class LogAtividade(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    tipo      = db.Column(db.String(50))
    descricao = db.Column(db.String(300))
    usuario   = db.Column(db.String(80))
    ip        = db.Column(db.String(45))        # IP para log de tentativas
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def registrar(tipo, descricao, usuario='admin', ip=None):
        db.session.add(LogAtividade(tipo=tipo, descricao=descricao,
                                    usuario=usuario, ip=ip))


class Tag(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    texto      = db.Column(db.String(50), nullable=False)
    cor        = db.Column(db.String(20), default='gold')

Cliente.tags = db.relationship('Tag', backref='cliente', lazy=True, cascade='all,delete')


class Configuracao(db.Model):
    chave = db.Column(db.String(60), primary_key=True)
    valor = db.Column(db.Text)

    @staticmethod
    def get(chave, padrao=''):
        c = Configuracao.query.get(chave)
        return c.valor if c else padrao

    @staticmethod
    def set(chave, valor):
        c = Configuracao.query.get(chave)
        if c:  c.valor = valor
        else:  db.session.add(Configuracao(chave=chave, valor=valor))


class Notificacao(db.Model):
    """Notificações internas para o admin."""
    id        = db.Column(db.Integer, primary_key=True)
    tipo      = db.Column(db.String(40))   # expiracao|sem_download|backup|avaliacao
    titulo    = db.Column(db.String(200))
    lida      = db.Column(db.Boolean, default=False)
    link      = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def criar(tipo, titulo, link=''):
        # evita duplicatas no mesmo dia
        hoje = datetime.utcnow().replace(hour=0, minute=0, second=0)
        existe = Notificacao.query.filter(
            Notificacao.tipo == tipo,
            Notificacao.titulo == titulo,
            Notificacao.criado_em >= hoje
        ).first()
        if not existe:
            db.session.add(Notificacao(tipo=tipo, titulo=titulo, link=link))



# ══════════════════════════════════════════════
#  EMAIL HELPERS
# ══════════════════════════════════════════════
def enviar_email(destinatario, assunto, corpo_html):
    """Envia e-mail se MAIL_ENABLED. Silencia erros para não quebrar o fluxo."""
    if not app.config.get('MAIL_ENABLED'):
        return False
    try:
        msg = Message(assunto, recipients=[destinatario])
        msg.html = corpo_html
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f'Erro ao enviar e-mail: {e}')
        return False


def email_boas_vindas(cliente, acesso, senha_plain, site_url):
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#2D261A">
      <div style="background:#110E09;padding:28px 32px;text-align:center">
        <h1 style="font-family:Georgia,serif;color:#C9A84C;font-weight:300;font-size:24px;margin:0">
          Harmonia Formaturas & Buffet
        </h1>
      </div>
      <div style="padding:32px">
        <p style="font-size:16px">Olá, <strong>{cliente.nome.split()[0]}</strong>! 🎓</p>
        <p style="color:#555;line-height:1.7">
          Seus álbuns digitais estão prontos para download!
        </p>
        <div style="background:#FAF7F2;border-left:3px solid #C9A84C;padding:16px 20px;margin:20px 0;border-radius:2px">
          <p style="margin:0 0 8px;font-size:13px;color:#8C7E6A">DADOS DE ACESSO</p>
          <p style="margin:0"><strong>📸 Álbum:</strong> {acesso.album.titulo}</p>
          <p style="margin:4px 0"><strong>👤 Usuário:</strong> {cliente.login}</p>
          <p style="margin:4px 0"><strong>🔑 Senha:</strong> {senha_plain}</p>
          <p style="margin:4px 0"><strong>⚠️ Expira em:</strong> {acesso.expira_em.strftime('%d/%m/%Y') if acesso.expira_em else '—'}</p>
        </div>
        <div style="text-align:center;margin:28px 0">
          <a href="{site_url}" style="background:#C9A84C;color:#110E09;padding:14px 32px;
             text-decoration:none;font-weight:500;font-size:14px;letter-spacing:1px;border-radius:2px">
            ACESSAR MEUS ÁLBUNS
          </a>
        </div>
        <p style="font-size:12px;color:#8C7E6A;line-height:1.6">
          Faça o download e salve em local seguro (HD externo, nuvem pessoal).
          Após o prazo o link expira permanentemente.
        </p>
      </div>
      <div style="background:#FAF7F2;padding:16px 32px;text-align:center;font-size:12px;color:#8C7E6A">
        Harmonia Formaturas & Buffet
      </div>
    </div>"""
    return html


def email_lembrete(cliente, acesso, site_url):
    dias = acesso.dias_restantes
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#2D261A">
      <div style="background:#110E09;padding:28px 32px;text-align:center">
        <h1 style="font-family:Georgia,serif;color:#C9A84C;font-weight:300;font-size:24px;margin:0">
          Harmonia Formaturas & Buffet
        </h1>
      </div>
      <div style="padding:32px">
        <p style="font-size:16px">Olá, <strong>{cliente.nome.split()[0]}</strong>!</p>
        <div style="background:#FFF3CD;border-left:3px solid #E8A73A;padding:16px 20px;margin:20px 0;border-radius:2px">
          <p style="margin:0;font-size:15px;color:#7A5A00">
            ⚠️ Seu álbum expira em <strong>{dias} dia{'s' if dias!=1 else ''}</strong>!
          </p>
          <p style="margin:6px 0 0;font-size:13px;color:#8C7E6A">
            Expira em: {acesso.expira_em.strftime('%d/%m/%Y') if acesso.expira_em else '—'}
          </p>
        </div>
        <p style="color:#555;line-height:1.7">
          Não esqueça de baixar e salvar seu álbum <strong>{acesso.album.titulo}</strong> em local seguro.
        </p>
        <div style="text-align:center;margin:28px 0">
          <a href="{site_url}" style="background:#C9A84C;color:#110E09;padding:14px 32px;
             text-decoration:none;font-weight:500;font-size:14px;letter-spacing:1px;border-radius:2px">
            BAIXAR AGORA
          </a>
        </div>
      </div>
      <div style="background:#FAF7F2;padding:16px;text-align:center;font-size:12px;color:#8C7E6A">
        Harmonia Formaturas & Buffet
      </div>
    </div>"""
    return html


def registrar_login_falha(rota, login_tent=''):
    ip = request.remote_addr or 'desconhecido'
    db.session.add(LoginFalha(ip=ip, rota=rota, login_tent=login_tent))
    # não commita aqui — quem chama commita


def checar_timeout_sessao():
    """Retorna True se a sessão expirou."""
    ultima = session.get('ultima_atividade')
    if not ultima:
        return False
    diff = (datetime.utcnow() - datetime.fromisoformat(ultima)).total_seconds() / 60
    if session.get('cliente_id'):
        return diff > app.config['SESSION_TIMEOUT_CLIENTE']
    if session.get('vendedor_id'):
        return diff > app.config['SESSION_TIMEOUT_VENDEDOR']
    return False


def atualizar_atividade():
    session['ultima_atividade'] = datetime.utcnow().isoformat()


# ══════════════════════════════════════════════
#  DECORATORS
# ══════════════════════════════════════════════
def login_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'cliente_id' not in session:
            flash(t('login_wrong'), 'warning')
            return redirect(url_for('login'))
        # Session timeout
        timeout = int(Configuracao.get('session_timeout', str(app.config['SESSION_TIMEOUT_MINUTES'])))
        last = session.get('last_active')
        if last and (datetime.utcnow() - datetime.fromisoformat(last)).seconds > timeout * 60:
            session.clear()
            flash('Sessão expirada por inatividade. Faça login novamente.', 'warning')
            return redirect(url_for('login'))
        session['last_active'] = datetime.utcnow().isoformat()
        return f(*a, **kw)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if not session.get('admin'):
            flash('Acesso restrito.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*a, **kw)
    return d

def vendedor_required(f):
    @wraps(f)
    def d(*a, **kw):
        if not session.get('vendedor_id'):
            flash('Faça login como vendedor.', 'warning')
            return redirect(url_for('vendedor_login'))
        # Session timeout para vendedor
        timeout = int(Configuracao.get('session_timeout', str(app.config['SESSION_TIMEOUT_MINUTES'])))
        last = session.get('last_active')
        if last and (datetime.utcnow() - datetime.fromisoformat(last)).seconds > timeout * 60:
            session.clear()
            flash('Sessão expirada por inatividade.', 'warning')
            return redirect(url_for('vendedor_login'))
        session['last_active'] = datetime.utcnow().isoformat()
        return f(*a, **kw)
    return d


# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════
def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in app.config['ALLOWED_EXTENSIONS']

def formatar_tamanho(nbytes):
    for u in ('B', 'KB', 'MB', 'GB'):
        if nbytes < 1024: return f'{nbytes:.1f} {u}'
        nbytes /= 1024
    return f'{nbytes:.2f} GB'

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()

def mail_disponivel():
    return bool(app.config.get('MAIL_USERNAME'))

def enviar_email(destinatario, assunto, corpo_html, corpo_txt=None):
    """Envia e-mail se configurado. Falha silenciosa se não configurado."""
    if not mail_disponivel() or not destinatario:
        return False
    try:
        msg = Message(assunto, recipients=[destinatario])
        msg.html = corpo_html
        msg.body = corpo_txt or assunto
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f'Email error: {e}')
        return False

def email_boas_vindas(cliente, acesso, senha_plain):
    site_url = app.config['SITE_URL']
    expira   = acesso.expira_em.strftime('%d/%m/%Y') if acesso and acesso.expira_em else '—'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#FAF7F2;padding:32px">
      <div style="text-align:center;margin-bottom:28px">
        <h1 style="font-family:Georgia,serif;color:#C9A84C;font-weight:300;font-size:28px;margin:0">
          Harmonia Formaturas & Buffet
        </h1>
      </div>
      <div style="background:#fff;border-radius:4px;padding:28px;border:1px solid #E8D5A0">
        <h2 style="color:#2D261A;font-family:Georgia,serif;font-weight:300;margin-top:0">
          Olá, {cliente.nome.split()[0]}! 🎓
        </h2>
        <p style="color:#4A3F30;line-height:1.7">
          Seus álbuns digitais estão prontos para download!
        </p>
        <div style="background:#FAF7F2;border-radius:4px;padding:16px;margin:20px 0;border-left:3px solid #C9A84C">
          <p style="margin:0 0 8px;color:#8A6A1F;font-size:12px;text-transform:uppercase;letter-spacing:1px">Seus dados de acesso</p>
          <p style="margin:4px 0;color:#2D261A"><strong>📸 Álbum:</strong> {acesso.album.titulo if acesso else '—'}</p>
          <p style="margin:4px 0;color:#2D261A"><strong>👤 Usuário:</strong> {cliente.login}</p>
          <p style="margin:4px 0;color:#2D261A"><strong>🔑 Senha:</strong> {senha_plain}</p>
          <p style="margin:4px 0;color:#B71C1C"><strong>⚠️ Expira em:</strong> {expira}</p>
        </div>
        <div style="text-align:center;margin:24px 0">
          <a href="{site_url}" style="background:#C9A84C;color:#fff;padding:14px 32px;
             border-radius:2px;text-decoration:none;font-size:13px;letter-spacing:1px;
             text-transform:uppercase;font-weight:500">
            Acessar meus álbuns
          </a>
        </div>
        <p style="color:#7A6E5E;font-size:12px;line-height:1.6">
          Após baixar, salve o arquivo em um local seguro: HD externo, Google Drive pessoal ou pendrive.
          O link expira em <strong>{expira}</strong> e não pode ser recuperado após essa data.
        </p>
      </div>
      <p style="text-align:center;color:#8C7E6A;font-size:11px;margin-top:20px">
        Harmonia Formaturas & Buffet — {site_url}
      </p>
    </div>"""
    return enviar_email(cliente.email, '📸 Seus álbuns digitais estão prontos!', html)

def email_lembrete(cliente, acesso):
    site_url = app.config['SITE_URL']
    dias     = acesso.dias_restantes
    expira   = acesso.expira_em.strftime('%d/%m/%Y') if acesso.expira_em else '—'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#FAF7F2;padding:32px">
      <div style="background:#fff;border-radius:4px;padding:28px;border:1px solid #E8D5A0">
        <h2 style="color:#C9A84C;font-family:Georgia,serif;font-weight:300;margin-top:0">⚠️ Lembrete de prazo</h2>
        <p style="color:#4A3F30;line-height:1.7">
          Olá, <strong>{cliente.nome.split()[0]}</strong>! Seu álbum <strong>{acesso.album.titulo}</strong>
          expira em <strong style="color:#B71C1C">{expira}</strong>
          ({dias} dia{'s' if dias!=1 else ''} restante{'s' if dias!=1 else ''}).
        </p>
        <div style="text-align:center;margin:24px 0">
          <a href="{site_url}" style="background:#C9A84C;color:#fff;padding:14px 32px;
             border-radius:2px;text-decoration:none;font-size:13px;letter-spacing:1px;
             text-transform:uppercase">Baixar agora</a>
        </div>
        <p style="color:#7A6E5E;font-size:12px">Usuário: {cliente.login}</p>
      </div>
    </div>"""
    return enviar_email(cliente.email, f'⚠️ Seu álbum expira em {dias} dia(s)!', html)

def gerar_notificacoes():
    """Gera notificações automáticas — chamado no painel do admin."""
    # Clientes expirando em 2 dias sem ter baixado
    for c in Cliente.query.all():
        for a in c.acessos:
            if not a.baixado and a.dias_restantes <= 2 and not a.expirado:
                Notificacao.criar('expiracao',
                    f'{c.nome} — álbum expira em {a.dias_restantes} dia(s)',
                    url_for('admin_lembrete', cliente_id=c.id))
            if a.expirado and not a.baixado:
                Notificacao.criar('sem_download',
                    f'{c.nome} — prazo expirou sem baixar',
                    url_for('admin_editar_cliente', cliente_id=c.id))
    # Backup atrasado
    ub = LogAtividade.query.filter_by(tipo='backup').order_by(LogAtividade.criado_em.desc()).first()
    if not ub or (datetime.utcnow() - ub.criado_em).days >= 7:
        Notificacao.criar('backup', 'Backup do banco de dados atrasado!',
                          url_for('admin_backup'))
    # Novas avaliações não lidas
    avals = Avaliacao.query.order_by(Avaliacao.criado_em.desc()).limit(5).all()
    for av in avals:
        if (datetime.utcnow() - av.criado_em).seconds < 3600:
            Notificacao.criar('avaliacao',
                f'Nova avaliação: {av.nota}★ de {av.cliente.nome}', '')
    db.session.commit()

def gerar_msg_whatsapp(cliente, acesso, site_url, senha_plain=None):
    primeiro = cliente.nome.split()[0]
    expira   = acesso.expira_em.strftime('%d/%m/%Y') if acesso and acesso.expira_em else '—'
    dias     = acesso.dias_restantes if acesso else 7
    titulo   = acesso.album.titulo if acesso else 'Álbum Digital'
    senha    = senha_plain or '(senha cadastrada)'
    tmpl = Configuracao.get('msg_whatsapp', app.config['MSG_TEMPLATE'])
    msg  = tmpl.format(primeiro=primeiro, titulo=titulo, site_url=site_url,
                       login=cliente.login, senha=senha, expira=expira,
                       dias=dias, s='s' if dias!=1 else '', s2='s' if dias!=1 else '')
    wa_link = ''
    if cliente.telefone:
        phone   = '55' + ''.join(filter(str.isdigit, cliente.telefone))
        wa_link = f"https://wa.me/{phone}?text={url_quote(msg)}"
    return msg, wa_link

def gerar_lembrete_whatsapp(cliente, acesso, site_url):
    primeiro = cliente.nome.split()[0]
    dias     = acesso.dias_restantes
    expira   = acesso.expira_em.strftime('%d/%m/%Y') if acesso.expira_em else '—'
    msg = (
        f"Olá, {primeiro}! 🎓\n\n⚠️ *Lembrete importante!*\n\n"
        f"Seu álbum *{acesso.album.titulo}* expira em *{expira}* "
        f"({dias} dia{'s' if dias!=1 else ''} restante{'s' if dias!=1 else ''}).\n\n"
        f"Não esqueça de fazer o download!\n\n"
        f"🌐 Acesse: {site_url}\n👤 Usuário: {cliente.login}\n\n"
        f"_Harmonia Formaturas & Buffet_"
    )
    wa_link = ''
    if cliente.telefone:
        phone   = '55' + ''.join(filter(str.isdigit, cliente.telefone))
        wa_link = f"https://wa.me/{phone}?text={url_quote(msg)}"
    return msg, wa_link


# ══════════════════════════════════════════════
#  MIDDLEWARE
# ══════════════════════════════════════════════
@app.before_request
def checar_manutencao():
    if request.endpoint in ('admin_login','admin_logout','static','vendedor_login'): return
    if session.get('admin'): return
    if Configuracao.get('manutencao','0') == '1':
        return render_template('manutencao.html'), 503

@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in ('pt','en','es'):
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))


# ══════════════════════════════════════════════
#  PUBLIC / CLIENT
# ══════════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        lv  = request.form.get('login','').strip()
        sv  = request.form.get('senha','')
        ip  = get_client_ip()
        c   = Cliente.query.filter_by(login=lv).first()
        if c and c.check_senha(sv):
            session['cliente_id']   = c.id
            session['cliente_nome'] = c.nome
            session['last_active']  = datetime.utcnow().isoformat()
            LogAtividade.registrar('cliente_login', f'{c.nome} fez login', c.nome, ip)
            db.session.commit()
            return redirect(url_for('area_cliente'))
        # Log failed attempt
        LogAtividade.registrar('login_falhou', f'Tentativa falha: usuário "{lv}"', 'anônimo', ip)
        db.session.commit()
        flash(t('login_wrong'), 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('cliente_id', None)
    session.pop('cliente_nome', None)
    return redirect(url_for('index'))

@app.route('/area')
@login_required
def area_cliente():
    cliente = Cliente.query.get_or_404(session['cliente_id'])
    suporte = Configuracao.get('suporte_whatsapp', app.config['SUPORTE_WHATSAPP'])
    # Check if client has reviewed
    ja_avaliou = Avaliacao.query.filter_by(cliente_id=cliente.id).first() is not None
    # Check if any album was downloaded (show review prompt)
    algum_baixado = any(a.baixado for a in cliente.acessos)
    return render_template('area_cliente.html', cliente=cliente, suporte=suporte,
                           ja_avaliou=ja_avaliou, algum_baixado=algum_baixado)

@app.route('/album/<int:acesso_id>/visualizar')
@login_required
def visualizar_album(acesso_id):
    acesso = ClienteAlbum.query.get_or_404(acesso_id)
    if acesso.cliente_id != session['cliente_id']:
        flash('Acesso negado.','danger'); return redirect(url_for('area_cliente'))
    if acesso.expirado:
        flash('O prazo de acesso expirou.','danger'); return redirect(url_for('area_cliente'))
    acesso.qtd_acessos = (acesso.qtd_acessos or 0) + 1
    if not acesso.visualizado:
        acesso.visualizado     = True
        acesso.dt_visualizacao = datetime.utcnow()
        LogAtividade.registrar('visualizou',
            f'{acesso.cliente.nome} visualizou "{acesso.album.titulo}"', acesso.cliente.nome)
    acesso.add_historico('Visualizou')
    db.session.commit()
    if acesso.album.drive_url: return redirect(acesso.album.drive_url)
    flash('Link não disponível.','warning'); return redirect(url_for('area_cliente'))

@app.route('/acesso/<int:acesso_id>/download')
@login_required
def download_album(acesso_id):
    acesso = ClienteAlbum.query.get_or_404(acesso_id)
    if acesso.cliente_id != session['cliente_id']:
        flash('Acesso negado.','danger'); return redirect(url_for('area_cliente'))
    if acesso.expirado:
        flash('O prazo expirou.','danger'); return redirect(url_for('area_cliente'))
    if not acesso.baixado:
        acesso.baixado     = True
        acesso.dt_download = datetime.utcnow()
        LogAtividade.registrar('baixou',
            f'{acesso.cliente.nome} baixou "{acesso.album.titulo}"', acesso.cliente.nome)
    acesso.add_historico('Baixou')
    db.session.commit()
    album = acesso.album
    if album.nome_arquivo:
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], album.nome_arquivo)
        if os.path.exists(caminho):
            ext = album.nome_arquivo.rsplit('.',1)[-1]
            return send_file(caminho, as_attachment=True, download_name=f"{album.titulo}.{ext}")
    if album.drive_url: return redirect(album.drive_url)
    flash('Arquivo não disponível.','warning'); return redirect(url_for('area_cliente'))

@app.route('/avaliar', methods=['POST'])
@login_required
def avaliar():
    cliente_id = session['cliente_id']
    if Avaliacao.query.filter_by(cliente_id=cliente_id).first():
        return jsonify({'ok': False, 'msg': 'Já avaliado'})
    nota = int(request.form.get('nota', 0))
    comt = request.form.get('comentario','').strip()
    if not 1 <= nota <= 5:
        return jsonify({'ok': False, 'msg': 'Nota inválida'})
    db.session.add(Avaliacao(cliente_id=cliente_id, nota=nota, comentario=comt))
    cliente = Cliente.query.get(cliente_id)
    LogAtividade.registrar('avaliacao', f'{cliente.nome} avaliou com {nota}★', cliente.nome)
    Notificacao.criar('avaliacao', f'Nova avaliação: {nota}★ de {cliente.nome}', '')
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/push/subscribe', methods=['POST'])
@login_required
def push_subscribe():
    data = request.get_json()
    cliente = Cliente.query.get(session['cliente_id'])
    if cliente and data:
        cliente.push_sub = json.dumps(data)
        db.session.commit()
    return jsonify({'ok': True})

@app.route('/historico-acessos')
@login_required
def historico_acessos():
    cliente = Cliente.query.get_or_404(session['cliente_id'])
    return render_template('historico_acessos.html', cliente=cliente)


# ══════════════════════════════════════════════
#  ADMIN AUTH
# ══════════════════════════════════════════════
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        ip = get_client_ip()
        if request.form.get('senha') == app.config['ADMIN_PASSWORD']:
            session['admin'] = True
            LogAtividade.registrar('admin_login','Admin fez login', ip=ip)
            db.session.commit()
            return redirect(url_for('admin_painel'))
        LogAtividade.registrar('login_falhou','Tentativa de login admin falhou','anônimo', ip)
        db.session.commit()
        flash('Senha incorreta.','danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


# ══════════════════════════════════════════════
#  ADMIN — PAINEL
# ══════════════════════════════════════════════
@app.route('/admin')
@admin_required
def admin_painel():
    filtro_status = request.args.get('status','todos')
    busca         = request.args.get('q','').strip().lower()
    clientes_q    = Cliente.query.order_by(Cliente.criado_em.desc())
    if busca:
        clientes_q = clientes_q.filter(Cliente.nome.ilike(f'%{busca}%'))
    clientes = clientes_q.all()

    def match(c):
        if filtro_status == 'todos': return True
        a = c.acessos[-1] if c.acessos else None
        if filtro_status == 'baixou':   return a and a.baixado
        if filtro_status == 'pendente': return a and not a.baixado and not a.expirado
        if filtro_status == 'expirado': return a and a.expirado and not a.baixado
        return True
    clientes = [c for c in clientes if match(c)]

    todos     = Cliente.query.all()
    total     = len(todos)
    baixaram  = sum(1 for c in todos if any(a.baixado for a in c.acessos))
    expirados = sum(1 for c in todos if any(a.expirado and not a.baixado for a in c.acessos))
    aguardando = max(0, total - baixaram - expirados)

    # Gráfico 7 dias
    graf_labels, graf_baixaram, graf_viram = [], [], []
    for i in range(6,-1,-1):
        d   = datetime.utcnow() - timedelta(days=i)
        ini = d.replace(hour=0, minute=0, second=0, microsecond=0)
        fim = ini + timedelta(days=1)
        graf_labels.append(d.strftime('%d/%m'))
        graf_baixaram.append(ClienteAlbum.query.filter(
            ClienteAlbum.dt_download >= ini, ClienteAlbum.dt_download < fim).count())
        graf_viram.append(ClienteAlbum.query.filter(
            ClienteAlbum.dt_visualizacao >= ini, ClienteAlbum.dt_visualizacao < fim).count())

    # Calendário
    hoje    = datetime.utcnow().date()
    cal_exp = {}
    for c in todos:
        for a in c.acessos:
            if a.expira_em and not a.baixado:
                d = a.expira_em.date()
                if hoje <= d <= hoje + timedelta(days=30):
                    cal_exp[str(d)] = cal_exp.get(str(d), 0) + 1

    # Ranking
    ranking = []
    for v in Vendedor.query.all():
        inicio = datetime.utcnow().replace(day=1,hour=0,minute=0,second=0)
        anots  = VendaAnotacao.query.filter(
            VendaAnotacao.vendedor_id==v.id, VendaAnotacao.criado_em>=inicio).all()
        vendidos = sum(1 for a in anots if a.status=='vendido')
        valor    = sum(a.valor_venda or 0 for a in anots if a.status=='vendido')
        pct_meta = min(100, int(vendidos/v.meta_mes*100)) if v.meta_mes else 0
        ranking.append({'vendedor':v,'vendidos':vendidos,'valor':valor,'total':len(anots),'pct_meta':pct_meta})
    ranking.sort(key=lambda x: x['vendidos'], reverse=True)

    # Avaliações
    avaliacoes  = Avaliacao.query.order_by(Avaliacao.criado_em.desc()).all()
    media_aval  = round(sum(a.nota for a in avaliacoes)/len(avaliacoes),1) if avaliacoes else 0

    # Backup
    ub = LogAtividade.query.filter_by(tipo='backup').order_by(LogAtividade.criado_em.desc()).first()
    if ub:
        dias_sem_backup   = (datetime.utcnow() - ub.criado_em).days
        ultimo_backup_str = ub.criado_em.strftime('%d/%m/%Y às %H:%M')
    else:
        dias_sem_backup, ultimo_backup_str = 999, None
    alerta_backup = dias_sem_backup >= 7

    # Notificações
    gerar_notificacoes()
    notifs_nao_lidas = Notificacao.query.filter_by(lida=False).order_by(
        Notificacao.criado_em.desc()).all()

    # Espaço em disco
    upload_dir = app.config['UPLOAD_FOLDER']
    total_bytes = sum(
        os.path.getsize(os.path.join(upload_dir, f))
        for f in os.listdir(upload_dir)
        if os.path.isfile(os.path.join(upload_dir, f))
    ) if os.path.exists(upload_dir) else 0
    espaco_usado = formatar_tamanho(total_bytes)
    qtd_arquivos = len([f for f in os.listdir(upload_dir)
                        if os.path.isfile(os.path.join(upload_dir, f))]) if os.path.exists(upload_dir) else 0

    # Tentativas de login falhas (últimas 24h)
    ontem = datetime.utcnow() - timedelta(hours=24)
    login_falhos = LogAtividade.query.filter(
        LogAtividade.tipo=='login_falhou',
        LogAtividade.criado_em >= ontem
    ).count()

    escolas    = Escola.query.order_by(Escola.nome).all()
    vendedores = Vendedor.query.order_by(Vendedor.nome).all()
    log        = LogAtividade.query.order_by(LogAtividade.criado_em.desc()).limit(80).all()

    return render_template('admin_painel.html',
        clientes=clientes, escolas=escolas, vendedores=vendedores,
        log=log, ranking=ranking, avaliacoes=avaliacoes, media_aval=media_aval,
        notifs_nao_lidas=notifs_nao_lidas,
        total=total, baixaram=baixaram, aguardando=aguardando, expirados=expirados,
        filtro_status=filtro_status, busca=busca,
        graf_labels=json.dumps(graf_labels),
        graf_baixaram=json.dumps(graf_baixaram),
        graf_viram=json.dumps(graf_viram),
        cal_exp=json.dumps(cal_exp), hoje=str(hoje),
        dias_sem_backup=dias_sem_backup, ultimo_backup_str=ultimo_backup_str, alerta_backup=alerta_backup,
        espaco_usado=espaco_usado, qtd_arquivos=qtd_arquivos,
        login_falhos=login_falhos)


# ══════════════════════════════════════════════
#  ADMIN — NOTIFICAÇÕES
# ══════════════════════════════════════════════
@app.route('/admin/notificacoes/ler', methods=['POST'])
@admin_required
def admin_ler_notificacoes():
    Notificacao.query.filter_by(lida=False).update({'lida': True})
    db.session.commit()
    return jsonify({'ok': True})


# ══════════════════════════════════════════════
#  ADMIN — BACKUP
# ══════════════════════════════════════════════
@app.route('/admin/backup')
@admin_required
def admin_backup():
    db_path = os.path.join(app.instance_path, 'harmonia.db')
    if not os.path.exists(db_path):
        flash(f'Banco não encontrado em {db_path}.','danger')
        return redirect(url_for('admin_painel'))
    bak_name = f"harmonia_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    bak_path = os.path.join('/tmp', bak_name)
    shutil.copy2(db_path, bak_path)
    LogAtividade.registrar('backup','Admin fez download do backup')
    db.session.commit()
    return send_file(bak_path, as_attachment=True, download_name=bak_name)


# ══════════════════════════════════════════════
#  ADMIN — GERENCIAR ARQUIVOS DO SERVIDOR
# ══════════════════════════════════════════════
@app.route('/admin/arquivos')
@admin_required
def admin_arquivos():
    upload_dir = app.config['UPLOAD_FOLDER']
    arquivos   = []
    if os.path.exists(upload_dir):
        for fname in os.listdir(upload_dir):
            fpath = os.path.join(upload_dir, fname)
            if not os.path.isfile(fpath): continue
            # Find which album uses this file
            album = Album.query.filter_by(nome_arquivo=fname).first()
            arquivos.append({
                'nome':    fname,
                'tamanho': formatar_tamanho(os.path.getsize(fpath)),
                'bytes':   os.path.getsize(fpath),
                'album':   album,
                'modificado': datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%d/%m/%Y %H:%M'),
                'orfao':   album is None,
            })
    arquivos.sort(key=lambda x: x['bytes'], reverse=True)
    total_bytes = sum(a['bytes'] for a in arquivos)
    return render_template('admin_arquivos.html',
                           arquivos=arquivos,
                           total=formatar_tamanho(total_bytes),
                           qtd=len(arquivos))

@app.route('/admin/arquivos/<fname>/excluir', methods=['POST'])
@admin_required
def admin_excluir_arquivo(fname):
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    if os.path.exists(fpath):
        os.remove(fpath)
        # Limpa referência no banco se existir
        album = Album.query.filter_by(nome_arquivo=fname).first()
        if album:
            album.nome_arquivo = None
            album.tamanho_fmt  = None
        LogAtividade.registrar('arquivo_excluido', f'Arquivo "{fname}" removido do servidor')
        db.session.commit()
        flash('Arquivo removido do servidor.','success')
    else:
        flash('Arquivo não encontrado.','danger')
    return redirect(url_for('admin_arquivos'))


# ══════════════════════════════════════════════
#  ADMIN — RELATÓRIO PDF
# ══════════════════════════════════════════════
@app.route('/admin/relatorio-pdf')
@admin_required
def admin_relatorio_pdf():
    """Gera HTML formatado para impressão como PDF via browser."""
    mes_atual = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    clientes  = Cliente.query.order_by(Cliente.criado_em.desc()).all()
    total     = len(clientes)
    baixaram  = sum(1 for c in clientes if any(a.baixado for a in c.acessos))
    expirados = sum(1 for c in clientes if any(a.expirado and not a.baixado for a in c.acessos))
    vendas_mes = VendaAnotacao.query.filter(VendaAnotacao.criado_em >= mes_atual).all()
    vendidos_mes = sum(1 for v in vendas_mes if v.status=='vendido')
    valor_mes    = sum(v.valor_venda or 0 for v in vendas_mes if v.status=='vendido')
    avaliacoes   = Avaliacao.query.all()
    media_aval   = round(sum(a.nota for a in avaliacoes)/len(avaliacoes),1) if avaliacoes else 0
    ranking = []
    for v in Vendedor.query.all():
        anots    = VendaAnotacao.query.filter(
            VendaAnotacao.vendedor_id==v.id, VendaAnotacao.criado_em>=mes_atual).all()
        vendidos = sum(1 for a in anots if a.status=='vendido')
        valor    = sum(a.valor_venda or 0 for a in anots if a.status=='vendido')
        ranking.append({'vendedor':v,'vendidos':vendidos,'valor':valor})
    ranking.sort(key=lambda x: x['vendidos'], reverse=True)
    LogAtividade.registrar('relatorio_pdf','Admin gerou relatório PDF')
    db.session.commit()
    return render_template('admin_relatorio_pdf.html',
        clientes=clientes, total=total, baixaram=baixaram, expirados=expirados,
        vendidos_mes=vendidos_mes, valor_mes=valor_mes,
        media_aval=media_aval, ranking=ranking,
        mes=datetime.utcnow().strftime('%B/%Y').capitalize(),
        gerado_em=datetime.utcnow().strftime('%d/%m/%Y %H:%M'))


# ══════════════════════════════════════════════
#  ADMIN — CONFIGURAÇÕES
# ══════════════════════════════════════════════
@app.route('/admin/configuracoes', methods=['GET','POST'])
@admin_required
def admin_configuracoes():
    if request.method == 'POST':
        Configuracao.set('msg_whatsapp',     request.form.get('msg_whatsapp','').strip() or app.config['MSG_TEMPLATE'])
        Configuracao.set('suporte_whatsapp', request.form.get('suporte_whatsapp','').strip())
        Configuracao.set('manutencao',       '1' if 'manutencao' in request.form else '0')
        Configuracao.set('dias_expiracao',   request.form.get('dias_expiracao','7').strip())
        Configuracao.set('session_timeout',  request.form.get('session_timeout','60').strip())
        app.config['DIAS_EXPIRACAO'] = int(Configuracao.get('dias_expiracao','7'))
        LogAtividade.registrar('config','Configurações atualizadas')
        db.session.commit()
        flash('Configurações salvas!','success')
        return redirect(url_for('admin_configuracoes'))
    cfg = {
        'msg_whatsapp':     Configuracao.get('msg_whatsapp',     app.config['MSG_TEMPLATE']),
        'suporte_whatsapp': Configuracao.get('suporte_whatsapp', app.config['SUPORTE_WHATSAPP']),
        'manutencao':       Configuracao.get('manutencao','0')=='1',
        'dias_expiracao':   Configuracao.get('dias_expiracao','7'),
        'session_timeout':  Configuracao.get('session_timeout','60'),
    }
    return render_template('admin_configuracoes.html', cfg=cfg, tmpl_padrao=app.config['MSG_TEMPLATE'],
                           mail_ok=mail_disponivel(),
                           vapid_ok=bool(app.config.get('VAPID_PUBLIC_KEY')))


# ══════════════════════════════════════════════
#  ADMIN — ESCOLAS / ÁLBUNS / CLIENTES / VENDEDORES
# ══════════════════════════════════════════════
@app.route('/admin/escola/nova', methods=['GET','POST'])
@admin_required
def admin_nova_escola():
    if request.method == 'POST':
        nome = request.form.get('nome','').strip()
        if not nome: flash('Nome obrigatório.','danger'); return render_template('admin_nova_escola.html')
        db.session.add(Escola(nome=nome))
        LogAtividade.registrar('escola_criada',f'Escola "{nome}" criada')
        db.session.commit(); flash(f'Escola "{nome}" criada.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_nova_escola.html')

@app.route('/admin/escola/<int:escola_id>/editar', methods=['GET','POST'])
@admin_required
def admin_editar_escola(escola_id):
    escola = Escola.query.get_or_404(escola_id)
    if request.method == 'POST':
        escola.nome = request.form.get('nome', escola.nome).strip()
        db.session.commit(); flash('Escola atualizada.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_editar_escola.html', escola=escola)

@app.route('/admin/escola/<int:escola_id>/excluir', methods=['POST'])
@admin_required
def admin_excluir_escola(escola_id):
    e = Escola.query.get_or_404(escola_id)
    LogAtividade.registrar('escola_excluida',f'Escola "{e.nome}" excluída')
    db.session.delete(e); db.session.commit()
    flash('Escola excluída.','success'); return redirect(url_for('admin_painel'))

@app.route('/admin/album/novo', methods=['GET','POST'])
@admin_required
def admin_novo_album():
    escolas = Escola.query.order_by(Escola.nome).all()
    if request.method == 'POST':
        escola_id = request.form.get('escola_id', type=int)
        titulo    = request.form.get('titulo','').strip()
        descricao = request.form.get('descricao','').strip()
        drive_url = request.form.get('drive_url','').strip()
        if not escola_id or not titulo:
            flash('Escola e título são obrigatórios.','danger')
            return render_template('admin_novo_album.html', escolas=escolas)
        nome_arquivo = tamanho_fmt = None
        arquivo = request.files.get('arquivo')
        if arquivo and arquivo.filename and allowed_file(arquivo.filename):
            ext = arquivo.filename.rsplit('.',1)[-1].lower()
            nome_arquivo = f"{uuid.uuid4().hex}.{ext}"
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            arquivo.save(caminho)
            tamanho_fmt = formatar_tamanho(os.path.getsize(caminho))
        db.session.add(Album(escola_id=escola_id, titulo=titulo, descricao=descricao,
                             drive_url=drive_url or None,
                             nome_arquivo=nome_arquivo, tamanho_fmt=tamanho_fmt))
        LogAtividade.registrar('album_criado',f'Álbum "{titulo}" criado')
        db.session.commit(); flash(f'Álbum "{titulo}" criado.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_novo_album.html', escolas=escolas)

@app.route('/admin/album/<int:album_id>/editar', methods=['GET','POST'])
@admin_required
def admin_editar_album(album_id):
    album   = Album.query.get_or_404(album_id)
    escolas = Escola.query.order_by(Escola.nome).all()
    if request.method == 'POST':
        album.escola_id = request.form.get('escola_id', type=int)
        album.titulo    = request.form.get('titulo', album.titulo).strip()
        album.descricao = request.form.get('descricao','').strip()
        album.drive_url = request.form.get('drive_url','').strip() or None
        arquivo = request.files.get('arquivo')
        if arquivo and arquivo.filename and allowed_file(arquivo.filename):
            if album.nome_arquivo:
                antigo = os.path.join(app.config['UPLOAD_FOLDER'], album.nome_arquivo)
                if os.path.exists(antigo): os.remove(antigo)
            ext = arquivo.filename.rsplit('.',1)[-1].lower()
            album.nome_arquivo = f"{uuid.uuid4().hex}.{ext}"
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], album.nome_arquivo)
            arquivo.save(caminho)
            album.tamanho_fmt = formatar_tamanho(os.path.getsize(caminho))
        if request.form.get('remover_arquivo') and album.nome_arquivo:
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], album.nome_arquivo)
            if os.path.exists(caminho): os.remove(caminho)
            album.nome_arquivo = album.tamanho_fmt = None
        db.session.commit(); flash('Álbum atualizado.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_editar_album.html', album=album, escolas=escolas)

@app.route('/admin/album/<int:album_id>/excluir', methods=['POST'])
@admin_required
def admin_excluir_album(album_id):
    a = Album.query.get_or_404(album_id)
    if a.nome_arquivo:
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], a.nome_arquivo)
        if os.path.exists(caminho): os.remove(caminho)
    LogAtividade.registrar('album_excluido',f'Álbum "{a.titulo}" excluído')
    db.session.delete(a); db.session.commit()
    flash('Álbum excluído.','success'); return redirect(url_for('admin_painel'))

@app.route('/admin/cliente/novo', methods=['GET','POST'])
@admin_required
def admin_novo_cliente():
    albums = Album.query.join(Escola).order_by(Escola.nome, Album.titulo).all()
    if request.method == 'POST':
        nome     = request.form.get('nome','').strip()
        evento   = request.form.get('evento','').strip()
        login_v  = request.form.get('login','').strip()
        senha    = request.form.get('senha','').strip()
        tel      = request.form.get('telefone','').strip()
        email_c  = request.form.get('email','').strip()
        album_id = request.form.get('album_id', type=int)
        if not nome or not login_v or not senha:
            flash('Nome, login e senha são obrigatórios.','danger')
            return render_template('admin_novo_cliente.html', albums=albums)
        if Cliente.query.filter_by(login=login_v).first():
            flash('Login já existe.','danger')
            return render_template('admin_novo_cliente.html', albums=albums)
        cliente = Cliente(nome=nome, evento=evento, login=login_v, telefone=tel, email=email_c)
        cliente.set_senha(senha); db.session.add(cliente); db.session.flush()
        for txt in request.form.get('tags','').split(','):
            txt = txt.strip()
            if txt: db.session.add(Tag(cliente_id=cliente.id, texto=txt))
        acesso = None
        if album_id:
            dias_cfg = int(Configuracao.get('dias_expiracao', str(app.config['DIAS_EXPIRACAO'])))
            acesso = ClienteAlbum(cliente_id=cliente.id, album_id=album_id,
                                  expira_em=datetime.utcnow()+timedelta(days=dias_cfg))
            db.session.add(acesso)
        LogAtividade.registrar('cliente_criado',f'Cliente "{nome}" criado')
        db.session.commit()
        session[f'senha_plain_{cliente.id}'] = senha
        # Enviar e-mail de boas-vindas
        if acesso and email_c:
            email_boas_vindas(cliente, acesso, senha)
        flash(f'Cliente {nome} criado!','success')
        if acesso: return redirect(url_for('admin_whatsapp', cliente_id=cliente.id))
        return redirect(url_for('admin_painel'))
    return render_template('admin_novo_cliente.html', albums=albums)

@app.route('/admin/cliente/<int:cliente_id>/editar', methods=['GET','POST'])
@admin_required
def admin_editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    albums  = Album.query.join(Escola).order_by(Escola.nome, Album.titulo).all()
    if request.method == 'POST':
        cliente.nome     = request.form.get('nome', cliente.nome).strip()
        cliente.evento   = request.form.get('evento', cliente.evento or '').strip()
        cliente.telefone = request.form.get('telefone', cliente.telefone or '').strip()
        cliente.email    = request.form.get('email', cliente.email or '').strip()
        nova_senha = request.form.get('nova_senha','').strip()
        if nova_senha: cliente.set_senha(nova_senha)
        novo_album_id = request.form.get('novo_album_id', type=int)
        if novo_album_id:
            if not ClienteAlbum.query.filter_by(cliente_id=cliente.id, album_id=novo_album_id).first():
                dias_cfg = int(Configuracao.get('dias_expiracao', str(app.config['DIAS_EXPIRACAO'])))
                db.session.add(ClienteAlbum(cliente_id=cliente.id, album_id=novo_album_id,
                    expira_em=datetime.utcnow()+timedelta(days=dias_cfg)))
        Tag.query.filter_by(cliente_id=cliente.id).delete()
        for txt in request.form.get('tags','').split(','):
            txt = txt.strip()
            if txt: db.session.add(Tag(cliente_id=cliente.id, texto=txt))
        LogAtividade.registrar('cliente_editado',f'Dados de "{cliente.nome}" atualizados')
        db.session.commit(); flash('Dados atualizados.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_editar_cliente.html', cliente=cliente, albums=albums)

@app.route('/admin/cliente/<int:cliente_id>/excluir', methods=['POST'])
@admin_required
def admin_excluir_cliente(cliente_id):
    c = Cliente.query.get_or_404(cliente_id)
    LogAtividade.registrar('cliente_excluido',f'Cliente "{c.nome}" excluído')
    db.session.delete(c); db.session.commit()
    flash('Cliente excluído.','success'); return redirect(url_for('admin_painel'))

@app.route('/admin/acesso/<int:acesso_id>/renovar', methods=['POST'])
@admin_required
def admin_renovar_prazo(acesso_id):
    acesso = ClienteAlbum.query.get_or_404(acesso_id)
    dias_cfg = int(Configuracao.get('dias_expiracao', str(app.config['DIAS_EXPIRACAO'])))
    acesso.expira_em = datetime.utcnow() + timedelta(days=dias_cfg)
    acesso.baixado   = False
    LogAtividade.registrar('prazo_renovado',f'Prazo de "{acesso.cliente.nome}" renovado')
    db.session.commit(); flash(f'Prazo renovado por mais {dias_cfg} dias.','success')
    return redirect(url_for('admin_editar_cliente', cliente_id=acesso.cliente_id))

@app.route('/admin/cliente/<int:cliente_id>/whatsapp')
@admin_required
def admin_whatsapp(cliente_id):
    cliente     = Cliente.query.get_or_404(cliente_id)
    acesso      = cliente.acessos[-1] if cliente.acessos else None
    senha_plain = session.pop(f'senha_plain_{cliente.id}','(senha cadastrada)')
    site_url    = app.config['SITE_URL']
    msg, wa_link = gerar_msg_whatsapp(cliente, acesso, site_url, senha_plain) if acesso else ('','')
    return render_template('admin_whatsapp.html', cliente=cliente, acesso=acesso,
                           msg_text=msg, wa_link=wa_link)

@app.route('/admin/cliente/<int:cliente_id>/lembrete')
@admin_required
def admin_lembrete(cliente_id):
    cliente  = Cliente.query.get_or_404(cliente_id)
    acesso   = cliente.acessos[-1] if cliente.acessos else None
    site_url = app.config['SITE_URL']
    msg, wa_link = gerar_lembrete_whatsapp(cliente, acesso, site_url) if acesso else ('','')
    # Enviar lembrete por e-mail também
    if acesso and cliente.email:
        enviado = email_lembrete(cliente, acesso)
        if enviado: flash('Lembrete por e-mail enviado!','success')
    return render_template('admin_lembrete.html', cliente=cliente, acesso=acesso,
                           msg_text=msg, wa_link=wa_link)

@app.route('/admin/lote-whatsapp')
@admin_required
def admin_lote_whatsapp():
    site_url  = app.config['SITE_URL']
    pendentes = []
    for c in Cliente.query.all():
        for acesso in c.acessos:
            if not acesso.baixado and not acesso.expirado and c.telefone:
                _, wa = gerar_lembrete_whatsapp(c, acesso, site_url)
                pendentes.append({'cliente':c,'acesso':acesso,'wa':wa})
    return render_template('admin_lote_whatsapp.html', pendentes=pendentes)

@app.route('/admin/vendedor/novo', methods=['GET','POST'])
@admin_required
def admin_novo_vendedor():
    escolas = Escola.query.order_by(Escola.nome).all()
    if request.method == 'POST':
        nome=request.form.get('nome','').strip(); login_v=request.form.get('login','').strip()
        senha=request.form.get('senha','').strip(); ids_sel=request.form.getlist('escolas_ids',type=int)
        meta=request.form.get('meta_mes',0,type=int)
        if not nome or not login_v or not senha:
            flash('Nome, login e senha são obrigatórios.','danger')
            return render_template('admin_novo_vendedor.html', escolas=escolas)
        if Vendedor.query.filter_by(login=login_v).first():
            flash('Login já existe.','danger'); return render_template('admin_novo_vendedor.html', escolas=escolas)
        v = Vendedor(nome=nome, login=login_v, meta_mes=meta)
        v.set_senha(senha); v.set_escolas_ids(ids_sel)
        db.session.add(v); LogAtividade.registrar('vendedor_criado',f'Vendedor "{nome}" criado')
        db.session.commit(); flash(f'Vendedor {nome} criado.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_novo_vendedor.html', escolas=escolas)

@app.route('/admin/vendedor/<int:vid>/editar', methods=['GET','POST'])
@admin_required
def admin_editar_vendedor(vid):
    vendedor=Vendedor.query.get_or_404(vid); escolas=Escola.query.order_by(Escola.nome).all()
    if request.method == 'POST':
        vendedor.nome     = request.form.get('nome', vendedor.nome).strip()
        vendedor.ativo    = 'ativo' in request.form
        vendedor.meta_mes = request.form.get('meta_mes', 0, type=int)
        nova_senha = request.form.get('nova_senha','').strip()
        if nova_senha: vendedor.set_senha(nova_senha)
        vendedor.set_escolas_ids(request.form.getlist('escolas_ids',type=int))
        db.session.commit(); flash('Vendedor atualizado.','success')
        return redirect(url_for('admin_painel'))
    return render_template('admin_editar_vendedor.html', vendedor=vendedor, escolas=escolas)

@app.route('/admin/vendedor/<int:vid>/excluir', methods=['POST'])
@admin_required
def admin_excluir_vendedor(vid):
    v=Vendedor.query.get_or_404(vid)
    LogAtividade.registrar('vendedor_excluido',f'Vendedor "{v.nome}" excluído')
    db.session.delete(v); db.session.commit()
    flash('Vendedor excluído.','success'); return redirect(url_for('admin_painel'))


# ══════════════════════════════════════════════
#  VENDEDOR
# ══════════════════════════════════════════════
@app.route('/vendedor/login', methods=['GET','POST'])
def vendedor_login():
    if request.method == 'POST':
        lv=request.form.get('login','').strip(); sv=request.form.get('senha','')
        ip=get_client_ip()
        v=Vendedor.query.filter_by(login=lv,ativo=True).first()
        if v and v.check_senha(sv):
            session['vendedor_id']=v.id; session['vendedor_nome']=v.nome
            session['last_active']=datetime.utcnow().isoformat()
            return redirect(url_for('vendedor_painel'))
        LogAtividade.registrar('login_falhou',f'Tentativa falha vendedor: "{lv}"','anônimo',ip)
        db.session.commit()
        flash('Login ou senha incorretos.','danger')
    return render_template('vendedor_login.html')

@app.route('/vendedor/logout')
def vendedor_logout():
    session.pop('vendedor_id',None); session.pop('vendedor_nome',None)
    return redirect(url_for('vendedor_login'))

@app.route('/vendedor')
@vendedor_required
def vendedor_painel():
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    ids=vendedor.get_escolas_ids()
    escolas=(Escola.query.filter(Escola.id.in_(ids)) if ids else Escola.query).order_by(Escola.nome).all()
    inicio_mes=datetime.utcnow().replace(day=1,hour=0,minute=0,second=0)
    vendas_mes=VendaAnotacao.query.filter(
        VendaAnotacao.vendedor_id==vendedor.id,VendaAnotacao.criado_em>=inicio_mes).all()
    total_mes=len(vendas_mes)
    vendidos_mes=sum(1 for v in vendas_mes if v.status=='vendido')
    interesse_mes=sum(1 for v in vendas_mes if v.status=='interesse')
    valor_mes=sum(v.valor_venda or 0 for v in vendas_mes if v.status=='vendido')
    pct_meta=min(100,int(vendidos_mes/vendedor.meta_mes*100)) if vendedor.meta_mes else 0
    return render_template('vendedor_painel.html',
        vendedor=vendedor, escolas=escolas,
        total_mes=total_mes, vendidos_mes=vendidos_mes,
        interesse_mes=interesse_mes, valor_mes=valor_mes,
        pct_meta=pct_meta)

@app.route('/vendedor/escola/<int:escola_id>')
@vendedor_required
def vendedor_escola(escola_id):
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    if not vendedor.pode_ver_escola(escola_id):
        flash('Acesso negado.','danger'); return redirect(url_for('vendedor_painel'))
    escola=Escola.query.get_or_404(escola_id)
    return render_template('vendedor_escola.html', vendedor=vendedor, escola=escola)

@app.route('/vendedor/album/<int:album_id>')
@vendedor_required
def vendedor_album(album_id):
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    album=Album.query.get_or_404(album_id)
    if not vendedor.pode_ver_escola(album.escola_id):
        flash('Acesso negado.','danger'); return redirect(url_for('vendedor_painel'))
    anotacoes=VendaAnotacao.query.filter_by(
        vendedor_id=vendedor.id,album_id=album_id
    ).order_by(VendaAnotacao.criado_em.desc()).all()
    site_url=app.config['SITE_URL']
    msg_venda=(
        f"Olá! 😊\n\nAcabamos de mostrar seu álbum de formatura da "
        f"*Harmonia Formaturas & Buffet*!\n\n"
        f"Você pode acessar em casa pelo link:\n🌐 {site_url}/login\n\n"
        f"Caso queira adquirir ou tiver dúvidas, entre em contato conosco!\n\n"
        f"_Harmonia Formaturas & Buffet_"
    )
    wa_venda=f"https://wa.me/?text={url_quote(msg_venda)}"
    return render_template('vendedor_album.html',
        vendedor=vendedor, album=album, anotacoes=anotacoes, wa_venda=wa_venda)

@app.route('/vendedor/album/<int:album_id>/apresentar')
@vendedor_required
def vendedor_apresentar(album_id):
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    album=Album.query.get_or_404(album_id)
    if not vendedor.pode_ver_escola(album.escola_id):
        flash('Acesso negado.','danger'); return redirect(url_for('vendedor_painel'))
    return render_template('vendedor_apresentar.html', album=album, vendedor=vendedor)

@app.route('/vendedor/album/<int:album_id>/anotar', methods=['POST'])
@vendedor_required
def vendedor_anotar(album_id):
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    album=Album.query.get_or_404(album_id)
    if not vendedor.pode_ver_escola(album.escola_id):
        flash('Acesso negado.','danger'); return redirect(url_for('vendedor_painel'))
    nome_c=request.form.get('nome_cliente','').strip()
    if not nome_c: flash('Informe o nome do cliente.','danger'); return redirect(url_for('vendedor_album',album_id=album_id))
    valor_s=request.form.get('valor_venda','').strip().replace(',','.')
    valor=float(valor_s) if valor_s else None
    visita_str=request.form.get('visita_agendada','').strip()
    visita_dt=None
    if visita_str:
        try: visita_dt=datetime.strptime(visita_str,'%Y-%m-%dT%H:%M')
        except: pass
    db.session.add(VendaAnotacao(
        vendedor_id=vendedor.id, album_id=album_id,
        nome_cliente=nome_c, telefone=request.form.get('telefone','').strip(),
        status=request.form.get('status','interesse'),
        obs=request.form.get('obs','').strip(),
        endereco=request.form.get('endereco','').strip(),
        valor_venda=valor, visita_agendada=visita_dt
    ))
    db.session.commit(); flash('Anotação registrada!','success')
    return redirect(url_for('vendedor_album', album_id=album_id))

@app.route('/vendedor/anotacao/<int:anot_id>/excluir', methods=['POST'])
@vendedor_required
def vendedor_excluir_anotacao(anot_id):
    anot=VendaAnotacao.query.get_or_404(anot_id)
    album_id=anot.album_id
    if anot.vendedor_id!=session['vendedor_id']: flash('Acesso negado.','danger'); return redirect(url_for('vendedor_painel'))
    db.session.delete(anot); db.session.commit()
    flash('Anotação removida.','success'); return redirect(url_for('vendedor_album',album_id=album_id))

@app.route('/vendedor/historico')
@vendedor_required
def vendedor_historico():
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    anotacoes=VendaAnotacao.query.filter_by(vendedor_id=vendedor.id).order_by(VendaAnotacao.criado_em.desc()).all()
    return render_template('vendedor_historico.html', vendedor=vendedor, anotacoes=anotacoes)

@app.route('/vendedor/agenda')
@vendedor_required
def vendedor_agenda():
    vendedor=Vendedor.query.get_or_404(session['vendedor_id'])
    agora=datetime.utcnow()
    proximas=VendaAnotacao.query.filter(
        VendaAnotacao.vendedor_id==vendedor.id,
        VendaAnotacao.visita_agendada>=agora
    ).order_by(VendaAnotacao.visita_agendada).all()
    passadas=VendaAnotacao.query.filter(
        VendaAnotacao.vendedor_id==vendedor.id,
        VendaAnotacao.visita_agendada<agora,
        VendaAnotacao.visita_agendada!=None
    ).order_by(VendaAnotacao.visita_agendada.desc()).limit(20).all()
    return render_template('vendedor_agenda.html', vendedor=vendedor, proximas=proximas, passadas=passadas)


# ══════════════════════════════════════════════
#  ERROS
# ══════════════════════════════════════════════
@app.errorhandler(404)
def erro_404(e): return render_template('erro.html',codigo=404,titulo='Página não encontrada',msg='O link que você acessou não existe ou foi removido.'),404
@app.errorhandler(500)
def erro_500(e): return render_template('erro.html',codigo=500,titulo='Erro interno',msg='Algo deu errado. Tente novamente em instantes.'),500
@app.errorhandler(503)
def erro_503(e): return render_template('manutencao.html'),503


# ══════════════════════════════════════════════
#  API
# ══════════════════════════════════════════════
@app.route('/api/acesso/<int:acesso_id>/status')
@admin_required
def api_acesso_status(acesso_id):
    a=ClienteAlbum.query.get_or_404(acesso_id)
    return jsonify({'visualizado':a.visualizado,'baixado':a.baixado,
                    'expirado':a.expirado,'dias_restantes':a.dias_restantes,
                    'qtd_acessos':a.qtd_acessos or 0,'segundos_restantes':a.segundos_restantes})

@app.route('/api/vapid-public-key')
def api_vapid_key():
    return jsonify({'key': app.config.get('VAPID_PUBLIC_KEY','')})


# ══════════════════════════════════════════════
#  INIT
# ══════════════════════════════════════════════
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
