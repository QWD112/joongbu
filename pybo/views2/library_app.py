from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'library.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT,
        phone TEXT, address TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, author TEXT NOT NULL,
        isbn TEXT, stock INTEGER DEFAULT 1,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.commit(); db.close(); print('library.db 생성완료!')

MEMBERS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>도서관 회원 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>이메일</th><th>전화번호</th><th>주소</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["email"] or "-" }}</td><td>{{ item["phone"] or "-" }}</td>
    <td>{{ item["address"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/members/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/members/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 회원이 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addmembers">+ 회원 등록</a> | <a href="/books">도서 목록</a></body></html>'''

@app.route('/members')
def list_members():
    db = get_db()
    items = db.execute('SELECT * FROM members ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(MEMBERS_LIST, items=items)

ADD_MEMBER = '''<!doctype html><html lang="ko"><body>
<h2>회원 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  이메일: <input name="email" type="email"><br><br>
  전화번호: <input name="phone"><br><br>
  주소: <input name="address"><br><br>
  <button>등록</button>
</form><a href="/members">목록으로</a></body></html>'''

@app.route('/addmembers', methods=['GET','POST'])
def add_members():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(ADD_MEMBER, error='이름을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO members (name,email,phone,address) VALUES (?,?,?,?)',
            (name, request.form.get('email') or None,
             request.form.get('phone') or None, request.form.get('address') or None))
        db.commit(); db.close()
        return redirect(url_for('list_members'))
    return render_template_string(ADD_MEMBER, error=None)

EDIT_MEMBER = '''<!doctype html><html lang="ko"><body>
<h2>회원 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  이메일: <input name="email" value="{{ item['email'] or '' }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  주소: <input name="address" value="{{ item['address'] or '' }}"><br><br>
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
        if not name: return render_template_string(EDIT_MEMBER, item=item, error='이름을 입력해주세요')
        db = get_db()
        db.execute('UPDATE members SET name=?,email=?,phone=?,address=? WHERE id=?',
            (name, request.form.get('email') or None,
             request.form.get('phone') or None,
             request.form.get('address') or None, mid))
        db.commit(); db.close()
        return redirect(url_for('list_members'))
    return render_template_string(EDIT_MEMBER, item=item, error=None)

@app.route('/members/<int:mid>/delete', methods=['POST'])
def delete_members(mid):
    db = get_db()
    db.execute('DELETE FROM members WHERE id=?',(mid,))
    db.commit(); db.close()
    return redirect(url_for('list_members'))

BOOKS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>도서 목록 (총 {{ items|length }}권)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>제목</th><th>저자</th><th>ISBN</th><th>재고</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["title"] }}</td>
    <td>{{ item["author"] }}</td><td>{{ item["isbn"] or "-" }}</td>
    <td>{{ item["stock"] }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/books/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/books/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 도서가 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addbooks">+ 도서 등록</a> | <a href="/members">회원 목록</a></body></html>'''

@app.route('/books')
def list_books():
    db = get_db()
    items = db.execute('SELECT * FROM books ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(BOOKS_LIST, items=items)

ADD_BOOK = '''<!doctype html><html lang="ko"><body>
<h2>도서 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  제목: <input name="title" required><br><br>
  저자: <input name="author" required><br><br>
  ISBN: <input name="isbn"><br><br>
  재고: <input name="stock" type="number" value="1"><br><br>
  <button>등록</button>
</form><a href="/books">목록으로</a></body></html>'''

@app.route('/addbooks', methods=['GET','POST'])
def add_books():
    if request.method == 'POST':
        title  = request.form.get('title','').strip()
        author = request.form.get('author','').strip()
        if not title:  return render_template_string(ADD_BOOK, error='제목을 입력해주세요')
        if not author: return render_template_string(ADD_BOOK, error='저자를 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO books (title,author,isbn,stock) VALUES (?,?,?,?)',
            (title, author, request.form.get('isbn') or None,
             request.form.get('stock') or 1))
        db.commit(); db.close()
        return redirect(url_for('list_books'))
    return render_template_string(ADD_BOOK, error=None)

EDIT_BOOK = '''<!doctype html><html lang="ko"><body>
<h2>도서 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  제목: <input name="title" required value="{{ item['title'] }}"><br><br>
  저자: <input name="author" required value="{{ item['author'] }}"><br><br>
  ISBN: <input name="isbn" value="{{ item['isbn'] or '' }}"><br><br>
  재고: <input name="stock" type="number" value="{{ item['stock'] }}"><br><br>
  <button>수정 완료</button>
</form><a href="/books">취소</a></body></html>'''

@app.route('/books/<int:bid>/edit', methods=['GET','POST'])
def edit_books(bid):
    db = get_db()
    item = db.execute('SELECT * FROM books WHERE id=?',(bid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        title  = request.form.get('title','').strip()
        author = request.form.get('author','').strip()
        if not title:  return render_template_string(EDIT_BOOK, item=item, error='제목을 입력해주세요')
        if not author: return render_template_string(EDIT_BOOK, item=item, error='저자를 입력해주세요')
        db = get_db()
        db.execute('UPDATE books SET title=?,author=?,isbn=?,stock=? WHERE id=?',
            (title, author, request.form.get('isbn') or None,
             request.form.get('stock') or 1, bid))
        db.commit(); db.close()
        return redirect(url_for('list_books'))
    return render_template_string(EDIT_BOOK, item=item, error=None)

@app.route('/books/<int:bid>/delete', methods=['POST'])
def delete_books(bid):
    db = get_db()
    db.execute('DELETE FROM books WHERE id=?',(bid,))
    db.commit(); db.close()
    return redirect(url_for('list_books'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
