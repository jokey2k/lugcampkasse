from datetime import datetime
from itertools import ifilter
import math
from juggernaut import Juggernaut

from flask import Flask, request, url_for, redirect, g, session, flash, \
     abort, render_template
from flask.signals import Namespace

from flaskext.csrf import csrf

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import event as sqla_event
from sqlalchemy.sql.expression import func as sqla_func
from sqlalchemy.orm.interfaces import SessionExtension, EXT_CONTINUE

# App definiton

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
jug = Juggernaut()
csrf(app)

# register additional template commands

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

# create custom signals
signals = Namespace()
before_flush = signals.signal('models-before-flush')


# Add flush signalling to session
class FlushSignalExtension(SessionExtension):
    def before_flush(self, session, flush_context, instances):
        before_flush.send(session.app, session=session, instances=instances)
        return EXT_CONTINUE


db = SQLAlchemy(app, session_extensions=[FlushSignalExtension()])

# Data Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6))
    name = db.Column(db.String(150))
    lug = db.Column(db.String(100))
    balance = db.Column(db.Integer, nullable=False, default=0)
    allowed_cashier = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False, nullable=False)

    @staticmethod
    def get_by_code(code):
        user = User.query.filter(User.code==code).first_or_404()
        if user.blocked:
            abort(403)
        return user

    def update_balance(self):
        self.balance = sum([bill.accumulated_price for bill in self.bills])


class BillEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'))
    bill = db.relationship('Bill', backref='entries')
    name = db.Column(db.String(150))
    price = db.Column(db.Integer, nullable=False, default=0)


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User, uselist=False, backref="bills")
    accumulated_items = db.Column(db.Integer, nullable=False, default=0)
    accumulated_price = db.Column(db.Integer, nullable=False, default=0)
    created = db.Column(db.DateTime, default=sqla_func.current_timestamp())

    def update_accumulated(self):
        self.accumulated_price = sum([entry.price for entry in self.entries])
        self.accumulated_items = len(self.entries)


class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8))
    redeemed = db.Column(db.Boolean)
    value = db.Column(db.Integer)


class ShopItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    price = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(200))
    category = db.Column(db.Integer, nullable=False)


def update_sums_and_balances(app, session, instances):
    """Handler for updating bill sum and user balance"""

    # First update all bill sums
    for session_changed in [session.new, session.deleted, session.dirty]:
        predicate = lambda s: isinstance(s, BillEntry)
        for entry in ifilter(predicate, session_changed):
            entry.bill.update_accumulated()
    # Then update all users balances
    for session_changed in [session.new, session.deleted, session.dirty]:
        predicate = lambda s: isinstance(s, Bill)
        for entry in ifilter(predicate, session_changed):
            entry.user.update_balance()

before_flush.connect(update_sums_and_balances)

# cashier and user notification helpers
def send_updated_balance_notification(user):
    """Notifies clients about updated balance"""

    data = {'balance': "%6.2f" % (user.balance/100),
            'updated_on': "Live aktualisiert: %s" % datetime.now().strftime('%H:%M @ %d.%m.%Y')}
    jug.publish('updated-balance:%s' % user.code, data)

def send_new_customer_notification(cashier_code, new_customer_code):
    """Notifies cashier clients about new user scan"""

    data = {'code': new_customer_code}
    jug.publish('new-customer:%s' % cashier_code, data)

def send_redeem_voucher_notification(cashier_code, voucher_code):
    """Notifies cashier about newly scanned voucher"""

    data = {'code': voucher_code}
    jug.publish('scanned-voucher:%s' % cashier_code, data)

# view functions
@app.before_request
def set_request_environment():
    g.cashier = None
    if 'cashier' in session:
        g.cashier = User.query.get(session['cashier'])
    if 'scan_device' not in session:
        session['scan_device'] = False

@app.errorhandler(403)
def access_denied(e):
    return render_template('error403.html'), 403

@app.errorhandler(404)
def access_denied(e):
    return render_template('error404.html'), 404

@app.route('/<string(length=6):code>')
def usercode(code):
    """Request from User to show balance or from cashier to change to User"""

    if g.cashier:
        if code == g.cashier.code:
            return redirect(url_for('devices', disable_navigation=True, ownercode=g.cashier.code))
        if session['scan_device']:
            send_new_customer_notification(g.cashier.code, code)
            user = User.get_by_code(code)
            return render_template('new_customer_notification.html', disable_navigation=True, user=user)
        return redirect(url_for('new_bill', code=code))

    return redirect(url_for('show_balance', code=code))

@app.route('/<string(length=6):code>/balance/', defaults={'page': 1})
@app.route('/<string(length=6):code>/balance/page/<int:page>')
def show_balance(code, page):
    user = User.get_by_code(code)
    pagination = Bill.query.filter_by(user=user).paginate(page)
    flens = int(math.floor(user.balance/70))
    return render_template('balance.html', user=user, pagination=pagination, flens=flens)

@app.route('/<string(length=6):code>/bill/<int:bill_id>')
def show_bill(code, bill_id):
    user = User.get_by_code(code)
    bill = Bill.query.filter_by(user=user).filter_by(id=bill_id).first_or_404()
    flens = int(math.floor(bill.user.balance/70))
    return render_template('show_bill.html', bill=bill, flens=flens)

@app.route('/<string(length=6):code>/new_bill', methods=['GET', 'POST'])
def new_bill(code):
    user = User.get_by_code(code)
    if request.method == "POST":
        try:
            bill_ids = request.form['bill_ids'].split(",")
            bill = Bill(user=user)
            db.session.add(bill)
            for bill_id in bill_ids:
                item = ShopItem.query.get(int(bill_id))
                billentry = BillEntry(name=item.name, price=-item.price, bill=bill)
                db.session.add(billentry)
            db.session.commit()
            return redirect(url_for('show_balance', code=user.code))
        except ValueError:
            flash("Error during bill creation, only provide integers!")
    items = ShopItem.query.order_by(ShopItem.category).all()
    return render_template('new_bill.html', user=user, items=items)

@app.route('/<string(length=6):code>/bill/<int:bill_id>/cancel_item/<int:item_id>', methods=['GET', 'POST'])
def cancel_item(code,bill_id,item_id):
    if not g.cashier:
        abort(403)
    user = User.get_by_code(code)
    bill = Bill.query.get(bill_id)
    item = BillEntry.query.get(item_id)
    if bill != item.bill:
        abort(403)
    if request.method == "POST":
        db.session.delete(item)
        flash("Removed item %s from bill %i" % (item.name, bill.id))
        if len(bill.accumulated_items) == 0:
            db.session.delete(bill)
            user.update_balance()
            flash("Removed whole bill %i" % (bill.id))
        db.session.commit()
        return redirect(url_for('show_bill', code=user.code, bill_id=bill_id))
    return render_template('cancel_item.html', user=user, bill=bill, item=item)

@app.route('/<string(length=6):code>/voucher', methods=['GET', 'POST'])
def redeem_voucher(code):
    if not g.cashier:
        abort(403)
    user = User.get_by_code(code)
    if request.method == "POST":
        voucher = Voucher.query.filter_by(code=request.form['vouchercode']).first()
        if voucher:
            if voucher.redeemed:
                flash("Used voucher already")
            else:
                bill = Bill(user=user)
                billentry = BillEntry(bill=bill)
                billentry.name = "Redeemed voucher (%s, code:%s)" % (g.cashier.name, voucher.code)
                billentry.price = voucher.value
                voucher.redeemed = True
                db.session.add(bill)
                db.session.add(billentry)
                db.session.commit()
                return render_template("voucher_redeemed.html", voucher=voucher, user=user)
        else:
            flash("No such voucher")
    return render_template("redeem_voucher.html", user=user)

@app.route('/<string(length=6):code>/quick_payment', methods=['GET', 'POST'])
def quick_payment(code):
    if not g.cashier:
        return redirect(url_for('show_balance', code=code))
    user = User.get_by_code(code)
    if request.method == "POST":
        if 'amount' in request.form:
            value = int(request.form['amount']) or 0
            bill = Bill(user=user)
            billentry = BillEntry(name="Einzahlung", price=value, bill=bill)
            db.session.add(billentry)
            db.session.add(bill)
            db.session.commit()
            flash("Konto aufgeladen mit %.2f EUR" % (value/100))
            return redirect(url_for('new_bill', code=code))
    return render_template('quick_payment.html', user=user)

@app.route('/cashier/devices', methods=['GET', 'POST'])
def devices():
    if not g.cashier:
        abort(403)
    if request.method == "POST":
        if not session['scan_device']:
            session['scan_device'] = True
        else:
            session['scan_device'] = False
        flash("Scan device status updated")
    is_scan_device = session['scan_device']
    return render_template("devices.html", disable_navigation=is_scan_device, is_scan_device=is_scan_device)

@app.route('/cashier/nextcustomer')
def nextcustomer():
    return render_template('nextcustomer.html')

@app.route('/cashier/signin', methods=['POST', ])
def signin():
    user = User.query.filter_by(code=request.form['code']).first_or_404()
    if request.method == "POST" and request.form['password'] == app.config['CASHIER_PASSWORD']:
        session['cashier'] = user.id
    else:
        flash("Login failed")
    return redirect(url_for('show_balance', code=user.code))

@app.route('/cashier/signout')
def signout():
    code = g.cashier.code
    session.clear()
    return redirect(url_for('show_balance', code=code))

@app.route('/graph/all')
def signout():
    sellings = {}

    for i in range(0, 72):
      sellings[i]=0

    entries = BillEntry.query.all()

    for entry in entries:
      key = entry.bill.created.hour + (entry.bill.created.day-17) * 24

      if key in sellings:
        old = sellings[key]
        sellings[key] = old + 1

    return render_template("graph.html", sellings=sellings)


@app.route('/voucher/<string(length=12):code>')
def vouchercode(code):
    voucher = Voucher.query.filter_by(code=code).first()
    if voucher:
        voucher.valid = True
    else:
        voucher = Voucher()
        voucher.code = code
        voucher.value = 0.0
        voucher.valid = False

    if voucher.valid and g.cashier and session['scan_device']:
        send_redeem_voucher_notification(g.cashier.code, code)

    return render_template("vouchercode.html", voucher=voucher)
