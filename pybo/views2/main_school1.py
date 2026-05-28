from flask import Flask,request,redirect
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT)''')

    cursor.execute("SELECT COUNT(*) FROM courses")
    count = cursor.fetchone()[0]



    conn.commit()
    conn.close()


init_db()


# 홈페이지 - 목록 보기
@app.route('/')
def index():
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    conn.close()

    courseList = ''
    for course in courses:
        courseList = courseList + f'<li><a href="/read/{course[0]}/">{course[1]}</a></li>'

    return f'''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <button onclick="location.href='/create/'">과목등록</button>
        <button onclick="location.href='/update/{course[0]}/'">수정</button>
        <ol>
            {courseList}
        </ol>
        <hr>
    </body>
</html>
'''

@app.route('/read/<id>/')
def read(id):
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()

    # 목록 가져오기
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    # 선택한 항목 가져오기
    cursor.execute("SELECT * FROM courses WHERE id = ?", (id,))
    course = cursor.fetchone()
    conn.close()

    courseList = ''
    for c in courses:
        courseList = courseList + f'<li><a href="/read/{c[0]}/">{c[1]}</a></li>'
    return f'''<!doctype html>
<html>
    <body>
        <h1><a href="/">webDB programing</a></h1>
        <ol>
            {courseList}
        </ol>
        <hr>
        <h2>{course[1]}</h2>
        {course[2]}
    </body>
</html>
'''
@app.route('/create/',methods=['GET','POST'])
def create():
    if request.method == 'POST':
        title=request.form['title']
        body=request.form['body']

        conn=sqlite3.connect('courses1.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO courses(title,body) VALUES (?,?)",(title,body))
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
                if (document.getElementById('title').value == '' || document.getElementById('body').value == '') {{
                    alert('제목과 내용을 입력해주세요!');
                }} else {{
                    document.querySelector('form').submit();
                }}
            ">
            <input type="button" value="취소" onclick="location.href='/'">
        </form>
    </body>
</html>
'''






@app.route('/update/<id>/', methods=['GET', 'POST'])
def update(id):
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()

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
                if (document.getElementById('title').value == '' || document.getElementById('body').value == '') {{
                    alert('제목과 내용을 입력해주세요!');
                }} else {{
                    document.querySelector('form').submit();
                }}
            ">
            <input type="button" value="취소" onclick="location.href='/read/{id}/'">
        </form>
    </body>
</html>
'''




app.run(debug=True)