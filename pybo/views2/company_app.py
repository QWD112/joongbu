from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'company.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, position TEXT,
        salary REAL DEFAULT 0, phone TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, location TEXT,
        budget REAL DEFAULT 0, manager TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.commit(); db.close(); print('company.db 생성완료!')

EMPLOYEES_LIST = '''<!doctype html><html lang="ko"><body>
<h2>직원 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>직급</th><th>급여</th><th>전화번호</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["position"] or "-" }}</td><td>{{ item["salary"] or 0 }}</td>
    <td>{{ item["phone"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/employees/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/employees/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 직원이 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addemployees">+ 직원 등록</a> | <a href="/departments">부서 목록</a></body></html>'''

@app.route('/employees')
def list_employees():
    db = get_db()
    items = db.execute('SELECT * FROM employees ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(EMPLOYEES_LIST, items=items)

ADD_EMPLOYEE = '''<!doctype html><html lang="ko"><body>
<h2>직원 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  직급: <input name="position"><br><br>
  급여: <input name="salary" type="number" step="0.01"><br><br>
  전화번호: <input name="phone"><br><br>
  <button>등록</button>
</form><a href="/employees">목록으로</a></body></html>'''

@app.route('/addemployees', methods=['GET','POST'])
def add_employees():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(ADD_EMPLOYEE, error='이름을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO employees (name,position,salary,phone) VALUES (?,?,?,?)',
            (name, request.form.get('position') or None,
             request.form.get('salary') or 0,
             request.form.get('phone') or None))
        db.commit(); db.close()
        return redirect(url_for('list_employees'))
    return render_template_string(ADD_EMPLOYEE, error=None)

EDIT_EMPLOYEE = '''<!doctype html><html lang="ko"><body>
<h2>직원 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  직급: <input name="position" value="{{ item['position'] or '' }}"><br><br>
  급여: <input name="salary" type="number" step="0.01" value="{{ item['salary'] or 0 }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/employees">취소</a></body></html>'''

@app.route('/employees/<int:eid>/edit', methods=['GET','POST'])
def edit_employees(eid):
    db = get_db()
    item = db.execute('SELECT * FROM employees WHERE id=?',(eid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(EDIT_EMPLOYEE, item=item, error='이름을 입력해주세요')
        db = get_db()
        db.execute('UPDATE employees SET name=?,position=?,salary=?,phone=? WHERE id=?',
            (name, request.form.get('position') or None,
             request.form.get('salary') or 0,
             request.form.get('phone') or None, eid))
        db.commit(); db.close()
        return redirect(url_for('list_employees'))
    return render_template_string(EDIT_EMPLOYEE, item=item, error=None)

@app.route('/employees/<int:eid>/delete', methods=['POST'])
def delete_employees(eid):
    db = get_db()
    db.execute('DELETE FROM employees WHERE id=?',(eid,))
    db.commit(); db.close()
    return redirect(url_for('list_employees'))

DEPARTMENTS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>부서 목록 (총 {{ items|length }}개)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>부서명</th><th>위치</th><th>예산</th><th>부서장</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["location"] or "-" }}</td><td>{{ item["budget"] or 0 }}</td>
    <td>{{ item["manager"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/departments/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/departments/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 부서가 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/adddepartments">+ 부서 등록</a> | <a href="/employees">직원 목록</a></body></html>'''

@app.route('/departments')
def list_departments():
    db = get_db()
    items = db.execute('SELECT * FROM departments ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(DEPARTMENTS_LIST, items=items)

ADD_DEPT = '''<!doctype html><html lang="ko"><body>
<h2>부서 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  부서명: <input name="name" required><br><br>
  위치: <input name="location"><br><br>
  예산: <input name="budget" type="number" step="0.01"><br><br>
  부서장: <input name="manager"><br><br>
  <button>등록</button>
</form><a href="/departments">목록으로</a></body></html>'''

@app.route('/adddepartments', methods=['GET','POST'])
def add_departments():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(ADD_DEPT, error='부서명을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO departments (name,location,budget,manager) VALUES (?,?,?,?)',
            (name, request.form.get('location') or None,
             request.form.get('budget') or 0,
             request.form.get('manager') or None))
        db.commit(); db.close()
        return redirect(url_for('list_departments'))
    return render_template_string(ADD_DEPT, error=None)

EDIT_DEPT = '''<!doctype html><html lang="ko"><body>
<h2>부서 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  부서명: <input name="name" required value="{{ item['name'] }}"><br><br>
  위치: <input name="location" value="{{ item['location'] or '' }}"><br><br>
  예산: <input name="budget" type="number" step="0.01" value="{{ item['budget'] or 0 }}"><br><br>
  부서장: <input name="manager" value="{{ item['manager'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/departments">취소</a></body></html>'''

@app.route('/departments/<int:did>/edit', methods=['GET','POST'])
def edit_departments(did):
    db = get_db()
    item = db.execute('SELECT * FROM departments WHERE id=?',(did,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(EDIT_DEPT, item=item, error='부서명을 입력해주세요')
        db = get_db()
        db.execute('UPDATE departments SET name=?,location=?,budget=?,manager=? WHERE id=?',
            (name, request.form.get('location') or None,
             request.form.get('budget') or 0,
             request.form.get('manager') or None, did))
        db.commit(); db.close()
        return redirect(url_for('list_departments'))
    return render_template_string(EDIT_DEPT, item=item, error=None)

@app.route('/departments/<int:did>/delete', methods=['POST'])
def delete_departments(did):
    db = get_db()
    db.execute('DELETE FROM departments WHERE id=?',(did,))
    db.commit(); db.close()
    return redirect(url_for('list_departments'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
