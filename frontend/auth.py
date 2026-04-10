from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import bcrypt
import uuid
import smtplib
from email.mime.text import MIMEText
import os

DB_FILE = 'users.db'

def init_db():
    """Létrehozza az adatbázist és a táblát, ha még nem léteznek."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT,
            is_verified BOOLEAN,
            verify_token TEXT
        )
    ''')
    conn.commit()
    conn.close()

def register_user(email, password):
    """Új felhasználó regisztrációja titkosított jelszóval."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Ellenőrizzük, hogy létezik-e már
    c.execute('SELECT email FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return False, "Ez az e-mail cím már regisztrálva van!"

    # Jelszó titkosítása
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Egyedi megerősítő token generálása
    verify_token = str(uuid.uuid4())
    
    c.execute('INSERT INTO users (email, password_hash, is_verified, verify_token) VALUES (?, ?, ?, ?)',
              (email, password_hash, False, verify_token))
    conn.commit()
    conn.close()
    
    # E-mail küldése (ezt a következő lépésben állítjuk be!)
    send_verification_email(email, verify_token)
    
    return True, "Sikeres regisztráció! Kérlek, erősítsd meg az e-mail címedet a kiküldött linkkel."

def login_user(email, password):
    """Felhasználó beléptetése jelszó és státusz ellenőrzéssel."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT password_hash, is_verified FROM users WHERE email = ?', (email,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False, "Helytelen e-mail vagy jelszó!"
    
    stored_hash, is_verified = row
    
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        return False, "Helytelen e-mail vagy jelszó!"
        
    if not is_verified:
        return False, "Az e-mail címed még nincs megerősítve! Kérlek, kattints az e-mailben kapott linkre."
        
    return True, "Sikeres belépés!"

def verify_email(token):
    """E-mail megerősítése a token alapján."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE verify_token = ?', (token,))
    row = c.fetchone()
    
    if row:
        c.execute('UPDATE users SET is_verified = 1, verify_token = NULL WHERE verify_token = ?', (token,))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def send_verification_email(to_email, token):
    """Megerősítő e-mail kiküldése Gmail SMTP-n keresztül."""
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    # A te domained, ami a linkben szerepelni fog
    domain = "https://mimir-ai.hu" 
    verify_link = f"{domain}/?token={token}"
    
    if not sender_email or not sender_password:
        print("Hiba: Nincs beállítva SMTP e-mail vagy jelszó! (Szimulációs mód)")
        print(f"Kattints ide a megerősítéshez: {verify_link}")
        return

    # E-mail felépítése
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Mimir AI - Fiók aktiválása"
    msg["From"] = f"Mimir AI <{sender_email}>"
    msg["To"] = to_email

    # HTML dizájn a levélhez
    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 30px; border-radius: 10px; background-color: #f9f9f9;">
            <h2 style="color: #2e6c80; text-align: center;">Üdvözlünk a Mimir AI rendszerben! 🧠</h2>
            <p>Kedves Felhasználó!</p>
            <p>A regisztrációd befejezéséhez és a fiókod aktiválásához kérlek, kattints az alábbi gombra:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_link}" style="background-color: #4CAF50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">Fiók aktiválása</a>
            </div>
            <p style="font-size: 12px; color: #666;">Ha a gomb nem működik, másold be az alábbi linket a böngésződbe:<br>{verify_link}</p>
            <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
            <p style="font-size: 12px; color: #999; text-align: center;">Ha nem te kérted a regisztrációt, kérjük, hagyd figyelmen kívül ezt az e-mailt.</p>
        </div>
      </body>
    </html>
    """
    
    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        # Biztonságos SSL kapcsolat a Gmail szerveréhez
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"Sikeres e-mail küldés: {to_email}")
    except Exception as e:
        print(f"Hiba az e-mail küldésekor: {str(e)}")