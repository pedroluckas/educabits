from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Troque em produção!

# E-mail do admin
EMAIL_ADMIN = 'admin@educabits.com'

# Simulação de dados em memória (por enquanto)
dados_aulas = {
    'phishing': [
        {'id_youtube': 'abc123', 'titulo': 'O que é Phishing?',
            'descricao': 'Aprenda a identificar golpes.'},
    ],
    'privacidade': [
        {'id_youtube': 'def456', 'titulo': 'Privacidade Online',
            'descricao': 'Proteja seus dados na web.'},
    ]
}


def criar_tabela():
    conn = sqlite3.connect('banco.db')
    c = conn.cursor()

    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')

    # Tabela de disciplinas
    c.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # Tabela de vídeos
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            id_youtube TEXT NOT NULL,
            FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id)
        )
    ''')

    conn.commit()
    conn.close()


criar_tabela()


@app.route('/')
def home():
    return redirect('/login')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])

        conn = sqlite3.connect('banco.db')
        c = conn.cursor()
        try:
            c.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
            conn.commit()
            flash('Cadastro realizado com sucesso! Faça o login.', 'sucesso')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Email já cadastrado! Use outro email.', 'erro')
            return redirect('/cadastro')
        finally:
            conn.close()
    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()
        cursor.execute('SELECT senha FROM usuarios WHERE email = ?', (email,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado and check_password_hash(resultado[0], senha):
            session['email'] = email
            return redirect('/dashboard')
        else:
            flash('Login inválido. Verifique seu email e senha.', 'erro')
            return redirect('/login')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session.get('email')
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome FROM usuarios WHERE email = ?', (email,))
    resultado = cursor.fetchone()
    conn.close()

    nome = resultado[0] if resultado else "Usuário"
    return render_template('tela.html', nome=nome)


@app.route('/aulas')
def aulas():
    if 'email' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome FROM disciplinas')
    disciplinas = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template('aulas.html', disciplinas=disciplinas)


@app.route('/aulas/<disciplina_url>')
def mostrar_disciplina(disciplina_url):
    if 'email' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # Pegar id da disciplina
    cursor.execute('SELECT id FROM disciplinas WHERE nome = ?',
                   (disciplina_url,))
    resultado = cursor.fetchone()

    if not resultado:
        flash("Disciplina não encontrada", "erro")
        return redirect(url_for('aulas'))

    disciplina_id = resultado[0]

    cursor.execute('''
        SELECT titulo, descricao, id_youtube FROM videos
        WHERE disciplina_id = ?
    ''', (disciplina_id,))
    videos = [{'titulo': row[0], 'descricao': row[1], 'id_youtube': row[2]}
              for row in cursor.fetchall()]
    conn.close()

    return render_template('disciplina_detalhe.html', disciplina_nome=disciplina_url.capitalize(), videos=videos)


@app.route('/admin/videos', methods=['GET', 'POST'])
def admin_videos():
    if 'email' not in session:
        return redirect(url_for('login'))
    if session['email'] != EMAIL_ADMIN:
        flash("Você não tem permissão para acessar esta página.", "erro")
        return redirect(url_for('dashboard'))

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # Cadastrar nova disciplina
    if request.method == 'POST':
        if 'nova_disciplina' in request.form:
            nova_disciplina = request.form['nova_disciplina'].strip().lower()
            try:
                cursor.execute(
                    'INSERT INTO disciplinas (nome) VALUES (?)', (nova_disciplina,))
                conn.commit()
                flash("Disciplina adicionada com sucesso!", "sucesso")
            except sqlite3.IntegrityError:
                flash("Essa disciplina já existe.", "erro")
        elif 'titulo' in request.form:
            disciplina_id = request.form['disciplina_id']
            titulo = request.form['titulo']
            descricao = request.form['descricao']
            id_youtube = request.form['id_youtube']
            cursor.execute('''
                INSERT INTO videos (disciplina_id, titulo, descricao, id_youtube)
                VALUES (?, ?, ?, ?)
            ''', (disciplina_id, titulo, descricao, id_youtube))
            conn.commit()
            flash("Vídeo cadastrado com sucesso!", "sucesso")

    # Buscar disciplinas e vídeos
    cursor.execute('SELECT id, nome FROM disciplinas')
    disciplinas = cursor.fetchall()

    dados = {}
    for disc_id, nome in disciplinas:
        cursor.execute(
            'SELECT titulo, id_youtube FROM videos WHERE disciplina_id = ?', (disc_id,))
        videos = cursor.fetchall()
        dados[nome] = [{'titulo': v[0], 'id_youtube': v[1]} for v in videos]

    conn.close()
    return render_template('admin_videos.html', disciplinas=disciplinas, dados=dados)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
