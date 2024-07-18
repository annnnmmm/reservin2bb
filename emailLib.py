import smtplib

login = "teleport-noreply@miomoor.info"
password = "9KT0uvKNSQEAcMGr8ig7"

def loginEmail():
    try:
        print('подключение к почтовому серверу')
        server = smtplib.SMTP_SSL('smtp.mail.ru:465')
        server.login(login, password)
        print('подключение успешно установлено')
        return server
    except Exception as ex:
        print('при подключении произошла ошибка:', ex)
        return False

def sendEmail(server, receiver, title, text):
    charset = 'Content-Type: text/plain; charset=utf-8'
    mime = 'MIME-Version: 1.0'
    body = "\r\n".join((f"From: {login}", f"To: {receiver}",
                        f"Subject: {title}", mime, charset, "", text))

    server.sendmail(login, receiver, body.encode("utf-8"))