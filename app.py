from ast import keyword
from operator import methodcaller
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from sqlalchemy import true
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps

# kullanıcı giriş decorator' ı=bir kullanıcı giriş yapmadan dashboard a gidememeyi sağlar
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın...", "danger")
            return redirect(url_for("login"))

    return decorated_function


# kullanıcı kayıt formu class
class RegisterForm(Form):
    name = StringField(
        "NAME-SURNAME:", validators=[validators.Length(min=4, max=25)])
    username = StringField("USERNAME:", validators=[
                           validators.Length(min=4, max=25)])
    email = StringField("E-MAIL:", validators=[validators.Length(min=4, max=25), validators.Email(
        message="Please enter a valid e-mail address...")])
    password = PasswordField("PASSWORD:", validators=[validators.Length(min=4, max=25), validators.DataRequired(
        message="Please enter a valid password..."), validators.EqualTo(fieldname="confirm", message="Your password does not match!")])
    confirm = PasswordField("CONFIRM PASSWORD")


# GİRİŞ YAP FORMU
class LoginForm(Form):
    username = StringField("USERNAME:")
    password = PasswordField("PASSWORD:")


# Otobüsüm nerede? FORMU
class otobusForm(Form):
    bus_name = StringField("Otobüs Adı:")


app = Flask(__name__)
app.secret_key = "takipsistemi"


# mysql ayarları
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blogsistemi"
app.config["MYSQLCURSORCLASS"] = "DictCursor"


mysql = MySQL(app)


@ app.route("/")
def index():
    return render_template("index.html")


@ app.route("/rota_bulucu")
def rotabul():
    return render_template("rota_bulucu.html")


@ app.route("/otobusumnerede")
def otobusumnerede():
    return render_template("otobusumnerede.html")

# kontrol paneli


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


# kayıt olma
@app.route("/register", methods=["GET", "POST"])
def register():
    # htmldeki tüm girilenler veri tabanına çekmeyi sağlayan kısım
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()  # mysql bağlantısı oluşturma
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()  # mysql bağlantı sonlandırma
        flash("You have successfully registered...", "success")
        return redirect(url_for("login"))

    else:
        return render_template("register.html", form=form)


# login işlemi
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username=%s "

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()  # kullanıcının tüm bilgilerini alırız
            # 4.indexte parola var onu check ediyoruz 0integer 1 name 2 username 3 email 4 password
            real_password = data[4]
            if password_entered == real_password:
                flash("You have successfully logged in.", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("profile"))
            else:
                flash("You entered your password incorrectly!", "danger")
                return redirect(url_for("login"))

        else:
            flash("No such user found...", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


# logout işlemi çıkış yap
@app.route("/logout")
def logout():
    session.clear()  # session son bulur
    return redirect(url_for("index"))


@app.route('/giris-yap/')
def girisyapbutonu():
    return redirect(url_for("login"))


@app.route('/kaydol/')
def kaydolbutonu():
    return redirect(url_for("register"))


# otobus arama
@app.route("/otobusumnerede", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * from bus where bus_name like '%"+keyword + "%' "

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Otobüs bulunamadı", "warning")
            return redirect(url_for("otobusumnerede"))
        else:
            bus_name = cursor.fetchall()
            return render_template("otobusum nerede", bus_name=bus_name)


if __name__ == "__main__":
    app.run(debug=True)
