from flask import Flask, render_template, redirect, url_for, flash, jsonify, session, request, current_app, send_from_directory
from flask_wtf import FlaskForm
from flask_session import Session
from flask_paginate import Pagination, get_page_args
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import mysqlDB as msq
import secrets
from datetime import datetime
import requests
import random
import json
import html
from markupsafe import Markup
import urllib.parse
import logging

from end_1 import decode_integer, encode_string

app = Flask(__name__)
msq.init_app(app)
app.config['PER_PAGE'] = 6  # Określa liczbę elementów na stronie
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'  # Możesz wybrać inny backend, np. 'redis', 'sqlalchemy', itp.
Session(app)

def getLangText(text, dest="en", source="pl"):
    if not text:
        return text
    # bezpiecznik: nie tłumacz "ścian"
    if len(text) > 8000:
        return text
    try:
        r = requests.post(
            "http://127.0.0.1:5055/translate",
            json={"text": text, "source": source, "target": dest, "format": "text"},
            timeout=(2, 8),
        )
        r.raise_for_status()
        return r.json().get("text", text)
    except Exception as e:
        print(f"Exception Error: {e}")
        return text

def format_date(date_input, pl=True):
    ang_pol = {
        'January': 'styczeń',
        'February': 'luty',
        'March': 'marzec',
        'April': 'kwiecień',
        'May': 'maj',
        'June': 'czerwiec',
        'July': 'lipiec',
        'August': 'sierpień',
        'September': 'wrzesień',
        'October': 'październik',
        'November': 'listopad',
        'December': 'grudzień'
    }
    # Sprawdzenie czy data_input jest instancją stringa; jeśli nie, zakładamy, że to datetime
    if isinstance(date_input, str):
        date_object = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    else:
        # Jeśli date_input jest już obiektem datetime, używamy go bezpośrednio
        date_object = date_input

    formatted_date = date_object.strftime('%d %B %Y')
    if pl:
        for en, pl in ang_pol.items():
            formatted_date = formatted_date.replace(en, pl)

    return formatted_date

#  Funkcja pobiera dane z bazy danych 
def take_data_where_ID(key, table, id_name, ID):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
    return dump_key

def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key

def generator_specialOffert(lang='pl', status='aktywna'): # status='aktywna', 'nieaktywna', 'wszystkie'
    took_specOffer = take_data_table('*', 'OfertySpecjalne')
    
    specOffer = []
    for data in took_specOffer:
        try: fotoList = take_data_where_ID('*', 'ZdjeciaOfert', 'ID', data[7])[0][1:-1]
        except IndexError: fotoList = []

        gps_json = {}
        try:
            if data[29] is not None:
                gps_json = json.loads(data[29])
                {"latitude": 52.229676, "longitude": 21.012229}
                "https://earth.google.com/web/@52.25242614,20.83096693,100.96310044a,116.2153688d,35y,0h,0t,0r/data=OgMKATA" # nowrmal
                "https://earth.google.com/web/@52.25250876,20.83139622,102.83373871a,0d,60y,333.15344169h,86.56713379t,0r" # 3D
            else: raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
        except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
        except TypeError as e: print(f"Błąd typu danych: {e}")
        except Exception as e: print(f"Nieoczekiwany błąd: {e}")

            
        opis_json = {}
        try:
            if data[2] is not None: opis_json = json.loads(data[2])
            else: raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
        except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
        except TypeError as e: print(f"Błąd typu danych: {e}")
        except Exception as e: print(f"Nieoczekiwany błąd: {e}")

        theme = {
            'ID': int(data[0]),
            'Tytul': data[1] if lang=='pl' else getLangText(data[1]),
            'Opis': opis_json,
            'Cena': data[3],
            'Lokalizacja': data[4],
            'LiczbaPokoi': 0 if data[5] is None else data[5],
            'Metraz': 0 if data[6] is None else data[6],
            'Zdjecia': [foto for foto in fotoList if foto is not None],
            'Status': data[8], #ENUM('aktywna', 'nieaktywna'): Używam typu ENUM do określenia statusu oferty. To sprawia, że tylko wartości 'aktywna' i 'nieaktywna' są dozwolone w tej kolumnie.
            'Rodzaj': data[9] if lang=='pl' else getLangText(data[8]),
            'DataRozpoczecia': None if data[10] is None else format_date(data[10]),
            'DataZakonczenia': None if data[11] is None else format_date(data[11]),
            'DataUtworzenia': None if data[12] is None else format_date(data[12]),
            'DataAktualizacji': None if data[13] is None else format_date(data[13]),
            'Kaucja': 0 if data[14] is None else data[14],
            'Czynsz': 0 if data[15] is None else data[15],
            'Umeblowanie': '' if data[16] is None else data[16],
            'LiczbaPieter': 0 if data[17] is None else data[17],
            'PowierzchniaDzialki': 0 if data[18] is None else data[18],
            'TechBudowy': '' if data[19] is None else data[19],
            'FormaKuchni': '' if data[20] is None else data[20],
            'TypDomu': '' if data[21] is None else data[21],
            'StanWykonczenia': '' if data[22] is None else data[22],
            'RokBudowy': 0 if data[23] is None else data[23],
            'NumerKW': '' if data[24] is None else data[24],
            'InformacjeDodatkowe': '' if data[25] is None else data[25],
            'Rynek': '' if data[26] is None else data[26],
            'PrzeznaczenieLokalu': '' if data[27] is None else data[27],
            'Poziom': 'None' if data[28] is None else data[28],
            'GPS': gps_json,
            'TelefonKontaktowy': '' if data[30] is None else data[30],
            'EmailKontaktowy': '' if data[31] is None else data[31]
        }

        if status == 'aktywna' or status == 'nieaktywna':
            if data[8] == status:
                specOffer.append(theme)
        if status == 'wszystkie':
            specOffer.append(theme)
    return specOffer

def generator_rentOffert(lang='pl'): # status='aktywna', 'nieaktywna', 'wszystkie'
    took_rentOffer = take_data_where_ID('*', 'OfertyNajmu', 'StatusOferty', 1)
    
    rentOffer = []
    for data in took_rentOffer:
        try: fotoList = take_data_where_ID('*', 'ZdjeciaOfert', 'ID', data[8])[0][1:-1]
        except IndexError: fotoList = []
        
        gps_json = {}
        try:
            if data[27] is not None: gps_json = json.loads(data[27])
            else: raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
        except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
        except TypeError as e: print(f"Błąd typu danych: {e}")
        except Exception as e: print(f"Nieoczekiwany błąd: {e}")

        opis_json = {}
        try:
            if data[2] is not None:
                opis_json = json.loads(data[2])
            else: raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
        except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
        except TypeError as e: print(f"Błąd typu danych: {e}")
        except Exception as e: print(f"Nieoczekiwany błąd: {e}")
        
            

        theme = {
            'ID': int(data[0]),
            'Tytul': data[1] if lang=='pl' else getLangText(data[1]),
            'Opis': opis_json,
            'Cena': data[3],
            'Kaucja': 0 if data[4] is None else data[4],
            'Lokalizacja': data[5],
            'LiczbaPokoi': 0 if data[6] is None else data[6],
            'Metraz': 0 if data[7] is None else data[7],
            'Zdjecia': [foto for foto in fotoList if foto is not None],
            'DataPublikacjiOlx': None if data[9] is None else format_date(data[9]),
            'DataPublikacjiAllegro': None if data[10] is None else format_date(data[10]),
            'DataPublikacjiOtoDom': None if data[11] is None else format_date(data[11]),
            'DataPublikacjiMarketplace': None if data[12] is None else format_date(data[12]),
            'DataUtworzenia': format_date(data[13]),
            'DataAktualizacji': format_date(data[14]),
            'RodzajZabudowy': '' if data[15] is None else data[15],
            'Czynsz': 0.00 if data[16] is None else data[16],
            'Umeblowanie': '' if data[17] is None else data[17],
            'LiczbaPieter': 0 if data[18] is None else data[18],
            'PowierzchniaDzialki': 0.00 if data[19] is None else data[19],
            'TechBudowy': '' if data[20] is None else data[20],
            'FormaKuchni': '' if data[21] is None else data[21],
            'TypDomu': data[22],
            'StanWykonczenia': '' if data[23] is None else data[23],
            'RokBudowy': 0 if data[24] is None else data[24],
            'NumerKW': '' if data[25] is None else data[25],
            'InformacjeDodatkowe': '' if data[26] is None else data[26],
            'GPS': gps_json,
            'TelefonKontaktowy': '' if data[28] is None else data[28],
            'EmailKontaktowy': '' if data[29] is None else data[29],
            'StatusOferty': 0 if data[30] is None else data[30]
        }

        rentOffer.append(theme)

    return rentOffer

def rentOffer_where_ID(idOffer, lang='pl'): #
    try: data = take_data_where_ID('*', 'OfertyNajmu', 'ID', idOffer)[0]
    except IndexError: return {}

    try: fotoList = take_data_where_ID('*', 'ZdjeciaOfert', 'ID', data[8])[0][1:-1]
    except IndexError: fotoList = []

    gps_json = {}
    try:
        if data[27] is not None:
            gps_json = json.loads(data[27])
        else:
            raise ValueError("Dane są None, nie można przetworzyć JSON")
    except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
    except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
    except TypeError as e: print(f"Błąd typu danych: {e}")
    except Exception as e: print(f"Nieoczekiwany błąd: {e}")

    opis_json = {}
    try:
        if data[2] is not None:
            opis_json = json.loads(data[2])
        else: raise ValueError("Dane są None, nie można przetworzyć JSON")
    except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
    except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
    except TypeError as e: print(f"Błąd typu danych: {e}")
    except Exception as e: print(f"Nieoczekiwany błąd: {e}")

    theme = {
        'ID': int(data[0]),
        'Tytul': data[1] if lang=='pl' else getLangText(data[1]),
        'Opis': opis_json,
        'Cena': data[3],
        'Kaucja': 0 if data[4] is None else data[4],
        'Lokalizacja': data[5],
        'LiczbaPokoi': 0 if data[6] is None else data[6],
        'Metraz': 0 if data[7] is None else data[7],
        'Zdjecia': [foto for foto in fotoList if foto is not None],
        'DataPublikacjiOlx': None if data[9] is None else format_date(data[9]),
        'DataPublikacjiAllegro': None if data[10] is None else format_date(data[10]),
        'DataPublikacjiOtoDom': None if data[11] is None else format_date(data[11]),
        'DataPublikacjiMarketplace': None if data[12] is None else format_date(data[12]),
        'DataUtworzenia': format_date(data[13]),
        'DataAktualizacji': format_date(data[14]),
        'RodzajZabudowy': '' if data[15] is None else data[15],
        'Czynsz': 0.00 if data[16] is None else data[16],
        'Umeblowanie': '' if data[17] is None else data[17],
        'LiczbaPieter': 0 if data[18] is None else data[18],
        'PowierzchniaDzialki': 0.00 if data[19] is None else data[19],
        'TechBudowy': '' if data[20] is None else data[20],
        'FormaKuchni': '' if data[21] is None else data[21],
        'TypDomu': data[22],
        'StanWykonczenia': '' if data[23] is None else data[23],
        'RokBudowy': 0 if data[24] is None else data[24],
        'NumerKW': '' if data[25] is None else data[25],
        'InformacjeDodatkowe': '' if data[26] is None else data[26],
        'GPS': gps_json,
        'TelefonKontaktowy': '' if data[28] is None else data[28],
        'EmailKontaktowy': '' if data[29] is None else data[29],
        'StatusOferty': 0 if data[30] is None else data[30]
    }
    if theme['StatusOferty'] == 0:
        return None
    return theme

def generator_sellOffert(lang='pl'): # status='aktywna', 'nieaktywna', 'wszystkie'
    took_rentOffer = take_data_where_ID('*', 'OfertySprzedazy', 'StatusOferty', 1)
    
    rentOffer = []
    for data in took_rentOffer:
        try: fotoList = take_data_where_ID('*', 'ZdjeciaOfert', 'ID', data[9])[0][1:-1]
        except IndexError: fotoList = []

        gps_json = {}
        try:
            if data[27] is not None: gps_json = json.loads(data[28])
            else: raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
        except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
        except TypeError as e: print(f"Błąd typu danych: {e}")
        except Exception as e: print(f"Nieoczekiwany błąd: {e}")

        opis_json = {}
        try:
            if data[4] is not None:
                opis_json = json.loads(data[4])
            else: raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
        except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
        except TypeError as e: print(f"Błąd typu danych: {e}")
        except Exception as e: print(f"Nieoczekiwany błąd: {e}")

        theme = {
            'ID': int(data[0]),
            'TypNieruchomosci': data[1] if lang=='pl' else getLangText(data[1]),
            'Tytul': data[2] if lang=='pl' else getLangText(data[2]),
            'Rodzaj': data[3] if data[3] is not None and lang == 'pl' else getLangText(data[3]) if data[3] is not None else '',
            'Opis': opis_json,
            'Cena': data[5],
            'Lokalizacja': data[6],
            'LiczbaPokoi': 0 if data[7] is None else data[7],
            'Metraz': 0 if data[8] is None else data[8],
            'Zdjecia': [foto for foto in fotoList if foto is not None],
            'DataPublikacjiOlx': None if data[10] is None else format_date(data[10]),#
            'DataPublikacjiAllegro': None if data[11] is None else format_date(data[11]),#
            'DataPublikacjiOtoDom': None if data[12] is None else format_date(data[12]),#
            'DataPublikacjiMarketplace': None if data[13] is None else format_date(data[13]),#
            'DataUtworzenia': format_date(data[14]),
            'DataAktualizacji': format_date(data[15]),
            'RodzajZabudowy': '' if data[16] is None else data[16],
            'Rynek': '' if data[17] is None else data[17],
            'LiczbaPieter': 0 if data[18] is None else data[18],
            'PrzeznaczenieLokalu': '' if data[19] is None else data[19],
            'Poziom': 'None' if data[20] is None else data[20],
            'TechBudowy': '' if data[21] is None else data[21],
            'FormaKuchni': '' if data[22] is None else data[22],
            'TypDomu': data[23],
            'StanWykonczenia': '' if data[24] is None else data[24],
            'RokBudowy': 0 if data[25] is None else data[25],
            'NumerKW': '' if data[26] is None else data[26],
            'InformacjeDodatkowe': '' if data[27] is None else data[27],
            'GPS': gps_json,
            'TelefonKontaktowy': '' if data[29] is None else data[29],
            'EmailKontaktowy': '' if data[30] is None else data[30],
            'StatusOferty': 0 if data[31] is None else data[31]
        }

        rentOffer.append(theme)

    return rentOffer

def sellOffer_where_ID(idOffer, lang='pl'): #
    try: data = take_data_where_ID('*', 'OfertySprzedazy', 'ID', idOffer)[0]
    except IndexError: return {}

    gps_json = {}

    try: fotoList = take_data_where_ID('*', 'ZdjeciaOfert', 'ID', data[9])[0][1:-1]
    except IndexError: fotoList = []

    try:
        if data[27] is not None: gps_json = json.loads(data[28])
        else: raise ValueError("Dane są None, nie można przetworzyć JSON")
    except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
    except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
    except TypeError as e: print(f"Błąd typu danych: {e}")
    except Exception as e: print(f"Nieoczekiwany błąd: {e}")

    opis_json = {}
    try:
        if data[4] is not None: opis_json = json.loads(data[4])
        else: raise ValueError("Dane są None, nie można przetworzyć JSON")
    except json.JSONDecodeError: print("Błąd: Podane dane nie są poprawnym JSON-em")
    except IndexError: print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
    except TypeError as e: print(f"Błąd typu danych: {e}")
    except Exception as e: print(f"Nieoczekiwany błąd: {e}")

    theme = {
        'ID': int(data[0]),
        'TypNieruchomosci': data[1] if lang=='pl' else getLangText(data[1]),
        'Tytul': data[2] if lang=='pl' else getLangText(data[2]),
        'Rodzaj': data[3] if data[3] is not None and lang == 'pl' else getLangText(data[3]) if data[3] is not None else '',
        'Opis': opis_json,
        'Cena': data[5],
        'Lokalizacja': data[6],
        'LiczbaPokoi': 0 if data[7] is None else data[7],
        'Metraz': 0 if data[8] is None else data[8],
        'Zdjecia': [foto for foto in fotoList if foto is not None],
        'DataPublikacjiOlx': None if data[10] is None else format_date(data[10]),#
        'DataPubkacjiOtoDom': None if data[12] is None else format_date(data[12]),#
        'DataPublilikacjiAllegro': None if data[11] is None else format_date(data[11]),#
        'DataPublikacjiMarketplace': None if data[13] is None else format_date(data[13]),#
        'DataUtworzenia': format_date(data[14]),
        'DataAktualizacji': format_date(data[15]),
        'RodzajZabudowy': '' if data[16] is None else data[16],
        'Rynek': '' if data[17] is None else data[17],
        'LiczbaPieter': 0 if data[18] is None else data[18],
        'PrzeznaczenieLokalu': '' if data[19] is None else data[19],
        'Poziom': 'None' if data[20] is None else data[20],
        'TechBudowy': '' if data[21] is None else data[21],
        'FormaKuchni': '' if data[22] is None else data[22],
        'TypDomu': data[23],
        'StanWykonczenia': '' if data[24] is None else data[24],
        'RokBudowy': 0 if data[25] is None else data[25],
        'NumerKW': '' if data[26] is None else data[26],
        'InformacjeDodatkowe': '' if data[27] is None else data[27],
        'GPS': gps_json,
        'TelefonKontaktowy': '' if data[29] is None else data[29],
        'EmailKontaktowy': '' if data[30] is None else data[30],
        'StatusOferty': 0 if data[31] is None else data[31]
    }
    if theme['StatusOferty'] == 0:
        return None
    return theme

def generator_teamDB(lang='pl'):
    took_teamD = take_data_table('*', 'workers_team')
    teamData = []
    for data in took_teamD:
        theme = {
            'ID': int(data[0]),
            'EMPLOYEE_PHOTO': data[1],
            'EMPLOYEE_NAME': data[2],
            'EMPLOYEE_ROLE': data[3] if lang=='pl' else getLangText(data[3]),
            'EMPLOYEE_DEPARTMENT': data[4],
            'PHONE':'' if data[5] is None else data[5],
            'EMAIL': '' if data[6] is None else data[6],
            'FACEBOOK': '' if data[7] is None else data[7],
            'LINKEDIN': '' if data[8] is None else data[8],
            'DATE_TIME': data[9],
            'STATUS': int(data[10])
        }
        # dostosowane dla dmd inwestycje
        if data[4] == 'dmd inwestycje':
            teamData.append(theme)
    return teamData

def generator_subsDataDB():
    subsData = []
    took_subsD = take_data_table('*', 'newsletter')
    for data in took_subsD:
        if data[4] != 1: continue
        ID = data[0]
        theme = {
            'id': ID, 
            'email':data[2],
            'name':data[1], 
            'status': str(data[4]), 
            }
        subsData.append(theme)
    return subsData

def _blog_rows(limit=None, post_id=None, detailed=False, offset=0):
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('offset must be a non-negative integer')
    if offset and limit is None:
        raise ValueError('offset requires a limit')
    columns = [
        ('p.ID', 'post_id'), ('c.ID', 'id'), ('c.TITLE', 'title'),
        ('c.HIGHLIGHTS', 'highlight'), ('c.HEADER_FOTO', 'mainFoto'),
        ('c.CATEGORY', 'category'), ('c.DATE_TIME', 'data'),
        ('a.NAME_AUTHOR', 'author'),
    ]
    if detailed:
        columns += [
            ('c.CONTENT_MAIN', 'introduction'), ('c.CONTENT_FOTO', 'contentFoto'),
            ('c.BULLETS', 'additionalList'), ('c.TAGS', 'tags'),
            ('a.ABOUT_AUTHOR', 'author_about'), ('a.AVATAR_AUTHOR', 'author_avatar'),
            ('a.FACEBOOK', 'author_facebook'), ('a.TWITER_X', 'author_twitter'),
            ('a.INSTAGRAM', 'author_instagram'),
        ]
    query = 'SELECT ' + ', '.join(column for column, _ in columns)
    query += """
        FROM blog_posts p
        LEFT JOIN contents c ON c.ID = p.CONTENT_ID
        LEFT JOIN authors a ON a.ID = p.AUTHOR_ID
    """
    params = []
    if post_id is not None:
        query += ' WHERE p.ID = %s'
        params.append(post_id)
    query += ' ORDER BY p.ID DESC'
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ValueError('limit must be a non-negative integer')
        query += ' LIMIT %s'
        params.append(limit)
        if offset:
            query += ' OFFSET %s'
            params.append(offset)
    rows = msq.safe_connect_to_database(query, tuple(params))
    return [dict(zip((key for _, key in columns), row)) for row in rows]


def _blog_theme(row, lang):
    theme = {key: value for key, value in row.items() if key != 'post_id'}
    if lang != 'pl':
        for key in ('title', 'highlight', 'category', 'introduction',
                    'additionalList', 'tags', 'author_about'):
            if key in theme:
                theme[key] = getLangText(theme[key])
    theme['data'] = format_date(theme['data'], lang == 'pl')
    if 'additionalList' in theme:
        bullets = str(theme['additionalList'])
        if lang != 'pl':
            bullets = bullets.replace('#SPLX#', '#splx#')
        theme['additionalList'] = bullets.split('#splx#')
        theme['tags'] = str(theme['tags']).split(', ')
    return theme


def _blog_details(lang='pl', post_id=None):
    rows = _blog_rows(post_id=post_id, detailed=True)
    if not rows:
        return []
    # Fetch comments and their authors once for the whole selected collection.
    query = """
        SELECT com.*, n.CLIENT_NAME, n.CLIENT_EMAIL, n.AVATAR_USER
        FROM comments com
        JOIN blog_posts p ON p.ID = com.BLOG_POST_ID
        LEFT JOIN newsletter n ON n.ID = com.AUTHOR_OF_COMMENT_ID
    """
    params = ()
    if post_id is not None:
        query += ' WHERE p.ID = %s'
        params = (post_id,)
    query += ' ORDER BY com.ID'
    comments = {}
    for com in msq.safe_connect_to_database(query, params):
        post_comments = comments.setdefault(com[1], {})
        post_comments[len(post_comments)] = {
            'id': com[0],
            'message': com[2] if lang == 'pl' else getLangText(com[2]),
            'user': com[-3], 'e-mail': com[-2], 'avatar': com[-1],
            'data-time': format_date(com[4], lang == 'pl'),
        }
    result = []
    for row in rows:
        theme = _blog_theme(row, lang)
        theme['comments'] = comments.get(row['post_id'], {})
        result.append(theme)
    return result


def generator_daneDBList(lang='pl'):
    return _blog_details(lang)


def generator_daneDBList_short(lang='pl', limit=None, offset=0):
    # Unlimited by default: the home page explicitly requests only three rows.
    return [_blog_theme(row, lang) for row in _blog_rows(limit=limit, offset=offset)]


def _blog_count():
    rows = msq.connect_to_database('SELECT COUNT(*) FROM blog_posts')
    return rows[0][0] if rows else 0


def generator_daneDBList_prev_next(main_id):
    rows = msq.safe_connect_to_database("""
        SELECT
            (SELECT MIN(ID) FROM blog_posts WHERE ID > %s),
            (SELECT MAX(ID) FROM blog_posts WHERE ID < %s)
        FROM blog_posts WHERE ID = %s
    """, (main_id, main_id, main_id))
    return dict(zip(('prev', 'next'), rows[0])) if rows else {'prev': None, 'next': None}


def generator_daneDBList_cetegory():
    took_allPost = msq.connect_to_database('SELECT CATEGORY FROM contents ORDER BY ID DESC;')
    cat_count = {}
    for (category,) in took_allPost:
        cat_count[category] = cat_count.get(category, 0) + 1
    return [f"{cat} ({count})" for cat, count in cat_count.items()], cat_count


def generator_daneDBList_RecentPosts(main_id, amount=3):
    # Preserve the existing random selection of suggested posts.
    rows = msq.safe_connect_to_database(
        'SELECT ID FROM contents WHERE ID != %s ORDER BY ID DESC', (main_id,))
    ids = [row[0] for row in rows]
    return random.sample(ids, min(amount, len(ids)))


def generator_daneDBList_one_post_id(id_post, lang='pl'):
    return _blog_details(lang, post_id=id_post)


def generator_daneDBList_3(lang='en'):
    posts = []
    for row in _blog_rows(limit=3):
        theme = _blog_theme(row, lang)
        # This legacy footer helper has always used English dates.
        theme['data'] = format_date(row['data'], False)
        posts.append({key: theme[key] for key in ('id', 'title', 'category', 'data', 'author')})
    return posts


def smart_truncate(content, length=200):
    if len(content) <= length:
        return content
    else:
        # Znajdujemy miejsce, gdzie jest koniec pełnego słowa, nie przekraczając maksymalnej długości
        truncated_content = content[:length].rsplit(' ', 1)[0]
        return f"{truncated_content}..."

############################
##      ######           ###
##      ######           ###
##     ####              ###
##     ####              ###
##    ####               ###
##    ####               ###
##   ####                ###
##   ####                ###
#####                    ###
#####                    ###
##   ####                ###
##   ####                ###
##    ####               ###
##    ####               ###
##     ####              ###
##     ####              ###
##      ######           ###
##      ######           ###
############################


logFileName = '/home/johndoe/app/dmdinwestycje/logs/access.log'  # 🔁 ZMIENIAJ dla każdej aplikacji

# Konfiguracja loggera
logging.basicConfig(filename=logFileName, level=logging.INFO,
                    format='%(asctime)s - %(message)s', filemode='a')

# Funkcja do logowania informacji o zapytaniu
def log_request():
    ip_address = request.remote_addr
    date_time = datetime.now()
    endpoint = request.endpoint or request.path  # fallback jeśli brak endpointu
    method = request.method

    logging.info(f'IP: {ip_address}, Time: {date_time}, Endpoint: {endpoint}, Method: {method}')

@app.before_request
def before_request_logging():
    log_request()


# @app.route('/.well-known/pki-validation/certum.txt')
# def download_file():
#     return send_from_directory(app.root_path, 'certum.txt')

@app.template_filter()
def decode_html_entities_filter(text):
    return html.unescape(text)

@app.template_filter()
def update_new_line_chars(text: str):
    text = text.replace('\r\n', '<br>')  # najpierw standard Windows
    text = text.replace('\n', '<br>')  # potem standard Unix/Linux
    return Markup(html.unescape(text))

@app.route('/')
def index():
    session['page'] = 'index'
    pageTitle = 'Strona Główna'

    if f'TEAM-ALL' not in session:
        team_list = generator_teamDB()
        session[f'TEAM-ALL'] = team_list
    else:
        team_list = session[f'TEAM-ALL']

    fourListTeam = []
    for i, member in enumerate(team_list):
        if  i < 4: fourListTeam.append(member)
        
    if f'BLOG-SHORT' not in session:
        blog_post = generator_daneDBList_short(limit=3)
        session[f'BLOG-SHORT'] = blog_post
    else:
        blog_post = session[f'BLOG-SHORT']
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    try:
        spcOfferON = True 
        secOffers = generator_specialOffert()[0]
        session['spcOfferON']=spcOfferON
    except IndexError: 
        spcOfferON = False
        secOffers = {}
        session['spcOfferON']=spcOfferON


    if spcOfferON:
        if "latitude" in secOffers['GPS'] and "longitude" in secOffers['GPS']:
            lat = secOffers['GPS']["latitude"]
            lon = secOffers['GPS']["longitude"]
        else:
            lat = 'None'
            lon = 'None'
    else:
            lat = 'None'
            lon = 'None'

    try: mainFoto = secOffers['Zdjecia'][0]
    except IndexError: mainFoto = ''
    except KeyError: mainFoto = ''

    rentOffer = generator_rentOffert()
    categoryOffer = {}
    categoryOffer['wynajem'] = '.Class_rentOffer_All'
    categoryOffer['sprzedaż'] = '.Class_sellOffer_All'
    for i, offerData in enumerate(rentOffer):
        try: 
            categoryOffer[offerData['TypDomu'].lower()] 
        except KeyError:
            categoryOffer[offerData['TypDomu'].lower()] = f'.Class_rentOffer_{i}'

    

    detailOffer = []
    for offerData in rentOffer:
        offerData['class'] = categoryOffer[offerData['TypDomu'].lower()][1:] + ' Class_rentOffer_All'
        
        try: mainFotorent = offerData['Zdjecia'][0]
        except IndexError: mainFotorent = ''
        except KeyError: mainFotorent = ''
        offerData['mainFoto'] = mainFotorent
        offerData['link'] = '/oferta-najmu-details?offerid='+str(offerData['ID'])
        offerData['oferta'] = 'Na Wynajem'
        detailOffer.append(offerData)

    sellOffer = generator_sellOffert()
    for i, offerData in enumerate(sellOffer):
        try: 
            categoryOffer[offerData['TypNieruchomosci'].lower()] 
        except KeyError:
            categoryOffer[offerData['TypNieruchomosci'].lower()] = f'.Class_sellOffer_{i}'

    

    for offerData in sellOffer:
        offerData['class'] = categoryOffer[offerData['TypNieruchomosci'].lower()][1:] + ' Class_sellOffer_All'
        try: mainFotosell = offerData['Zdjecia'][0]
        except IndexError: mainFotosell = ''
        except KeyError: mainFotosell = ''
        offerData['mainFoto'] = mainFotosell
        offerData['link'] = '/oferta-sprzedazy-details?offerid='+str(offerData['ID'])
        offerData['oferta'] = 'Na Sprzedaż'
        detailOffer.append(offerData)


    return render_template(
        f'index.html', 
        pageTitle=pageTitle,
        spcOfferON=spcOfferON,
        fourListTeam=fourListTeam, 
        blog_post_three=blog_post_three,
        coordinates=[lat, lon],
        mainFoto=mainFoto,
        secOffers=secOffers,
        categoryOffer=categoryOffer,
        detailOffer=detailOffer
        )

@app.route('/oferta-inwestycyjna')
def ofertaInwestycyjna():
    session['page'] = 'ofertaInwestycyjna'
    pageTitle = 'Oferta Inwestycyjna'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            session['spcOfferON']=spcOfferON

    return render_template(
        f'ofertaInwestycyjna.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/oferta-najmu')
def ofertaNajmu():
    session['page'] = 'ofertaNajmu'
    pageTitle = 'Oferta Najmu'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            session['spcOfferON']=spcOfferON

    rentOffer = generator_rentOffert()
    categoryOffer = {}
    for i, offerData in enumerate(rentOffer):
        try: 
            categoryOffer[offerData['TypDomu'].lower()] 
        except KeyError:
            categoryOffer[offerData['TypDomu'].lower()] = f'.Class_Offer_{i}'
    detailOffer = []
    for offerData in rentOffer:
        offerData['class'] = categoryOffer[offerData['TypDomu'].lower()][1:]
        
        try: mainFoto = offerData['Zdjecia'][0]
        except IndexError: mainFoto = ''
        except KeyError: mainFoto = ''
        offerData['mainFoto'] = mainFoto
        detailOffer.append(offerData)



    return render_template(
        f'ofertaNajmu.html',
        pageTitle=pageTitle,
        categoryOffer=categoryOffer,
        detailOffer=detailOffer,
        spcOfferON=session['spcOfferON']
        )

@app.route('/oferta-najmu-details', methods=['GET'])
def ofertaNajmuDetails():
    session['page'] = 'ofertaNajmu'
    pageTitle = 'Oferta Najmu'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            session['spcOfferON']=spcOfferON

    if 'offerid' in request.args:
        idOffer = request.args.get('offerid')
    else:
        idOffer = None

    if idOffer:
        try: 
            rentOffers = rentOffer_where_ID(idOffer) #take_data_where_ID('*', 'OfertyNajmu', 'ID', idOffer)[0]
            rentOffers['StatusOferty']

        except IndexError: rentOffers = {
                'ID': 0, 'Tytul': 'Brak danych!', 'Opis': 'Brak danych!', 'Cena': 'Brak danych!', 'Kaucja': 'Brak danych!',
                'Lokalizacja': 'Brak danych!','LiczbaPokoi': 'Brak danych!', 'Metraz': 'Brak danych!', 'Zdjecia': [],
                'DataPublikacjiOlx': 'Brak danych!','DataPublikacjiAllegro': 'Brak danych!','DataPublikacjiOtoDom': 'Brak danych!',
                'DataPublikacjiMarketplace': 'Brak danych!', 'DataUtworzenia': 'Brak danych!', 'DataAktualizacji': 'Brak danych!',
                'RodzajZabudowy': 'Brak danych!', 'Czynsz': 'Brak danych!', 'Umeblowanie': 'Brak danych!', 'LiczbaPieter': 'Brak danych!',
                'PowierzchniaDzialki': 'Brak danych!', 'TechBudowy': 'Brak danych!', 'FormaKuchni': 'Brak danych!', 'TypDomu': 'Brak danych!',
                'StanWykonczenia': 'Brak danych!', 'RokBudowy': 'Brak danych!', 'NumerKW': 'Brak danych!', 'InformacjeDodatkowe': 'Brak danych!',
                'GPS': {}, 'TelefonKontaktowy': 'Brak danych!', 'EmailKontaktowy': 'Brak danych!'
            }
        except KeyError:
            return redirect(url_for('ofertaNajmu'))
        except TypeError:
            return redirect(url_for('ofertaNajmu'))

        if "latitude" in rentOffers['GPS'] and "longitude" in rentOffers['GPS']:
            lat = rentOffers['GPS']["latitude"]
            lon = rentOffers['GPS']["longitude"]
        else:
            lat = 'None'
            lon = 'None'

        try: mainFoto = rentOffers['Zdjecia'][0]
        except IndexError: mainFoto = ''
        except KeyError: mainFoto = ''

    return render_template(
        f'ofertaNajmuDetails.html',
        pageTitle=pageTitle,
        coordinates=[lat, lon],
        mainFoto=mainFoto,
        rentOffers=rentOffers,
        spcOfferON=session['spcOfferON']
        )

@app.route('/oferta-sprzedazy')
def ofertaSprzedazy():
    session['page'] = 'ofertaSprzedazy'
    pageTitle = 'Oferta Sprzedaży'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            session['spcOfferON']=spcOfferON

    sellOffer = generator_sellOffert()
    categoryOffer = {}
    for i, offerData in enumerate(sellOffer):
        try: 
            categoryOffer[offerData['TypNieruchomosci'].lower()] 
        except KeyError:
            categoryOffer[offerData['TypNieruchomosci'].lower()] = f'.Class_sellOffer_{i}'
    detailOffer = []
    for offerData in sellOffer:
        offerData['class'] = categoryOffer[offerData['TypNieruchomosci'].lower()][1:]
        try: mainFoto = offerData['Zdjecia'][0]
        except IndexError: mainFoto = ''
        except KeyError: mainFoto = ''
        offerData['mainFoto'] = mainFoto
        detailOffer.append(offerData)

    

    return render_template(
        f'ofertaSprzedazy.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON'],
        categoryOffer=categoryOffer,
        detailOffer=detailOffer
        )

@app.route('/oferta-sprzedazy-details', methods=['GET'])
def ofertaSprzedazyDetails():
    session['page'] = 'ofertaSprzedazy'
    pageTitle = 'Oferta Sprzedaży'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            session['spcOfferON']=spcOfferON

    if 'offerid' in request.args:
        idOffer = request.args.get('offerid')
    else:
        idOffer = None

    if idOffer:
        try: 
            sellOffers = sellOffer_where_ID(idOffer) #take_data_where_ID('*', 'OfertyNajmu', 'ID', idOffer)[0]
            sellOffers['StatusOferty']
        except IndexError: sellOffers = {
                'ID': 0, 'Tytul': 'Brak danych!', 'Opis': 'Brak danych!', 'Cena': 'Brak danych!', 'Kaucja': 'Brak danych!',
                'Lokalizacja': 'Brak danych!','LiczbaPokoi': 'Brak danych!', 'Metraz': 'Brak danych!', 'Zdjecia': [],
                'DataPublikacjiOlx': 'Brak danych!','DataPublikacjiAllegro': 'Brak danych!','DataPublikacjiOtoDom': 'Brak danych!',
                'DataPublikacjiMarketplace': 'Brak danych!', 'DataUtworzenia': 'Brak danych!', 'DataAktualizacji': 'Brak danych!',
                'RodzajZabudowy': 'Brak danych!', 'Czynsz': 'Brak danych!', 'Umeblowanie': 'Brak danych!', 'LiczbaPieter': 'Brak danych!',
                'PowierzchniaDzialki': 'Brak danych!', 'TechBudowy': 'Brak danych!', 'FormaKuchni': 'Brak danych!', 'TypDomu': 'Brak danych!',
                'StanWykonczenia': 'Brak danych!', 'RokBudowy': 'Brak danych!', 'NumerKW': 'Brak danych!', 'InformacjeDodatkowe': 'Brak danych!',
                'GPS': {}, 'TelefonKontaktowy': 'Brak danych!', 'EmailKontaktowy': 'Brak danych!'
            }
        except KeyError:
            return redirect(url_for('ofertaSprzedazy'))
        except TypeError:
            return redirect(url_for('ofertaSprzedazy'))

        if "latitude" in sellOffers['GPS'] and "longitude" in sellOffers['GPS']:
            lat = sellOffers['GPS']["latitude"]
            lon = sellOffers['GPS']["longitude"]
        else:
            lat = 'None'
            lon = 'None'

        try: mainFoto = sellOffers['Zdjecia'][0]
        except IndexError: mainFoto = ''
        except KeyError: mainFoto = ''

    return render_template(
        f'ofertaSprzedazyDetails.html',
        pageTitle=pageTitle,
        coordinates=[lat, lon],
        mainFoto=mainFoto,
        sellOffers=sellOffers,
        spcOfferON=session['spcOfferON']
        )

@app.route('/oferta-specjalna')
def ofertaSpecjalna():
    session['page'] = 'ofertaSpecjalna'
    pageTitle = 'Ofeta Specjalna'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    try: secOffers = generator_specialOffert()[0]
    except IndexError: secOffers = {
            'ID': 0,
            'Tytul': 'Brak danych o tytule',
            'Opis': 'Brak danych o opisie',
            'Cena': 'Brak danych o cenie',
            'Lokalizacja':'Brak danych o lokalizacji',
            'LiczbaPokoi': 'Brak danych!',
            'Metraz': 'Brak danych!',
            'Zdjecia': [],
            'Status': 'Brak danych!',
            'Rodzaj': 'Brak danych!',
            'DataRozpoczecia': 'Brak danych!',
            'DataZakonczenia': 'Brak danych!',
            'DataUtworzenia': 'Brak danych!',
            'DataAktualizacji': 'Brak danych!',
            'Kaucja': 'Brak danych!',
            'Czynsz': 'Brak danych!',
            'Umeblowanie': 'Brak danych!',
            'LiczbaPieter': 'Brak danych!',
            'PowierzchniaDzialki': 'Brak danych!',
            'TechBudowy': 'Brak danych!',
            'FormaKuchni': 'Brak danych!',
            'TypDomu': 'Brak danych!',
            'StanWykonczenia': 'Brak danych!',
            'RokBudowy': 'Brak danych!',
            'NumerKW': 'Brak danych!',
            'InformacjeDodatkowe': 'Brak danych!',
            'Rynek': 'Brak danych!',
            'PrzeznaczenieLokalu': 'Brak danych!',
            'Poziom': 'None',
            'GPS': {},
            'TelefonKontaktowy': 'Brak danych!',
            'EmailKontaktowy': 'Brak danych!'
        }

    if "latitude" in secOffers['GPS'] and "longitude" in secOffers['GPS']:
        lat = secOffers['GPS']["latitude"]
        lon = secOffers['GPS']["longitude"]
    else:
        lat = 'None'
        lon = 'None'

    try: mainFoto = secOffers['Zdjecia'][0]
    except IndexError: mainFoto = ''
    except KeyError: mainFoto = ''

    return render_template(
        f'ofertaSpecjalna.html',
        pcOfferON=False,
        coordinates=[lat, lon],
        pageTitle=pageTitle,
        mainFoto=mainFoto,
        secOffers=secOffers
        )

@app.route('/my-jestesmy')
def myJestesmy():
    session['page'] = 'myJestesmy'
    pageTitle = 'O nas'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'myJestesmy.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/my-zespol')
def myZespol():
    session['page'] = 'myZespol'
    pageTitle = 'Zespół'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    if f'TEAM-ALL' not in session:
        team_list = generator_teamDB()
        session[f'TEAM-ALL'] = team_list
    else:
        team_list = session[f'TEAM-ALL']

    fullListTeam = []
    for i, member in enumerate(team_list):
       fullListTeam.append(member)
    
    return render_template(
        f'myZespol.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON'],
        fullListTeam=fullListTeam
        )

@app.route('/my-partnerzy')
def myPartnerzy():
    session['page'] = 'myPartnerzy'
    pageTitle = 'Partnerzy'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'myPartnerzy.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/inwestycje-odkup')
def inwestycjeOdkup():
    session['page'] = 'inwestycjeOdkup'
    pageTitle = 'Odkup Działki'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'inwestycjeOdkup.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/inwestycje-wspolne')
def inwestycjeWspolne():
    session['page'] = 'inwestycjeWspolne'
    pageTitle = 'Inwestycja Wspólna'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'inwestycjeWspolne.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/inwestycje-pomoc')
def inwestycjePomoc():
    session['page'] = 'inwestycjePomoc'
    pageTitle = 'Pomoc Prawna'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'inwestycjePomoc.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/inwestycje-projekt')
def inwestycjeProjekt():
    session['page'] = 'inwestycjeProjekt'
    pageTitle = 'Projekt Inwestycju'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'inwestycjeProjekt.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/inwestycje-budowa')
def inwestycjeBudowa():
    session['page'] = 'inwestycjeBudowa'
    pageTitle = 'Kompleksowa Budowa'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'inwestycjeBudowa.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/inwestycje-maksymalizacja')
def inwestycjeMaksymalizacja():
    session['page'] = 'inwestycjeMaksymalizacja'
    pageTitle = 'Maksymalizacja Wartości'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'inwestycjeMaksymalizacja.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/blogs')
def blogs():
    session['page'] = 'blogs'
    pageTitle = 'Blog'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    page = max(1, page)
    per_page = max(1, per_page)
    offset = (page - 1) * per_page
    total = _blog_count()
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Fetch only the card data needed by this page, directly in SQL.
    posts = generator_daneDBList_short(limit=per_page, offset=offset)

    return render_template(
        f'blogs.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON'],
        pagination=pagination,
        posts=posts
        )

@app.route('/blog-one', methods=['GET'])
def blogOne():
    session['page'] = 'blogOne'

    if 'post' in request.args:
        post_id = request.args.get('post')
        try: post_id_int = int(post_id)
        except ValueError: return redirect(url_for('blogs'))
    else:
        return redirect(url_for(f'blogs'))
    
    choiced = generator_daneDBList_one_post_id(post_id_int)[0]
    choiced['len'] = len(choiced['comments'])

    pre_next = generator_daneDBList_prev_next(post_id_int)

    cats = generator_daneDBList_cetegory()
    cat_dict = cats[1]
    take_id_rec_pos = generator_daneDBList_RecentPosts(post_id_int)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        recentPosts.append(theme)
    
    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'blogOne.html',
        spcOfferON=session['spcOfferON'],
        choiced=choiced,
        pre_next=pre_next,
        cat_dict=cat_dict,
        recentPosts=recentPosts
        )

@app.route('/kontakt')
def kontakt():
    session['page'] = 'kontakt'
    pageTitle = 'Kontakt z Nami'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'kontakt.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/polityka-prv')
def politykaPrv():
    session['page'] = 'politykaPrv'
    pageTitle = 'Polityka prywatności'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'politykaPrv.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/rulez')
def rulez():
    session['page'] = 'rulez'
    pageTitle = 'Zasady witryny'
    
    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'rulez.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.route('/help')
def help():
    session['page'] = 'help'
    pageTitle = 'Pomoc'

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        f'help.html',
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON']
        )

@app.errorhandler(404)
def page_not_found(e):
    # Tutaj możesz przekierować do dowolnej trasy, którą chcesz wyświetlić jako stronę błędu 404.
    return redirect(url_for(f'index'))


@app.route('/find-by-category', methods=['GET'])
def findByCategory():

    query = request.args.get('category')
    if not query:
        print('Błąd requesta')
        return redirect(url_for('index'))
        
    sqlQuery = """
                SELECT ID FROM contents 
                WHERE CATEGORY LIKE %s 
                ORDER BY ID DESC;
                """
    params = (f'%{query}%', )
    results = msq.safe_connect_to_database(sqlQuery, params)
    pageTitle = f'Wyniki wyszukiwania dla categorii {query}'

    searchResults = []
    for find_id in results:
        post_id = int(find_id[0])
        t_post = generator_daneDBList_one_post_id(post_id)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'introduction': smart_truncate(t_post['introduction'], 200),
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        searchResults.append(theme)

    found = len(searchResults)

    take_id_rec_pos = generator_daneDBList_RecentPosts(0)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        recentPosts.append(theme)

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(searchResults)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = searchResults[offset: offset + per_page]

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        "searchBlog.html",
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON'],
        posts=posts,
        found=found,
        pagination=pagination,
        recentPosts=recentPosts
        )


@app.route('/search-post-blog', methods=['GET', 'POST']) #, methods=['GET', 'POST']
def searchBlog():
    if request.method == "POST":
        query = request.form["query"]
        if query == '':
            print('Błąd requesta')
            return redirect(url_for('index'))
        
        session['last_search'] = query
    elif 'last_search' in session:
        query = session['last_search']
    else:
        print('Błąd requesta')
        return redirect(url_for('index'))  # Uwaga: poprawiłem 'f' na 'index'

    sqlQuery = """
                SELECT ID FROM contents 
                WHERE TITLE LIKE %s 
                OR CONTENT_MAIN LIKE %s 
                OR HIGHLIGHTS LIKE %s 
                OR BULLETS LIKE %s 
                ORDER BY ID DESC;
                """
    params = (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
    results = msq.safe_connect_to_database(sqlQuery, params)
    pageTitle = f'Wyniki wyszukiwania dla {query}'

    searchResults = []
    for find_id in results:
        post_id = int(find_id[0])
        t_post = generator_daneDBList_one_post_id(post_id)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'introduction': smart_truncate(t_post['introduction'], 200),
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        searchResults.append(theme)

    found = len(searchResults)

    take_id_rec_pos = generator_daneDBList_RecentPosts(0)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        recentPosts.append(theme)

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(searchResults)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = searchResults[offset: offset + per_page]

    if f'spcOfferON' not in session:
        try:
            spcOfferON = True 
            secOffers = generator_specialOffert()[0]
            session['spcOfferON']=spcOfferON
        except IndexError: 
            spcOfferON = False
            secOffers = {}
            session['spcOfferON']=spcOfferON

    return render_template(
        "searchBlog.html",
        pageTitle=pageTitle,
        spcOfferON=session['spcOfferON'],
        posts=posts,
        found=found,
        pagination=pagination,
        recentPosts=recentPosts
        )


@app.route('/send-mess-pl', methods=['POST'])
def sendMess():

    if request.method == 'POST':
        form_data = request.json
        CLIENT_NAME = form_data['name']
        CLIENT_SUBJECT = form_data['subject']
        CLIENT_EMAIL = form_data['email']
        CLIENT_MESSAGE = form_data['message']

        if 'condition' not in form_data:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz zaakceptować naszą politykę prywatności!'
                })
        if CLIENT_NAME == '':
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać swoje Imię i Nazwisko!'
                })
        if CLIENT_SUBJECT == '':
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać temat wiadomości!'
                })
        if CLIENT_EMAIL == '' or '@' not in CLIENT_EMAIL or '.' not in CLIENT_EMAIL or len(CLIENT_EMAIL) < 7:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać adres email!'
                })
        if CLIENT_MESSAGE == '':
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać treść wiadomości!'
                })

        # --- meta z żądania (Flask/FastAPI) ---
        ref = request.headers.get('Referer')
        ua  = request.headers.get('User-Agent')
        # Host: w Flask jest też request.host; w FastAPI/Starlette z ASGI bywa tylko nagłówek
        host = request.headers.get('Host') or getattr(request, 'host', None)

        # Realne IP z uwzględnieniem proxy/CDN:
        xff = request.headers.get('X-Forwarded-For', '')
        ip_from_xff = xff.split(',')[0].strip() if xff else None
        ip = (request.headers.get('CF-Connecting-IP') or ip_from_xff or request.remote_addr)

        zapytanie_sql = '''
            INSERT INTO contact 
                (CLIENT_NAME, CLIENT_EMAIL, SUBJECT, MESSAGE, DONE, remote_ip, referer, user_agent, source_host) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        dane = (
            CLIENT_NAME,
            CLIENT_EMAIL,
            CLIENT_SUBJECT,
            CLIENT_MESSAGE,
            1,
            ip,
            ref,
            ua,
            host
        )
    
        if msq.insert_to_database(zapytanie_sql, dane):
            return jsonify(
                {
                    'success': True, 
                    'message': f'Wiadomość została wysłana!'
                })
        else:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Wystąpił problem z wysłaniem Twojej wiadomości, skontaktuj się w inny sposób lub spróbuj później!'
                })

    return redirect(url_for('index'))

@app.route('/add-subs-pl', methods=['POST'])
def addSubs():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

    if request.method == 'POST':
        form_data = request.json

        SUB_NAME = form_data['Imie']
        SUB_EMAIL = form_data['Email']
        USER_HASH = secrets.token_hex(20)

        allowed = True
        for subscriber in subsList:
            if subscriber['email'] == SUB_EMAIL:
                allowed = False

        if allowed:
            # --- meta z żądania (Flask/FastAPI) ---
            ref = request.headers.get('Referer')
            ua  = request.headers.get('User-Agent')
            host = request.headers.get('Host') or getattr(request, 'host', None)

            # Realne IP z uwzględnieniem proxy/CDN:
            xff = request.headers.get('X-Forwarded-For', '')
            ip_from_xff = xff.split(',')[0].strip() if xff else None
            ip = (request.headers.get('CF-Connecting-IP') or ip_from_xff or request.remote_addr)

            # (opcjonalnie) bardzo prosty anty-bot: wymagaj swojej domeny w referer + niepusty UA
            # if (not ua or not ua.strip()) or (ref and 'dmdbudownictwo.pl' not in ref):
            #     abort(403)

            zapytanie_sql = '''
                INSERT INTO newsletter 
                    (CLIENT_NAME, CLIENT_EMAIL, ACTIVE, USER_HASH, remote_ip, referer, user_agent, source_host) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            '''
            dane = (SUB_NAME, SUB_EMAIL, 0, USER_HASH, ip, ref, ua, host)
            if msq.insert_to_database(zapytanie_sql, dane):
                return jsonify(
                    {
                        'success': True, 
                        'message': f'Zgłoszenie nowego subskrybenta zostało wysłane, aktywuj przez email!'
                    })
            else:
                return jsonify(
                {
                    'success': False, 
                    'message': f'Niestety nie udało nam się zarejestrować Twojej subskrypcji z powodu niezidentyfikowanego błędu!'
                })
        else:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Podany adres email jest już zarejestrowany!'
                })
    return redirect(url_for('index'))

@app.route('/add-comm-pl', methods=['POST'])
def addComm():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

    if request.method == 'POST':
        form_data = request.json
        # print(form_data)
        SUB_ID = None
        SUB_NAME = form_data['Name']
        SUB_EMAIL = form_data['Email']
        SUB_COMMENT = form_data['Comment']
        POST_ID = form_data['id']
        allowed = False
        for subscriber in subsList:
            if subscriber['email'] == SUB_EMAIL and subscriber['name'] == SUB_NAME and int(subscriber['status']) == 1:
                allowed = True
                SUB_ID = subscriber['id']
                break
        if allowed and SUB_ID:
            # print(form_data)
            zapytanie_sql = '''
                    INSERT INTO comments 
                        (BLOG_POST_ID, COMMENT_CONNTENT, AUTHOR_OF_COMMENT_ID) 
                        VALUES (%s, %s, %s);
                    '''
            dane = (POST_ID, SUB_COMMENT, SUB_ID)
            if msq.insert_to_database(zapytanie_sql, dane):
                return jsonify({'success': True, 'message': f'Post został skomentowany!'})
        else:
            return jsonify({'success': False, 'message': f'Musisz być naszym subskrybentem żeby komentować naszego bloga!'})
    return redirect(url_for('blogs'))

# ===============================================
# ===============================================
# ===========    ENCODE PROJECT   ===============
# ===============================================
# ===============================================

@app.route('/encode', methods=['POST', 'GET'])
def receive_token():
    # print(request.args)
    token = request.args.get('token')
    print(f'Print token: {str(token)}')
    print(f'Len token: {len(str(token))}')
    
    if not token:
        return render_template("encode-project.html", errorMessage=None)

    # print(request.method)
    if request.method == 'POST':
        form_data = request.form.to_dict()
        if form_data["advancedToken"] != '':
            token = form_data["advancedToken"]
        # print([token], form_data)
        decoded_data = decode_integer(token, form_data['pinCode'])
        # print([token], form_data, decoded_data)
        if 'success' in decoded_data:
            decoded_string = decoded_data.get('success')
        else:
            decoded_string_error = decoded_data.get('error')
            return render_template("encode-project.html", errorMessage=decoded_string_error)
        
        decoded_pin = decoded_data.get('PIN')
        decoded_from = decoded_data.get('FROM')
        decoded_to = decoded_data.get('TO')

        return render_template(
            "answer-project.html",
            deCodedMessage=decoded_string,
            formatCode='link',
            pinCode=decoded_pin,
            DirectWatsApp=decoded_from,
            SelftWatsApp=decoded_to
            )
    else:
        return render_template("decode-project-pin.html")


@app.route('/get-whatsapp-data', methods=['POST'])
def get_whatsapp_data():
    data = request.json
    phone = data.get("direct_whatsapp")
    pin = data.get("pin")
    from_wa = data.get("own_whatsapp")
    message = data.get("message")
    format = data.get("format")

    if '@' in phone:
        prepared_phone = phone
    else:
        prepared_phone = '+48' + str(phone).replace(' ', '')

    if '@' in from_wa:
        prepared_from_wa = from_wa
    else:
        prepared_from_wa = '+48' + str(from_wa).replace(' ', '')

    encode_message = encode_string(message, pin, auth_from=prepared_from_wa, direct_to=prepared_phone)

    if format == 'LINK':
        if '@' in phone or '@' in from_wa:
            # prepared_message = urllib.parse.quote(f'https://dmdinwestycje.pl/encode?token={encode_message["TK"]}', safe='')
            prepared_message = f'https://dmdinwestycje.pl/encode?token={encode_message["TK"]}'
        else:
            prepared_message = f'https://dmdinwestycje.pl/encode?token={encode_message["TK"]}'
    elif format == 'TOKEN':
        prepared_message = f'{encode_message["TK"]}'
    else:
        prepared_message = f'{encode_message["EI"]}'

    response_data = {
        "phone": prepared_phone,
        "message": prepared_message
    }
    return jsonify(response_data)

# @app.route('/get-whatsapp-data', methods=['POST'])
# def get_whatsapp_data():
#     data = request.json
#     # print(data)
#     phone = data.get("direct_whatsapp")
#     pin = data.get("pin")
#     from_wa = data.get("own_whatsapp")
#     message = data.get("message")
#     format = data.get("format")
#     # print(format)
#     prepared_from_wa = '+48'+str(from_wa).replace(' ', '')
#     prepared_phone = '+48'+str(phone).replace(' ', '')
#     encode_message = encode_string(message, pin, auth_from=prepared_from_wa, direct_to=prepared_phone)
#     if format == 'LINK':
#         prepared_message = f'https://dmdinwestycje.pl/encode?token={encode_message["TK"]}'
#     elif format == 'TOKEN':
#         prepared_message = f'{encode_message["TK"]}'
#     else:
#         prepared_message = f'{encode_message["EI"]}'
#     # print(prepared_message)
#     # Przetwarzanie danych (np. formatowanie wiadomości)
#     response_data = {
#         "phone": prepared_phone,
#         "message": prepared_message
#     }
#     return jsonify(response_data)

if __name__ == '__main__':
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4000)
