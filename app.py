from flask import Flask, render_template, request, redirect, url_for
from flask import session, json, jsonify
import pymysql

MYSQL_HOST = 'localhost'
MYSQL_DB = 'website'
MYSQL_USER = 'root'
MYSQL_PASS = '資料庫密碼'

app = Flask(
    __name__,
    static_folder="static", #靜態檔案資料夾名稱
    static_url_path="/static" #靜態檔案對應網址路徑
    )

#session 必須要設置一組 secret_key 
app.secret_key = "ji324ARWR#3j"

#網頁訊息統整
pageTitle1 = "歡迎光臨，請註冊或登入系統"   
pageTitle2 = "歡迎光臨，這是會員頁"
pageTitle3 = "失敗頁面"

#新增的全域變數，遊走各個 function 要秀到前台的錯誤的訊息
message = None


#連線資料庫函式
def connect_mysql():  
    global connect, cursor #把資料庫抓到的東西設定全域變數，大家才能用

    #cursorclass = pymysql.cursors.DictCursor 代表抓出來 DB 資料是用字典方式提供，沒設定時為預設 tuple 方式
    connect = pymysql.connect(host = MYSQL_HOST, db = MYSQL_DB, user = MYSQL_USER, password = MYSQL_PASS,
            charset = 'utf8', use_unicode = True, cursorclass = pymysql.cursors.DictCursor)
    cursor = connect.cursor()


@app.route("/")
def index():
        return render_template("index.html", pageTitle = pageTitle1)

#處理註冊
@app.route("/singup", methods=["GET", "POST"])
def singup():
    if request.method == "POST":

        #先將表單資料存到變數
        name = request.form["name"]
        username = request.form["username"]
        pwd = request.form["password"]

        #連線資料庫
        connect_mysql()

        #下資料庫指令，找看看資料庫註冊的帳號中是否有存在目前這位正要註冊的使用者
        selectsql = "select * from user WHERE username = '%s'" %(username)
        cursor.execute(selectsql)  

        #將指令結果存到變數
        selectDBusername = cursor.fetchone()

        #如果帳號存在，秀錯誤已註冊；如果不存在，將新的註冊資料寫入資料庫，並導回首頁
        if selectDBusername:
            return redirect(url_for('error', message = "帳號已經被註冊"))
        else:
            insertsql = "INSERT INTO user (name, username, password) \
                        VALUES ('%s', '%s', '%s')" % (name, username, pwd) 
            cursor.execute(insertsql)
            connect.commit()
            return redirect(url_for('index'))



#處理登入
@app.route("/signin", methods=["GET", "POST"])
def singin():

    #收到登入 POST 資料時，先將 session 清空
    if request.method == "POST":
        session.pop("loginUsername", None)
        session.pop("loginname", None)
        session["loginState"] = False

    #將 POST 資料存入變數，GET 資料寫法 變數 = request.args.get('參數名稱')
    username = request.form["username"]
    pwd = request.form["password"]

    
    connect_mysql()
    selectsql = "select * from user WHERE username = '%s'" %(username)
    cursor.execute(selectsql)  

    selectDBusername = cursor.fetchone()
    if selectDBusername != None:
        if (selectDBusername['username'] == username) and selectDBusername['password'] == pwd:
            session["loginUsername"] = selectDBusername['username']
            session["loginname"] = selectDBusername['name'] 
            session["loginState"] = True 
            return redirect(url_for('member'))

        else:
            #print(session)
            return redirect(url_for('error', message = "帳號或密碼輸入錯誤"))
        
    else:
        #print("資料庫無該帳號")
        return redirect(url_for('error', message = "帳號或密碼輸入錯誤"))


#錯誤導向頁
@app.route("/error")
def error():
    message = request.args.get('message')
    return render_template("error.html", pageTitle = pageTitle3, message = message)


#會員頁，有登入狀態才能看到資訊，沒登入導回首頁
@app.route("/member")
def member():
    #判斷 session loginState 是否為真
    if session["loginState"] == True:
        return render_template("member.html", pageTitle = pageTitle2, name = session["loginname"])
    else:
        return redirect(url_for('index'))


#登出，清掉 session 並導回首頁
@app.route("/signout")
def signout():
    session.pop("loginUsername", None)
    session.pop("loginname", None)
    session["loginState"] = False
    return redirect(url_for('index'))


# API users 查詢會員姓名
@app.route("/api/users", methods=["GET"])
def apiusers():

    #如果未登入，導回首頁
    if session["loginState"] != True:
        return redirect(url_for('index'))
    
    if request.method == "GET":
        username = request.args.get('username')

        connect_mysql()
        selectsql = "select * from user WHERE username = '%s'" %(username)
        cursor.execute(selectsql)  

        selectDBusername = cursor.fetchone()

        #如果資料庫有撈到資料
        if selectDBusername != None:
            #把不要的資料剃除
            selectDBusername.pop('password')
            selectDBusername.pop('time')

            #手動將輸出字串調整為 json 格式
            data = str(selectDBusername)
            userdata = data.replace("'", '"')
            userdata = "{ \"data\":"+userdata+"}"
            #print(userdata)
            return userdata
        else:
            userdata = "{ \"data\" : null }"
            return userdata


# API user 修改會員姓名
@app.route("/api/user", methods=["POST"])
def apiuser():

    if request.method == "POST":
        #擷取前端發來的 json 資料
        data = request.json
        #print(data, data["name"])

        name = data["name"]
        username = session["loginUsername"]
        #print (name, username)

        connect_mysql()
        updatasql = "UPDATE user SET name ='%s' WHERE username = '%s'" %(name, username)
        
        #進行更新動作，如果異常返回 error，執行正常返回 ok
        try:
            cursor.execute(updatasql)
            connect.commit() 
        except:
            return jsonify({"error" : "true",})
        else:
            return jsonify({"ok" : "true",})


#設定 host & port
app.run(host="127.0.0.1" ,port=3000)
