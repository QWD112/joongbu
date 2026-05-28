from flask import Flask
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()

    # 테이블 만들기 ✅ 한 줄로 정리!
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT)''')


    # 데이터가 없을 때만 넣기
    cursor.execute("SELECT COUNT(*) FROM courses")
    count = cursor.fetchone()[0]

    if count == 0:
        data = [
            ('flask', 'flask is ...'),
            ('python', 'python is ...'),
            ('webDB', 'webDB is ...'),
        ]
        for d in data:
            cursor.execute("INSERT INTO courses (title, body) VALUES (?, ?)", d)

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

    cursor.execute("SELECT * FROM courses WHERE id = ?", (id,))
    course = cursor.fetchone()
    conn.close()

    courseList = ''
    for course in courses:
        courseList = courseList + f'<li><a href="/read/{course[0]}/">{course[1]}</a></li>'

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


app.run(debug=True)