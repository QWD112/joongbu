from flask import Flask, request, redirect, render_template, session, jsonify
import sqlite3
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = 'indievault_secret_2024'

# ─── DB 연결 ───────────────────────────────────────────
def get_db():
    conn = sqlite3.connect('indievault.db')
    conn.execute("PRAGMA foreign_keys = ON")   # 외래키 활성화
    cursor = conn.cursor()
    return conn, cursor

# ─── DB 초기화 ─────────────────────────────────────────
def init_db():
    conn, cursor = get_db()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role     TEXT NOT NULL DEFAULT 'user',
        points   INTEGER NOT NULL DEFAULT 50000
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        title          TEXT NOT NULL,
        description    TEXT,
        genre          TEXT,
        goal_amount    INTEGER NOT NULL,
        current_amount INTEGER NOT NULL DEFAULT 0,
        creator        TEXT NOT NULL,
        deadline       TEXT NOT NULL,
        status         TEXT NOT NULL DEFAULT 'pending',
        created_date   TEXT NOT NULL,
        refunded       INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (creator) REFERENCES users(username)
    )''')
    # 기존 DB에 refunded 컬럼 없으면 추가 (IF NOT EXISTS 미지원 대응)
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN refunded INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass  # 이미 존재하면 무시

    cursor.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER NOT NULL,
        amount      INTEGER NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS fundings (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER NOT NULL,
        user_id     INTEGER NOT NULL,
        username    TEXT NOT NULL,
        amount      INTEGER NOT NULL,
        funded_date TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS updates (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id   INTEGER NOT NULL,
        author       TEXT NOT NULL,
        content      TEXT NOT NULL,
        type         TEXT NOT NULL,
        created_date TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )''')

    # 관리자 + 샘플 데이터 (최초 1회)
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username,password,role,points) VALUES (?,?,?,?)",
            [('admin','1234','admin',9999999),
             ('devkim','1234','user',50000),
             ('gamer01','1234','user',80000),
             ('luna99','1234','user',120000)]
        )
        today_str = date.today().strftime('%Y-%m-%d')
        d_close  = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')   # 이미 마감
        d_urgent = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')   # 2일 남음
        d_soon   = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        d_far    = (date.today() + timedelta(days=40)).strftime('%Y-%m-%d')

        sample_projects = [
            # title, desc, genre, goal, current, creator, deadline, status, created
            ('픽셀 던전 오디세이',
             '80년대 감성의 로그라이크 RPG. 절차적으로 생성되는 던전과 50가지 직업 클래스가 여러분을 기다립니다.',
             'RPG', 5000000, 5800000, 'devkim', d_soon, 'active',
             (date.today()-timedelta(days=20)).strftime('%Y-%m-%d')),

            ('네온 레이서 2077',
             '사이버펑크 세계관의 레이싱 게임. 도심 한복판을 질주하며 경쟁자들을 제치세요.',
             '레이싱', 8000000, 2100000, 'devkim', d_urgent, 'active',
             (date.today()-timedelta(days=15)).strftime('%Y-%m-%d')),

            ('숲의 수호자',
             '아름다운 손그림 스타일의 어드벤처 게임. 마법 숲을 지키는 정령이 되어보세요.',
             '어드벤처', 3000000, 3100000, 'devkim', d_close, 'active',
             (date.today()-timedelta(days=60)).strftime('%Y-%m-%d')),

            ('좀비 팜 타이쿤',
             '좀비들과 함께하는 농장 경영 시뮬레이션. 독특한 유머와 전략성을 함께!',
             '시뮬레이션', 2000000, 800000, 'luna99', d_far, 'pending', today_str),

            ('별빛 탐험대',
             '우주를 배경으로 한 협동 퍼즐 어드벤처. 2~4인 멀티플레이 지원.',
             '퍼즐', 4000000, 1200000, 'gamer01', d_soon, 'active',
             (date.today()-timedelta(days=5)).strftime('%Y-%m-%d')),

            ('드래곤 키친',
             '드래곤이 운영하는 레스토랑에서 벌어지는 쿠킹 시뮬레이션 게임!',
             '시뮬레이션', 1500000, 200000, 'luna99', d_far, 'active', today_str),
        ]
        for p in sample_projects:
            cursor.execute(
                "INSERT INTO projects (title,description,genre,goal_amount,current_amount,creator,deadline,status,created_date) VALUES (?,?,?,?,?,?,?,?,?)",
                p
            )

        # 리워드
        rewards_data = [
            (1,10000,'게임 얼리 액세스 키 1개'),
            (1,30000,'게임 키 + 디지털 아트북 + OST'),
            (1,100000,'위 모든 것 + 크레딧 등재 + 개발자 직통 Discord'),
            (2,15000,'게임 얼리 액세스 키'),
            (2,50000,'게임 키 + 익스클루시브 차량 스킨 팩'),
            (5,20000,'게임 키 + 개발자 응원 메시지'),
            (6,10000,'게임 사전 예약 키'),
        ]
        cursor.executemany("INSERT INTO rewards (project_id,amount,description) VALUES (?,?,?)", rewards_data)

        # 샘플 후원 & 댓글
        funding_data = [
            (1,2,'gamer01',30000,(date.today()-timedelta(days=3)).strftime('%Y-%m-%d')),
            (1,4,'luna99',10000,(date.today()-timedelta(days=2)).strftime('%Y-%m-%d')),
            (2,4,'luna99',15000,(date.today()-timedelta(days=1)).strftime('%Y-%m-%d')),
            (5,2,'gamer01',20000,today_str),
        ]
        cursor.executemany("INSERT INTO fundings (project_id,user_id,username,amount,funded_date) VALUES (?,?,?,?,?)", funding_data)

        updates_data = [
            (1,'devkim','던전 3층 맵 생성 알고리즘 완성! 이제 보스 AI를 작업 중입니다 🎮','update',(date.today()-timedelta(days=5)).strftime('%Y-%m-%d')),
            (1,'gamer01','정말 기대되는 프로젝트예요! 얼리 후원합니다 💪','comment',(date.today()-timedelta(days=3)).strftime('%Y-%m-%d')),
        ]
        cursor.executemany("INSERT INTO updates (project_id,author,content,type,created_date) VALUES (?,?,?,?,?)", updates_data)

    conn.commit()
    conn.close()

init_db()

# ─── 마감 자동 처리 헬퍼 ───────────────────────────────
def auto_close_projects(cursor, conn):
    """매 요청마다 마감일 지난 active 프로젝트를 closed로 변경"""
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute(
        "UPDATE projects SET status='closed' WHERE status='active' AND deadline < ?",
        (today,)
    )
    conn.commit()

# ─── 메인 (프로젝트 목록) ──────────────────────────────
@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login/')

    conn, cursor = get_db()
    auto_close_projects(cursor, conn)

    sort        = request.args.get('sort', 'rate')
    genre_filter = request.args.get('genre', '')

    cursor.execute("SELECT DISTINCT genre FROM projects WHERE status='active'")
    genres = [r[0] for r in cursor.fetchall()]

    # 모든 active 프로젝트를 가져와서 JS에서 필터/정렬
    cursor.execute("""
        SELECT p.*,
               COUNT(DISTINCT f.id)   AS funder_count,
               COALESCE(SUM(CASE WHEN f.funded_date >= date('now','-1 day') THEN f.amount ELSE 0 END),0) AS recent_amount
        FROM projects p
        LEFT JOIN fundings f ON f.project_id = p.id
        WHERE p.status = 'active'
        GROUP BY p.id
    """)
    rows = cursor.fetchall()
    conn.close()

    today_str = date.today().strftime('%Y-%m-%d')
    projects = []
    for r in rows:
        p = list(r)
        goal    = p[4] or 1
        current = p[5]
        rate    = round(current / goal * 100, 1)
        deadline_date = datetime.strptime(p[7], '%Y-%m-%d').date()
        days_left     = (deadline_date - date.today()).days

        projects.append({
            'id':            p[0],
            'title':         p[1],
            'description':   p[2],
            'genre':         p[3],
            'goal_amount':   goal,
            'current_amount': current,
            'creator':       p[6],
            'deadline':      p[7],
            'status':        p[8],
            'created_date':  p[9],
            'rate':          rate,
            'days_left':     days_left,
            'funder_count':  p[10],
            'recent_amount': p[11],
        })

    return render_template('index.html',
                           projects=projects,
                           sort=sort,
                           genre_filter=genre_filter,
                           genres=genres,
                           today=today_str)

# ─── API: 프로젝트 목록 (Fetch용) ─────────────────────
@app.route('/api/projects')
def api_projects():
    if 'username' not in session:
        return jsonify([])

    conn, cursor = get_db()
    auto_close_projects(cursor, conn)

    genre_filter = request.args.get('genre', '')
    show_closed  = request.args.get('show_closed', '0')

    status_cond = "p.status IN ('active','closed')" if show_closed == '1' else "p.status = 'active'"
    genre_cond  = "AND p.genre = ?" if genre_filter else ""
    params      = [genre_filter] if genre_filter else []

    cursor.execute(f"""
        SELECT p.*,
               COUNT(DISTINCT f.id) AS funder_count,
               COALESCE(SUM(CASE WHEN f.funded_date >= date('now','-1 day') THEN f.amount ELSE 0 END),0) AS recent_amount
        FROM projects p
        LEFT JOIN fundings f ON f.project_id = p.id
        WHERE {status_cond} {genre_cond}
        GROUP BY p.id
    """, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        goal    = r[4] or 1
        current = r[5]
        rate    = round(current / goal * 100, 1)
        deadline_date = datetime.strptime(r[7], '%Y-%m-%d').date()
        days_left     = (deadline_date - date.today()).days
        result.append({
            'id':             r[0],
            'title':          r[1],
            'description':    r[2],
            'genre':          r[3],
            'goal_amount':    goal,
            'current_amount': current,
            'creator':        r[6],
            'deadline':       r[7],
            'status':         r[8],
            'created_date':   r[9],
            'rate':           rate,
            'days_left':      days_left,
            'funder_count':   r[10],
            'recent_amount':  r[11],
        })
    return jsonify(result)

# ─── 회원가입 ──────────────────────────────────────────
@app.route('/register/', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error='모든 항목을 입력해주세요.')
        conn, cursor = get_db()
        cursor.execute('SELECT id FROM users WHERE username=?', (username,))
        if cursor.fetchone():
            conn.close()
            return render_template('register.html', error='이미 존재하는 아이디입니다.')
        cursor.execute('INSERT INTO users (username,password) VALUES (?,?)', (username, password))
        conn.commit()
        conn.close()
        session['username'] = username
        session['role']     = 'user'
        return redirect('/')
    return render_template('register.html', error='')

# ─── 로그인 ────────────────────────────────────────────
@app.route('/login/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn, cursor = get_db()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = user[1]
            session['role']     = user[3]
            session['user_id']  = user[0]
            return redirect('/admin/' if user[3] == 'admin' else '/')
        return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')
    return render_template('login.html', error='')

# ─── 로그아웃 ──────────────────────────────────────────
@app.route('/logout/')
def logout():
    session.clear()
    return redirect('/login/')

# ─── 프로젝트 등록 ─────────────────────────────────────
@app.route('/project/create/', methods=['GET','POST'])
def project_create():
    if 'username' not in session:
        return redirect('/login/')
    if request.method == 'POST':
        title       = request.form['title']
        description = request.form['description']
        genre       = request.form['genre']
        goal_amount = int(request.form['goal_amount'])
        deadline    = request.form['deadline']
        today       = date.today().strftime('%Y-%m-%d')
        conn, cursor = get_db()
        cursor.execute(
            'INSERT INTO projects (title,description,genre,goal_amount,creator,deadline,created_date) VALUES (?,?,?,?,?,?,?)',
            (title, description, genre, goal_amount, session['username'], deadline, today)
        )
        pid = cursor.lastrowid
        for i in range(1, 4):
            amt  = request.form.get(f'reward_amount_{i}','').strip()
            desc = request.form.get(f'reward_desc_{i}','').strip()
            if amt and desc:
                cursor.execute('INSERT INTO rewards (project_id,amount,description) VALUES (?,?,?)',
                               (pid, int(amt), desc))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('project_create.html')

# ─── 프로젝트 상세 ─────────────────────────────────────
@app.route('/project/<int:id>/')
def project_detail(id):
    if 'username' not in session:
        return redirect('/login/')
    conn, cursor = get_db()
    auto_close_projects(cursor, conn)

    cursor.execute('SELECT * FROM projects WHERE id=?', (id,))
    project = cursor.fetchone()
    if not project:
        conn.close(); return redirect('/')

    cursor.execute('SELECT * FROM rewards WHERE project_id=? ORDER BY amount', (id,))
    rewards = cursor.fetchall()

    cursor.execute('SELECT * FROM updates WHERE project_id=? ORDER BY created_date DESC', (id,))
    upd_list = cursor.fetchall()

    cursor.execute('SELECT COUNT(DISTINCT username) FROM fundings WHERE project_id=?', (id,))
    funder_count = cursor.fetchone()[0]

    cursor.execute('SELECT * FROM users WHERE username=?', (session['username'],))
    user = cursor.fetchone()
    conn.close()

    rate      = round(project[5] / project[4] * 100, 1) if project[4] else 0
    deadline_d = datetime.strptime(project[7], '%Y-%m-%d').date()
    days_left  = (deadline_d - date.today()).days

    return render_template('project_detail.html',
                           project=project, rewards=rewards,
                           updates=upd_list, rate=rate,
                           user=user, funder_count=funder_count,
                           days_left=days_left)

# ─── 후원하기 ──────────────────────────────────────────
@app.route('/project/<int:id>/fund/', methods=['POST'])
def fund_project(id):
    if 'username' not in session:
        return redirect('/login/')
    try:
        amount = int(request.form['amount'])
    except (ValueError, KeyError):
        return redirect(f'/project/{id}/?error=invalid')

    conn, cursor = get_db()
    cursor.execute('SELECT * FROM users WHERE username=?', (session['username'],))
    user = cursor.fetchone()

    if user[4] < amount:
        conn.close()
        return redirect(f'/project/{id}/?error=points')   # 포인트 부족 플래그

    today = date.today().strftime('%Y-%m-%d')
    cursor.execute('INSERT INTO fundings (project_id,user_id,username,amount,funded_date) VALUES (?,?,?,?,?)',
                   (id, user[0], user[1], amount, today))
    cursor.execute('UPDATE projects SET current_amount=current_amount+? WHERE id=?', (amount, id))
    cursor.execute('UPDATE users SET points=points-? WHERE username=?', (amount, session['username']))
    conn.commit()
    conn.close()
    return redirect(f'/project/{id}/?success=1')

# ─── 댓글 ──────────────────────────────────────────────
@app.route('/project/<int:id>/comment/', methods=['POST'])
def add_comment(id):
    if 'username' not in session:
        return redirect('/login/')
    content = request.form.get('content','').strip()
    if content:
        conn, cursor = get_db()
        cursor.execute('INSERT INTO updates (project_id,author,content,type,created_date) VALUES (?,?,?,?,?)',
                       (id, session['username'], content, 'comment', date.today().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
    return redirect(f'/project/{id}/')

# ─── 개발 소식 ─────────────────────────────────────────
@app.route('/project/<int:id>/update/', methods=['GET','POST'])
def post_update(id):
    if 'username' not in session:
        return redirect('/login/')
    conn, cursor = get_db()
    cursor.execute('SELECT * FROM projects WHERE id=?', (id,))
    project = cursor.fetchone()
    if not project or project[6] != session['username']:
        conn.close(); return redirect('/')
    if request.method == 'POST':
        content = request.form.get('content','').strip()
        if content:
            cursor.execute('INSERT INTO updates (project_id,author,content,type,created_date) VALUES (?,?,?,?,?)',
                           (id, session['username'], content, 'update', date.today().strftime('%Y-%m-%d')))
            conn.commit()
        conn.close()
        return redirect(f'/project/{id}/')
    conn.close()
    return render_template('project_edit.html', project=project)

# ─── 관리자 대시보드 ────────────────────────────────────
@app.route('/admin/')
def admin():
    if session.get('role') != 'admin':
        return redirect('/login/')
    conn, cursor = get_db()
    auto_close_projects(cursor, conn)

    cursor.execute('SELECT COUNT(*) FROM users WHERE role!="admin"')
    user_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM fundings')
    funding_count = cursor.fetchone()[0]

    cursor.execute('SELECT COALESCE(SUM(amount),0) FROM fundings')
    total_funded = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM projects WHERE status="active"')
    active_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM projects WHERE status="pending"')
    pending_count = cursor.fetchone()[0]

    # 심사 대기
    cursor.execute("SELECT * FROM projects WHERE status='pending' ORDER BY created_date DESC")
    pending_projects = cursor.fetchall()

    # 전체 프로젝트 (active + closed + rejected)
    cursor.execute("SELECT * FROM projects WHERE status!='pending' ORDER BY created_date DESC")
    all_projects = cursor.fetchall()

    # 전체 회원
    cursor.execute("SELECT * FROM users ORDER BY id")
    users = cursor.fetchall()

    # 후원 내역
    cursor.execute("""
        SELECT f.*, p.title FROM fundings f
        JOIN projects p ON p.id = f.project_id
        ORDER BY f.funded_date DESC LIMIT 50
    """)
    fundings = cursor.fetchall()

    conn.close()
    return render_template('admin.html',
        user_count=user_count, funding_count=funding_count,
        total_funded=total_funded, active_count=active_count,
        pending_count=pending_count,
        pending_projects=pending_projects,
        all_projects=all_projects,
        users=users, fundings=fundings)

# ─── 관리자 API: 상세 목록 (탭 클릭용) ───────────────
@app.route('/admin/api/detail')
def admin_api_detail():
    if session.get('role') != 'admin':
        return jsonify({'error': 'unauthorized'}), 403
    kind = request.args.get('kind','')
    conn, cursor = get_db()
    if kind == 'users':
        cursor.execute("SELECT id,username,role,points FROM users WHERE role!='admin' ORDER BY id")
        rows = [{'id':r[0],'username':r[1],'role':r[2],'points':r[3]} for r in cursor.fetchall()]
    elif kind == 'projects':
        cursor.execute("SELECT id,title,genre,goal_amount,current_amount,creator,deadline,status FROM projects WHERE status='active' ORDER BY id DESC")
        rows = [{'id':r[0],'title':r[1],'genre':r[2],'goal':r[3],'current':r[4],'creator':r[5],'deadline':r[6],'status':r[7]} for r in cursor.fetchall()]
    elif kind == 'fundings':
        cursor.execute("""SELECT f.id,f.username,f.amount,f.funded_date,p.title
                          FROM fundings f JOIN projects p ON p.id=f.project_id
                          ORDER BY f.funded_date DESC LIMIT 50""")
        rows = [{'id':r[0],'username':r[1],'amount':r[2],'date':r[3],'project':r[4]} for r in cursor.fetchall()]
    else:
        rows = []
    conn.close()
    return jsonify(rows)

# ─── 승인 / 거절 / 삭제 ────────────────────────────────
@app.route('/admin/approve/<int:id>/')
def admin_approve(id):
    if session.get('role') != 'admin': return redirect('/')
    conn, cursor = get_db()
    cursor.execute("UPDATE projects SET status='active' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin/')

@app.route('/admin/reject/<int:id>/')
def admin_reject(id):
    if session.get('role') != 'admin': return redirect('/')
    conn, cursor = get_db()
    cursor.execute("UPDATE projects SET status='rejected' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin/')

@app.route('/admin/delete/project/<int:id>/')
def admin_delete_project(id):
    if session.get('role') != 'admin': return redirect('/')
    conn, cursor = get_db()
    # ON DELETE CASCADE로 rewards/fundings/updates 자동 삭제
    cursor.execute("DELETE FROM projects WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin/')

@app.route('/admin/delete/user/<int:id>/')
def admin_delete_user(id):
    if session.get('role') != 'admin': return redirect('/')
    conn, cursor = get_db()
    cursor.execute("DELETE FROM users WHERE id=? AND role!='admin'", (id,))
    conn.commit(); conn.close()
    return redirect('/admin/')

# ─── 정산 페이지 ───────────────────────────────────────
@app.route('/admin/settle/')
def admin_settle():
    if session.get('role') != 'admin': return redirect('/')
    conn, cursor = get_db()
    auto_close_projects(cursor, conn)

    cursor.execute("SELECT * FROM projects WHERE status='closed'")
    closed = cursor.fetchall()

    # 환불 완료 프로젝트 id 목록 (refunded=1, index 10)
    refunded_ids = {p[0] for p in closed if p[10] == 1}

    # 실패 프로젝트별 후원자 수 / 환불 예정 총액
    failed_detail = []
    for p in closed:
        if p[5] < p[4]:   # 목표 미달 = 실패
            cursor.execute(
                "SELECT COUNT(DISTINCT user_id), COALESCE(SUM(amount),0) FROM fundings WHERE project_id=?",
                (p[0],)
            )
            row = cursor.fetchone()
            failed_detail.append({
                'project':    p,
                'funder_cnt': row[0],
                'refund_sum': row[1],
                'refunded':   p[10] == 1,
            })

    success = [p for p in closed if p[5] >= p[4]]
    conn.close()

    flash_msg = request.args.get('msg', '')
    return render_template('admin_settle.html',
                           success=success,
                           failed_detail=failed_detail,
                           flash_msg=flash_msg)

# ─── 일괄 환불 실행 ────────────────────────────────────
@app.route('/admin/refund/<int:project_id>/', methods=['POST'])
def admin_refund(project_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn, cursor = get_db()
    try:
        # ① 대상 프로젝트 확인
        cursor.execute("SELECT * FROM projects WHERE id=? AND status='closed'", (project_id,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            return redirect('/admin/settle/?msg=err_notfound')

        # ② 이미 환불 처리된 경우 중복 방지
        if project[10] == 1:
            conn.close()
            return redirect('/admin/settle/?msg=err_already')

        # ③ 해당 프로젝트의 모든 후원 내역 조회
        cursor.execute(
            "SELECT user_id, SUM(amount) FROM fundings WHERE project_id=? GROUP BY user_id",
            (project_id,)
        )
        fundings = cursor.fetchall()   # [(user_id, total_amount), ...]

        if not fundings:
            # 후원자가 없으면 refunded만 표시
            cursor.execute("UPDATE projects SET refunded=1 WHERE id=?", (project_id,))
            conn.commit()
            conn.close()
            return redirect('/admin/settle/?msg=ok_nofunders')

        # ④ 트랜잭션: 후원자 전원 포인트 일괄 환불
        #    SQLite는 Python sqlite3 모듈에서 conn.isolation_level로 트랜잭션 관리
        #    여기서는 명시적으로 BEGIN / COMMIT / ROLLBACK 사용
        cursor.execute("BEGIN")
        for user_id, total_amount in fundings:
            cursor.execute(
                "UPDATE users SET points = points + ? WHERE id = ?",
                (total_amount, user_id)
            )
        # ⑤ 프로젝트를 '환불 완료' 상태로 표시
        cursor.execute("UPDATE projects SET refunded=1 WHERE id=?", (project_id,))
        conn.commit()
        conn.close()
        return redirect(f'/admin/settle/?msg=ok&cnt={len(fundings)}')

    except Exception as e:
        # 오류 발생 시 전체 롤백 → 데이터 일관성 보장
        conn.rollback()
        conn.close()
        return redirect('/admin/settle/?msg=err_rollback')

# ─── 테스트용: 특정 프로젝트 마감일을 어제로 변경 ──────
@app.route('/admin/test/expire/<int:id>/')
def admin_test_expire(id):
    """발표 시연용: 마감일을 어제로 변경 + 즉시 status도 closed로 변경"""
    if session.get('role') != 'admin': return redirect('/')
    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    conn, cursor = get_db()
    # ① 마감일을 어제로 조작
    cursor.execute("UPDATE projects SET deadline=? WHERE id=?", (yesterday, id))
    # ② 마감일이 지난 active 프로젝트를 즉시 closed로 전환 (auto_close와 동일한 SQL)
    cursor.execute(
        "UPDATE projects SET status='closed' WHERE status='active' AND deadline < ?",
        (date.today().strftime('%Y-%m-%d'),)
    )
    conn.commit(); conn.close()
    return redirect('/admin/settle/')

app.run(debug=True)
