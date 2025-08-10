import imaplib
import email
import datetime
import os
import re

#  Gmail
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "acaciomarianosilvadebrito@gmail.com"
EMAIL_PASSWORD = "test"
DT_EMAIL = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%d-%b-%Y")

# Palavras-chave
KEYWORDS = ["boleto", 
            #"cobrança", 
            #"nota", 
            #"recibo", 
            #"fatura"
            ]

# Pasta onde salvar anexos
SAVE_FOLDER = "automatizar/BOLETOS"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def sanitize_filename(name):
    # remover caracteres especiais e substituir espaços por underline
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name.replace(" ", "_")

def connect_gmail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")
    return mail

def search_emails(mail):
    search_query = ' OR '.join([f'(BODY "{k}")' for k in KEYWORDS])
    status, data = mail.search('UTF-8', f'(SENTSINCE {DT_EMAIL})', f'({search_query})')
    if status != "OK":
        print("Nenhum e-mail encontrado.")
        return []
    return data[0].split()

def download_attachments(mail, email_ids):
    for e_id in email_ids:
        status, data = mail.fetch(e_id, "(RFC822)")
        if status != "OK":
            print(f"Erro ao buscar e-mail {e_id}")
            continue

        msg = email.message_from_bytes(data[0][1])

        # Pegar remetente e data
        remetente = sanitize_filename(msg["From"]) or "remetente_desconhecido"
        data_email = msg["Date"] or "data_desconhecida"

        try:
            data_formatada = datetime.datetime.strptime(data_email[:25], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
        except:
            data_formatada = datetime.datetime.now().strftime("%Y-%m-%d")

        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename and (filename.lower().endswith(".pdf") or filename.lower().endswith(".xml")):
                    ext = os.path.splitext(filename)[1]
                    novo_nome = f"{remetente} - {data_formatada}{ext}"
                    filepath = os.path.join(SAVE_FOLDER, novo_nome)

                    contador = 1
                    while os.path.exists(filepath):
                        contador += 1
                        novo_nome = f"{remetente} - {data_formatada} ({contador}){ext}"
                        filepath = os.path.join(SAVE_FOLDER, novo_nome)

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"📂 Anexo salvo: {filepath}")

if __name__ == "__main__":
    mail = connect_gmail()
    emails = search_emails(mail)
    print(f"📧 {len(emails)} e-mails encontrados com palavras-chave.")
    download_attachments(mail, emails)
    mail.logout()
