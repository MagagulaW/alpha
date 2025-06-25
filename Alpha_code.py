import cv2
import face_recognition
import speech_recognition as sr
import psycopg2
from psycopg2 import sql, extras
import json
import os
import numpy as np
import pickle
from datetime import datetime
import time
import logging
from pathlib import Path
import configparser
from gtts import gTTS
import tempfile
import subprocess
import sys
import uuid
import base64
import hashlib
from enum import Enum
import sqlite3
import re

# ==================== CONFIGURATION ====================

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler('alpha_robot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enhanced language translations with all languages
TRANSLATIONS = {
    'en': {
        'lang_code': 'en',
        'greeting': (
            "Hello there! Welcome to the Jumpstart Centre! "
            "I'm Alpha, your friendly AI assistant robot, and I'm absolutely delighted to meet you today. "
            "I'm here to help you with all kinds of things like career services, job assistance, and digital literacy support. "
            "I can help you create a professional CV, find exciting job opportunities, and guide you through all of our wonderful services. "
            "Think of me as your personal career companion!"
        ),
        'language_selection': "Please choose your language: English, Siswati, Zulu, or Tsonga.",
        'name_question': "What's your name?",
        'surname_question': "What's your surname?",
        'id_question': "Please say your ID number",
        'phone_question': "What's your phone number?",
        'email_question': "What's your email address?",
        'face_capture': "Please look at the camera for facial registration.",
        'registration_success': "Thank you! Your registration is complete.",
        'services_intro': (
            "We offer these services: "
            "1. Life Skills Training - Developing essential skills for personal and professional growth. "
            "2. Entrepreneurship Support - Guidance for starting and growing your business. "
            "3. Job Application Assistance - Help with finding and applying for jobs. "
            "4. Career Guidance - Exploring career paths and opportunities. "
            "5. University Application Help - Support with tertiary education applications. "
            "6. Digital Literacy Training - Learning computer and internet basics. "
            "7. Internet Access - Free internet for job searches and applications. "
            "8. Computer Center Usage - Access to computers with necessary software."
        ),
        'service_details': {
            'life_skills': (
                "Life Skills Training helps you develop essential abilities like communication, "
                "problem-solving, and time management. These skills are vital for both personal "
                "development and workplace success. Our 4-week program covers emotional intelligence, "
                "financial literacy, and workplace etiquette."
            ),
            'entrepreneurship': (
                "Entrepreneurship Support provides guidance on business planning, funding options, "
                "marketing strategies, and legal requirements. We offer mentorship programs and "
                "workshops on developing business ideas into viable enterprises."
            ),
            'job_applications': (
                "Job Application Assistance includes CV writing, interview preparation, and job search "
                "strategies. We can help you identify suitable positions, create tailored applications, "
                "and practice interview techniques with feedback."
            ),
            'career_guidance': (
                "Career Guidance helps you explore different career paths based on your skills and "
                "interests. We provide aptitude assessments, industry information, and education "
                "pathways to help you make informed career decisions."
            ),
            'university_applications': (
                "University Application Help guides you through the entire application process including "
                "program selection, application forms, personal statements, and financial aid options. "
                "We have information on all South African universities and their requirements."
            ),
            'digital_literacy': (
                "Digital Literacy Training teaches essential computer skills including using email, "
                "internet browsing, word processing, and online safety. Our courses range from basic "
                "to intermediate levels, helping you become comfortable with technology."
            ),
            'internet_access': (
                "We provide free internet access for job searches, online applications, and research. "
                "Our internet lounge has high-speed connectivity and staff to assist with any technical "
                "questions."
            ),
            'computer_center': (
                "Our Computer Center offers access to computers with all necessary software including "
                "office applications, design tools, and specialized career software. Printing and "
                "scanning services are also available."
            )
        },
        'human_assistance': "Would you like to speak with a human assistant instead?",
        'offline_mode': "Internet unavailable. Running in offline mode with limited functionality.",
        'goodbye': "Thank you for visiting the Jumpstart Centre! Have a wonderful day!",
        'error_general': "I'm having some technical difficulties. Please try again later.",
        'error_face': "I couldn't capture your face properly. Please try again.",
        'error_audio': "I didn't hear you clearly. Could you please repeat that?",
        'error_db': "I'm having trouble accessing my database. Some features may be limited.",
        'error_camera': "I can't access my camera right now. We'll continue without facial recognition."
    },
    'ss': {  # Siswati
        'lang_code': 'en',  # Using English TTS as fallback
        'greeting': (
            "Sawubona! Wemukela ku Jumpstart Centre! "
            "Ngingu Alpha, robot loyisekeli lomuhle futsi ngiyajabula kukubona namuhla. "
            "Ngilapha kukusita ngetindaba temsebenti, kusita etimisebentini, nekufundzisa ngetekwentisa. "
            "Ngingakusita kwakha i-CV leyikhethekile, kutfola emathuba emsebenti, nekukuhola kusemasebitini etfu wonkhe. "
            "Ngicabanga ngami njengemngani wakho wetimisebenti!"
        ),
        'language_selection': (
            "Sicela ukhetse lulwimi lofuna kulutfola. "
            "Tsho 'English' ku English. "
            "Tsho 'Swati' ku Siswati. "
            "Tsho 'Zulu' ku IsiZulu. "
            "Tsho 'Tsonga' ku Xitsonga."
        ),
        'name_question': "Ngubani libito lakho?",
        'surname_question': "Ngubani isibongo sakho?",
        'id_question': "Sicela usho inombolo yakho yekutiphatsela",
        'phone_question': "Ngubani inombolo yakho yelucingo?",
        'email_question': "Ngubani ikheli lakho le-imeyili?",
        'face_capture': "Sicela ubheke ekhamera kugcwaliswa kwesifanakaliso sakho.",
        'registration_success': "Ngiyabonga! Ukubhalisa kwakho kuphelele.",
        'services_intro': (
            "Sikuveta letisebenti: "
            "1. Kufundziswa kwemakhono ekuphila - Kutfutfukisa emakhono labalulekile ekutfutfukiseni umuntfu nekumsebenti. "
            "2. Kusekelwa kwebhizinisi - Kuhola ekucaleni nekutfutfukisa bhizinisi yakho. "
            "3. Kusita ekufakeni sicelo semsebenti - Kusita ekutfoleni nekufaka ticelo temisebenti. "
            "4. Kuhola ngemsebenti - Kutsandza tindzawo temisebenti netithuba. "
            "5. Kusita ekufakeni sicelo senyuvesi - Kusita ngenchubo yekufaka sicelo. "
            "6. Kufundziswa kwemakhono edijithali - Kufundza emakhono ekhompyutha ne-inthanethi. "
            "7. Kuvuleleka kwe-inthanethi - Inthanethi yemahhala yekucinga imisebenti nekufaka ticelo. "
            "8. Kusetjentiswa kwendzawo yemakhompyutha - Kuvuleleka kwemakhompyutha naletinhlelo letisetshenziswayo."
        ),
        'service_details': {
            'life_skills': (
                "Kufundziswa kwemakhono ekuphila kukusita utfutfukise emakhono labalulekile njengekukhulumisana, "
                "kuxazulula tinkinga, nekulawula sikhatsi. Lamakhono abalulekile ekutfutfukiseni umuntfu kanye "
                "nekusebenta. Uhlelo lwetinsuku leti-4 lufaka ekutini ucondze imizwa, emakhono emali, nekuziphatha "
                "endzaweni yemsebenti."
            ),
            'entrepreneurship': (
                "Kusekelwa kwebhizinisi kunika luhla lwebhizinisi, tindlela tekutfola imali, "
                "tindlela tekumaketha, nemitsetfo yebhizinisi. Sinemaphrojekhi ekweseka nekufundzisa "
                "ngetindlela tekucala bhizinisi."
            ),
            'job_applications': (
                "Kusita ekufakeni sicelo semsebenti kufaka ekubhaleni i-CV, kulungiselela inhlolokhono, "
                "netindlela tekucinga imisebenti. Singakusita ukutibona tindzawo temisebenti, kwakha ticelo, "
                "nekulalela inhlolokhono."
            ),
            'career_guidance': (
                "Kuhola ngemsebenti kukusita utsandze tindzawo temisebenti ngetikhono netintandzakwako. "
                "Sinemakhono ekuhlola, lwati lwemkhakha, netindlela tekufundza kusita uthatse tincumo letifanele."
            ),
            'university_applications': (
                "Kusita ekufakeni sicelo senyuvesi kuhola ngenchubo yekufaka sicelo kufaka ekukhetfweni kwephrojekhi, "
                "tafomu, tincwadzi, netindlela tekutfola imali. Sinelwati ngetinyuvesi takulelive lonkhe "
                "naletifunwa tato."
            ),
            'digital_literacy': (
                "Kufundziswa kwemakhono edijithali kufundzisa emakhono ebalulekile ekhompyuthini kufaka i-imeyili, "
                "kucinga nge-inthanethi, kubhala, nekuphepha ku-inthanethi. Emakhono etfu asukela kulokubalulekile "
                "kuya kulokunengi."
            ),
            'internet_access': (
                "Sinikeleta inthanethi yemahhala yekucinga imisebenti, kufaka ticelo, nekucwaninga. "
                "Indzawo yetfu ye-inthanethi inekusebenta lokusheshayo kanye nebantfu labangakusita."
            ),
            'computer_center': (
                "Indzawo yetfu yemakhompyutha inemakhompyutha naletinhlelo letisetshenziswayo kufaka "
                "letinhlelo temisebenti, tekwakha, nekumisebenti yemakhono. Sikhipha nemasikeni."
            )
        },
        'human_assistance': "Ungathanda khona ukukhuluma nomuntfu yini?",
        'offline_mode': "Ayikho inthanethi. Sisebenta ngetindlela letincane.",
        'goodbye': "Siyabonga ngekuvakashela ku Jumpstart Centre! Ube nelilanga lelihle!",
        'error_general': "Nginenkinga yeteknoloji. Sicela uphindze emuva.",
        'error_face': "Angikwati kubamba isifanakaliso sakho. Sicela uphindze.",
        'error_audio': "Angikuzwanga kahle. Ungakusho futsi?",
        'error_db': "Nginenkinga ne-database yami. Eminye imisebenti ingasebenzi.",
        'error_camera': "Angikwati kusebentisa ikhamera yami. Sizoqhubeka ngaphandle kwekubona ubuso."
    },
    'zu': {  # Zulu
        'lang_code': 'zu',
        'greeting': (
            "Sawubona! Siyakwamukela e-Jumpstart Centre! "
            "NginguAlpha, irobhothi yakho enobungane futhi ngijabule ukukubona namuhla. "
            "Ngilapha ukukukusiza ngezinhlobo zonke zezinto ezifana nesevisi yomsebenzi, ukusiza emisebenzi, kanye nokufundisa ukuphila ngokwedijithali. "
            "Ngingakusiza wakhe i-CV efanelekile, uthole amathuba omsebenzi amahle, futhi ngikuhole kuwo wonke amasevisi ethu amahle. "
            "Ngicabanga ngami njengomngane wakho womsebenzi!"
        ),
        'language_selection': (
            "Sicela ukhethe ulimi olufunayo. "
            "Thi 'English' olimi lwesiNgisi. "
            "Thi 'Swati' olimi lwesiSwati. "
            "Thi 'Zulu' olimi lwesiZulu. "
            "Thi 'Tsonga' olimi lwesiTsonga."
        ),
        'name_question': "Ubani igama lakho?",
        'surname_question': "Ubani isibongo sakho?",
        'id_question': "Sicela usho inombolo yakho yemazisi",
        'phone_question': "Ubani inombolo yakho yocingo?",
        'email_question': "Ubani ikheli lakho le-imeyili?",
        'face_capture': "Sicela ubheke ngqo ekhamereni ukubamba ubuso bakho.",
        'registration_success': "Ngiyabonga! Ukubhalisa kwakho kuphelele.",
        'services_intro': (
            "Sinikezela ngezinsizakalo ezilandelayo: "
            "1. Ukuqeqeshwa kwamakhono okuphila - Ukuthuthukisa amakhono abalulekile okukhula komuntu nangomsebenzi. "
            "2. Ukusekelwa kobhizinisi - Isiqondiso sokuqala nokukhulisa ibhizinisi lakho. "
            "3. Usizo lokufaka isicelo somsebenzi - Usizo ekutholeni nasekufakeni izicelo zomsebenzi. "
            "4. Isiqondiso somsebenzi - Ukuhlola izindlela zomsebenzi namathuba. "
            "5. Usizo lokufaka izicelo zonyuvesi - Usizo ngenqubo yokufaka isicelo. "
            "6. Ukuqeqeshwa kwamakhono edijithali - Ukufunda amakhono ekhompyutha ne-inthanethi. "
            "7. Ukufinyelela kwe-inthanethi - I-inthanethi yamahhala yokusesha umsebenzi nokufaka izicelo. "
            "8. Ukusetshenziswa kwendawo yamakhompyutha - Ukufinyelela kumakhompyutha nezinhlelo ezidingekayo."
        ),
        'service_details': {
            'life_skills': (
                "Ukuqeqeshwa kwamakhono okuphila kukusiza ukuthi uthuthukise amakhono abalulekile afana nokuxhumana, "
                "ukuxazulula izinkinga, nokulawula isikhathi. Lamakhono abalulekile ekuthuthukiseni umuntu kanye "
                "nomsebenzi. Uhlelo lwethu lwamasonto ama-4 lufaka ukuqonda imizwa, amakhono ezezimali, nokuziphatha "
                "endaweni yomsebenzi."
            ),
            'entrepreneurship': (
                "Ukusekelwa kobhizinisi kunikeza isiqondiso mayelana nokuhlela ibhizinisi, izindlela zokuthola imali, "
                "amasu okumaketha, nemithetho yebhizinisi. Sinohlelo lwabeluleki namathilishi okuthuthukisa imibono "
                "yebhizinisi ibe ngamabhizinisi angasebenza."
            ),
            'job_applications': (
                "Usizo lokufaka izicelo zomsebenzi lufaka ukubhala i-CV, ukulungiselela inhlolokhono, kanye "
                "namasu okusesha umsebenzi. Singakusiza ukuthola izikhundla ezifanele, ukwenza izicelo, "
                "nokuzilolonga inhlolokhono."
            ),
            'career_guidance': (
                "Isiqondiso somsebenzi kukusiza ucwaninge izindlela zomsebenzi ngokususelwa kumakhono nakho "
                "okuthandayo. Sinokuhlolwa kwamakhono, ulwazi lwemikhakha, nezindlela zokufunda ukuze uthathe "
                "izinqumo ezifanele."
            ),
            'university_applications': (
                "Usizo lokufaka izicelo zonyuvesi kuhola ngenqubo yokufaka isicelo efaka ukukhetha uhlelo, "
                "amafomu, izincwadi zokuzikhulumela, nezindlela zokuthola usizo lwezimali. Sinolwazi mayelana "
                "nazo zonke izinyuvesi zaseNingizimu Afrika nezimfuneko zazo."
            ),
            'digital_literacy': (
                "Ukuqeqeshwa kwamakhono edijithali kufundisa amakhono abalulekile ekhompyuthini afaka i-imeyili, "
                "ukuphenya kwi-inthanethi, ukubhala, nokuphepha ku-inthanethi. Izifundo zethu zisukela ezisisekelo "
                "kuya kwezingenela."
            ),
            'internet_access': (
                "Sinikezela nge-inthanethi yamahhala yokusesha umsebenzi, ukufaka izicelo, nokucwaninga. "
                "Indawo yethu ye-inthanethi inokuxhumana okusheshayo kanye nabasebenzi abangakusiza."
            ),
            'computer_center': (
                "Indawo yethu yamakhompyutha inamakhompyutha nazo zonke izinhlelo ezidingekayo kufaka "
                "izinhlelo zomsebenzi, zokuklama, nezomkhakha womsebenzi. Sikhipha futhi si-scan."
            )
        },
        'human_assistance': "Ungathanda ukukhuluma nomuntu yini?",
        'offline_mode': "Ayikho i-inthanethi. Sisebenza ngamandla omncane.",
        'goodbye': "Siyabonga ngokuvakashela e-Jumpstart Centre! Ube nosuku oluhle!",
        'error_general': "Nginenkinga yobuchwepheshe. Ngicela uzame futhi.",
        'error_face': "Angikwazanga ukuthatha isithombe sakho. Ngicela uzame futhi.",
        'error_audio': "Angikuzwanga kahle. Ungakusho futhi?",
        'error_db': "Nginenkinga ne-database yami. Ezinye izinsizakalo zingasebenzi.",
        'error_camera': "Angikwazi ukusebenzisa ikhamera yami. Sizoqhubeka ngaphandle kokubona ubuso."
    },
    'ts': {  # Tsonga
        'lang_code': 'en',  # Using English TTS as fallback
        'greeting': (
            "Avuxeni! Mi amukekiwile eka Jumpstart Centre! "
            "A ndzi Alpha, robot ya vutshila bya mina leyi nga hotelela futhi ndzi tsakile ku mi vona namuntlha. "
            "A ndzi kona ku mi pfuna hi swo hlawuleka swo fambisa ntirho, ku pfuna emisebenzini, na dyondzo ya digital. "
            "A ndzi nga mi pfuna ku aka CV leyinene, ku kuma switirhisiwa swin'wana swa ntirho, na ku mi rhangela emisebenzini ya hina hinkwayo. "
            "A ndzi ehleketa hi mina tanihi munghana wa wena wa ntirho!"
        ),
        'language_selection': (
            "Hi kombela mi hlawula ririmi leri mi ri lavaka. "
            "Vutsani 'English' eka English. "
            "Vutsani 'Swati' eka Siswati. "
            "Vutsani 'Zulu' eka IsiZulu. "
            "Vutsani 'Tsonga' eka Xitsonga."
        ),
        'name_question': "I mani vito ra wena?",
        'surname_question': "I mani xivongo xa wena?",
        'id_question': "Hi kombela mi vulavula nomoro ya wena ya xitifikheta",
        'phone_question': "I mani nomoro ya wena ya mugagula?",
        'email_question': "I mani adressee ya wena ya email?",
        'face_capture': "Hi kombela u languta eka kamera ku teka xifaniso xa wena.",
        'registration_success': "Ndzi khensa! Ku tsarisiwa ka wena ku hetile.",
        'services_intro': (
            "Hi nyika tinhlengeletano leti: "
            "1. Dyondzo ya makhono ya vutomi - Ku hluvukisa makhono ya nkoka ya ku hluvukisa munhu na ntirho. "
            "2. Nhlangano wa bisimusi - Vuhlayisi bya ku sungula na ku hluvukisa bisimusi ra wena. "
            "3. Pfuno ra ku tsandzeka ka ntirho - Pfuno eku kumeni na ku tsandzeka ka ntirho. "
            "4. Vuhlayisi bya ntirho - Ku lavisisa tindzimi ta ntirho na mahanyelo. "
            "5. Pfuno ra ku tsandzeka ka yunivhesiti - Pfuno hi ndlela ya ku tsandzeka. "
            "6. Dyondzo ya makhono ya dijithali - Ku dyondza makhono ya khompyuta na internet. "
            "7. Ku fikelela ka internet - Internet ya mahala ya ku lava ntirho na ku tsandzeka. "
            "8. Ku tirhisiwa ka xiyimo xa khompyuta - Ku fikelela ka tikhompyuta na switirhisiwa leswi fanaka."
        ),
        'service_details': {
            'life_skills': (
                "Dyondzo ya makhono ya vutomi yi pfuna ku hluvukisa makhono ya nkoka hinkwawo ku fana na vululami, "
                "ku hetiseka ka swiphiqo, na ku lawula nkarhi. Makhono lawa ya nkoka eku hluvukiseni munhu na "
                "ntirho. Purogireme ya hina ya mavhiki mana yi katsa ku twisisa milorho, makhono ya mali, na "
                "maendlelo ya ntirho."
            ),
            'entrepreneurship': (
                "Nhlangano wa bisimusi wu nyika vuhlayisi mayelana na ku hlanganisa bisimusi, tindlela ta ku kuma "
                "mali, maendlelo ya makete, na swileriso swa bisimusi. Hi na tipurogireme ta vatirhisi na "
                "tithili tona ku hundzuluxa mianakanyo ya bisimusi eka mabindzu lowa tirhaka."
            ),
            'job_applications': (
                "Pfuno ra ku tsandzeka ka ntirho ri katsa ku tsala CV, ku lungiselela inthaviwu, na maendlelo ya "
                "ku lava ntirho. Hi nga ku pfuna ku kuma swiyimo leswi fanaka, ku endla switirhisiwa, na "
                "ku practisa inthaviwu."
            ),
            'career_guidance': (
                "Vuhlayisi bya ntirho byi pfuna ku lavisisa tindzimi ta ntirho hi ku ya hi makhono na leswi "
                "u swi rhandzaka. Hi na ku kambisisa ka makhono, vutivi bya mindzimi, na tindlela ta ku dyondza "
                "leswi ku pfumalaka ku endla tinqumo leti fanaka."
            ),
            'university_applications': (
                "Pfuno ra ku tsandzeka ka yunivhesiti ri pfuna hi ndlela ya ku tsandzeka leyi katsaka ku hlawula "
                "purogireme, tifomu, switirhisiwa, na tindlela ta ku kuma pfuno ra mali. Hi na vutivi bya "
                "tiyunivhesiti hinkwato ta Afrika Dzonga na swikombelo swa tona."
            ),
            'digital_literacy': (
                "Dyondzo ya makhono ya dijithali yi dyondza makhono ya nkoka ya khompyuta lawa ya katsaka email, "
                "ku lava hi internet, ku tsala, na ku hlayisa eka internet. Switirhisiwa swa hina swi sukela "
                "eka swa le henhla ku ya eka swa le xikarhi."
            ),
            'internet_access': (
                "Hi nyika internet ya mahala ya ku lava ntirho, ku tsandzeka, na ku lavisisa. "
                "Xiyimo xa hina xa internet xi na ku angarhela lokululamile na vatirhi lava nga ku pfuna."
            ),
            'computer_center': (
                "Xiyimo xa hina xa khompyuta xi na tikhompyuta na switirhisiwa hinkwaswo leswi fanaka ku katsa "
                "switirhisiwa swa ntirho, swa disayini, na swa ntirho wa makhono. Hi tirhisa na swi scanner."
            )
        },
        'human_assistance': "Xana mi lava ku vulavula na munhu?",
        'offline_mode': "A ku na internet. Hi tirha hi swikongomelo swa le henhla.",
        'goodbye': "Hi khensa ku ta eka Jumpstart Centre! Mi va na siku rinene!",
        'error_general': "Ndi na xiphiqo xa thekinoloji. Hi kombela mi ringeta nakambe.",
        'error_face': "A ndzi swi koti ku teka xifaniso xa wena. Hi kombela mi ringeta nakambe.",
        'error_audio': "A ndzi ku twanga kahle. Xana mi nga vulavula nakambe?",
        'error_db': "Ndi na xiphiqo xa database ya mina. Swin'wana switirhisiwa swinga nga tirhi.",
        'error_camera': "A ndzi swi koti ku tirhisa kamera ya mina. Hi ta ya emahlweni hi ndlela yin'wana."
    }
}

# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    """Handles both online (PostgreSQL) and offline (SQLite) database operations"""
    def __init__(self, config):
        self.config = config
        self.online = True
        self.connection = None
        self.setup_databases()
        
    def setup_databases(self):
        """Initialize both database connections"""
        try:
            # Try PostgreSQL first
            self.connection = psycopg2.connect(
                host=self.config['POSTGRES']['host'],
                database=self.config['POSTGRES']['database'],
                user=self.config['POSTGRES']['user'],
                password=self.config['POSTGRES']['password'],
                connect_timeout=5
            )
            logger.info("Connected to PostgreSQL database")
            self._ensure_schema()
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {str(e)}. Falling back to SQLite.")
            self.online = False
            offline_db_path = Path(self.config['PATHS']['offline_db'])
            offline_db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(offline_db_path)
            self._ensure_schema()
    
    def _ensure_schema(self):
        """Create tables if they don't exist with appropriate schema for each DB"""
        commands = []
        if self.online:
            # PostgreSQL schema
            commands.extend([
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    id_number VARCHAR(20) UNIQUE NOT NULL,
                    phone VARCHAR(15),
                    email VARCHAR(100),
                    face_encoding BYTEA,
                    registration_date TIMESTAMP NOT NULL,
                    language_preference VARCHAR(5) DEFAULT 'en'
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS services (
                    service_id SERIAL PRIMARY KEY,
                    service_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    offline_available BOOLEAN DEFAULT TRUE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    visit_time TIMESTAMP NOT NULL,
                    recognized BOOLEAN NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS service_requests (
                    request_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    service_id INTEGER REFERENCES services(service_id),
                    request_time TIMESTAMP NOT NULL,
                    assisted_by_robot BOOLEAN NOT NULL
                )
                """
            ])
        else:
            # SQLite schema
            commands.extend([
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    id_number TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    email TEXT,
                    face_encoding BLOB,
                    registration_date TEXT NOT NULL,
                    language_preference TEXT DEFAULT 'en'
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS services (
                    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    description TEXT,
                    offline_available INTEGER DEFAULT 1
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(user_id),
                    visit_time TEXT NOT NULL,
                    recognized INTEGER NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS service_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(user_id),
                    service_id INTEGER REFERENCES services(service_id),
                    request_time TEXT NOT NULL,
                    assisted_by_robot INTEGER NOT NULL
                )
                """
            ])
        
        try:
            cursor = self.connection.cursor()
            
            # Check if services table is empty
            cursor.execute("SELECT COUNT(*) FROM services")
            if cursor.fetchone()[0] == 0:
                # Insert default services
                default_services = [
                    ("Life Skills Training", "Developing essential life skills", True),
                    ("Entrepreneurship Support", "Business startup guidance", True),
                    ("Job Application Assistance", "Help with job applications", True),
                    ("Career Guidance", "Career counseling services", True),
                    ("University Application Help", "Assistance with university applications", False),
                    ("Digital Literacy Training", "Basic computer skills training", True),
                    ("Internet Access", "Free internet access", False),
                    ("Computer Center Usage", "Access to computer equipment", True)
                ]
                
                if self.online:
                    insert_sql = """
                        INSERT INTO services(service_name, description, offline_available) 
                        VALUES (%s, %s, %s)
                    """
                else:
                    insert_sql = """
                        INSERT INTO services(service_name, description, offline_available) 
                        VALUES (?, ?, ?)
                    """
                
                cursor.executemany(insert_sql, default_services)
            
            # Execute schema creation commands
            for command in commands:
                try:
                    cursor.execute(command)
                except Exception as e:
                    logger.warning(f"Table may already exist: {str(e)}")
                    self.connection.rollback()
                    continue
            
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Schema setup failed: {str(e)}")
            raise

    def register_user(self, user_data, face_encoding):
        """Register a new user with facial data"""
        try:
            query = """
                INSERT INTO users 
                (first_name, last_name, id_number, phone, email, face_encoding, registration_date, language_preference)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING user_id
            """ if self.online else """
                INSERT INTO users 
                (first_name, last_name, id_number, phone, email, face_encoding, registration_date, language_preference)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                user_data['first_name'],
                user_data['last_name'],
                user_data['id_number'],
                user_data.get('phone'),
                user_data.get('email'),
                pickle.dumps(face_encoding) if face_encoding else None,
                datetime.now().isoformat(),
                user_data.get('language_preference', 'en')
            )
            
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            if self.online:
                user_id = cursor.fetchone()[0]
            else:
                user_id = cursor.lastrowid
                
            self.connection.commit()
            logger.info(f"Registered new user with ID: {user_id}")
            return user_id
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"User registration failed: {str(e)}")
            raise

    def recognize_user(self, face_encoding):
        """Attempt to recognize a known user by face"""
        try:
            cursor = self.connection.cursor()
            
            if self.online:
                cursor.execute("""
                    SELECT user_id, first_name, last_name, face_encoding 
                    FROM users 
                    WHERE face_encoding IS NOT NULL
                """)
            else:
                cursor.execute("""
                    SELECT user_id, first_name, last_name, face_encoding 
                    FROM users 
                    WHERE face_encoding IS NOT NULL
                """)
            
            for row in cursor.fetchall():
                try:
                    stored_encoding = pickle.loads(row[3]) if row[3] else None
                    if stored_encoding and face_recognition.compare_faces(
                        [stored_encoding], face_encoding, tolerance=0.6
                    )[0]:
                        return {
                            'user_id': row[0],
                            'first_name': row[1],
                            'last_name': row[2]
                        }
                except Exception as e:
                    logger.warning(f"Face comparison failed for user {row[0]}: {str(e)}")
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"User recognition failed: {str(e)}")
            raise

    def log_visit(self, user_id, recognized):
        """Record user visit in database"""
        try:
            query = """
                INSERT INTO visits (user_id, visit_time, recognized)
                VALUES (%s, %s, %s)
            """ if self.online else """
                INSERT INTO visits (user_id, visit_time, recognized)
                VALUES (?, ?, ?)
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (
                user_id,
                datetime.now().isoformat(),
                recognized
            ))
            self.connection.commit()
            logger.info(f"Logged visit for user {user_id}")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Visit logging failed: {str(e)}")
            raise

    def log_service_request(self, user_id, service_id, assisted_by_robot):
        """Record service request to database"""
        try:
            query = """
                INSERT INTO service_requests 
                (user_id, service_id, request_time, assisted_by_robot)
                VALUES (%s, %s, %s, %s)
            """ if self.online else """
                INSERT INTO service_requests 
                (user_id, service_id, request_time, assisted_by_robot)
                VALUES (?, ?, ?, ?)
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (
                user_id,
                service_id,
                datetime.now().isoformat(),
                assisted_by_robot
            ))
            self.connection.commit()
            logger.info(f"Logged service request for user {user_id}")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Service request logging failed: {str(e)}")
            raise

# ==================== VOICE ENGINE ====================

class VoiceEngine:
    """Handles all voice interactions with offline fallback"""
    def __init__(self, config):
        self.config = config
        self.current_language = 'en'
        self.offline = False
        self.recognizer = sr.Recognizer()
        self.microphone = self.select_microphone()
        self.test_audio_system()
        
    def select_microphone(self):
        """Select USB camera microphone if available"""
        mics = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphones: {mics}")
        
        # Find USB camera microphone
        usb_mic_index = None
        for i, name in enumerate(mics):
            if 'usb' in name.lower() or 'camera' in name.lower():
                usb_mic_index = i
                logger.info(f"Using USB microphone: {name} at index {i}")
                break
            elif 'mic' in name.lower() or 'input' in name.lower():
                usb_mic_index = i  # Fallback to any mic
                
        if usb_mic_index is None:
            logger.warning("No specific USB microphone found, using default")
            return sr.Microphone()
        return sr.Microphone(device_index=usb_mic_index)
    
    def test_audio_system(self):
        """Check if required audio components are available"""
        try:
            # Test internet-dependent components
            test_tts = gTTS(text="test", lang='en')
            with tempfile.NamedTemporaryFile() as f:
                test_tts.save(f.name)
            
            # Test system audio
            subprocess.run(['which', 'mpg123'], check=True, 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Calibrate microphone
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            
            logger.info("Audio system fully operational")
        except Exception as e:
            logger.warning(f"Audio system limited: {str(e)}")
            self.offline = True
    
    def set_language(self, language_code):
        """Set the current language for voice interactions"""
        if language_code in TRANSLATIONS:
            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
        else:
            logger.warning(f"Unsupported language code: {language_code}")

    def speak(self, text, slow=False):
        """Text-to-speech with offline fallback"""
        try:
            if not self.offline:
                tts = gTTS(
                    text=text,
                    lang=TRANSLATIONS[self.current_language]['lang_code'],
                    slow=slow
                )
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as f:
                    tts.save(f.name)
                    subprocess.run(
                        ['mpg123', '-q', f.name],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
            else:
                # Fallback to espeak if available
                try:
                    subprocess.run(
                        ['espeak', '-v', self.current_language, text],
                        check=True
                    )
                except:
                    # Final fallback - just print
                    print(f"SPEAK: {text}")
        except Exception as e:
            logger.error(f"Speech synthesis failed: {str(e)}")
            raise

    def listen(self, timeout=5, phrase_time_limit=10):
        """Speech recognition with offline fallback"""
        try:
            with self.microphone as source:
                logger.debug("Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                if not self.offline:
                    try:
                        text = self.recognizer.recognize_google(audio)
                        logger.debug(f"Recognized: {text}")
                        return text.lower()
                    except sr.UnknownValueError:
                        logger.warning("Could not understand audio")
                        return None
                    except sr.RequestError as e:
                        logger.warning(f"Speech recognition service error: {str(e)}")
                        return None
                else:
                    # Offline fallback - basic voice recording without recognition
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
                        with open(f.name, "wb") as audio_file:
                            audio_file.write(audio.get_wav_data())
                        logger.info("Audio captured in offline mode")
                        return "offline_audio_captured"
                    
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout reached")
            return None
        except Exception as e:
            logger.error(f"Listening failed: {str(e)}")
            return None

# ==================== FACE RECOGNITION ====================

class FaceRecognition:
    """Handles face capture and recognition"""
    def __init__(self, config):
        self.config = config
        self.camera = None
        self.setup_camera()
        
    def setup_camera(self):
        """Initialize camera with error handling"""
        # Try different camera indices
        for i in range(0, 4):
            try:
                self.camera = cv2.VideoCapture(i)
                if self.camera.isOpened():
                    # Set camera properties
                    width = int(self.config['CAMERA']['width'])
                    height = int(self.config['CAMERA']['height'])
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    # Test camera
                    ret, frame = self.camera.read()
                    if ret:
                        logger.info(f"Camera initialized successfully at index {i}")
                        return
                    else:
                        logger.warning(f"Camera at index {i} opened but couldn't capture frame")
                        self.camera.release()
                else:
                    logger.warning(f"Could not open camera at index {i}")
            except Exception as e:
                logger.warning(f"Camera test at index {i} failed: {str(e)}")
        
        # Try device paths if indices failed
        device_paths = ["/dev/video0", "/dev/video1", "/dev/video2"]
        for path in device_paths:
            try:
                self.camera = cv2.VideoCapture(path)
                if self.camera.isOpened():
                    width = int(self.config['CAMERA']['width'])
                    height = int(self.config['CAMERA']['height'])
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    ret, frame = self.camera.read()
                    if ret:
                        logger.info(f"Camera initialized at path {path}")
                        return
                    else:
                        logger.warning(f"Camera at path {path} opened but couldn't capture frame")
                        self.camera.release()
                else:
                    logger.warning(f"Could not open camera at path {path}")
            except Exception as e:
                logger.warning(f"Camera test at path {path} failed: {str(e)}")
        
        logger.error("All camera initialization attempts failed")
        self.camera = None
        raise RuntimeError("Could not open any camera")

    def capture_face(self):
        """Capture and encode a face from the camera"""
        try:
            if not self.camera:
                # Try to reinitialize camera once
                try:
                    self.setup_camera()
                    if not self.camera:
                        raise ValueError("Camera not available")
                except:
                    raise ValueError("Camera not available")
                
            ret, frame = self.camera.read()
            if not ret:
                # Try reopening the camera
                self.camera.release()
                self.setup_camera()
                ret, frame = self.camera.read()
                if not ret:
                    raise ValueError("Could not capture frame after retry")
            
            # Convert to RGB for face_recognition
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb)
            face_encodings = face_recognition.face_encodings(rgb, face_locations)
            
            if not face_encodings:
                raise ValueError("No face detected")
            
            # Return the first face found
            return face_encodings[0], frame
            
        except Exception as e:
            logger.error(f"Face capture failed: {str(e)}")
            raise
        finally:
            # Don't release camera - keep it open for subsequent captures
            pass

    def release_camera(self):
        """Release camera resources"""
        if self.camera:
            self.camera.release()
            self.camera = None

# ==================== ALPHA ROBOT MAIN CLASS ====================

class AlphaRobot:
    """Main robot controller class"""
    def __init__(self, config_file='config.ini'):
        self.load_config(config_file)
        self.db = DatabaseManager(self.config)
        self.voice = VoiceEngine(self.config)
        
        try:
            self.face_rec = FaceRecognition(self.config)
        except Exception as e:
            logger.error(f"Camera initialization failed: {str(e)}")
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_camera'])
            self.face_rec = None
            
        self.current_user = None
        self.services_offline = [
            "Life Skills Training",
            "Entrepreneurship Support",
            "Job Application Assistance",
            "Career Guidance",
            "Digital Literacy Training",
            "Computer Center Usage"
        ]
        
        if self.db.online:
            logger.info("Running in online mode")
        else:
            logger.info("Running in offline mode")
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['offline_mode'])

    def load_config(self, config_file):
        """Load and validate configuration"""
        self.config = configparser.ConfigParser()
        if not self.config.read(config_file):
            raise FileNotFoundError(f"Config file {config_file} not found")
        
        required_sections = ['POSTGRES', 'PATHS', 'CAMERA']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing config section: {section}")

    def run(self):
        """Main execution flow"""
        try:
            self.greet_user()
            self.handle_language_selection()
            self.handle_user_identification()
            self.handle_service_selection()
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['goodbye'])
        except KeyboardInterrupt:
            logger.info("Session interrupted by user")
        except Exception as e:
            logger.error(f"Runtime error: {str(e)}")
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_general'])
        finally:
            self.cleanup()

    def greet_user(self):
        """Play the full greeting message"""
        self.voice.speak(TRANSLATIONS['en']['greeting'])

    def handle_language_selection(self, max_attempts=3):
        """Language selection process"""
        for attempt in range(max_attempts):
            self.voice.speak(TRANSLATIONS['en']['language_selection'])
            response = self.voice.listen()
            
            if not response:
                if attempt < max_attempts - 1:
                    self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_audio'])
                continue
                
            lang = self._match_language(response.lower())
            if lang:
                self.voice.set_language(lang)
                return
                
        logger.warning("Using default language after failed attempts")

    def _match_language(self, input_text):
        """Match spoken language to supported options"""
        language_map = {
            'english': 'en',
            'siswati': 'ss',
            'zulu': 'zu',
            'tsonga': 'ts'
        }
        for lang_name, code in language_map.items():
            if lang_name in input_text:
                return code
        return None

    def handle_user_identification(self):
        """User recognition or registration"""
        try:
            if not self.face_rec or not self.face_rec.camera:
                logger.warning("Skipping face recognition - camera not available")
                self._register_new_user_without_face()
                return
                
            # Try face recognition first
            face_encoding, _ = self.face_rec.capture_face()
            user = self.db.recognize_user(face_encoding)
            
            if user:
                self.current_user = user
                self.db.log_visit(user['user_id'], recognized=True)
                logger.info(f"Recognized user: {user['first_name']}")
                return
                
            # New user registration
            self._register_new_user(face_encoding)
            
        except Exception as e:
            logger.error(f"User identification failed: {str(e)}")
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_face'])
            self._register_new_user_without_face()

    def _register_new_user(self, face_encoding=None):
        """Complete new user registration with face capture"""
        user_data = {'language_preference': self.voice.current_language}
        
        # Collect required information
        for field, question_key in [
            ('first_name', 'name_question'),
            ('last_name', 'surname_question'),
            ('id_number', 'id_question')
        ]:
            while True:
                self.voice.speak(TRANSLATIONS[self.voice.current_language][question_key])
                response = self.voice.listen()
                
                if response and self._validate_input(response, field):
                    user_data[field] = response.title() if field in ['first_name', 'last_name'] else response
                    break
                else:
                    self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_audio'])
        
        # Collect optional information
        for field, question_key in [
            ('phone', 'phone_question'),
            ('email', 'email_question')
        ]:
            self.voice.speak(TRANSLATIONS[self.voice.current_language][question_key])
            response = self.voice.listen()
            
            if response and self._validate_input(response, field):
                user_data[field] = response

        # Complete registration
        try:
            user_id = self.db.register_user(user_data, face_encoding)
            self.current_user = {'user_id': user_id, **user_data}
            self.db.log_visit(user_id, recognized=False)
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['registration_success'])
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise

    def _register_new_user_without_face(self):
        """Register new user when camera is unavailable"""
        user_data = {'language_preference': self.voice.current_language}
        
        # Collect required information
        for field, question_key in [
            ('first_name', 'name_question'),
            ('last_name', 'surname_question'),
            ('id_number', 'id_question')
        ]:
            while True:
                self.voice.speak(TRANSLATIONS[self.voice.current_language][question_key])
                response = self.voice.listen()
                
                if response and self._validate_input(response, field):
                    user_data[field] = response.title() if field in ['first_name', 'last_name'] else response
                    break
                else:
                    self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_audio'])
        
        # Collect optional information
        for field, question_key in [
            ('phone', 'phone_question'),
            ('email', 'email_question')
        ]:
            self.voice.speak(TRANSLATIONS[self.voice.current_language][question_key])
            response = self.voice.listen()
            
            if response and self._validate_input(response, field):
                user_data[field] = response

        # Complete registration without face
        try:
            user_id = self.db.register_user(user_data, None)
            self.current_user = {'user_id': user_id, **user_data}
            self.db.log_visit(user_id, recognized=False)
            self.voice.speak(TRANSLATIONS[self.voice.current_language]['registration_success'])
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise

    def _validate_input(self, input_text, input_type):
        """Basic input validation"""
        if input_type in ['first_name', 'last_name']:
            return len(input_text) >= 2 and all(c.isalpha() or c.isspace() for c in input_text)
        elif input_type == 'id_number':
            return input_text.isdigit() and len(input_text) >= 6
        elif input_type == 'phone':
            return input_text.replace(" ", "").isdigit() and len(input_text.replace(" ", "")) >= 10
        elif input_type == 'email':
            return re.match(r"[^@]+@[^@]+\.[^@]+", input_text)
        return True

    def handle_service_selection(self):
        """Service selection and information flow"""
        self.voice.speak(TRANSLATIONS[self.voice.current_language]['services_intro'])
        
        while True:
            response = self.voice.listen()
            if not response:
                self.voice.speak(TRANSLATIONS[self.voice.current_language]['error_audio'])
                continue
                
            service = self._match_service(response)
            if service:
                self._provide_service_details(service)
                
                # Offer human assistance
                self.voice.speak(TRANSLATIONS[self.voice.current_language]['human_assistance'])
                human_response = self.voice.listen()
                if human_response and 'yes' in human_response.lower():
                    self._handle_human_assistance(service)
                else:
                    # Log service request handled by robot
                    self._log_service(service, assisted_by_robot=True)
                
                return
                
            self.voice.speak("I didn't understand. Please say the name of the service you want.")

    def _match_service(self, input_text):
        """Match user input to available services"""
        cursor = self.db.connection.cursor()
        
        if not self.db.online:
            cursor.execute("""
                SELECT service_id, service_name FROM services 
                WHERE offline_available = TRUE
            """)
        else:
            cursor.execute("SELECT service_id, service_name FROM services")
        
        available_services = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        for service_name, service_id in available_services.items():
            if service_name in input_text.lower():
                return {'id': service_id, 'name': service_name}
                
        return None

    def _provide_service_details(self, service):
        """Provide detailed information about a service"""
        service_key = service['name'].lower().replace(" ", "_")
        details = TRANSLATIONS[self.voice.current_language]['service_details'].get(service_key)
        
        if details:
            self.voice.speak(details)
        else:
            self.voice.speak(f"Here is information about our {service['name']} service.")

    def _handle_human_assistance(self, service):
        """Handle request for human assistance"""
        desk_mapping = {
            "life skills training": "Life Skills Area",
            "entrepreneurship support": "Business Desk",
            "job application assistance": "Job Center",
            "career guidance": "Career Counselor",
            "university application help": "Education Desk",
            "digital literacy training": "Computer Lab",
            "internet access": "Internet Lounge",
            "computer center usage": "Computer Center"
        }
        
        desk = desk_mapping.get(service['name'].lower(), "Main Desk")
        self.voice.speak(f"Please proceed to the {desk}. A staff member will assist you shortly.")
        
        # Log service request handled by human
        self._log_service(service, assisted_by_robot=False)

    def _log_service(self, service, assisted_by_robot):
        """Log service request to database"""
        if self.current_user:
            try:
                self.db.log_service_request(
                    self.current_user['user_id'],
                    service['id'],
                    assisted_by_robot
                )
            except Exception as e:
                logger.error(f"Failed to log service request: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'db') and self.db.connection:
                self.db.connection.close()
            if hasattr(self, 'face_rec') and self.face_rec:
                self.face_rec.release_camera()
            cv2.destroyAllWindows()
            logger.info("Resources cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    try:
        # Create default config if it doesn't exist
        config_path = Path('config.ini')
        if not config_path.exists():
            default_config = configparser.ConfigParser()
            default_config['POSTGRES'] = {
                'host': 'localhost',
                'database': 'alpha_robot',
                'user': 'postgres',
                'password': 'jumpstart'
            }
            default_config['PATHS'] = {
                'offline_db': 'alpha_data/offline.db',
                'log_file': 'alpha_data/alpha.log'
            }
            default_config['CAMERA'] = {
                'device_id': '0',
                'width': '1280',
                'height': '720'
            }
            
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as configfile:
                default_config.write(configfile)
            logger.info("Created default configuration file")
        
        # Initialize and run the robot
        robot = AlphaRobot(config_path)
        robot.run()
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        sys.exit(1)