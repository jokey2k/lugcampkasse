// LUG Camp Kasse 20XX (originally 2012) //

Cash managing for soft drinks and junk food. Used at LUG Camp 2012.

**What can it do?**

  * Realtime push notifications (no Node.js usage any more, yey!)
  * Past bills
  * Voucher handling
  * Scanning codes with a second device
    * To do that, just scan your cashier-allowed code, type in password, scan again and click "activate"

**What you need beforehand**

  * Python 2.7.x, not 2.6 or 3.x, this is not ported to 3 yet
  * Redis server
  * Libevent for gevent usage

**How to use it?**

  0. edit config.py, pick a random long secret key and disable DEBUG
  1. make a virtualenv, maybe
  ``virtualenv my_env && source my_env/bin/activate``
  2. ``pip install -r requirements.txt``
  3. ``python manage.py import_csv -i import.csv``
  4. ``python manage.py runserver``

**The import.csv file layout**

  To get your user info (typically badge to name mapping), vouchers and buyable items into the system, a simple table is used. The following colums are required when you want to import something, the ordering does not matter. Simply use the default file and populate with rows as you need.

  For user import::

    * usercode (6 chars A-Za-z0-9 string)
    * name
    * lug
    * cashier (1 or 0, if the usercode should be able to login with shared secret)
    * initialcredit (integers -> cents, format in the template to EUR/USD/whatever !)
    * blocked (1 or 0)

  For voucher import::

    * vouchercode
    * vouchervalue (integers -> cents, format in the template to EUR/USD/whatever !)

  For shop item imports::

    * itemname
    * itemprice (integers -> cents, format in the template to EUR/USD/whatever !)
    * itemcategory (0 or 1 or 2, can be others but then you need to rewrite the html template)
