#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说生成器 - 共享配置
"""

# ============================================================
# 全局配置
# ============================================================
DEFAULT_CHAPTERS = 3
DEFAULT_MODEL = "qwen2.5:7b"

# ============================================================
# 语言名称映射
# ============================================================
LANG_NAMES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ko": "한국어",
    "ar": "العربية",
    "th": "ภาษาไทย",
    "nl": "Nederlands",
    "pl": "Polski",
    "sv": "Svenska",
    "fi": "Suomi",
    "el": "Ελληνικά",
    "he": "עברית",
    "hi": "हिन्दी",
}

# ============================================================
# 多语言配置 - 所有语言相关配置集中管理
# ============================================================
LANG_CONFIG = {
    "zh": {
        "name": "中文",
        "voice": "zh-CN-XiaoxiaoNeural",
        "genre": "科幻",
        "title": "星际行者",
        "outline": "一个普通少年意外获得星际航行能力，在宇宙中探索未知文明",
        "characters": "主角阿星，16岁，好奇心强；AI助手小智，幽默风趣",
        "chapter_patterns": [r'第\d+章'],
        "labels": {
            "title": "标题",
            "genre": "类型",
            "language": "语言",
            "model": "模型",
            "generated_at": "生成时间",
            "total_words": "总字数",
            "summary": "小说简介",
        }
    },
    "en": {
        "name": "English",
        "voice": "en-US-JennyNeural",
        "genre": "science fiction",
        "title": "Star Walker",
        "outline": "An ordinary teenager accidentally gains interstellar travel ability and explores unknown civilizations",
        "characters": "The protagonist Star, 16 years old, curious; AI assistant Smart, witty and humorous",
        "chapter_patterns": [r'Chapter \d+'],
        "labels": {
            "title": "Title",
            "genre": "Genre",
            "language": "Language",
            "model": "Model",
            "generated_at": "Generated At",
            "total_words": "Total Words",
            "summary": "Synopsis",
        }
    },
    "ja": {
        "name": "日本語",
        "voice": "ja-JP-NanamiNeural",
        "genre": "SF",
        "title": "星の旅人",
        "outline": "普通の少年が偶然に星間航行能力を獲得し、宇宙で未知の文明を探検する",
        "characters": "主人公アキラ、16歳、好奇心旺盛；AIアシスタントのチエ、ユーモアたっぷり",
        "chapter_patterns": [r'第\d+章'],
        "labels": {
            "title": "タイトル",
            "genre": "ジャンル",
            "language": "言語",
            "model": "モデル",
            "generated_at": "生成時間",
            "total_words": "総文字数",
            "summary": "あらすじ",
        }
    },
    "es": {
        "name": "Español",
        "voice": "es-ES-ElviraNeural",
        "genre": "ciencia ficción",
        "title": "Caminante Estelar",
        "outline": "Un adolescente común adquiere accidentalmente la capacidad de viajar por el espacio",
        "characters": "El protagonista Estrella, 16 años, curioso; Asistente IA Sabio, ingenioso",
        "chapter_patterns": [r'Capítulo \d+'],
        "labels": {
            "title": "Título",
            "genre": "Género",
            "language": "Idioma",
            "model": "Modelo",
            "generated_at": "Generado el",
            "total_words": "Palabras totales",
            "summary": "Sinopsis",
        }
    },
    "fr": {
        "name": "Français",
        "voice": "fr-FR-DeniseNeural",
        "genre": "science-fiction",
        "title": "Voyageur Stellaire",
        "outline": "Un adolescent ordinaire acquiert la capacité de voyager dans l'espace",
        "characters": "Le protagoniste Étoile, 16 ans, curieux; Assistant IA Sage, humoristique",
        "chapter_patterns": [r'Chapitre \d+'],
        "labels": {
            "title": "Titre",
            "genre": "Genre",
            "language": "Langue",
            "model": "Modèle",
            "generated_at": "Généré le",
            "total_words": "Mots totaux",
            "summary": "Résumé",
        }
    },
    "de": {
        "name": "Deutsch",
        "voice": "de-DE-KatjaNeural",
        "genre": "Science-Fiction",
        "title": "Sternenwanderer",
        "outline": "Ein gewöhnlicher Teenager erhält die Fähigkeit, durch das Universum zu reisen",
        "characters": "Der Protagonist Stern, 16 Jahre alt, neugierig; KI-Assistent Weise, humorvoll",
        "chapter_patterns": [r'Kapitel \d+'],
        "labels": {
            "title": "Titel",
            "genre": "Genre",
            "language": "Sprache",
            "model": "Modell",
            "generated_at": "Erstellt am",
            "total_words": "Wörter insgesamt",
            "summary": "Zusammenfassung",
        }
    },
    "it": {
        "name": "Italiano",
        "voice": "it-IT-IsabellaNeural",
        "genre": "fantascienza",
        "title": "Viaggiatore Stellare",
        "outline": "Un adolescente comune acquisisce la capacità di viaggiare nello spazio",
        "characters": "Il protagonista Stella, 16 anni, curioso; Assistente IA Saggio, spiritoso",
        "chapter_patterns": [r'Capitolo \d+'],
        "labels": {
            "title": "Titolo",
            "genre": "Genere",
            "language": "Lingua",
            "model": "Modello",
            "generated_at": "Generato il",
            "total_words": "Parole totali",
            "summary": "Sinossi",
        }
    },
    "pt": {
        "name": "Português",
        "voice": "pt-BR-FranciscaNeural",
        "genre": "ficção científica",
        "title": "Viajante Estelar",
        "outline": "Um adolescente comum adquire a capacidade de viajar pelo espaço",
        "characters": "O protagonista Estrela, 16 anos, curioso; Assistente IA Sábio, humorístico",
        "chapter_patterns": [r'Capítulo \d+'],
        "labels": {
            "title": "Título",
            "genre": "Gênero",
            "language": "Idioma",
            "model": "Modelo",
            "generated_at": "Gerado em",
            "total_words": "Palavras totais",
            "summary": "Sinopse",
        }
    },
    "ko": {
        "name": "한국어",
        "voice": "ko-KR-SunHiNeural",
        "genre": "공상과학",
        "title": "별의 여행자",
        "outline": "평범한 소년이 우연히 성간 항해 능력을 얻고 우주에서 미지의 문명을 탐험한다",
        "characters": "주인공 별이, 16세, 호기심 많음; AI 어시스턴트 지혜, 유머러스함",
        "chapter_patterns": [r'제\d+장'],
        "labels": {
            "title": "제목",
            "genre": "장르",
            "language": "언어",
            "model": "모델",
            "generated_at": "생성 시간",
            "total_words": "총 글자수",
            "summary": "줄거리",
        }
    },
    "ar": {
        "name": "العربية",
        "voice": "ar-EG-SalmaNeural",
        "genre": "خيال علمي",
        "title": "المتجول النجمي",
        "outline": "مراهق عادي يكتسب القدرة على السفر بين النجوم",
        "characters": "البطل نجم، 16 سنة، فضولي؛ مساعد الذكاء الاصطناعي حكيم، فكاهي",
        "chapter_patterns": [r'الفصل \d+'],
        "labels": {
            "title": "العنوان",
            "genre": "النوع",
            "language": "اللغة",
            "model": "النموذج",
            "generated_at": "تاريخ الإنشاء",
            "total_words": "إجمالي الكلمات",
            "summary": "ملخص",
        }
    },
    "th": {
        "name": "ภาษาไทย",
        "voice": "th-TH-PremwadeeNeural",
        "genre": "นิยายวิทยาศาสตร์",
        "title": "นักเดินทางดวงดาว",
        "outline": "วัยรุ่นธรรมดาได้รับความสามารถในการเดินทางข้ามดวงดาว",
        "characters": "ตัวเอก ดาว, อายุ 16 ปี, ช่างสงสัย; ผู้ช่วย AI ปรีชา, มีอารมณ์ขัน",
        "chapter_patterns": [r'บทที่ \d+'],
        "labels": {
            "title": "ชื่อเรื่อง",
            "genre": "ประเภท",
            "language": "ภาษา",
            "model": "โมเดล",
            "generated_at": "สร้างเมื่อ",
            "total_words": "จำนวนคำทั้งหมด",
            "summary": "เรื่องย่อ",
        }
    },
    "nl": {
        "name": "Nederlands",
        "voice": "nl-NL-FennaNeural",
        "genre": "sciencefiction",
        "title": "Sterrenwandelaar",
        "outline": "Een gewone tiener krijgt de mogelijkheid om door de ruimte te reizen",
        "characters": "De protagonist Ster, 16 jaar, nieuwsgierig; AI-assistent Wijze, humoristisch",
        "chapter_patterns": [r'Hoofdstuk \d+'],
        "labels": {
            "title": "Titel",
            "genre": "Genre",
            "language": "Taal",
            "model": "Model",
            "generated_at": "Gegenereerd op",
            "total_words": "Totaal woorden",
            "summary": "Samenvatting",
        }
    },
    "pl": {
        "name": "Polski",
        "voice": "pl-PL-AgnieszkaNeural",
        "genre": "science fiction",
        "title": "Gwiezdny Wędrowiec",
        "outline": "Zwykły nastolatek zyskuje zdolność podróżowania między gwiazdami",
        "characters": "Protagonista Gwiazda, 16 lat, ciekawski; Asystent AI Mądry, dowcipny",
        "chapter_patterns": [r'Rozdział \d+'],
        "labels": {
            "title": "Tytuł",
            "genre": "Gatunek",
            "language": "Język",
            "model": "Model",
            "generated_at": "Wygenerowano",
            "total_words": "Całkowita liczba słów",
            "summary": "Streszczenie",
        }
    },
    "sv": {
        "name": "Svenska",
        "voice": "sv-SE-HilleviNeural",
        "genre": "science fiction",
        "title": "Stjärnvandraren",
        "outline": "En vanlig tonåring får förmågan att resa i rymden",
        "characters": "Protagonisten Stjärna, 16 år, nyfiken; AI-assistent Vis, humoristisk",
        "chapter_patterns": [r'Kapitel \d+'],
        "labels": {
            "title": "Titel",
            "genre": "Genre",
            "language": "Språk",
            "model": "Modell",
            "generated_at": "Genererad",
            "total_words": "Totalt antal ord",
            "summary": "Sammanfattning",
        }
    },
    "fi": {
        "name": "Suomi",
        "voice": "fi-FI-SelmaNeural",
        "genre": "tieteiskirjallisuus",
        "title": "Tähtivaeltaja",
        "outline": "Tavallinen teini saa kyvyn matkustaa avaruudessa",
        "characters": "Päähenkilö Tähti, 16-vuotias, utelias; AI-assistentti Viisas, humoristinen",
        "chapter_patterns": [r'Luku \d+'],
        "labels": {
            "title": "Otsikko",
            "genre": "Laji",
            "language": "Kieli",
            "model": "Malli",
            "generated_at": "Luotu",
            "total_words": "Sanat yhteensä",
            "summary": "Yhteenveto",
        }
    },
    "el": {
        "name": "Ελληνικά",
        "voice": "el-GR-AthinaNeural",
        "genre": "επιστημονική φαντασία",
        "title": "Αστεροβάτης",
        "outline": "Ένας συνηθισμένος έφηβος αποκτά την ικανότητα να ταξιδεύει στο διάστημα",
        "characters": "Ο πρωταγωνιστής Αστέρι, 16 ετών, περίεργος; Βοηθός AI Σοφός, χιουμοριστικός",
        "chapter_patterns": [r'Κεφάλαιο \d+'],
        "labels": {
            "title": "Τίτλος",
            "genre": "Είδος",
            "language": "Γλώσσα",
            "model": "Μοντέλο",
            "generated_at": "Δημιουργήθηκε",
            "total_words": "Σύνολο λέξεων",
            "summary": "Περίληψη",
        }
    },
    "he": {
        "name": "עברית",
        "voice": "he-IL-HilaNeural",
        "genre": "מדע בדיוני",
        "title": "נווד הכוכבים",
        "outline": "נער רגיל רוכש יכולת לנוע בין כוכבים",
        "characters": "הגיבור כוכב, בן 16, סקרן; עוזר AI חכם, הומוריסטי",
        "chapter_patterns": [r'פרק \d+'],
        "labels": {
            "title": "כותרת",
            "genre": "ז'אנר",
            "language": "שפה",
            "model": "מודל",
            "generated_at": "תאריך יצירה",
            "total_words": "סה\"כ מילים",
            "summary": "תקציר",
        }
    },
    "hi": {
        "name": "हिन्दी",
        "voice": "hi-IN-SwaraNeural",
        "genre": "विज्ञान कथा",
        "title": "सितारों का यात्री",
        "outline": "एक सामान्य किशोर को अंतरिक्ष यात्रा की क्षमता मिलती है",
        "characters": "मुख्य पात्र सितारा, 16 साल, जिज्ञासु; AI सहायक बुद्धिमान, हास्यप्रिय",
        "chapter_patterns": [r'अध्याय \d+'],
        "labels": {
            "title": "शीर्षक",
            "genre": "शैली",
            "language": "भाषा",
            "model": "मॉडल",
            "generated_at": "निर्माण तिथि",
            "total_words": "कुल शब्द",
            "summary": "सारांश",
        }
    },
}