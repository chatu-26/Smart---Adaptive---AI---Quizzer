from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# WARNING: Change this key in a production environment
app.secret_key = "change_this_secret_key"
DB_FILE = "users.db"

# ------------------ Database helpers ------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )""")
    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

def create_user(username, hashed_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username,password) VALUES (?,?)", (username, hashed_password))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def get_user_password(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def user_exists(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username=?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def update_password(username, hashed_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?", (hashed_password, username))
    conn.commit()
    conn.close()

# ------------------ Questions data ------------------
questions_data = {
    "C Programming": {
        "Easy":[
            {"question":"sizeof(char) is?","options":["1","2","4","8"],"answer":"1"},
            {"question":"Header for printf?","options":["stdio.h","stdlib.h","string.h","conio.h"],"answer":"stdio.h"},
            {"question":"Which keyword for loop?","options":["for","each","loop","iterate"],"answer":"for"},
            {"question":"malloc() does?","options":["Allocates memory","Opens file","Sorts array","Compiles code"],"answer":"Allocates memory"},
            {"question":"Pointer declared using?","options":["*","&","#","@"],"answer":"*"}
        ],
        "Medium":[
            {"question":"Which is not a storage class?","options":["auto","register","static","dynamic"],"answer":"dynamic"},
            {"question":"sizeof('A') returns?","options":["1","2","4","Depends"],"answer":"1"},
            {"question":"Operator for dereference?","options":["*","&","->","."],"answer":"*"},
            {"question":"C developed at?","options":["Bell Labs","IBM","Microsoft","Google"],"answer":"Bell Labs"},
            {"question":"Who developed C?","options":["Dennis Ritchie","Bjarne Stroustrup","James Gosling","Guido"],"answer":"Dennis Ritchie"}
        ],
        "Hard":[
            {"question":"malloc() failure returns?","options":["0","NULL","-1","Garbage"],"answer":"NULL"},
            {"question":"Header that defines NULL?","options":["stdio.h","stddef.h","stdlib.h","string.h"],"answer":"stddef.h"},
            {"question":"Function pointer syntax?","options":["int *f()","int (*f)()","int f(*)()","int *(*f)"],"answer":"int (*f)()"},
            {"question":"What is dangling pointer?","options":["Not initialized","Freed but not NULLed","Pointer to NULL","None"],"answer":"Freed but not NULLed"},
            {"question":"Which frees memory?","options":["malloc","calloc","free","alloc"],"answer":"free"}
        ]
    },
    "Python": {
        "Easy":[
            {"question":"Keyword to define function?","options":["def","function","fun","define"],"answer":"def"},
            {"question":"Which type is immutable?","options":["list","set","tuple","dict"],"answer":"tuple"},
            {"question":"Comment symbol?","options":["//","#","/*","--"],"answer":"#"},
            {"question":"Print to output?","options":["printf","cout","print","echo"],"answer":"print"},
            {"question":"Python files extension?","options":[".pt",".py",".pyt",".python"],"answer":".py"}
        ],
        "Medium":[
            {"question":"What does len('abc') return?","options":["2","3","4","Error"],"answer":"3"},
            {"question":"Which creates a set?","options":["{}","[]","set()","()"],"answer":"set()"},
            {"question":"Which is immutable?","options":["tuple","list","set","dict"],"answer":"tuple"},
            {"question":"Keyword for exceptions?","options":["try","catch","throw","except"],"answer":"try"},
            {"question":"Which converts to int?","options":["int()","str()","float()","eval()"],"answer":"int()"}
        ],
        "Hard":[
            {"question":"What is a decorator?","options":["Design pattern","Function that modifies another","Class","None"],"answer":"Function that modifies another"},
            {"question":"What is GIL?","options":["Global Interpreter Lock","Global Instance Library","General I/O Layer","None"],"answer":"Global Interpreter Lock"},
            {"question":"Module for JSON?","options":["os","json","pickle","io"],"answer":"json"},
            {"question":"Generator keyword?","options":["yield","return","gen","next"],"answer":"yield"},
            {"question":"What does @ denote?","options":["Decorator","Comment","Multiply","None"],"answer":"Decorator"}
        ]
    },
    "Data Structures": {
        "Easy":[
            {"question":"Which uses LIFO?","options":["Queue","Stack","Array","List"],"answer":"Stack"},
            {"question":"Which uses FIFO?","options":["Queue","Stack","Tree","Graph"],"answer":"Queue"},
            {"question":"Non-linear DS?","options":["Array","Linked List","Tree","Stack"],"answer":"Tree"},
            {"question":"Top operation of stack?","options":["push","pop","enqueue","dequeue"],"answer":"push"},
            {"question":"Array index starts at?","options":["0","1","2","Depends"],"answer":"0"}
        ],
        "Medium":[
            {"question":"Inorder traversal yields?","options":["Sorted for BST","Random","Reverse order","None"],"answer":"Sorted for BST"},
            {"question":"Queue implemented using?","options":["Array","Linked List","Both","None"],"answer":"Both"},
            {"question":"Time to insert at head of linked list?","options":["O(1)","O(n)","O(log n)","O(n^2)"],"answer":"O(1)"},
            {"question":"Height of single node tree?","options":["0","1","2","Depends"],"answer":"0"},
            {"question":"Which is linear?","options":["Tree","Graph","Array","None"],"answer":"Array"}
        ],
        "Hard":[
            {"question":"Best case QuickSort?","options":["O(n^2)","O(n log n)","O(n)","O(log n)"],"answer":"O(n log n)"},
            {"question":"Data structure for recursion?","options":["Queue","Stack","Heap","Graph"],"answer":"Stack"},
            {"question":"B-Tree commonly used in?","options":["Databases","OS","Compilers","Networking"],"answer":"Databases"},
            {"question":"AVL tree balance factor options?","options":["0,1,-1","2,-2","Any","Only 0"],"answer":"0,1,-1"},
            {"question":"Heap sort worst-case?","options":["O(n^2)","O(n log n)","O(n)","O(log n)"],"answer":"O(n log n)"}
        ]
    },
    "Databases": {
        "Easy":[
            {"question":"SQL stands for?","options":["Structured Query Language","Sequential Query Language","Simple Query Language","None"],"answer":"Structured Query Language"},
            {"question":"Command to retrieve data?","options":["SELECT","GET","FETCH","SHOW"],"answer":"SELECT"},
            {"question":"Filter rows using?","options":["WHERE","FROM","GROUP","HAVING"],"answer":"WHERE"},
            {"question":"Remove duplicates with?","options":["UNIQUE","DISTINCT","REMOVE","FILTER"],"answer":"DISTINCT"},
            {"question":"Count rows uses?","options":["SUM()","COUNT()","AVG()","MIN()"],"answer":"COUNT()"}
        ],
        "Medium":[
            {"question":"Update data uses?","options":["UPDATE","MODIFY","CHANGE","ALTER"],"answer":"UPDATE"},
            {"question":"Pattern match operator?","options":["LIKE","MATCH","IN","BETWEEN"],"answer":"LIKE"},
            {"question":"Group rows using?","options":["GROUP BY","ORDER BY","JOIN","UNION"],"answer":"GROUP BY"},
            {"question":"Primary key is?","options":["Unique identifier","Foreign key","Duplicate","None"],"answer":"Unique identifier"},
            {"question":"ACID stands for?","options":["Atomicity Consistency Isolation Durability","Add Commit Integrity Data","None","All"],"answer":"Atomicity Consistency Isolation Durability"}
        ],
        "Hard":[
            {"question":"Removes transitive dependency (normal form)?","options":["1NF","2NF","3NF","BCNF"],"answer":"3NF"},
            {"question":"Returns only matches?","options":["INNER JOIN","LEFT JOIN","RIGHT JOIN","FULL JOIN"],"answer":"INNER JOIN"},
            {"question":"Combine results of two queries?","options":["UNION","JOIN","INTERSECT","MERGE"],"answer":"UNION"},
            {"question":"TRUNCATE does?","options":["Remove all rows quickly","Delete table structure","Update rows","None"],"answer":"Remove all rows quickly"},
            {"question":"Index improves?","options":["Search speed","Integrity","Storage","Redundancy"],"answer":"Search speed"}
        ]
    },
    "Computer Networks": {
        "Easy":[
            {"question":"LAN stands for?","options":["Local Area Network","Large Area Network","Linked Access Network","Long Area Node"],"answer":"Local Area Network"},
            {"question":"Device connecting two networks?","options":["Switch","Router","Hub","Bridge"],"answer":"Router"},
            {"question":"IP works on which layer?","options":["Network","Transport","Application","Data Link"],"answer":"Network"},
            {"question":"TCP stands for?","options":["Transmission Control Protocol","Transport Control Protocol","Transfer Control Protocol","None"],"answer":"Transmission Control Protocol"},
            {"question":"Device at data link layer?","options":["Switch","Router","Hub","Repeater"],"answer":"Switch"}
        ],
        "Medium":[
            {"question":"HTTP default port?","options":["21","25","80","110"],"answer":"80"},
            {"question":"Protocol for email sending?","options":["SMTP","FTP","HTTP","DNS"],"answer":"SMTP"},
            {"question":"Connectionless protocol?","options":["TCP","UDP","FTP","SMTP"],"answer":"UDP"},
            {"question":"127.0.0.1 is?","options":["Localhost","Gateway","Broadcast","None"],"answer":"Localhost"},
            {"question":"DNS maps?","options":["Domain to IP","IP to Domain","MAC to IP","None"],"answer":"Domain to IP"}
        ],
        "Hard":[
            {"question":"Routing protocol using distance vector?","options":["RIP","OSPF","BGP","EIGRP"],"answer":"RIP"},
            {"question":"IPv6 address size?","options":["32 bits","64 bits","128 bits","256 bits"],"answer":"128 bits"},
            {"question":"Layer for encryption?","options":["Presentation","Application","Transport","Network"],"answer":"Presentation"},
            {"question":"DNS typically uses?","options":["UDP","TCP","Both","None"],"answer":"Both"},
            {"question":"Topology with central node?","options":["Star","Ring","Bus","Mesh"],"answer":"Star"}
        ]
    }
}

# ------------------ Templates (render_template_string) ------------------

home_page = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Smart Adaptive AI Quizzer</title>
    <style>
        *{box-sizing:border-box}
        body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;min-height:100vh;align-items:center;justify-content:center;}
        .card{background:rgba(255,255,255,0.04);padding:48px;border-radius:16px; text-align:center; width:720px; box-shadow:0 8px 30px rgba(0,0,0,0.6);}
        h1{color:#fbbf24;margin-bottom:18px;font-size:32px}
        p{color:#cbd5e1;margin-bottom:28px}
        .btn{display:inline-block;padding:14px 32px;border-radius:999px;background:#fbbf24;color:#071019;font-weight:700;text-decoration:none;box-shadow:0 6px 18px rgba(0,0,0,0.35)}
        .btn:hover{background:#f59e0b}
    </style>
</head>
<body>
    <div class="card">
        <h1>Smart Adaptive AI Quizzer</h1>
        <p>Interactive quizzes for CSE topics — login/register to get started.</p>
        <a class="btn" href="{{ url_for('auth') }}">Get Started</a>
    </div>
</body>
</html>
"""

auth_page = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Auth</title>
    <style>
        body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;}
        .topbar{display:flex;justify-content:flex-end;padding:18px 36px;gap:12px;}
        .topbar a{color:#fff;text-decoration:none;padding:10px 18px;border-radius:10px;background:rgba(255,255,255,0.03)}
        .center{display:flex;min-height:calc(100vh - 72px);align-items:center;justify-content:center;}
        .panel{background:rgba(255,255,255,0.03);padding:36px;border-radius:14px;width:760px;text-align:center}
        h2{color:#fbbf24}
        .btn{display:inline-block;padding:12px 26px;border-radius:999px;background:#2575fc;color:#fff;text-decoration:none;margin:10px}
        .btn:hover{background:#1b56d6}
    </style>
</head>
<body>
    <div class="topbar">
        <a href="{{ url_for('login') }}">Login</a>
        <a href="{{ url_for('register') }}">Register</a>
    </div>
    <div class="center">
        <div class="panel">
            <h2>Welcome!</h2>
            <p>Choose Login if you already have an account, otherwise Register.</p>
            <a class="btn" href="{{ url_for('login') }}">Login</a>
            <a class="btn" href="{{ url_for('register') }}">Register</a>
        </div>
    </div>
</body>
</html>
"""

register_page = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Register</title>
    <style>
        body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;align-items:center;justify-content:center;height:100vh}
        .box{background:rgba(255,255,255,0.04);padding:28px;border-radius:12px;width:380px;box-shadow:0 8px 24px rgba(0,0,0,0.6)}
        input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:#fff}
        button{width:100%;padding:12px;border-radius:10px;border:none;background:#fbbf24;color:#071019;font-weight:700;cursor:pointer}
        .msg{margin-bottom:10px;padding:10px;border-radius:8px}
        .success{background:rgba(34,197,94,0.12);color:#86efac}
        .danger{background:rgba(239,68,68,0.08);color:#fca5a5}
        a{color:#9bd1ff;text-decoration:none;display:block;text-align:center;margin-top:12px}
    </style>
</head>
<body>
    <div class="box">
        <h3 style="color:#fbbf24;text-align:center">Register</h3>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="msg {{ 'success' if category=='success' else 'danger' }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
        <a href="{{ url_for('login') }}">Already have an account? Login</a>
    </div>
</body>
</html>
"""

login_page = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Login</title>
    <style>
        body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;align-items:center;justify-content:center;height:100vh}
        .box{background:rgba(255,255,255,0.04);padding:28px;border-radius:12px;width:380px;box-shadow:0 8px 24px rgba(0,0,0,0.6)}
        input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:#fff}
        button{width:100%;padding:12px;border-radius:10px;border:none;background:#2575fc;color:#fff;font-weight:700;cursor:pointer}
        .msg{margin-bottom:10px;padding:10px;border-radius:8px}
        .danger{background:rgba(239,68,68,0.08);color:#fca5a5}
        a{color:#9bd1ff;text-decoration:none;display:block;text-align:center;margin-top:12px}
    </style>
</head>
<body>
    <div class="box">
        <h3 style="color:#fbbf24;text-align:center">Login</h3>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="msg {{ 'danger' if category=='danger' else 'success' }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <a href="{{ url_for('forgot') }}">Forgot Password?</a>
        <a href="{{ url_for('register') }}">Create an account</a>
    </div>
</body>
</html>
"""

forgot_page = """
<!doctype html>
<html><head><meta charset="utf-8"><title>Forgot Password</title>
<style>
body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;align-items:center;justify-content:center;height:100vh}
.box{background:rgba(255,255,255,0.04);padding:28px;border-radius:12px;width:380px}
input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:#fff}
button{width:100%;padding:12px;border-radius:10px;border:none;background:#fbbf24;color:#071019;font-weight:700;cursor:pointer}
a{color:#9bd1ff;display:block;text-align:center;margin-top:12px}
</style></head>
<body>
    <div class="box">
        <h3 style="color:#fbbf24;text-align:center">Forgot Password</h3>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div style="background:rgba(34,197,94,0.08);color:#86efac;padding:10px;border-radius:6px;margin-bottom:8px">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input name="username" placeholder="Enter your username" required>
            <button type="submit">Submit</button>
        </form>
        <a href="{{ url_for('login') }}">Back to Login</a>
    </div>
</body></html>
"""

reset_page = """
<!doctype html>
<html><head><meta charset="utf-8"><title>Reset Password</title>
<style>
body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;align-items:center;justify-content:center;height:100vh}
.box{background:rgba(255,255,255,0.04);padding:28px;border-radius:12px;width:380px}
input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:#fff}
button{width:100%;padding:12px;border-radius:10px;border:none;background:#fbbf24;color:#071019;font-weight:700;cursor:pointer}
</style></head>
<body>
    <div class="box">
        <h3 style="color:#fbbf24;text-align:center">Reset Password for <span style="color:#fff">{{ username }}</span></h3>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div style="background:rgba(34,197,94,0.08);color:#86efac;padding:10px;border-radius:6px;margin-bottom:8px">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="password" name="password" placeholder="Enter new password" required>
            <button type="submit">Reset Password</button>
        </form>
    </div>
</body></html>
"""

dashboard_page = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Dashboard</title>
<style>
body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px 28px}
.btn{padding:10px 14px;border-radius:8px;background:#fbbf24;color:#071019;text-decoration:none;font-weight:700}
.container{padding:40px;display:flex;gap:18px;flex-wrap:wrap;justify-content:center}
.card{background:rgba(255,255,255,0.04);padding:20px;border-radius:12px;width:220px;text-align:center}
.card a{color:#fff;text-decoration:none;font-weight:600}
</style>
</head>
<body>
    <div class="header">
        <div style="padding-left:18px"><strong>Smart Adaptive AI Quizzer</strong></div>
        <div>
            <span style="margin-right:12px">Hello, <strong>{{ username }}</strong></span>
            <a class="btn" href="{{ url_for('logout') }}">Logout</a>
        </div>
    </div>

    <div class="container">
        {% for t in topics %}
            <div class="card">
                <a href="{{ url_for('topic', topic=t) }}">{{ t }}</a>
            </div>
        {% endfor %}
    </div>
</body></html>
"""

difficulty_page = """
<!doctype html>
<html><head><meta charset="utf-8"><title>Select Difficulty</title>
<style>
body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;flex-direction:column;align-items:center}
.header{width:100%;padding:16px 28px;display:flex;justify-content:space-between}
.container{margin-top:60px;text-align:center}
.btn{padding:14px 28px;border-radius:999px;background:#2575fc;color:#fff;margin:10px;text-decoration:none}
.btn:hover{background:#1b56d6}
</style></head>
<body>
    <div class="header"><div></div><div><a class="btn" href="{{ url_for('dashboard') }}">Back</a></div></div>
    <div class="container">
        <h2 style="color:#fbbf24">{{ topic }}</h2>
        <p>Select difficulty:</p>
        <a class="btn" href="{{ url_for('quiz', topic=topic, difficulty='Easy') }}">Easy</a>
        <a class="btn" href="{{ url_for('quiz', topic=topic, difficulty='Medium') }}">Medium</a>
        <a class="btn" href="{{ url_for('quiz', topic=topic, difficulty='Hard') }}">Hard</a>
    </div>
</body></html>
"""

# Quiz Page (Unchanged from previous fix)
quiz_page = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{ topic }} - {{ difficulty }} Quiz</title>
<style>
body{
    margin:0;
    font-family:Segoe UI,Arial;
    background:linear-gradient(180deg,#0b1220,#1b2430);
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    min-height:100vh;
}
.container{
    width:760px;
    background:rgba(255,255,255,0.03);
    padding:28px;
    border-radius:14px;
}
h2{
    color:#fbbf24;
    text-align:center;
}
.question{
    background:rgba(255,255,255,0.02);
    padding:14px;
    border-radius:10px;
    margin:12px 0;
}
label{
    display:block;
    padding:10px;
    border-radius:8px;
    margin:6px 0;
    cursor:pointer;
    transition:all 0.2s ease;
    border:1px solid transparent;
}
label:hover{
    background:rgba(255,255,255,0.06);
}
input[type="radio"]{
    appearance:none;
    width:18px;
    height:18px;
    border:2px solid #fbbf24;
    border-radius:50%;
    margin-right:10px;
    vertical-align:middle;
    position:relative;
    top:-1px;
    cursor:pointer;
}
input[type="radio"]:checked{
    background-color:#fbbf24;
    box-shadow:0 0 0 3px rgba(251,191,36,0.3);
}
.submit{
    width:100%;
    padding:12px;
    border-radius:10px;
    border:none;
    background:#fbbf24;
    color:#071019;
    font-weight:700;
    cursor:pointer;
    margin-top:10px;
}
</style>

</head>
<body>
    <div class="container">
        <h2>{{ topic }} — {{ difficulty }} Level</h2>
        <form method="POST">
            {% for q in questions %}
                {% set question_index = loop.index %}
                <div class="question">
                    <div style="font-weight:700;margin-bottom:8px">Q{{ question_index }}. {{ q['question'] }}</div>
                    {% for opt in q['options'] %}
                        <label>
                            <input type="radio" name="q{{ question_index }}" value="{{ opt }}" required> {{ opt }}
                        </label>
                    {% endfor %}
                </div>
            {% endfor %}
            <button type="submit" class="submit">Submit</button>
        </form>
    </div>
</body>
</html>
"""

# Result Page (Updated to show certificate link)
result_page = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Result</title>
<style>
body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(180deg,#0b1220,#1b2430);color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:rgba(255,255,255,0.03);padding:30px;border-radius:12px;text-align:center}
.btn{padding:10px 16px;border-radius:8px;background:#2575fc;color:#fff;text-decoration:none;margin:8px;display:inline-block}
.score{font-size:48px;color:#fbbf24;margin:12px 0}
.cert-btn{background:#22c55e;}
</style>
</head>
<body>
    <div class="card">
        <h2>Quiz Completed</h2>
        <div class="score">{{ score }} / {{ total }}</div>
        
        <a class="btn cert-btn" href="{{ url_for('certificate') }}">Generate Certificate</a>
        
        <a class="btn" href="{{ url_for('dashboard') }}">Back to Dashboard</a>
        <a class="btn" href="{{ url_for('logout') }}">Logout</a>
    </div>
</body>
</html>
"""

# NEW CERTIFICATE PAGE
certificate_page = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Certificate of Achievement</title>
<style>
body{
    margin:0;
    font-family:Georgia, serif;
    background:#1b2430;
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    min-height:100vh;
}
.certificate-container{
    width:800px;
    height:600px;
    border: 20px solid #fbbf24;
    padding: 20px;
    text-align: center;
    background: #0b1220;
    box-shadow: 0 0 20px rgba(251, 191, 36, 0.5);
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}
.title{
    font-size: 40px;
    color: #fff;
    margin-bottom: 10px;
    border-bottom: 2px solid #fbbf24;
    padding-bottom: 10px;
    font-family: 'Times New Roman', serif;
}
.subtitle{
    font-size: 20px;
    color: #ccc;
    margin-bottom: 20px;
}
.recipient-name{
    font-size: 60px;
    font-family: 'Monotype Corsiva', cursive;
    color: #fbbf24;
    margin: 10px 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}
.achievement-text{
    font-size: 24px;
    margin: 20px 0;
    line-height: 1.5;
}
.score-detail{
    font-size: 30px;
    color: #86efac;
    font-weight: bold;
}
.signature-line{
    margin-top: 40px;
    display: flex;
    justify-content: space-around;
    font-size: 16px;
    color: #ccc;
}
.signature-line div{
    border-top: 1px dashed #fff;
    padding-top: 5px;
}
</style>
</head>
<body>
    <div class="certificate-container">
        <div class="header">
            <div class="title">CERTIFICATE OF ACHIEVEMENT</div>
            <div class="subtitle">Awarded by Smart Adaptive AI Quizzer</div>
        </div>
        
        <div class="body-content">
            <div class="achievement-text">
                This certifies that
                <div class="recipient-name">{{ username | upper }}</div>
                has successfully completed the **{{ topic }}** quiz at the **{{ difficulty }}** level.
            </div>
            
            <div class="score-detail">
                Final Score: {{ score }} out of {{ total }}
            </div>
        </div>

        <div class="signature-line">
            <div>
                Date: {{ date }}
            </div>
            <div>
                Quiz Master Signature
            </div>
        </div>
    </div>
</body>
</html>
"""


# ------------------ Routes ------------------

@app.route('/')
def home():
    return render_template_string(home_page)

@app.route('/auth')
def auth():
    return render_template_string(auth_page)

# ... (Auth routes remain the same) ...

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        if not username or not password:
            flash("Please provide username and password.", "danger")
            return render_template_string(register_page)
        hashed = generate_password_hash(password)
        ok = create_user(username, hashed)
        if ok:
            flash("Registered successfully — please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already exists. Choose another.", "danger")
    return render_template_string(register_page)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        stored = get_user_password(username)
        if stored and check_password_hash(stored, password):
            session['username'] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template_string(login_page)

@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        if user_exists(username):
            session['reset_user'] = username
            flash("User found — please enter a new password.", "success")
            return redirect(url_for('reset'))
        else:
            flash("Username not found.", "danger")
    return render_template_string(forgot_page)

@app.route('/reset', methods=['GET','POST'])
def reset():
    username = session.get('reset_user')
    if not username:
        flash("No user selected for reset. Please use Forgot Password.", "danger")
        return redirect(url_for('forgot'))
    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password:
            flash("Enter a valid password.", "danger")
            return render_template_string(reset_page, username=username)
        hashed = generate_password_hash(new_password)
        update_password(username, hashed)
        session.pop('reset_user', None)
        flash("Password reset successful. Please login.", "success")
        return redirect(url_for('login'))
    return render_template_string(reset_page, username=username)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    topics = list(questions_data.keys())
    return render_template_string(dashboard_page, username=session['username'], topics=topics)

@app.route('/topic/<topic>')
def topic(topic):
    if 'username' not in session:
        return redirect(url_for('login'))
    if topic not in questions_data:
        flash("Invalid topic.", "danger")
        return redirect(url_for('dashboard'))
    return render_template_string(difficulty_page, topic=topic)

# Quiz view + submit (Updated to store quiz context)
@app.route('/quiz/<topic>/<difficulty>', methods=['GET','POST'])
def quiz(topic, difficulty):
    if 'username' not in session:
        return redirect(url_for('login'))
    if topic not in questions_data or difficulty not in questions_data[topic]:
        flash("Invalid topic or difficulty.", "danger")
        return redirect(url_for('dashboard'))
    
    questions = questions_data[topic][difficulty]
    total_questions = len(questions)
    
    if request.method == 'POST':
        score = 0
        for i in range(1, total_questions + 1):
            user_answer = request.form.get(f"q{i}")
            correct_answer = questions[i-1]['answer']
            if user_answer == correct_answer:
                score += 1
        
        # Store ALL necessary information for result and certificate in session
        session['last_score'] = score
        session['last_total'] = total_questions
        session['last_topic'] = topic
        session['last_difficulty'] = difficulty
        return redirect(url_for('result'))
        
    return render_template_string(quiz_page, topic=topic, difficulty=difficulty, questions=questions)

# Result route
@app.route('/result')
def result():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    score = session.get('last_score')
    total = session.get('last_total')
    
    if score is None or total is None:
        flash("No quiz result found. Please take a quiz first.", "danger")
        return redirect(url_for('dashboard'))

    return render_template_string(result_page, score=score, total=total)

# NEW CERTIFICATE ROUTE
@app.route('/certificate')
def certificate():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    score = session.get('last_score')
    total = session.get('last_total')
    topic = session.get('last_topic')
    difficulty = session.get('last_difficulty')
    username = session.get('username')

    # Basic data validation
    if None in [score, total, topic, difficulty]:
        flash("Quiz context missing. Please complete a quiz.", "danger")
        return redirect(url_for('dashboard'))
    
    import datetime
    current_date = datetime.date.today().strftime("%B %d, %Y")

    return render_template_string(
        certificate_page,
        username=username,
        topic=topic,
        difficulty=difficulty,
        score=score,
        total=total,
        date=current_date
    )

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for('home'))

# ------------------ Run ------------------
if __name__ == "__main__":
    app.run(debug=True)