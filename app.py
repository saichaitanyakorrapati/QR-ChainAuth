from __future__ import annotations


import hashlib

import os

import socket

import sqlite3

from datetime import datetime, timezone

from functools import wraps

from pathlib import Path

from typing import Any

from uuid import uuid4


import qrcode

from flask import (

    Flask,

    flash,

    g,

    redirect,

    render_template,

    request,

    send_from_directory,

    session,

    url_for,

)


BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "instance" / "qr_chainauth.db"

QR_DIR = BASE_DIR / "static" / "qrcodes"


def get_default_base_url() -> str:

    try:

        local_ip = socket.gethostbyname(socket.gethostname())

        if local_ip and not local_ip.startswith("127."):

            return f"http://{local_ip}:5000"

    except OSError:

        pass

    return "http://127.0.0.1:5000"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME")
    app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD")
    app.config["BASE_URL"] = os.environ.get("BASE_URL", get_default_base_url())

    if not all(
        app.config[key]
        for key in ("SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD")
    ):
        raise RuntimeError(
            "Set SECRET_KEY, ADMIN_USERNAME, and ADMIN_PASSWORD "
            "environment variables before starting the application."
        )

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    QR_DIR.mkdir(parents=True, exist_ok=True)


    @app.before_request

    def before_request() -> None:

        g.db = get_db()


    @app.teardown_appcontext

    def teardown_db(_exception: BaseException | None) -> None:

        db = g.pop("db", None)

        if db is not None:

            db.close()


    register_routes(app)


    with app.app_context():

        init_db()


    return app


def get_db() -> sqlite3.Connection:

    if "db" not in g:

        connection = sqlite3.connect(DATABASE_PATH)

        connection.row_factory = sqlite3.Row

        g.db = connection

    return g.db


def init_db() -> None:

    db = get_db()

    db.executescript(

        """

        CREATE TABLE IF NOT EXISTS products (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_uid TEXT NOT NULL UNIQUE,

            product_name TEXT NOT NULL,

            brand TEXT NOT NULL,

            category TEXT NOT NULL,

            batch_number TEXT NOT NULL,

            manufacturer TEXT NOT NULL,

            manufacture_date TEXT NOT NULL,

            expiry_date TEXT,

            description TEXT,

            status TEXT NOT NULL DEFAULT 'unsold',

            qr_filename TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            sold_at TEXT

        );


        CREATE TABLE IF NOT EXISTS ledger (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_uid TEXT NOT NULL,

            event_type TEXT NOT NULL,

            actor TEXT NOT NULL,

            event_message TEXT NOT NULL,

            event_time TEXT NOT NULL,

            event_data TEXT NOT NULL,

            previous_hash TEXT NOT NULL,

            current_hash TEXT NOT NULL

        );

        """

    )

    db.commit()


def utc_now_iso() -> str:

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def login_required(view):

    @wraps(view)

    def wrapped_view(*args, **kwargs):

        if not session.get("admin_logged_in"):

            flash("Please log in as admin to continue.", "warning")

            return redirect(url_for("login", next=request.path))

        return view(*args, **kwargs)


    return wrapped_view


def register_ledger_event(

    *,

    db: sqlite3.Connection,

    product_uid: str,

    event_type: str,

    actor: str,

    event_message: str,

    event_data: str,

) -> None:

    previous_entry = db.execute(

        "SELECT current_hash FROM ledger WHERE product_uid = ? ORDER BY id DESC LIMIT 1",

        (product_uid,),

    ).fetchone()

    previous_hash = previous_entry["current_hash"] if previous_entry else "GENESIS"

    event_time = utc_now_iso()

    payload = "|".join(

        [product_uid, event_type, actor, event_message, event_time, event_data, previous_hash]

    )

    current_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    db.execute(

        """

        INSERT INTO ledger (

            product_uid, event_type, actor, event_message, event_time, event_data, previous_hash, current_hash

        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """,

        (

            product_uid,

            event_type,

            actor,

            event_message,

            event_time,

            event_data,

            previous_hash,

            current_hash,

        ),

    )


def generate_qr_code(product_uid: str, base_url: str) -> str:

    filename = f"{product_uid}.png"

    verification_url = f"{base_url.rstrip('/')}/verify/{product_uid}"

    image = qrcode.make(verification_url)

    image.save(QR_DIR / filename)

    return filename


def verify_chain(entries: list[sqlite3.Row]) -> bool:

    previous_hash = "GENESIS"

    for entry in entries:

        payload = "|".join(

            [

                entry["product_uid"],

                entry["event_type"],

                entry["actor"],

                entry["event_message"],

                entry["event_time"],

                entry["event_data"],

                previous_hash,

            ]

        )

        recalculated_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        if entry["previous_hash"] != previous_hash or entry["current_hash"] != recalculated_hash:

            return False

        previous_hash = entry["current_hash"]

    return True


def fetch_dashboard_stats(db: sqlite3.Connection) -> dict[str, Any]:

    stats_row = db.execute(

        """

        SELECT

            COUNT(*) AS total_products,

            SUM(CASE WHEN status = 'sold' THEN 1 ELSE 0 END) AS sold_products,

            SUM(CASE WHEN status = 'unsold' THEN 1 ELSE 0 END) AS unsold_products

        FROM products

        """

    ).fetchone()

    scan_count_row = db.execute(

        "SELECT COUNT(*) AS total_scans FROM ledger WHERE event_type = 'scan'"

    ).fetchone()

    latest_products = db.execute(

        "SELECT * FROM products ORDER BY created_at DESC LIMIT 5"

    ).fetchall()

    return {

        "total_products": stats_row["total_products"] or 0,

        "sold_products": stats_row["sold_products"] or 0,

        "unsold_products": stats_row["unsold_products"] or 0,

        "total_scans": scan_count_row["total_scans"] or 0,

        "latest_products": latest_products,

    }


def register_routes(app: Flask) -> None:

    @app.route("/")

    def home():

        return render_template("home.html", stats=fetch_dashboard_stats(get_db()))


    @app.route("/login", methods=["GET", "POST"])

    def login():

        if request.method == "POST":

            username = request.form.get("username", "").strip()

            password = request.form.get("password", "").strip()

            if (

                username == app.config["ADMIN_USERNAME"]

                and password == app.config["ADMIN_PASSWORD"]

            ):

                session["admin_logged_in"] = True

                session["admin_username"] = username

                flash("Admin login successful.", "success")

                return redirect(request.args.get("next") or url_for("admin_dashboard"))

            flash("Invalid admin credentials.", "error")

        return render_template("login.html")


    @app.route("/logout")

    def logout():

        session.clear()

        flash("You have been logged out.", "success")

        return redirect(url_for("home"))


    @app.route("/admin")

    @login_required

    def admin_dashboard():

        db = get_db()

        products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()

        return render_template(

            "dashboard.html", stats=fetch_dashboard_stats(db), products=products

        )


    @app.route("/products/new", methods=["GET", "POST"])

    @login_required

    def create_product():

        if request.method == "POST":

            form = {

                "product_name": request.form.get("product_name", "").strip(),

                "brand": request.form.get("brand", "").strip(),

                "category": request.form.get("category", "").strip(),

                "batch_number": request.form.get("batch_number", "").strip(),

                "manufacturer": request.form.get("manufacturer", "").strip(),

                "manufacture_date": request.form.get("manufacture_date", "").strip(),

                "expiry_date": request.form.get("expiry_date", "").strip(),

                "description": request.form.get("description", "").strip(),

            }

            required_fields = [

                "product_name",

                "brand",

                "category",

                "batch_number",

                "manufacturer",

                "manufacture_date",

            ]

            if any(not form[field] for field in required_fields):

                flash("Please fill in all required product details.", "error")

                return render_template("create_product.html", form=form)


            db = get_db()

            product_uid = uuid4().hex[:12].upper()

            created_at = utc_now_iso()

            qr_base_url = request.host_url or app.config["BASE_URL"]

            qr_filename = generate_qr_code(product_uid, qr_base_url)


            db.execute(

                """

                INSERT INTO products (

                    product_uid, product_name, brand, category, batch_number, manufacturer,

                    manufacture_date, expiry_date, description, status, qr_filename, created_at, updated_at

                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unsold', ?, ?, ?)

                """,

                (

                    product_uid,

                    form["product_name"],

                    form["brand"],

                    form["category"],

                    form["batch_number"],

                    form["manufacturer"],

                    form["manufacture_date"],

                    form["expiry_date"] or None,

                    form["description"],

                    qr_filename,

                    created_at,

                    created_at,

                ),

            )

            register_ledger_event(

                db=db,

                product_uid=product_uid,

                event_type="registration",

                actor=session.get("admin_username", "admin"),

                event_message="Product registered on QR ChainAuth.",

                event_data=(

                    f"{form['product_name']}|{form['brand']}|{form['category']}|{form['batch_number']}"

                ),

            )

            db.commit()

            flash("Product created successfully and QR code generated.", "success")

            return redirect(url_for("product_detail", product_uid=product_uid))


        return render_template("create_product.html", form={})


    @app.route("/products/<product_uid>")

    @login_required

    def product_detail(product_uid: str):

        db = get_db()

        product = db.execute(

            "SELECT * FROM products WHERE product_uid = ?",

            (product_uid,),

        ).fetchone()

        if product is None:

            flash("Product not found.", "error")

            return redirect(url_for("admin_dashboard"))

        history = db.execute(

            "SELECT * FROM ledger WHERE product_uid = ? ORDER BY id ASC",

            (product_uid,),

        ).fetchall()

        return render_template(

            "product_detail.html",

            product=product,

            history=history,

            chain_valid=verify_chain(list(history)),

        )


    @app.route("/products/<product_uid>/mark-sold", methods=["POST"])

    @login_required

    def mark_sold(product_uid: str):

        db = get_db()

        product = db.execute(

            "SELECT * FROM products WHERE product_uid = ?",

            (product_uid,),

        ).fetchone()

        if product is None:

            flash("Product not found.", "error")

            return redirect(url_for("admin_dashboard"))

        if product["status"] == "sold":

            flash("This product is already marked as sold.", "warning")

            return redirect(url_for("product_detail", product_uid=product_uid))


        sold_at = utc_now_iso()

        db.execute(

            """

            UPDATE products

            SET status = 'sold', sold_at = ?, updated_at = ?

            WHERE product_uid = ?

            """,

            (sold_at, sold_at, product_uid),

        )

        register_ledger_event(

            db=db,

            product_uid=product_uid,

            event_type="sale",

            actor=session.get("admin_username", "admin"),

            event_message="Product marked as sold after verification scan.",

            event_data=f"sold_at={sold_at}",

        )

        db.commit()

        flash("Product has been marked as sold.", "success")

        return redirect(url_for("verify_product", product_uid=product_uid))


    @app.route("/products/<product_uid>/regenerate-qr", methods=["POST"])

    @login_required

    def regenerate_qr(product_uid: str):

        db = get_db()

        product = db.execute(

            "SELECT * FROM products WHERE product_uid = ?",

            (product_uid,),

        ).fetchone()

        if product is None:

            flash("Product not found.", "error")

            return redirect(url_for("admin_dashboard"))


        qr_base_url = request.host_url or app.config["BASE_URL"]

        qr_filename = generate_qr_code(product_uid, qr_base_url)

        updated_at = utc_now_iso()

        db.execute(

            "UPDATE products SET qr_filename = ?, updated_at = ? WHERE product_uid = ?",

            (qr_filename, updated_at, product_uid),

        )

        register_ledger_event(

            db=db,

            product_uid=product_uid,

            event_type="qr_regenerated",

            actor=session.get("admin_username", "admin"),

            event_message="QR code regenerated with current verification URL.",

            event_data=f"base_url={qr_base_url}",

        )

        db.commit()

        flash("QR code regenerated successfully.", "success")

        return redirect(url_for("product_detail", product_uid=product_uid))


    @app.route("/verify/<product_uid>")

    def verify_product(product_uid: str):

        db = get_db()

        product = db.execute(

            "SELECT * FROM products WHERE product_uid = ?",

            (product_uid,),

        ).fetchone()

        if product is None:

            return render_template("verify_not_found.html", product_uid=product_uid), 404


        register_ledger_event(

            db=db,

            product_uid=product_uid,

            event_type="scan",

            actor="scanner",

            event_message="QR code scanned for authenticity check.",

            event_data=f"status_at_scan={product['status']}",

        )

        db.commit()


        history = db.execute(

            "SELECT * FROM ledger WHERE product_uid = ? ORDER BY id ASC",

            (product_uid,),

        ).fetchall()

        return render_template(

            "verify_product.html",

            product=product,

            history=history,

            chain_valid=verify_chain(list(history)),

        )


    @app.route("/history")

    @login_required

    def history():

        db = get_db()

        records = db.execute(

            """

            SELECT ledger.*, products.product_name, products.brand

            FROM ledger

            JOIN products ON products.product_uid = ledger.product_uid

            ORDER BY ledger.id DESC

            """

        ).fetchall()

        return render_template("history.html", records=records)


    @app.route("/qrcodes/<filename>")

    def qrcodes(filename: str):

        return send_from_directory(QR_DIR, filename)


app = create_app()


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
