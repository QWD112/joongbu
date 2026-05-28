from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'shop.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT,
        phone TEXT, address TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, price REAL DEFAULT 0,
        stock INTEGER DEFAULT 0, category TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP)''')
    db.commit(); db.close(); print('shop.db 생성완료!')

CUSTOMERS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>고객 목록 (총 {{ items|length }}명)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>이름</th><th>이메일</th><th>전화번호</th><th>주소</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["email"] or "-" }}</td><td>{{ item["phone"] or "-" }}</td>
    <td>{{ item["address"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/customers/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/customers/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 고객이 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addcustomers">+ 고객 등록</a> | <a href="/products">상품 목록</a></body></html>'''

@app.route('/customers')
def list_customers():
    db = get_db()
    items = db.execute('SELECT * FROM customers ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(CUSTOMERS_LIST, items=items)

ADD_CUSTOMER = '''<!doctype html><html lang="ko"><body>
<h2>고객 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required><br><br>
  이메일: <input name="email" type="email"><br><br>
  전화번호: <input name="phone"><br><br>
  주소: <input name="address"><br><br>
  <button>등록</button>
</form><a href="/customers">목록으로</a></body></html>'''

@app.route('/addcustomers', methods=['GET','POST'])
def add_customers():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(ADD_CUSTOMER, error='이름을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO customers (name,email,phone,address) VALUES (?,?,?,?)',
            (name, request.form.get('email') or None,
             request.form.get('phone') or None,
             request.form.get('address') or None))
        db.commit(); db.close()
        return redirect(url_for('list_customers'))
    return render_template_string(ADD_CUSTOMER, error=None)

EDIT_CUSTOMER = '''<!doctype html><html lang="ko"><body>
<h2>고객 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  이름: <input name="name" required value="{{ item['name'] }}"><br><br>
  이메일: <input name="email" value="{{ item['email'] or '' }}"><br><br>
  전화번호: <input name="phone" value="{{ item['phone'] or '' }}"><br><br>
  주소: <input name="address" value="{{ item['address'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/customers">취소</a></body></html>'''

@app.route('/customers/<int:cid>/edit', methods=['GET','POST'])
def edit_customers(cid):
    db = get_db()
    item = db.execute('SELECT * FROM customers WHERE id=?',(cid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(EDIT_CUSTOMER, item=item, error='이름을 입력해주세요')
        db = get_db()
        db.execute('UPDATE customers SET name=?,email=?,phone=?,address=? WHERE id=?',
            (name, request.form.get('email') or None,
             request.form.get('phone') or None,
             request.form.get('address') or None, cid))
        db.commit(); db.close()
        return redirect(url_for('list_customers'))
    return render_template_string(EDIT_CUSTOMER, item=item, error=None)

@app.route('/customers/<int:cid>/delete', methods=['POST'])
def delete_customers(cid):
    db = get_db()
    db.execute('DELETE FROM customers WHERE id=?',(cid,))
    db.commit(); db.close()
    return redirect(url_for('list_customers'))

PRODUCTS_LIST = '''<!doctype html><html lang="ko"><body>
<h2>상품 목록 (총 {{ items|length }}개)</h2>
<table border="1" cellpadding="6">
  <tr><th>ID</th><th>상품명</th><th>가격</th><th>재고</th><th>카테고리</th><th>등록일</th><th>관리</th></tr>
  {% for item in items %}<tr>
    <td>{{ item["id"] }}</td><td>{{ item["name"] }}</td>
    <td>{{ item["price"] or 0 }}원</td><td>{{ item["stock"] or 0 }}</td>
    <td>{{ item["category"] or "-" }}</td><td>{{ (item["created"] or "")[:10] }}</td>
    <td><a href="/products/{{ item["id"] }}/edit">수정</a> |
      <form method="POST" action="/products/{{ item["id"] }}/delete" style="display:inline"
            onsubmit="return confirm('삭제?')"><button>삭제</button></form></td>
  </tr>{% else %}
  <tr><td colspan="7" align="center">등록된 상품이 없습니다</td></tr>{% endfor %}
</table><br>
<a href="/addproducts">+ 상품 등록</a> | <a href="/customers">고객 목록</a></body></html>'''

@app.route('/products')
def list_products():
    db = get_db()
    items = db.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    db.close()
    return render_template_string(PRODUCTS_LIST, items=items)

ADD_PRODUCT = '''<!doctype html><html lang="ko"><body>
<h2>상품 등록</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  상품명: <input name="name" required><br><br>
  가격: <input name="price" type="number" step="0.01"><br><br>
  재고: <input name="stock" type="number"><br><br>
  카테고리: <input name="category"><br><br>
  <button>등록</button>
</form><a href="/products">목록으로</a></body></html>'''

@app.route('/addproducts', methods=['GET','POST'])
def add_products():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(ADD_PRODUCT, error='상품명을 입력해주세요')
        db = get_db()
        db.execute('INSERT INTO products (name,price,stock,category) VALUES (?,?,?,?)',
            (name, request.form.get('price') or 0,
             request.form.get('stock') or 0,
             request.form.get('category') or None))
        db.commit(); db.close()
        return redirect(url_for('list_products'))
    return render_template_string(ADD_PRODUCT, error=None)

EDIT_PRODUCT = '''<!doctype html><html lang="ko"><body>
<h2>상품 수정</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  상품명: <input name="name" required value="{{ item['name'] }}"><br><br>
  가격: <input name="price" type="number" step="0.01" value="{{ item['price'] or 0 }}"><br><br>
  재고: <input name="stock" type="number" value="{{ item['stock'] or 0 }}"><br><br>
  카테고리: <input name="category" value="{{ item['category'] or '' }}"><br><br>
  <button>수정 완료</button>
</form><a href="/products">취소</a></body></html>'''

@app.route('/products/<int:pid>/edit', methods=['GET','POST'])
def edit_products(pid):
    db = get_db()
    item = db.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
    db.close()
    if not item: return '없음', 404
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name: return render_template_string(EDIT_PRODUCT, item=item, error='상품명을 입력해주세요')
        db = get_db()
        db.execute('UPDATE products SET name=?,price=?,stock=?,category=? WHERE id=?',
            (name, request.form.get('price') or 0,
             request.form.get('stock') or 0,
             request.form.get('category') or None, pid))
        db.commit(); db.close()
        return redirect(url_for('list_products'))
    return render_template_string(EDIT_PRODUCT, item=item, error=None)

@app.route('/products/<int:pid>/delete', methods=['POST'])
def delete_products(pid):
    db = get_db()
    db.execute('DELETE FROM products WHERE id=?',(pid,))
    db.commit(); db.close()
    return redirect(url_for('list_products'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
