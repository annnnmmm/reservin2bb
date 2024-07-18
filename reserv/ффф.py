import datetime
import random
from datetime import datetime
import time
import psycopg2
import pytz
from fastapi import FastAPI, Request, Form
from starlette import status
from starlette.responses import JSONResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
import emailLib
from fastapi.templating import Jinja2Templates
import string

app = FastAPI()
mailserver = emailLib.loginEmail()
templates = Jinja2Templates("templates")
app.mount('/css', StaticFiles(directory='css', html=True), name='css')
app.mount('/fonts', StaticFiles(directory='fonts', html=True), name='fonts')
app.mount('/images', StaticFiles(directory='images', html=True), name='images')
app.mount('/js', StaticFiles(directory='js', html=True), name='js')
admin_email = 'teleportadmn@mail.ru'

try:
    connection = psycopg2.connect('postgresql://tables:1234@127.0.0.1:5432/tables')
    @app.get("/")
    async def main(request: Request, error_auth: bool = False, error_reserve: bool = False, success_reserve: bool = False, success_cancel: bool = False):
        datetime_obj = datetime.strptime(datetime.fromtimestamp(time.time(), pytz.timezone('Europe/Moscow')).strftime('%d/%m/%Y'), "%d/%m/%Y")
        date_today = round(time.mktime(datetime_obj.timetuple()))
        with connection.cursor() as cursor:
            if request.cookies.get('email') is not None:
                is_register = False
                is_email = True
            elif request.cookies.get('pass') is None or request.cookies.get('id') is None:
                is_register = False
                is_email = False
            else:
                is_register = True
                is_email = True

            cursor.execute("select date_reserve, table_id from reservations where date_reserve >= %(date)s and user_id = %(user_id)s order by date_reserve desc",
                           {"date": date_today, "user_id": request.cookies.get('id')})
            get_my_reservation = cursor.fetchone()
            if get_my_reservation is not None:
                is_reserve = True
                cursor.execute("select count_guests from tables where id = %(id)s",
                    {"id": get_my_reservation[1]})
                get_table = cursor.fetchone()
                date_reserve = datetime.fromtimestamp(get_my_reservation[0], pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y')
            else:
                is_reserve = False
                date_reserve = ""
                get_table = ""
            return templates.TemplateResponse("index.html", {"request": request,
                                                         "is_register": is_register,
                                                         "is_email": is_email,
                                                         "error_auth": error_auth,
                                                         "error_reserve": error_reserve,
                                                         "success_reserve": success_reserve,
                                                         "success_cancel": success_cancel,
                                                         "is_reserve": is_reserve,
                                                         "date_reserve": date_reserve,
                                                         "table": get_table})


    @app.get("/logout")
    async def cancel_reserve(request: Request):
        try:
            re = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            re.delete_cookie("id")
            re.delete_cookie("pass")
            return re
        except Exception as ex:
            print(ex)
            return JSONResponse(status_code=200, content={"result": "error", "text_error": ex})

    @app.get("/cancel_reserve")
    async def cancel_reserve(request: Request):
        try:
            datetime_obj = datetime.strptime(datetime.fromtimestamp(time.time(), pytz.timezone('Europe/Moscow')).strftime('%d/%m/%Y'), "%d/%m/%Y")
            date_today = round(time.mktime(datetime_obj.timetuple()))
            with connection.cursor() as cursor:
                cursor.execute("select id, table_id, name, date_reserve from reservations where date_reserve >= %(date)s and user_id = %(user_id)s order by date_reserve desc",
                    {"date": date_today, "user_id": request.cookies.get('id')})
                get_my_reservation = cursor.fetchone()
                cursor.execute(
                    "select email from users where id = %(user_id)s",
                    {"user_id": request.cookies.get('id')})
                get_my_user = cursor.fetchone()
                if get_my_reservation is not None:
                    cursor.execute("delete from reservations where id = %(id)s",
                        {"id": get_my_reservation[0]})
                    connection.commit()
                    date_reserve_cancel = datetime.fromtimestamp(get_my_reservation[3],
                                                          pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y')
                    emailLib.sendEmail(mailserver, admin_email, "Отмена бронирования",
                                       f"Было отменено бронирование :(( Почта клиента: {get_my_user[0]}; Дата, на которую забронировано: {date_reserve_cancel}; Номер забронированного столика: {get_my_reservation[1]}; Имя клиента: {get_my_reservation[2]}")
                    emailLib.sendEmail(mailserver, get_my_user[0], "Отмена бронирования",
                                       f"Было отменено бронирование. Дата, на которую забронировано: {date_reserve_cancel}. По возникшим вопросам пишите по адресу {admin_email} или обращайтесь в тгк https://t.me/teleportrestik")
                    re = RedirectResponse(url="/?success_cancel=true", status_code=status.HTTP_303_SEE_OTHER)
                    return re
                else:
                    re = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
                    return re

        except Exception as ex:
            print(ex)
            return JSONResponse(status_code=200, content={"result": "error", "text_error": ex})


    @app.post("/reserve_table")
    async def reserve_table(request: Request, name: str = Form(...), date: str = Form(...),
                            count_guests: str = Form(...)):
        try:
            datetime_obj = datetime.strptime(
                datetime.fromtimestamp(time.time(), pytz.timezone('Europe/Moscow')).strftime('%d/%m/%y %H/%M'), "%d/%m/%y %H/%M")
            date_today = round(time.mktime(datetime_obj.timetuple()))
            user_id = request.cookies.get('id')
            password = request.cookies.get('pass')

            # Combine date and time into a single datetime object
            combined_datetime = datetime.strptime(f"{date} {time}", "%d/%m/%y %H/%M")
            timestamp = round(time.mktime(combined_datetime.timetuple()))

            with connection.cursor() as cursor:
                cursor.execute(
                    "select id from reservations where date_reserve >= %(date)s and user_id = %(user_id)s order by date_reserve desc",
                    {"date": date_today, "user_id": request.cookies.get('id')})
                get_my_reservation = cursor.fetchone()
                if get_my_reservation is None:
                    cursor.execute(
                        "select * from tables where count_guests >= %(count_guests)s order by count_guests asc, id asc",
                        {"count_guests": count_guests})
                    get_table = cursor.fetchall()
                    cursor.execute("select email from users where id = %(user_id)s and pass = %(password)s",
                                   {"user_id": user_id, "password": password})
                    user = cursor.fetchone()
                    if get_table is not None:
                        table_reserve = 0
                        for tab in range(len(get_table)):
                            cursor.execute(
                                "select * from reservations where date_reserve = %(date)s and table_id = %(table_id)s",
                                {"date": timestamp, "table_id": get_table[tab][0]})
                            get_reservation = cursor.fetchone()
                            if get_reservation is None:
                                table_reserve = get_table[tab][0]
                                break
                        if table_reserve > 0:
                            cursor.execute(
                                "insert into reservations (table_id, date_reserve, name, user_id) values (%(table_id)s, %(date_reserve)s, %(name)s, %(user_id)s)",
                                {"table_id": table_reserve, "date_reserve": timestamp, "name": name,
                                 "user_id": user_id})
                            connection.commit()
                            emailLib.sendEmail(mailserver, admin_email, "Забронирован столик",
                                               f"Был забронирован столик; Почта клиента: {user[0]}; Дата, на которую забронировано: {date}; Количество гостей: {count_guests}; Номер забронированного столика: {table_reserve}")
                            re = RedirectResponse(url="/?success_reserve=true", status_code=status.HTTP_303_SEE_OTHER)
                            return re
                        else:
                            re = RedirectResponse(url="/?error_reserve=true", status_code=status.HTTP_303_SEE_OTHER)
                            return re
                    else:
                        re = RedirectResponse(url="/?error_reserve=true", status_code=status.HTTP_303_SEE_OTHER)
                        return re
                else:
                    re = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
                    return re
        except Exception as ex:
            print(ex)
            return JSONResponse(status_code=200, content={"result": "error", "text_error": ex})

    @app.post("/send_code")
    async def reg_user(email: str = Form(...)):
        try:
            code_verify = random.randint(10000, 99999)
            with connection.cursor() as cursor:
                cursor.execute("select * from users where email = %(email)s", {"email": email})
                us = cursor.fetchone()
                if us is None:
                    cursor.execute("insert into users (email, code) values (%(email)s, %(code)s)", {"email": email, "code": code_verify})
                else:
                    cursor.execute("update users set code = %(code)s where email = %(email)s", {"code": code_verify, "email": email})
                connection.commit()
            emailLib.sendEmail(mailserver, email, "Код подтверждения", f"Ваш код подтверждения: {code_verify}. Никому его не сообщайте!")
            re = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            re.set_cookie(key="email", value=email)
            return re
        except Exception as ex:
            print(ex)
            return JSONResponse(status_code=200, content={"result": "error", "text_error": ex})


    @app.post("/auth")
    async def reg_user(request: Request, code: str = Form(...)):
        try:
            email = request.cookies.get('email')
            with connection.cursor() as cursor:
                passw = ''.join(random.choices(string.ascii_lowercase+string.digits, k=30))
                cursor.execute(f"select * from users where email = %(email)s and code = %(code)s limit 1", {"code": code, "email": email})
                us = cursor.fetchone()
                if us is None:
                    re = RedirectResponse(url="/?error_auth=true", status_code=status.HTTP_303_SEE_OTHER)
                    return re
                else:
                    cursor.execute(f"update users set pass = %(pass)s where email = %(email)s", {"pass": passw, "email": email})
                    connection.commit()
                    re = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
                    re.set_cookie(key="id", value=us[2])
                    re.set_cookie(key="pass", value=passw)
                    re.delete_cookie("email")
                    return re
        except Exception as ex:
            print(ex)
            return JSONResponse(status_code=200, content={"result": "error", "text_error": ex})

except Exception as ex:
    print(ex)