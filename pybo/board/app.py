from flask import Flask, request, redirect, render_template, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = '12345'



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'board.db')

# ─── DB 연결 함수 ────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

# ─── DB 초기화 ───────────────────────────────────────

def init_db():
    conn, cursor = get_db()

    cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        title   TEXT,
        content TEXT,
        author  TEXT,
        date    TEXT,
        views   INTEGER DEFAULT 0
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role     TEXT DEFAULT 'user'
    )''')

    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', '1234', 'admin')
        )

    conn.commit()
    conn.close()

init_db()



# ─── 목록 ────────────────────────────────────────────
@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login/')

    conn, cursor = get_db()

    cursor.execute('SELECT COUNT(*) FROM posts')
    count = cursor.fetchone()[0]

    keyword = request.args.get('keyword', '')

    if keyword:
        cursor.execute(
            'SELECT * FROM posts WHERE title LIKE ? ORDER BY id DESC',
            ('%' + keyword + '%',))
    else:
        cursor.execute('SELECT * FROM posts ORDER BY id DESC')

    posts = cursor.fetchall()
    conn.close()

    if keyword and len(posts) == 0:
        searchResult = f'"{keyword}" 검색 결과가 없습니다.'
    elif not keyword:
        searchResult = '검색어를 입력해주세요.'
    else:
        searchResult = ''

    return render_template('index.html',
        count=count,
        keyword=keyword,
        posts=posts,
        searchResult=searchResult)

# ─── 회원 삭제 (관리자 전용) ──────────────────────────
@app.route('/admin/delete/<id>/')
def admin_delete(id):
    if session.get('role') != 'admin':
        return redirect('/')
    conn, cursor = get_db()
    cursor.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/')


# ─── 회원 권한 변경 (관리자 전용) ────────────────────
@app.route('/admin/role/<id>/')
def admin_role(id):
    if session.get('role') != 'admin':
        return redirect('/')
    conn, cursor = get_db()
    cursor.execute('SELECT role FROM users WHERE id = ?', (id,))
    user = cursor.fetchone()
    if user[0] == 'user':
        newRole = 'admin'
    else:
        newRole = 'user'
    cursor.execute('UPDATE users SET role=? WHERE id=?', (newRole, id))
    conn.commit()
    conn.close()
    return redirect('/admin/')

# ─── 게시글 삭제 (관리자 전용) ───────────────────────
@app.route('/admin/post/delete/<id>/')
def admin_post_delete(id):
    if session.get('role') != 'admin':
        return redirect('/')
    conn, cursor = get_db()
    cursor.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/')

# ─── 관리자 페이지 ────────────────────────────────────
@app.route('/admin/')
def admin():
    if 'username' not in session:        # ← 로그인 안했으면 로그인으로
        return redirect('/login/')
    if session.get('role') != 'admin':   # ← 관리자 아니면 게시판으로
        return redirect('/')

    conn, cursor = get_db()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) FROM users')
    userCount = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM posts')
    postCount = cursor.fetchone()[0]
    conn.close()

    return render_template('admin.html',
        users=users,
        posts=posts,
        userCount=userCount,
        postCount=postCount)


# ─── 로그아웃 ─────────────────────────────────────────
@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect('/')


# ─── 로그인 ──────────────────────────────────────────
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn, cursor = get_db()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['role'] = user[3]

            # 관리자면 /admin/ 으로, 일반유저면 / 으로
            if user[3] == 'admin':
                return redirect('/admin/')
            else:
                return redirect('/')
        else:
            return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')

    return render_template('login.html', error='')

# ─── 회원가입 ─────────────────────────────────────────

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn, cursor = get_db()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:
            conn.close()
            return render_template('register.html', error='이미 존재하는 아이디입니다.', success='')

        cursor.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, password)
        )
        conn.commit()
        conn.close()

        # ✅ 회원가입 성공 → 자동 로그인 + 축하 메세지
        session['username'] = username
        return render_template('register.html', error='', success='회원가입을 축하합니다!')

    # ✅ 처음 접속할 때 → 빈 폼 표시
    return render_template('register.html', error='', success='')


# ─── 상세보기 ─────────────────────────────────────────
@app.route('/detail/<id>/')
def detail(id):
    if 'username' not in session:
        return redirect('/login/')

    conn, cursor = get_db()

    cursor.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (id,))
    conn.commit()

    cursor.execute('SELECT * FROM posts WHERE id = ?', (id,))
    post = cursor.fetchone()
    conn.close()


    return render_template('detail.html', post=post)

# ─── 글쓰기 ──────────────────────────────────────────
@app.route('/create/', methods=['GET', 'POST'])
def create():
    if 'username' not in session:
        return redirect('/login/')

    if request.method == 'POST':
        title   = request.form['title']
        content = request.form['content']
        author  = request.form['author']
        date    = datetime.now().strftime('%Y-%m-%d')

        conn, cursor = get_db()
        cursor.execute(
            'INSERT INTO posts (title, content, author, date) VALUES (?, ?, ?, ?)',
            (title, content, author, date)
        )
        conn.commit()
        conn.close()
        return redirect('/')


    return render_template('create.html')

# ─── 수정 ─────────────────────────────────────────────
@app.route('/update/<id>/', methods=['GET', 'POST'])
def update(id):

    conn, cursor = get_db()
    if request.method == 'POST':
        title   = request.form['title']
        content = request.form['content']
        author  = request.form['author']

        cursor.execute(
            'UPDATE posts SET title=?, content=?, author=? WHERE id=?',
            (title, content, author, id)
        )
        conn.commit()
        conn.close()
        return redirect(f'/detail/{id}/')

    cursor.execute('SELECT * FROM posts WHERE id = ?', (id,))
    post = cursor.fetchone()
    conn.close()

    return render_template('update.html', post=post)


# ─── 삭제 ─────────────────────────────────────────────
@app.route('/delete/<id>/')
def delete(id):

    conn, cursor = get_db()
    cursor.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()

    cursor.execute('SELECT id FROM posts ORDER BY id LIMIT 1')
    first = cursor.fetchone()
    conn.close()

    if first:
        return redirect(f'/detail/{first[0]}/')
    else:
        return redirect('/empty/')

# ─── 빈 페이지 ────────────────────────────────────────
@app.route('/empty/')
def empty():


    return render_template('empty.html')


# app.run(debug=True)