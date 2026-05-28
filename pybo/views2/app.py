from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'students.db'

# ── DB 연결 함수 ──────────────────────────────────────────
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

# ── 테이블 생성 (최초 1회) ───────────────────────────────
def init_db():
    db = get_db()

    # students 테이블
    db.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    NOT NULL,
            major TEXT    NOT NULL,
            score REAL    DEFAULT 0.0
        )
    ''')

    # teachers 테이블
    db.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            subject TEXT    NOT NULL,
            email   TEXT,
            phone   TEXT,
            created TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    db.close()
    print('테이블 생성 완료!')

# ════════════════════════════════════════════════════════
# ① 학생 목록
# ════════════════════════════════════════════════════════
@app.route('/students')
def list_students():
    db = get_db()
    students = db.execute(
        'SELECT * FROM students ORDER BY score DESC'
    ).fetchall()
    db.close()

    rows = ''.join(
        f'<tr><td>{s["id"]}</td><td>{s["name"]}</td>'
        f'<td>{s["major"]}</td><td>{s["score"]}</td></tr>'
        for s in students
    )
    return f'''
    <h2>학생 목록</h2>
    <table border="1" cellpadding="6">
      <tr><th>ID</th><th>이름</th><th>전공</th><th>점수</th></tr>
      {rows}
    </table>
    <br>
    <a href="/add">+ 학생 등록</a> |
    <a href="/teachers">교사 목록 보기</a>
    '''

# ════════════════════════════════════════════════════════
# ② 학생 등록
# ════════════════════════════════════════════════════════
ADD_STUDENT_FORM = '''
<!doctype html>
<html lang="ko">
<body>
  <h2>학생 등록</h2>
  <form method="POST">
    이름: <input name="name" required><br><br>
    전공: <input name="major" required><br><br>
    점수: <input name="score" type="number" step="0.1" value="0"><br><br>
    <button type="submit">등록</button>
  </form>
  <a href="/students">목록으로</a>
</body>
</html>
'''

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name  = request.form['name']
        major = request.form['major']
        score = float(request.form.get('score', 0))

        db = get_db()
        db.execute(
            'INSERT INTO students (name, major, score) VALUES (?, ?, ?)',
            (name, major, score)
        )
        db.commit()
        db.close()
        return redirect(url_for('list_students'))  # PRG 패턴

    return render_template_string(ADD_STUDENT_FORM)

# ════════════════════════════════════════════════════════
# ③ 교사 목록  →  /teachers
# ════════════════════════════════════════════════════════
TEACHERS_LIST = '''
<!doctype html>
<html lang="ko">
<body>
  <h2>교사 목록 (총 {{ teachers|length }}명)</h2>
  <table border="1" cellpadding="6">
    <tr>
      <th>ID</th>
      <th>이름</th>
      <th>담당 과목</th>
      <th>이메일</th>
      <th>전화번호</th>
      <th>등록일</th>
      <th>관리</th>
    </tr>
    {% for t in teachers %}
    <tr>
      <td>{{ t['id'] }}</td>
      <td>{{ t['name'] }}</td>
      <td>{{ t['subject'] }}</td>
      <td>{{ t['email'] or '-' }}</td>
      <td>{{ t['phone'] or '-' }}</td>
      <td>{{ t['created'][:10] if t['created'] else '-' }}</td>
      <td>
        <a href="/teachers/{{ t['id'] }}/edit">수정</a> |
        <form method="POST" action="/teachers/{{ t['id'] }}/delete"
              style="display:inline"
              onsubmit="return confirm('정말 삭제하시겠습니까?')">
          <button type="submit">삭제</button>
        </form>
      </td>
    </tr>
    {% else %}
    <tr>
      <td colspan="7" style="text-align:center">
        등록된 교사가 없습니다
      </td>
    </tr>
    {% endfor %}
  </table>
  <br>
  <a href="/addteachers">+ 교사 등록</a> |
  <a href="/students">학생 목록 보기</a>
</body>
</html>
'''

@app.route('/teachers')
def list_teachers():
    db = get_db()
    teachers = db.execute(
        'SELECT * FROM teachers ORDER BY id DESC'
    ).fetchall()
    db.close()
    return render_template_string(TEACHERS_LIST, teachers=teachers)

# ════════════════════════════════════════════════════════
# ④ 교사 등록  →  /addteachers
# ════════════════════════════════════════════════════════
ADD_TEACHER_FORM = '''
<!doctype html>
<html lang="ko">
<body>
  <h2>교사 등록</h2>

  {% if error %}
  <p style="color:red">{{ error }}</p>
  {% endif %}

  <form method="POST">
    이름:      <input name="name"    required
                     value="{{ form.name }}"><br><br>
    담당 과목: <input name="subject" required
                     value="{{ form.subject }}"><br><br>
    이메일:    <input name="email"   type="email"
                     value="{{ form.email }}"><br><br>
    전화번호:  <input name="phone"
                     value="{{ form.phone }}"><br><br>
    <button type="submit">등록</button>
  </form>
  <a href="/teachers">목록으로</a>
</body>
</html>
'''

@app.route('/addteachers', methods=['GET', 'POST'])
def add_teacher():
    form = {'name': '', 'subject': '', 'email': '', 'phone': ''}

    if request.method == 'POST':
        form['name']    = request.form.get('name',    '').strip()
        form['subject'] = request.form.get('subject', '').strip()
        form['email']   = request.form.get('email',   '').strip()
        form['phone']   = request.form.get('phone',   '').strip()

        if not form['name']:
            return render_template_string(ADD_TEACHER_FORM,
                form=form, error='이름을 입력해주세요')
        if not form['subject']:
            return render_template_string(ADD_TEACHER_FORM,
                form=form, error='담당 과목을 입력해주세요')

        db = get_db()
        db.execute(
            '''INSERT INTO teachers (name, subject, email, phone)
               VALUES (?, ?, ?, ?)''',
            (
                form['name'],
                form['subject'],
                form['email'] or None,
                form['phone'] or None
            )
        )
        db.commit()
        db.close()
        return redirect(url_for('list_teachers'))

    return render_template_string(ADD_TEACHER_FORM,
        form=form, error=None)

# ════════════════════════════════════════════════════════
# ⑤ 교사 수정
# ════════════════════════════════════════════════════════
EDIT_TEACHER_FORM = '''
<!doctype html>
<html lang="ko">
<body>
  <h2>교사 수정</h2>

  {% if error %}
  <p style="color:red">{{ error }}</p>
  {% endif %}

  <form method="POST">
    이름:      <input name="name"    required
                     value="{{ t['name'] }}"><br><br>
    담당 과목: <input name="subject" required
                     value="{{ t['subject'] }}"><br><br>
    이메일:    <input name="email"   type="email"
                     value="{{ t['email'] or '' }}"><br><br>
    전화번호:  <input name="phone"
                     value="{{ t['phone'] or '' }}"><br><br>
    <button type="submit">수정 완료</button>
  </form>
  <a href="/teachers">취소</a>
</body>
</html>
'''

@app.route('/teachers/<int:tid>/edit', methods=['GET', 'POST'])
def edit_teacher(tid):
    db = get_db()
    t  = db.execute(
        'SELECT * FROM teachers WHERE id = ?', (tid,)
    ).fetchone()
    db.close()

    if t is None:
        return '교사를 찾을 수 없습니다', 404

    if request.method == 'POST':
        name    = request.form.get('name',    '').strip()
        subject = request.form.get('subject', '').strip()
        email   = request.form.get('email',   '').strip() or None
        phone   = request.form.get('phone',   '').strip() or None

        if not name:
            return render_template_string(EDIT_TEACHER_FORM,
                t=t, error='이름을 입력해주세요')
        if not subject:
            return render_template_string(EDIT_TEACHER_FORM,
                t=t, error='담당 과목을 입력해주세요')

        db = get_db()
        db.execute(
            '''UPDATE teachers
               SET name=?, subject=?, email=?, phone=?
               WHERE id=?''',
            (name, subject, email, phone, tid)
        )
        db.commit()
        db.close()
        return redirect(url_for('list_teachers'))

    return render_template_string(EDIT_TEACHER_FORM, t=t, error=None)

# ════════════════════════════════════════════════════════
# ⑥ 교사 삭제
# ════════════════════════════════════════════════════════
@app.route('/teachers/<int:tid>/delete', methods=['POST'])
def delete_teacher(tid):
    db = get_db()
    db.execute('DELETE FROM teachers WHERE id = ?', (tid,))
    db.commit()
    db.close()
    return redirect(url_for('list_teachers'))

# ════════════════════════════════════════════════════════
# 앱 실행
# ════════════════════════════════════════════════════════
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
