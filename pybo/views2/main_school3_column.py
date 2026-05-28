from flask import Flask, request, redirect
import sqlite3

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()
    return conn, cursor


def init_db():
    conn, cursor = get_db()
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        title     TEXT,
        body      TEXT,
        professor TEXT,
        grade     INTEGER,
        room      TEXT)''')
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
        <button onclick="location.href='/create/'">과목등록</button>
        <ol>{courseList}</ol>
        <hr>
        <h2>{course[1]}</h2>
        <p>담당교수 : {course[3]}</p>
        <p>학년     : {course[4]}</p>
        <p>강의실   : {course[5]}</p>
        <p>{course[2]}</p>
        <button onclick="location.href='/update/{course[0]}/'">수정</button>
        <button onclick="location.href='/delete/{course[0]}/'">삭제</button>
    </body>
</html>'''


@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title     = request.form['title']
        body      = request.form['body']
        professor = request.form['professor']
        grade     = request.form['grade']
        room      = request.form['room']
        conn, cursor = get_db()
        cursor.execute(
            "INSERT INTO courses (title, body, professor, grade, room) VALUES (?, ?, ?, ?, ?)",
            (title, body, professor, grade, room)
        )
        conn.commit()
        conn.close()
        return redirect('/')

    return '''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <h2>과목등록</h2>
        <form method="post">
            <table>
                <tr>
                    <td>과목명</td>
                    <td><input type="text" name="title" id="title" placeholder="예) 웹DB프로그래밍"></td>
                </tr>
                <tr>
                    <td>내용</td>
                    <td><textarea name="body" id="body" rows="4" cols="40" placeholder="과목 내용을 입력하세요"></textarea></td>
                </tr>
                <tr>
                    <td>담당교수</td>
                    <td><input type="text" name="professor" id="professor" placeholder="예) 홍길동"></td>
                </tr>
                <tr>
                    <td>학년</td>
                    <td><input type="text" name="grade" id="grade" placeholder="예) 2"></td>
                </tr>
                <tr>
                    <td>강의실</td>
                    <td><input type="text" name="room" id="room" placeholder="예) 101호"></td>
                </tr>
                <tr>
                    <td></td>
                    <td>
                        <input type="button" value="저장" onclick="
                            if(document.getElementById('title').value==''
                               ||document.getElementById('body').value==''
                               ||document.getElementById('professor').value==''
                               ||document.getElementById('grade').value==''
                               ||document.getElementById('room').value==''){
                                alert('모든 항목을 입력해주세요');
                            } else {
                                document.querySelector('form').submit();
                            }">
                        <input type="button" value="취소" onclick="location.href='/'">
                    </td>
                </tr>
            </table>
        </form>
    </body>
</html>'''


@app.route('/update/<id>/', methods=['GET', 'POST'])
def update(id):
    conn, cursor = get_db()
    if request.method == 'POST':
        title     = request.form['title']
        body      = request.form['body']
        professor = request.form['professor']
        grade     = request.form['grade']
        room      = request.form['room']
        cursor.execute(
            "UPDATE courses SET title=?, body=?, professor=?, grade=?, room=? WHERE id=?",
            (title, body, professor, grade, room, id)
        )
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
            <table>
                <tr>
                    <td>과목명</td>
                    <td><input type="text" name="title" id="title" value="{course[1]}" placeholder="예) 웹DB프로그래밍"></td>
                </tr>
                <tr>
                    <td>내용</td>
                    <td><textarea name="body" id="body" rows="4" cols="40" placeholder="과목 내용을 입력하세요">{course[2]}</textarea></td>
                </tr>
                <tr>
                    <td>담당교수</td>
                    <td><input type="text" name="professor" id="professor" value="{course[3]}" placeholder="예) 홍길동"></td>
                </tr>
                <tr>
                    <td>학년</td>
                    <td><input type="text" name="grade" id="grade" value="{course[4]}" placeholder="예) 2"></td>
                </tr>
                <tr>
                    <td>강의실</td>
                    <td><input type="text" name="room" id="room" value="{course[5]}" placeholder="예) 101호"></td>
                </tr>
                <tr>
                    <td></td>
                    <td>
                        <input type="button" value="저장" onclick="
                            if(document.getElementById('title').value==''
                               ||document.getElementById('body').value==''
                               ||document.getElementById('professor').value==''
                               ||document.getElementById('grade').value==''
                               ||document.getElementById('room').value==''){{
                                alert('모든 항목을 입력해주세요');
                            }} else {{
                                document.querySelector('form').submit();
                            }}">
                        <input type="button" value="취소" onclick="location.href='/read/{id}/'">
                    </td>
                </tr>
            </table>
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