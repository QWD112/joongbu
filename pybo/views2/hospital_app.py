from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'hospital.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, age INTEGER,
        phone TEXT, blood TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, major TEXT NOT NULL,
        license TEXT, phone TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.commit(); db.close(); print('hospital.db 생성완료!')

PATIENTS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>환자 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>나이</th><th>전화번호</th><th>혈액형</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["age"] or "-" }}</td><td>{{ item["phone"] or "-" }}</td>
    <td>{{ item["blood"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/patients/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/patients/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 환자가 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addpatients">+ 환자 등록</a> | <a href="/doctors">의사 목록</a></body></html>'''

@app.route('/patients')
def list_patients():
    db = get_db()
    items = db.execute('SELECT * FROM patients ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(PATIENTS_LIST, items=items)

ADD_PATIENT = '''<!doctype html><html lang="ko"><body>
<h2>환자 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  나이: <input name="age" type="number"><br><br>
  전화번호: <input name="phone"><br><br>
  혈액형: <input name="blood" placeholder="예) A형"><br><br>
  <button>등록</button>
</form><a href="/patients">목록으로</a></body></html>'''

@app.route('/addpatients', methods=['GET','POST'])
def add_patients():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(ADD_PATIENT, error='이름을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO patients (name,age,phone,blood) VALUES (?,?,?,?)',
            (name, request.form.get('age') or None,
             request.form.get('phone') or None, request.form.get('blood') or None))
        db.commit(); db.close()
        return redirect(url_for('list_patients'))
    return render_template_string(ADD_PATIENT, error=None)

EDIT_PATIENT = '''<!doctype html><html lang="ko"><body>
<h2>환자 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  나이: <input name="age" type="number" value="{{ item['age'] or '' }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  혈액형: <input name="blood" value="{{ item['blood'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/patients">취소</a></body></html>'''

@app.route('/patients/<int:pid>/edit', methods=['GET','POST'])
def edit_patients(pid):
    db = get_db()
    item = db.execute('SELECT * FROM patients WHERE id=?',(pid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(EDIT_PATIENT, item=item, error='이름을 입력해주세요')
        db = get_db()
        db.execute('UPDATE patients SET name=?,age=?,phone=?,blood=? WHERE id=?',
            (name, request.form.get('age') or None,
             request.form.get('phone') or None,
             request.form.get('blood') or None, pid))
        db.commit(); db.close()
        return redirect(url_for('list_patients'))
    return render_template_string(EDIT_PATIENT, item=item, error=None)

@app.route('/patients/<int:pid>/delete', methods=['POST'])
def delete_patients(pid):
    db = get_db()
    db.execute('DELETE FROM patients WHERE id=?',(pid,))
    db.commit(); db.close()
    return redirect(url_for('list_patients'))

DOCTORS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>의사 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>전문과목</th><th>면허번호</th><th>전화번호</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["major"] }}</td><td>{{ item["license"] or "-" }}</td>
    <td>{{ item["phone"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/doctors/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/doctors/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 의사가 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/adddoctors">+ 의사 등록</a> | <a href="/patients">환자 목록</a></body></html>'''

@app.route('/doctors')
def list_doctors():
    db = get_db()
    items = db.execute('SELECT * FROM doctors ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(DOCTORS_LIST, items=items)

ADD_DOCTOR = '''<!doctype html><html lang="ko"><body>
<h2>의사 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  전문과목: <input name="major" required><br><br>
  면허번호: <input name="license"><br><br>
  전화번호: <input name="phone"><br><br>
  <button>등록</button>
</form><a href="/doctors">목록으로</a></body></html>'''

@app.route('/adddoctors', methods=['GET','POST'])
def add_doctors():
    if request.method == 'POST':
        name  = request.form.get('name','').strip()
        major = request.form.get('major','').strip()
        if not name:  return render_template_string(ADD_DOCTOR, error='이름을 입력해주세요')
        if not major: return render_template_string(ADD_DOCTOR, error='전문과목을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO doctors (name,major,license,phone) VALUES (?,?,?,?)',
            (name, major, request.form.get('license') or None, request.form.get('phone') or None))
        db.commit(); db.close()
        return redirect(url_for('list_doctors'))
    return render_template_string(ADD_DOCTOR, error=None)

EDIT_DOCTOR = '''<!doctype html><html lang="ko"><body>
<h2>의사 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  전문과목: <input name="major" required value="{{ item['major'] }}"><br><br>
  면허번호: <input name="license" value="{{ item['license'] or '' }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/doctors">취소</a></body></html>'''

@app.route('/doctors/<int:did>/edit', methods=['GET','POST'])
def edit_doctors(did):
    db = get_db()
    item = db.execute('SELECT * FROM doctors WHERE id=?',(did,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name  = request.form.get('name','').strip()
        major = request.form.get('major','').strip()
        if not name:  return render_template_string(EDIT_DOCTOR, item=item, error='이름을 입력해주세요')
        if not major: return render_template_string(EDIT_DOCTOR, item=item, error='전문과목을 입력해주세요')
        db = get_db()
        db.execute('UPDATE doctors SET name=?,major=?,license=?,phone=? WHERE id=?',
            (name, major, request.form.get('license') or None,
             request.form.get('phone') or None, did))
        db.commit(); db.close()
        return redirect(url_for('list_doctors'))
    return render_template_string(EDIT_DOCTOR, item=item, error=None)

@app.route('/doctors/<int:did>/delete', methods=['POST'])
def delete_doctors(did):
    db = get_db()
    db.execute('DELETE FROM doctors WHERE id=?',(did,))
    db.commit(); db.close()
    return redirect(url_for('list_doctors'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
