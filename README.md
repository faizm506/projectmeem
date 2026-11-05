# MEEM Version 1 (Django + SQLite)

One trusted space for every Muslim-owned brand. Version 1 is a complete marketplace you can test today:
buyers, sellers, checkout, an automatic donation ledger and a public Impact page, all on **SQLite**.
It looks like the MEEM landing page and works on phones, tablets, laptops and desktops.

## 1. Run it in GitHub Codespaces

1. Upload this folder to a **private** GitHub repo, then **Code > Codespaces > Create codespace**.
   The `.devcontainer` file installs everything, builds the database, creates the cache table and loads demo data.
2. Open the terminal and run:

```bash
python manage.py test                 # all tests should pass before you build anything else
python manage.py createsuperuser      # your admin account (use a long password)
python manage.py runserver 0.0.0.0:8000
```

3. Open port 8000 from the **Ports** tab. The admin is at `/admin/`.

If the automatic setup did not run: `pip install -r requirements.txt`, `python manage.py makemigrations`,
`python manage.py migrate`, `python manage.py createcachetable`, `python manage.py seed_demo`.

Demo logins (development only, password `meem12345`): `demo_buyer`, `seller_amina`, `seller_yusuf`, `seller_noor`.

## 2. What you can test (10 minutes)

1. **Home:** loader, the shop and charity animation, the 3D category carousel, the live Impact numbers.
2. **Buy:** log in as `demo_buyer`, add items from two shops, check out, press **Complete test payment**. Emails print in the terminal.
3. **Impact page:** the donation total rose and is split across causes.
4. **Sell:** log in as `seller_amina` in a private window. Open **My shop**, add a tracking number, mark shipped, then delivered. **Available for payout** goes up.
5. **Admin:** record a **Seller payout**, **Refund** the order (the donation is reversed, nothing is edited), add a charity **Disbursement** with a receipt.
6. **New seller:** sign up with "Sell on MEEM", open a shop, approve it in admin (**Shops > Approve selected shops**).
7. **Problem report:** use "Report a problem" on a paid order and see it under **Disputes** in admin.
8. **Phone check:** open the site on your phone (Codespaces port URL). Menu, cart, checkout and tables all fit the screen.

## 2b. Load a full test marketplace (50 sellers + 50 shoppers)

```bash
python manage.py seed_bulk            # ~50 sellers, ~50 shoppers, ~270 products, ~220 orders over 60 days
python manage.py seed_bulk --sellers 50 --shoppers 50 --orders 400   # change the numbers if you like
```

You get: 50 sellers across all six categories (a few waiting for approval and one suspended, so you can practise the admin),
50 shoppers with delivery addresses, products with prices and stock, orders in every state (paid, shipped, delivered,
refunded, cancelled, unpaid), the matching donation ledger, seller payouts, charity transfers, a few disputes and 40 waitlist emails.
The Impact page, seller dashboards and admin all fill with realistic numbers.

Logins (password `meem12345`): `seller_001` to `seller_050` and `shopper_001` to `shopper_050`.
Running it again adds more orders. To start clean: stop the server, delete `db.sqlite3` and `media/`, then run
`python manage.py migrate`, `python manage.py createcachetable`, `python manage.py seed_bulk`.
It only runs with `DEBUG=1` and never sends emails.

Things worth trying with the bigger data: search and page through the shop (12 per page), open a busy seller's dashboard,
approve a pending shop, refund an order and watch the Impact total drop, and check the monthly table.

**Troubleshooting:** "403 Origin checking failed" on a form means the address in your browser is not trusted.
In development `localhost:8000`, `127.0.0.1:8000` and `*.app.github.dev` are trusted. For any other address add it to
`CSRF_TRUSTED_ORIGINS` in `.env`, for example `CSRF_TRUSTED_ORIGINS=https://my-name-8000.app.github.dev`.

## 3. Security: which gates are closed

| Risk | What protects you |
|---|---|
| Password guessing | 5 wrong passwords lock that username + IP for 15 minutes (website **and** admin login). Passwords need 10+ characters and are checked against common-password lists. Passwords are stored hashed (PBKDF2). |
| Stolen session | Sessions are stored in the database, so **logout really ends them**. Cookies are HttpOnly, SameSite, and Secure in production. Signed-in pages are never cached. |
| Form forgery (CSRF) | Every form has a CSRF token. Logout and every change of data need POST. |
| Script injection (XSS) | Django escapes all output. No `|safe` anywhere. A strict **Content Security Policy** blocks inline scripts and unknown script sources. |
| Clickjacking, sniffing, data leaks | `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `nosniff`, referrer and permissions policies. |
| SQL injection | Only the Django ORM is used. No raw SQL. |
| Bots and spam | Hidden honeypot fields on sign-up and waitlist, plus per-IP rate limits on sign-up, waitlist, checkout and reports. |
| Malicious uploads | Every image is proven real with Pillow, limited to JPG/PNG/WebP, 3 MB and 25 MP, shrunk, **re-encoded** (hidden data removed) and renamed to a random name. |
| Seeing other people's data | Every order, shop, product and seller action checks ownership. Tests try to break this. |
| Price tampering | Prices, shipping, commission and donation are always computed on the server. |
| Fake payments | Card details never touch your server. Webhooks are signature-checked and safe to repeat. The fake "test payment" **only works when DEBUG is on**, and the app **refuses to start** in production with it. |
| Unsafe deployment | With `DEBUG=0` the app refuses to start unless: `SECRET_KEY` is long and random, `ADMIN_URL` is a private path, `ALLOWED_HOSTS` is your real domain, and payments are not in test mode. HTTPS redirect and HSTS turn on automatically. |
| Donation records | The ledger is append-only in code and in the admin. Refunds add reversing rows. |

Tests for all of this are in `core/tests.py` and `orders/tests.py`.

**Not covered in Version 1 (plan these for Version 2):** two-factor login for the admin, email verification at sign-up, password-reset emails, antivirus scanning of uploads, and an off-site log/alert service. Until then: use a long unique admin password, keep `ADMIN_URL` private, and watch the terminal log for "Failed login" lines.

## 4. Real payments (Razorpay)

1. Create a Razorpay account and use **test mode** keys first.
2. Set `PAYMENT_PROVIDER=razorpay`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`.
3. In Razorpay add a webhook to `https://YOUR-SITE/payments/razorpay/webhook/` with events `payment.captured` and `order.paid`.
4. Pay with a Razorpay test card. Test mode must work before live keys.

The Razorpay code follows the documented API but has not been run against their servers. Charity money needs care: keep it in a separate account, pay registered charities, and ask a lawyer and an accountant about your country's rules. The four policy pages are **drafts** for a lawyer to review.

## 5. Your routine as owner

* **Daily:** approve shops, answer disputes, read the log for failed logins.
* **Every 15 minutes (cron):** `python manage.py expire_pending_orders`. Daily: `python manage.py clearsessions`.
* **Weekly:** record seller payouts. **Monthly:** send the donation total to charities, then add a Disbursement with the receipt.
* **Always:** back up `db.sqlite3` and the `media/` folder. Test restoring a backup.

## 6. Going live checklist

1. Copy `.env.example` to `.env` and set: `DEBUG=0`, a random 50+ character `SECRET_KEY`, `ALLOWED_HOSTS=yourdomain.com`, `CSRF_TRUSTED_ORIGINS=https://yourdomain.com`, `ADMIN_URL=a-private-path/`, `PAYMENT_PROVIDER=razorpay`, real email settings. Set `TRUST_PROXY_HEADERS=1` **only** behind your own proxy.
2. `python manage.py check --deploy` and fix every warning.
3. Run behind gunicorn and a proxy with HTTPS. Serve `/media/` from the proxy, not from Django.
4. `python manage.py collectstatic --noinput`
5. Continuous SQLite backups (for example Litestream), and a restore drill.
6. Lawyer reviews Terms, Privacy, Refunds and the Seller Agreement.

## 7. Folder map

```
config/      settings (hardened), urls
core/        home, waitlist, policies, emails, security helpers, middleware (CSP), upload cleaner, seed_demo
accounts/    custom user, sign-up, login with lockout
shops/       shops, seller dashboard, products, shipping, payouts
catalog/     categories, products, search, filters
cart/        session cart
orders/      checkout, orders, disputes, money logic, tests
payments/    test payment + Razorpay (verify, signed webhook)
donations/   causes, append-only ledger, disbursements, Impact page
templates/   all HTML (same design as the landing page)
static/      css/site.css, js/site.js, js/boot.js, js/razorpay.js
```

## 8. Known limits of Version 1 (by design)

SQLite means one server and one writer at a time (fine for hundreds of orders a day). Search is simple "contains" matching.
Payouts, charity transfers and gateway refunds are recorded by hand. Photos live on the server disk. Shipping is one flat rate.
Login is by username. Move to PostgreSQL, automatic payouts and courier APIs in Version 2.

Made with purpose.
