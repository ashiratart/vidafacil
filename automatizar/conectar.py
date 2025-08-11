import imaplib

# Configurações
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "acaciomarianosilvadebrito@gmail.com"
EMAIL_PASSWORD = "test"

def test_connection():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        print("✅ Conexão bem-sucedida com o Gmail!")
        mail.logout()
    except imaplib.IMAP4.error as e:
        print(f"❌ Erro de autenticação: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_connection()


# Conecao imap Microsoft
IMAP_SERVER_MS = "outlook.office365.com"
EMAIL_ACCOUNT_MS = "email@outlook.com"
EMAIL_PASSWORD_MS = "sua_senha"

def test_connection_ms():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER_MS)
        mail.login(EMAIL_ACCOUNT_MS, EMAIL_PASSWORD_MS)
        print("✅ Conexão bem-sucedida com o Outlook!")
        mail.logout()
    except imaplib.IMAP4.error as e:
        print(f"❌ Erro de autenticação: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_connection()

