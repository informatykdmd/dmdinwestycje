from flask import Flask, render_template, redirect, url_for, flash, jsonify, session, request, current_app
from flask_wtf import FlaskForm
from flask_paginate import Pagination, get_page_args
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import mysqlDB as msq
import secrets
from datetime import datetime
from googletrans import Translator
import random
import json

app = Flask(__name__)
app.config['PER_PAGE'] = 6  # Określa liczbę elementów na stronie
app.config['SECRET_KEY'] = secrets.token_hex(16)

def getLangText(text):
    """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
    translator = Translator()
    translation = translator.translate(str(text), dest='en')
    return translation.text

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

        try:
            if data[29] is not None:
                gps_json = json.loads(data[29])
                {"latitude": 52.229676, "longitude": 21.012229}
                "https://earth.google.com/web/@52.25242614,20.83096693,100.96310044a,116.2153688d,35y,0h,0t,0r/data=OgMKATA" # nowrmal
                "https://earth.google.com/web/@52.25250876,20.83139622,102.83373871a,0d,60y,333.15344169h,86.56713379t,0r" # 3D
            else:
                raise ValueError("Dane są None, nie można przetworzyć JSON")
        except json.JSONDecodeError:
            print("Błąd: Podane dane nie są poprawnym JSON-em")
            gps_json = {}
        except IndexError:
            print("Błąd: Próba dostępu do indeksu, który nie istnieje w liście")
            gps_json = {}
        except TypeError as e:
            print(f"Błąd typu danych: {e}")
            gps_json = {}
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")
            gps_json = {}
            

        theme = {
            'ID': int(data[0]),
            'Tytul': data[1] if lang=='pl' else getLangText(data[1]),
            'Opis': data[2] if lang=='pl' else getLangText(data[2]),
            'Cena': data[3],
            'Lokalizacja': data[4],
            'LiczbaPokoi': '' if data[5] is None else data[5],
            'Metraz': '' if data[6] is None else data[6],
            'Zdjecia': [foto for foto in fotoList if foto is not None],
            'Status': data[8], #ENUM('aktywna', 'nieaktywna'): Używam typu ENUM do określenia statusu oferty. To sprawia, że tylko wartości 'aktywna' i 'nieaktywna' są dozwolone w tej kolumnie.
            'Rodzaj': data[9] if lang=='pl' else getLangText(data[8]),
            'DataRozpoczecia': format_date(data[10]),
            'DataZakonczenia': format_date(data[11]),
            'DataUtworzenia': format_date(data[12]),
            'DataAktualizacji': format_date(data[13]),
            'Kaucja': 0.00 if data[14] is None else data[14],
            'Czynsz': 0.00 if data[15] is None else data[15],
            'Umeblowanie': '' if data[16] is None else data[16],
            'LiczbaPieter': 0 if data[17] is None else data[17],
            'PowierzchniaDzialki': 0.00 if data[18] is None else data[18],
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

def generator_daneDBList(lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2] if lang=='pl' else getLangText(com[2])
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['avatar'] = take_data_where_ID('AVATAR_USER', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = format_date(com[4]) if lang=='pl' else format_date(com[4], False)
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0]),
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': str(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0]).split('#splx#') if lang=='pl' else str(getLangText(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0])).replace('#SPLX#', '#splx#').split('#splx#'),
            'tags': str(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0]).split(', ') if lang=='pl' else str(getLangText(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0])).split(', '),
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

            'author_about': take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0] if lang=='pl' else getLangText(take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0]),
            'author_avatar': take_data_where_ID('AVATAR_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'author_facebook': take_data_where_ID('FACEBOOK', 'authors', 'ID', id_author)[0][0],
            'author_twitter': take_data_where_ID('TWITER_X', 'authors', 'ID', id_author)[0][0],
            'author_instagram': take_data_where_ID('INSTAGRAM', 'authors', 'ID', id_author)[0][0],

            'comments': comments_dict
        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_short(lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for post in took_allPost:

        id_content = post[1]
        id_author = post[2]

        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_prev_next(main_id):
    # Załóżmy, że msq.connect_to_database() zwraca listę tuple'i reprezentujących posty, np. [(1, 'Content1'), (2, 'Content2'), ...]
    took_allPost = msq.connect_to_database('SELECT ID FROM blog_posts ORDER BY ID DESC;')
    
    # Przekształcenie wyników z bazy danych do listy ID dla łatwiejszego wyszukiwania
    id_list = [post[0] for post in took_allPost]
    
    # Inicjalizacja słownika dla wyników
    pre_next = {
        'prev': None,
        'next': None
    }
    
    # Znajdowanie indeksu podanego ID w liście
    if main_id in id_list:
        current_index = id_list.index(main_id)
        
        # Sprawdzanie i przypisywanie poprzedniego ID, jeśli istnieje
        if current_index > 0:
            pre_next['prev'] = id_list[current_index - 1]
        
        # Sprawdzanie i przypisywanie następnego ID, jeśli istnieje
        if current_index < len(id_list) - 1:
            pre_next['next'] = id_list[current_index + 1]
    
    return pre_next

def generator_daneDBList_cetegory():
    # Pobranie kategorii z bazy danych
    took_allPost = msq.connect_to_database('SELECT CATEGORY FROM contents ORDER BY ID DESC;')
    
    # Zliczanie wystąpień każdej kategorii
    cat_count = {}
    for post in took_allPost:
        category = post[0]
        if category in cat_count:
            cat_count[category] += 1
        else:
            cat_count[category] = 1

    # Tworzenie listy stringów z nazwami kategorii i ilością wystąpień
    cat_list = [f"{cat} ({count})" for cat, count in cat_count.items()]
    cat_dict = cat_count
    
    return cat_list, cat_dict

def generator_daneDBList_RecentPosts(main_id, amount = 3):
    # Pobieranie ID wszystkich postów oprócz main_id
    query = f"SELECT ID FROM contents WHERE ID != {main_id} ORDER BY ID DESC;"
    took_allPost = msq.connect_to_database(query)

    # Przekształcanie wyników zapytania na listę ID
    all_post_ids = [post[0] for post in took_allPost]

    # Losowanie unikalnych ID z listy (zakładając, że chcemy np. 5 losowych postów, lub mniej jeśli jest mniej dostępnych)
    num_posts_to_select = min(amount, len(all_post_ids))  
    posts = random.sample(all_post_ids, num_posts_to_select)

    return posts

def generator_daneDBList_one_post_id(id_post, lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts WHERE ID={id_post};') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2] if lang=='pl' else getLangText(com[2])
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['avatar'] = take_data_where_ID('AVATAR_USER', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = format_date(com[4]) if lang=='pl' else format_date(com[4], False)
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0]),
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': str(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0]).split('#splx#') if lang=='pl' else str(getLangText(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0])).replace('#SPLX#', '#splx#').split('#splx#'),
            'tags': str(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0]).split(', ') if lang=='pl' else str(getLangText(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0])).split(', '),
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

            'author_about': take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0] if lang=='pl' else getLangText(take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0]),
            'author_avatar': take_data_where_ID('AVATAR_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'author_facebook': take_data_where_ID('FACEBOOK', 'authors', 'ID', id_author)[0][0],
            'author_twitter': take_data_where_ID('TWITER_X', 'authors', 'ID', id_author)[0][0],
            'author_instagram': take_data_where_ID('INSTAGRAM', 'authors', 'ID', id_author)[0][0],

            'comments': comments_dict
        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_3(lang='en'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for i, post in enumerate(took_allPost):
        id_content = post[1]
        id_author = post[2]

        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

        }
        daneList.append(theme)
        if i == 2:
            break
    return daneList

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
        blog_post = generator_daneDBList_short()
        session[f'BLOG-SHORT'] = blog_post
    else:
        blog_post = session[f'BLOG-SHORT']
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

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

    {"latitude": 52.229676, "longitude": 21.012229}
    if "latitude" in secOffers['GPS'] and "longitude" in secOffers['GPS']:
        lat = secOffers['GPS']["latitude"]
        lon = secOffers['GPS']["longitude"]
    else:
        lat = 'None'
        lon = 'None'

    try: mainFoto = secOffers['Zdjecia'][0]
    except IndexError: mainFoto = ''

    return render_template(
        f'index.html', 
        pageTitle=pageTitle,
        fourListTeam=fourListTeam, 
        blog_post_three=blog_post_three,
        coordinates=[lat, lon],
        mainFoto=mainFoto,
        secOffers=secOffers
        )

@app.route('/oferta-inwestycyjna')
def ofertaInwestycyjna():
    session['page'] = 'ofertaInwestycyjna'
    pageTitle = 'Oferta Inwestycyjna'

    return render_template(
        f'ofertaInwestycyjna.html',
        pageTitle=pageTitle,
        )

@app.route('/oferta-najmu')
def ofertaNajmu():
    session['page'] = 'ofertaNajmu'
    pageTitle = 'Oferta Najmu'

    return render_template(
        f'ofertaNajmu.html',
        pageTitle=pageTitle,
        )

@app.route('/oferta-sprzedazy')
def ofertaSprzedazy():
    session['page'] = 'ofertaSprzedazy'
    pageTitle = 'Oferta Sprzedaży'

    return render_template(
        f'ofertaSprzedazy.html',
        pageTitle=pageTitle,
        )

@app.route('/oferta-specjalna')
def ofertaSpecjalna():
    session['page'] = 'ofertaSpecjalna'
    pageTitle = 'Ofeta Specjalna'

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

    {"latitude": 52.229676, "longitude": 21.012229}
    if "latitude" in secOffers['GPS'] and "longitude" in secOffers['GPS']:
        lat = secOffers['GPS']["latitude"]
        lon = secOffers['GPS']["longitude"]
    else:
        lat = 'None'
        lon = 'None'

    try: mainFoto = secOffers['Zdjecia'][0]
    except IndexError: mainFoto = ''

    return render_template(
        f'ofertaSpecjalna.html',
        coordinates=[lat, lon],
        pageTitle=pageTitle,
        mainFoto=mainFoto,
        secOffers=secOffers
        )

@app.route('/my-jestesmy')
def myJestesmy():
    session['page'] = 'myJestesmy'
    pageTitle = 'O nas'

    return render_template(
        f'myJestesmy.html',
        pageTitle=pageTitle,
        )

@app.route('/my-zespol')
def myZespol():
    session['page'] = 'myZespol'
    pageTitle = 'Zespół'

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
        fullListTeam=fullListTeam
        )

@app.route('/my-partnerzy')
def myPartnerzy():
    session['page'] = 'myPartnerzy'
    pageTitle = 'Partnerzy'

    return render_template(
        f'myPartnerzy.html',
        pageTitle=pageTitle,
        )

@app.route('/inwestycje-odkup')
def inwestycjeOdkup():
    session['page'] = 'inwestycjeOdkup'
    pageTitle = 'Odkup Działki'

    return render_template(
        f'inwestycjeOdkup.html',
        pageTitle=pageTitle,
        )

@app.route('/inwestycje-wspolne')
def inwestycjeWspolne():
    session['page'] = 'inwestycjeWspolne'
    pageTitle = 'Inwestycja Wspólna'

    return render_template(
        f'inwestycjeWspolne.html',
        pageTitle=pageTitle,
        )

@app.route('/inwestycje-pomoc')
def inwestycjePomoc():
    session['page'] = 'inwestycjePomoc'
    pageTitle = 'Pomoc Prawna'

    return render_template(
        f'inwestycjePomoc.html',
        pageTitle=pageTitle,
        )

@app.route('/inwestycje-projekt')
def inwestycjeProjekt():
    session['page'] = 'inwestycjeProjekt'
    pageTitle = 'Projekt Inwestycju'

    return render_template(
        f'inwestycjeProjekt.html',
        pageTitle=pageTitle,
        )

@app.route('/inwestycje-budowa')
def inwestycjeBudowa():
    session['page'] = 'inwestycjeBudowa'
    pageTitle = 'Kompleksowa Budowa'

    return render_template(
        f'inwestycjeBudowa.html',
        pageTitle=pageTitle,
        )

@app.route('/inwestycje-maksymalizacja')
def inwestycjeMaksymalizacja():
    session['page'] = 'inwestycjeMaksymalizacja'
    pageTitle = 'Maksymalizacja Wartości'

    return render_template(
        f'inwestycjeMaksymalizacja.html',
        pageTitle=pageTitle,
        )

@app.route('/blogs')
def blogs():
    session['page'] = 'blogs'
    pageTitle = 'Blog'

    blog_post = generator_daneDBList()

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(blog_post)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = blog_post[offset: offset + per_page]

    return render_template(
        f'blogs.html',
        pageTitle=pageTitle,
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

    pre_next = {
        'prev': generator_daneDBList_prev_next(post_id_int)['prev'],  
        'next': generator_daneDBList_prev_next(post_id_int)['next']
        }

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
    

    return render_template(
        f'blogOne.html',
        choiced=choiced,
        pre_next=pre_next,
        cat_dict=cat_dict,
        recentPosts=recentPosts
        )

@app.route('/kontakt')
def kontakt():
    session['page'] = 'kontakt'
    pageTitle = 'Kontakt z Nami'

    return render_template(
        f'kontakt.html',
        pageTitle=pageTitle,
        )

@app.route('/polityka-prv')
def politykaPrv():
    session['page'] = 'politykaPrv'
    pageTitle = 'Polityka prywatności'

    return render_template(
        f'politykaPrv.html',
        pageTitle=pageTitle,
        )

@app.route('/rulez')
def rulez():
    session['page'] = 'rulez'
    pageTitle = 'Zasady witryny'

    return render_template(
        f'rulez.html',
        pageTitle=pageTitle,
        )

@app.route('/help')
def help():
    session['page'] = 'help'
    pageTitle = 'Pomoc'

    return render_template(
        f'help.html',
        pageTitle=pageTitle,
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

    return render_template(
        "searchBlog.html",
        pageTitle=pageTitle,
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

    return render_template(
        "searchBlog.html",
        pageTitle=pageTitle,
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

        zapytanie_sql = '''
                INSERT INTO contact 
                    (CLIENT_NAME, CLIENT_EMAIL, SUBJECT, MESSAGE, DONE) 
                    VALUES (%s, %s, %s, %s, %s);
                '''
        dane = (CLIENT_NAME, CLIENT_EMAIL, CLIENT_SUBJECT, CLIENT_MESSAGE, 1)
    
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
            zapytanie_sql = '''
                    INSERT INTO newsletter 
                        (CLIENT_NAME, CLIENT_EMAIL, ACTIVE, USER_HASH) 
                        VALUES (%s, %s, %s, %s);
                    '''
            dane = (SUB_NAME, SUB_EMAIL, 0, USER_HASH)
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

if __name__ == '__main__':
    # app.run(debug=True, port=4000)
    app.run(debug=True, host='0.0.0.0', port=4000)