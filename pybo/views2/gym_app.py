from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'gym.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, age INTEGER,
        phone TEXT, goal TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS trainers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, specialty TEXT NOT NULL,
        career TEXT, phone TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.commit(); db.close(); print('gym.db 생성완료!')

# ── 회원 목록 ──
MEMBERS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>헬스장 회원 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>나이</th><th>전화번호</th><th>목표</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["age"] or "-" }}</td><td>{{ item["phone"] or "-" }}</td>
    <td>{{ item["goal"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/members/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/members/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 회원이 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addmembers">+ 회원 등록</a> | <a href="/trainers">트레이너 목록</a>
</body></html>'''

@app.route('/members')
def list_members():
    db = get_db()
    items = db.execute('SELECT * FROM members ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(MEMBERS_LIST, items=items)

# ── 회원 등록 ──
ADD_MEMBER = '''<!doctype html><html lang="ko"><body>
<h2>회원 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  나이: <input name="age" type="number"><br><br>
  전화번호: <input name="phone"><br><br>
  목표: <input name="goal"><br><br>
  <button>등록</button>
</form><a href="/members">목록으로</a></body></html>'''

@app.route('/addmembers', methods=['GET','POST'])
def add_members():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name:
            return render_template_string(ADD_MEMBER, error='이름을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO members (name,age,phone,goal) VALUES (?,?,?,?)',
            (name, request.form.get('age') or None,
             request.form.get('phone') or None, request.form.get('goal') or None))
        db.commit(); db.close()
        return redirect(url_for('list_members'))
    return render_template_string(ADD_MEMBER, error=None)

# ── 회원 수정 ──
EDIT_MEMBER = '''<!doctype html><html lang="ko"><body>
<h2>회원 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  나이: <input name="age" type="number" value="{{ item['age'] or '' }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  목표: <input name="goal" value="{{ item['goal'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/members">취소</a></body></html>'''

@app.route('/members/<int:mid>/edit', methods=['GET','POST'])
def edit_members(mid):
    db = get_db()
    item = db.execute('SELECT * FROM members WHERE id=?',(mid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name:
            return render_template_string(EDIT_MEMBER, item=item, error='이름을 입력해주세요')
        db = get_db()
        db.execute('UPDATE members SET name=?,age=?,phone=?,goal=? WHERE id=?',
            (name, request.form.get('age') or None,
             request.form.get('phone') or None,
             request.form.get('goal') or None, mid))
        db.commit(); db.close()
        return redirect(url_for('list_members'))
    return render_template_string(EDIT_MEMBER, item=item, error=None)

@app.route('/members/<int:mid>/delete', methods=['POST'])
def delete_members(mid):
    db = get_db()
    db.execute('DELETE FROM members WHERE id=?',(mid,))
    db.commit(); db.close()
    return redirect(url_for('list_members'))

# ── 트레이너 목록 ──
TRAINERS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>트레이너 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>전문분야</th><th>경력</th><th>전화번호</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["specialty"] }}</td><td>{{ item["career"] or "-" }}</td>
    <td>{{ item["phone"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/trainers/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/trainers/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 트레이너가 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addtrainers">+ 트레이너 등록</a> | <a href="/members">회원 목록</a>
</body></html>'''

@app.route('/trainers')
def list_trainers():
    db = get_db()
    items = db.execute('SELECT * FROM trainers ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(TRAINERS_LIST, items=items)

# ── 트레이너 등록 ──
ADD_TRAINER = '''<!doctype html><html lang="ko"><body>
<h2>트레이너 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  전문분야: <input name="specialty" required><br><br>
  경력: <input name="career"><br><br>
  전화번호: <input name="phone"><br><br>
  <button>등록</button>
</form><a href="/trainers">목록으로</a></body></html>'''

@app.route('/addtrainers', methods=['GET','POST'])
def add_trainers():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        spec = request.form.get('specialty','').strip()
        if not name: return render_template_string(ADD_TRAINER, error='이름을 입력해주세요')
        if not spec: return render_template_string(ADD_TRAINER, error='전문분야를 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO trainers (name,specialty,career,phone) VALUES (?,?,?,?)',
            (name, spec, request.form.get('career') or None, request.form.get('phone') or None))
        db.commit(); db.close()
        return redirect(url_for('list_trainers'))
    return render_template_string(ADD_TRAINER, error=None)

# ── 트레이너 수정 ──
EDIT_TRAINER = '''<!doctype html><html lang="ko"><body>
<h2>트레이너 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  전문분야: <input name="specialty" required value="{{ item['specialty'] }}"><br><br>
  경력: <input name="career" value="{{ item['career'] or '' }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/trainers">취소</a></body></html>'''

@app.route('/trainers/<int:tid>/edit', methods=['GET','POST'])
def edit_trainers(tid):
    db = get_db()
    item = db.execute('SELECT * FROM trainers WHERE id=?',(tid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        spec = request.form.get('specialty','').strip()
        if not name: return render_template_string(EDIT_TRAINER, item=item, error='이름을 입력해주세요')
        if not spec: return render_template_string(EDIT_TRAINER, item=item, error='전문분야를 입력해주세요')
        db = get_db()
        db.execute('UPDATE trainers SET name=?,specialty=?,career=?,phone=? WHERE id=?',
            (name, spec, request.form.get('career') or None, request.form.get('phone') or None, tid))
        db.commit(); db.close()
        return redirect(url_for('list_trainers'))
    return render_template_string(EDIT_TRAINER, item=item, error=None)

@app.route('/trainers/<int:tid>/delete', methods=['POST'])
def delete_trainers(tid):
    db = get_db()
    db.execute('DELETE FROM trainers WHERE id=?',(tid,))
    db.commit(); db.close()
    return redirect(url_for('list_trainers'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
