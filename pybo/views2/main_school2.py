
from flask import Flask, request, redirect
import sqlite3

app = Flask(__name__)


# DB 연결 함수 — 모든 route에서 재사용
def get_db():
    conn = sqlite3.connect('courses2.db')
    cursor = conn.cursor()
    return conn, cursor


def init_db():
    conn, cursor = get_db()
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT)''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    conn.close()

    courseList = ''
    for course in courses:
        courseList += f'<li><a href="/read/{course[0]}/">{course[1]}</a></li>'

    return f'''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <button onclick="location.href='/create/'">과목등록</button>
        <ol>{courseList}</ol>
        <hr>
    </body>
</html>'''


@app.route('/read/<id>/')
def read(id):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    cursor.execute("SELECT * FROM courses WHERE id = ?", (id,))
    course = cursor.fetchone()
    conn.close()

    courseList = ''
    for c in courses:
        courseList += f'<li><a href="/read/{c[0]}/">{c[1]}</a></li>'

    return f'''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <ol>{courseList}</ol>
        <hr>
        <h2>{course[1]}</h2>
        <p>{course[2]}</p>
        <button onclick="location.href='/update/{course[0]}/'">수정</button>
        <button onclick="location.href='/delete/{course[0]}/'">삭제</button>
    </body>
</html>'''


@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        conn, cursor = get_db()
        cursor.execute("INSERT INTO courses (title, body) VALUES (?, ?)", (title, body))
        conn.commit()
        conn.close()
        return redirect('/')

    return f'''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <h2>과목등록</h2>
        <form method="post">
            제목 : <input type="text" name="title" id="title"><br><br>
            내용 : <textarea name="body" id="body"></textarea><br><br>
            <input type="button" value="저장" onclick="
                if(document.getElementById('title').value==''||document.getElementById('body').value==''){{
                    alert('제목과 내용을 입력해주세요');
                }} else {{
                    document.querySelector('form').submit();
                }}">
            <input type="button" value="취소" onclick="location.href='/'">
        </form>
    </body>
</html>'''


@app.route('/update/<id>/', methods=['GET', 'POST'])
def update(id):
    conn, cursor = get_db()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        cursor.execute("UPDATE courses SET title=?, body=? WHERE id=?", (title, body, id))
        conn.commit()
        conn.close()
        return redirect(f'/read/{id}/')

    cursor.execute("SELECT * FROM courses WHERE id = ?", (id,))
    course = cursor.fetchone()
    conn.close()

    return f'''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <h2>과목수정</h2>
        <form method="post">
            제목 : <input type="text" name="title" id="title" value="{course[1]}"><br><br>
            내용 : <textarea name="body" id="body">{course[2]}</textarea><br><br>
            <input type="button" value="저장" onclick="
                if(document.getElementById('title').value==''||document.getElementById('body').value==''){{
                    alert('제목과 내용을 입력해주세요!');
                }} else {{
                    document.querySelector('form').submit();
                }}">
            <input type="button" value="취소" onclick="location.href='/read/{id}/'">
        </form>
    </body>
</html>'''


@app.route('/delete/<id>/')
def delete(id):
    conn, cursor = get_db()
    cursor.execute("DELETE FROM courses WHERE id = ?", (id,))
    conn.commit()
    cursor.execute("SELECT id FROM courses LIMIT 1")
    first = cursor.fetchone()
    conn.close()
    if first:
        return redirect(f'/read/{first[0]}/')
    else:
        return redirect('/empty/')


@app.route('/empty/')
def empty():
    return '''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <button onclick="location.href='/create/'">과목등록</button>
        <hr>
        <p>등록된 과목이 없습니다.</p>
    </body>
</html>'''


app.run(debug=True)