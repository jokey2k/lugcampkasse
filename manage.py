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
def import_csv(csv_filename):
    """Imports accounts and vouchers from given CSV file. NOTE: delimiter char is ';', quotation is '"' """

    with open(csv_filename) as input_file:
        reader = csv.DictReader(input_file, delimiter=";")
        for row in reader:
            # row containing user(data)
            if "usercode" in row and row["usercode"]:
                users = User.query.filter(User.code==row['usercode'])
                if not users:
                    user = User(code=row["usercode"])
                    print "Created user for code %s" % user.code
                    db.session.add(user)
                else:
                    user = users[0]
                user.name = row['name']
                user.lug = row['lug']
                user.allowed_cashier = True if row['cashier'] else False
                user.blocked = True if row['blocked'] else False

                if row["initialcredit"]:
                    if value:
                        bill = Bill(user=user)
                        billentry = BillEntry(name="Initial credit", price=value, bill=bill)
                        db.session.add(billentry)
                        db.session.add(bill)
            elif "vouchercode" in row and row["vouchercode"]:
                vouchers = Voucher.query.filter(Voucher.code==row['vouchercode'])
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
                items = ShopItem.query.filter(ShopItem.name==row['itemname'])
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
                    item.value = value
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
