from flask import Flask
import random
import sqlite3
app=Flask(__name__)

def init_db():
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS courses1 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT)''')
    cursor.execute("SELECT COUNT() FROM courses1")
    count=cursor.fetchone()[0]

    if count==0:
        data=[
            ('flask','flask is ...'),
            ('fython','fython is ...'),
            ('webDB','webDB is ...')
        ]
        for item in data:
            cursor.execute("INSERT INTO courses1(title,body) VALUES (?,?)",item)

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # DB에서 데이터 가져오기
    conn = sqlite3.connect('courses1.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses1")
    courses = cursor.fetchall()
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
    </body>
</html>
'''

app.run(debug=True)