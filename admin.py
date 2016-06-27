# -*- encoding: utf-8 -*-
import datetime
import os
import socket
import threading
import time
import flask_admin as admin_moudle
from flask import Flask, request, render_template, redirect, url_for
from flask_admin import BaseView, expose, AdminIndexView
from flask_admin.contrib import sqla
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
import dl_find


version = 1.01

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/leddb'
db = SQLAlchemy(app)

##################################################################################################
# Create models


class DownloadList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.Text)

    def __init__(self, link):
        self.link = link


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(20))
    port = db.Column(db.Integer)
    name = db.Column(db.String(50))


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer)
    time = db.Column(db.DateTime)
    event = db.Column(db.Text)

    def __init__(self, pid, time, event):
        self.pid = pid
        self.time = time
        self.event = event


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    code = db.Column(db.String(10))
    address = db.Column(db.Text, nullable=False)
    country = db.Column(db.Integer)
    page = db.Column(db.Integer)
    pos = db.Column(db.Integer)


class Profit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime, nullable=False)


class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    path = db.Column(db.String(500))
    date = db.Column(db.DateTime)


class DlList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    fid = db.Column(db.String(200))
    state = db.Column(db.Text)
    size = db.Column(db.String(200))
    progress = db.Column(db.Text)

    def __init__(self, name, fid, state, size, progress):
        self.name = name
        self.fid = fid
        self.state = state
        self.size = size
        self.progress = progress


################################################################################################
# Get some objects

@app.route('/say_something', methods=['GET', 'POST'])
def say_something():
    if request.form['submit'] == 'send':
        stock_socket.send("7)(!"+request.form['text'])
    return redirect(url_for('say.sent'))


def conn_close(tcpCliSocket, addr):
    try:
        if addr == rp_addr:
            global rp_state
            global rp_socket
            rp_socket = None
            rp_state = "rp not connected2"
    except NameError:
        pass
    try:
        if addr == stock_addr:
            global stock_state
            global stock_socket
            stock_socket = None
            stock_state = "stock not connected2"
    except NameError:
        pass
    try:
        if addr == dl_addr:
            global dl_state
            global dl_socket
            dl_socket = None
            dl_state = "download not connected2"
    except NameError:
        pass
    tcpCliSocket.close()
    print addr, " disconnected"


def conn_thread(tcpCliSocket, addr):
    while True:
        try:
            data = tcpCliSocket.recv(1024)
            if data:
                if len(data.split("@&")) == 2:
                    module, state = data.split("@&")
                    # receive from rp
                    if module == "rp":
                        global rp_addr
                        global rp_socket
                        rp_socket = tcpCliSocket
                        rp_addr = addr
                        if state == 'Alive':
                            global rp_state
                            rp_state = "Alive"
                        if state == 'Dead':
                            global rp_state
                            rp_state = "Dead"
                    # receive from stock
                    if module == "st":
                        global stock_addr
                        global stock_socket
                        stock_socket = tcpCliSocket
                        stock_addr = addr
                        if state == 'Alive':
                            global stock_state
                            stock_state = "Alive"
                        if state == 'Dead':
                            global stock_state
                            stock_state = "Dead"
                    # receive from download
                    if module == "dl":
                        global dl_addr
                        global dl_socket
                        dl_socket = tcpCliSocket
                        dl_addr = addr
                        if state == 'Alive':
                            global dl_state
                            dl_state = "Alive"
                        if state == 'Dead':
                            global dl_state
                            dl_state = "Dead"
            else:
                conn_close(tcpCliSocket, addr)
                break
        except socket.error:
            conn_close(tcpCliSocket, addr)
            break


def timer_r():
    timer = 0
    while 1:
        time.sleep(60)
        global timer
        timer += 1


def conn():
    web = Device.query.filter_by(name='web').first()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("gmail.com", 80))
    web.ip = s.getsockname()[0]
    db.session.commit()
    s.close()
    while 1:
        try:
            web_conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            web_conn_socket.bind(('', 21568))
            web_conn_socket.listen(5)
            db.session.add(Log('0', datetime.datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S'), "web connected"))
            db.session.commit()

            threading.Thread(target=timer_r).start()

            while 1:
                try:
                    tcpCliSocket, addr = web_conn_socket.accept()
                    db.session.add(Log('0', datetime.datetime.now(), "connected from " + str(addr)))
                    db.session.commit()
                    print "connected from ", addr
                    threading.Thread(target=conn_thread, args=(tcpCliSocket, addr)).start()
                except socket.error:
                    db.session.add(Log('0', datetime.datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S'), "conn error"))
                    db.session.commit()
                    print "conn error"
        except socket.error:
            db.session.add(Log('0', datetime.datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S'), "web_conn_socket error"))
            db.session.commit()
            print "web_conn_socket error"
            time.sleep(100)


@app.route('/foo', methods=['GET', 'POST'])
def foo():
    try:
        # 1:stock,
        if request.form['submit'] == 'Turn On':
            global server_thread
            server_thread = threading.Thread(target=conn, name='server')
            server_thread.start()
        if request.form['submit'] == 'Turn On Download Server':
            dl_socket.send("0")
        if request.form['submit'] == 'Turn Off Download Server':
            dl_socket.send("1")
        if request.form['submit'] == 'Turn On Stock Server':
            stock_socket.send("9")
        if request.form['submit'] == 'Turn Off Stock Server':
            stock_socket.send("8")
        if request.form['submit'] == 'Turn On RP':
            rp_socket.send("0")
        if request.form['submit'] == 'Turn Off RP':
            rp_socket.send("1")

        time.sleep(5)
        return redirect(url_for('server.index'))
    except socket.error:
        return redirect(url_for('server.index'))


@app.route('/add_to_dl_list', methods=['GET', 'POST'])
def add_to_dl_list():
    if request.form['submit'] == 'submit':
        hrefs = request.form.getlist('download')
        for href in hrefs:
            db.session.add(DownloadList(href))
            db.session.commit()
        dl_socket.send("2")
    time.sleep(5)
    return redirect(url_for('download.index'))


@app.route('/find_download', methods=['GET', 'POST'])
def find_download():
    if request.form['submit'] == 'keyword':
        webs = request.form.getlist('web')
        files = dl_find.find(request.form['keyword'].encode('utf-8'), webs)
        return render_template("/admin/find_table.html", files=files)
    # form[name tag]
    if request.form['submit'] == 'resume':
        dl_socket.send("4@@" + request.form['torrent_id'])
        time.sleep(2)
        return redirect(url_for('download.index'))
    if request.form['submit'] == 'stop':
        dl_socket.send("5@@" + request.form['torrent_id'])
        time.sleep(2)
        return redirect(url_for('download.index'))
    if request.form['submit'] == 'delete':
        dl_socket.send("6@@" + request.form['torrent_id'])
        time.sleep(2)
        return redirect(url_for('download.index'))

##############################################################################################################


class Download(BaseView):
    @expose('/')
    def index(self):
        if request.method == 'GET':
            dl_list = DlList.query.all()
            try:
                dl_socket.send("3")
                time.sleep(1)
            except:
                global dl_state
                dl_state = "download not connected"

            time.sleep(1)
            return self.render('/admin/download.html', dl_state=dl_state, dl_list=dl_list)


class Server(BaseView):
    @expose('/')
    def index(self):
        if request.method == 'GET':
            # check stock
            try:
                stock_socket.send("999")
            except:
                global stock_state
                stock_state = "stock not connected"
            # check rp
            try:
                rp_socket.send("999")
            except:
                global rp_state
                rp_state = "rp not connected"
            # check dl
            try:
                dl_socket.send("999")
            except:
                global dl_state
                dl_state = "download not connected"

            try:
                if server_thread.isAlive():
                    server_state = "Working"

                    hour = timer / 60
                    min = timer % 60
                    day = hour / 12
                    time_l = " " + str(day) + "D/" + str(hour) + "H/" + str(min) + "M"
                else:
                    server_state = "Closing2"
                    global timer
                    timer = 0
                    time_l = ""
            except:
                server_state = "Closing1"
                global timer
                timer = 0
                time_l = ""

            time.sleep(1)
            return self.render('/admin/server.html', server_state=server_state, stock_state=stock_state,
                               rp_state=rp_state, dl_state=dl_state, time_l=time_l)


# Customized User model admin
class MyProfit(sqla.ModelView):
    def on_model_change(self, form, model, is_created):
        stock_socket.send("3")

    def on_model_delete(self, model):
        stock_socket.send("3")


class MyData(sqla.ModelView):
    def on_model_change(self, form, model, is_created):
        stock_socket.send("3")

    def on_model_delete(self, model):
        stock_socket.send("3")


class Say(BaseView):
    @expose('/')
    def index(self):
        if request.method == 'GET':
            return self.render('/admin/say.html')

    @expose('/sent')
    def sent(self):
        if request.method == 'GET':
            return self.render('/admin/say.html', send=True)


class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        # Get profits
        profits_data = Profit.query.order_by(Profit.id.desc()).first()
        profits = profits_data.rate
        if "-" not in str(profits):
            profits = "+" + str(profits)
        else:
            profits = str(profits)
        # Get US stock
        us_stock_data = Stock.query.filter_by(country=1).all()
        cn_stock_data = Stock.query.filter_by(country=2).all()

        return self.render('admin/index.html', profits=profits, date=profits_data.date,
                           us_stock_data=us_stock_data, cn_stock_data=cn_stock_data, version=version)


# Flask views
@app.route('/')
def index():
    return render_template('index.html')

# Create admin
admin_moudle = admin_moudle.Admin(app, name='Smart Home', template_mode='bootstrap3',
                                  index_view=MyHomeView(menu_icon_type='glyph', menu_icon_value='glyphicon-home'))

# Add views
admin_moudle.add_view(sqla.ModelView(Stock, db.session, category='Stock'))
admin_moudle.add_view(MyProfit(Profit, db.session, category='Stock'))
admin_moudle.add_view(Download(name='Download', category='Data'))
admin_moudle.add_view(MyData(Data, db.session, category='Data'))
admin_moudle.add_view(Say(name='Say'))
admin_moudle.add_view(Server(name='Server', category='Settings'))
admin_moudle.add_view(sqla.ModelView(Log, db.session, category='Settings'))


if __name__ == '__main__':
    # Start app
    # app.run(debug=True)
    app.run()
