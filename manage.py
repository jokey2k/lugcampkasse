#!/usr/bin/env python
import csv

from flask.ext.script import Manager

from lugcampkasse import app, db, User, Bill, BillEntry, Voucher, ShopItem

from gevent import monkey
from socketio.server import SocketIOServer

manager = Manager(app)


@manager.command
def initdb():
    """Creates all database tables."""
    db.create_all()

@manager.command
def dropdb():
    """Drops all database tables."""
    db.drop_all()

@manager.command
@manager.option("-i", "--init-db", dest="init_db", help="Init database before import")
def import_csv(csv_filename, init_db=False):
    """Imports accounts and vouchers from given CSV file. See docs for required fields"""

    if init_db:
        db.create_all()

    with open(csv_filename) as input_file:
        reader = csv.DictReader(input_file, delimiter=";")
        for row in reader:
            # row containing user(data)
            if "usercode" in row and row["usercode"]:
                usercode = row["usercode"].strip()
                users = User.query.filter(User.code==usercode).all()
                if not users:
                    user = User(code=usercode)
                    print "Created user for code %s" % usercode
                    db.session.add(user)
                else:
                    user = users[0]
                user.name = row['name'].strip()
                user.lug = row['lug'].strip()
                user.allowed_cashier = True if row['cashier'] == "1" else False
                user.blocked = True if row['blocked'] == "1"  else False

                if row["initialcredit"]:
                    try:
                        value = int(row["initialcredit"])
                    except ValueError:
                        value = 0
                    if value:
                        bill = Bill(user=user)
                        billentry = BillEntry(name="Initial credit", price=value, bill=bill)
                        db.session.add(billentry)
                        db.session.add(bill)
            elif "vouchercode" in row and row["vouchercode"]:
                vouchers = Voucher.query.filter(Voucher.code==row['vouchercode']).all()
                if not vouchers:
                    voucher = Voucher(code=row["vouchercode"])
                    print "Created voucher for code %s" % voucher.code
                    db.session.add(voucher)
                else:
                    voucher = vouchers[0]
                if row['vouchervalue']:
                    try:
                        value = int(row["vouchervalue"])
                    except ValueError:
                        value = 0
                    voucher.value = value
            elif "itemname" in row and row["itemname"]:
                items = ShopItem.query.filter(ShopItem.name==row['itemname']).all()
                if not items:
                    item = ShopItem(name=row["itemname"])
                    print "Created ShopItem %s" % item.name
                    db.session.add(item)
                else:
                    item = items[0]
                if row["itemprice"]:
                    try:
                        price = int(row["itemprice"])
                    except ValueError:
                        price = 0
                    item.price = price
                if row["itemcategory"]:
                    try:
                        category = int(row["itemcategory"])
                    except ValueError:
                        category = 0
                    item.category = category
        db.session.commit()

@manager.command
def runserver():
    """Runs webserver as SocketIOServer"""

    monkey.patch_all()

    print "Listening on http://%s:%s and port %s for flash policy requests" % (
        app.config["BIND_IP"], app.config["HTTP_PORT"], app.config["FLASH_POLICY_PORT"])
    SocketIOServer(
        (app.config["BIND_IP"], app.config["HTTP_PORT"]),
        app, resource="socket.io",
        policy_server=True,
        policy_listener=(app.config["BIND_IP"], app.config["FLASH_POLICY_PORT"])).serve_forever()

if __name__ == '__main__':
    manager.run()
