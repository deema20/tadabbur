from datetime import date
from functools import lru_cache

import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)
API = "https://api.alquran.cloud/v1"
EDITIONS = "quran-uthmani,ar.muyassar,ar.jalalayn"

# آيات مختارة لكل حالة (سورة، آية)
MOODS = {
    "القلق": [(13, 28), (94, 5), (2, 286)],
    "الحزن": [(9, 40), (12, 86), (93, 3)],
    "الصبر": [(2, 153), (39, 10), (3, 200)],
    "الشكر": [(14, 7), (31, 12)],
    "التوبة": [(39, 53), (4, 110)],
    "الرزق": [(65, 3), (11, 6)],
    "الخوف": [(3, 173), (2, 38)],
    "الهداية": [(1, 6), (29, 69)],
}
DAILY = [v for lst in MOODS.values() for v in lst]


@lru_cache(maxsize=512)
def get_ayah(s, a):
    r = requests.get(f"{API}/ayah/{s}:{a}/editions/{EDITIONS}", timeout=10)
    r.raise_for_status()
    d = r.json()["data"]
    return {
        "s": s, "a": a,
        "surah": d[0]["surah"]["name"],
        "text": d[0]["text"],
        "muyassar": d[1]["text"],
        "jalalayn": d[2]["text"],
    }


def safe_ayah(s, a):
    try:
        return get_ayah(s, a)
    except Exception:
        return None


BASE = """
<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>تدبّر</title>
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{--g:#0f5132;--g2:#198754;--gold:#c9a227;--bg:#fbf8ef;--card:#fff;--tx:#1d2a22}
@media(prefers-color-scheme:dark){:root{--bg:#0e1612;--card:#17231c;--tx:#eef3ee}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font-family:Tajawal,sans-serif;line-height:1.9}
header{background:linear-gradient(135deg,var(--g),var(--g2));color:#fff;text-align:center;padding:36px 16px}
header a{color:#fff;text-decoration:none}
header h1{margin:0;font-family:Amiri,serif;font-size:2.6rem;color:#f5e6a8}
main{max-width:860px;margin:auto;padding:20px}
.card{background:var(--card);border-radius:16px;padding:22px;margin:16px 0;box-shadow:0 2px 12px #0002;border-top:4px solid var(--gold)}
.ayah{font-family:Amiri,serif;font-size:1.9rem;text-align:center;line-height:2.4}
.chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.chip{background:var(--g2);color:#fff;padding:8px 20px;border-radius:30px;text-decoration:none}
.chip:hover{background:var(--gold)}
input,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #8886;font:inherit;background:var(--bg);color:var(--tx)}
button{background:var(--g);color:#fff;border:0;padding:10px 22px;border-radius:10px;font:inherit;cursor:pointer;margin-top:8px}
.ref{color:var(--gold);font-weight:700;text-align:center}
.nav{display:flex;justify-content:space-between}
a{color:var(--g2)}
h3{color:var(--g2);margin-bottom:4px}
</style></head><body>
<header><a href="/"><h1>﷽ تدبّر</h1></a><div>اقرأ الآية بحسب حالك، وافهمها بتفسيرها</div></header>
<main>{{ body|safe }}</main></body></html>
"""

HOME = """
<div class="card"><h3>✨ آية اليوم</h3>
{% if d %}<div class="ayah">{{ d.text }}</div>
<div class="ref">سورة {{ d.surah }} - آية {{ d.a }}</div>
<p style="text-align:center"><a href="/ayah/{{ d.s }}/{{ d.a }}">اقرأ التفسير ←</a></p>
{% else %}<p>تعذر الاتصال بالإنترنت لجلب الآية.</p>{% endif %}</div>

<div class="card"><h3>💚 كيف حالك اليوم؟</h3>
<div class="chips">{% for m in moods %}<a class="chip" href="/mood/{{ m }}">{{ m }}</a>{% endfor %}</div></div>

<div class="card"><h3>🔎 ابحث في القرآن</h3>
<form action="/search"><input name="q" placeholder="اكتب كلمة مثل: الصبر" required>
<button>بحث</button></form></div>
"""

MOOD = """
<h2 style="text-align:center">آيات في موضوع «{{ mood }}»</h2>
{% for d in items %}<div class="card"><div class="ayah">{{ d.text }}</div>
<div class="ref">سورة {{ d.surah }} - آية {{ d.a }}</div>
<h3>التفسير الميسّر</h3><p>{{ d.muyassar }}</p>
<a href="/ayah/{{ d.s }}/{{ d.a }}">التفسير الكامل وكتابة تدبّرك ←</a></div>
{% else %}<p>تعذر جلب الآيات، تأكد من الإنترنت.</p>{% endfor %}
"""

AYAH = """
<div class="card"><div class="ayah">{{ d.text }}</div>
<div class="ref">سورة {{ d.surah }} - آية {{ d.a }}</div></div>
<div class="card"><h3>📖 تفسير الميسّر</h3><p>{{ d.muyassar }}</p>
<h3>📖 تفسير الجلالين</h3><p>{{ d.jalalayn }}</p></div>
<div class="card"><h3>📝 دفتر تدبّري</h3>
<textarea id="n" rows="4" placeholder="ماذا تعلمت من هذه الآية؟ وكيف أطبقها؟"></textarea>
<button onclick="save()">حفظ</button> <button onclick="share()">مشاركة</button>
<span id="m"></span></div>
<div class="nav">
{% if d.a > 1 %}<a href="/ayah/{{ d.s }}/{{ d.a - 1 }}">→ الآية السابقة</a>{% else %}<span></span>{% endif %}
<a href="/ayah/{{ d.s }}/{{ d.a + 1 }}">الآية التالية ←</a></div>
<script>
const k="note-{{ d.s }}-{{ d.a }}", n=document.getElementById("n"), m=document.getElementById("m");
try{n.value=localStorage.getItem(k)||""}catch(e){}
function save(){try{localStorage.setItem(k,n.value);m.textContent=" ✓ تم الحفظ"}catch(e){}}
function share(){const t=n.value+"\\n\\n"+{{ d.text|tojson }}+" ("+{{ d.surah|tojson }}+": {{ d.a }})";
 if(navigator.share){navigator.share({text:t})}else{navigator.clipboard.writeText(t);m.textContent=" ✓ تم النسخ"}}
</script>
"""

SEARCH = """
<div class="card"><form><input name="q" value="{{ q }}" required><button>بحث</button></form></div>
<p>{{ count }} نتيجة (نعرض أول 15)</p>
{% for r in results %}<div class="card"><div class="ayah" style="font-size:1.5rem">{{ r.text }}</div>
<div class="ref">{{ r.surah.name }} - آية {{ r.numberInSurah }}</div>
<p style="text-align:center"><a href="/ayah/{{ r.surah.number }}/{{ r.numberInSurah }}">التفسير ←</a></p></div>
{% endfor %}
"""


def page(tpl, **kw):
    return render_template_string(BASE, body=render_template_string(tpl, **kw))


@app.route("/")
def home():
    s, a = DAILY[date.today().toordinal() % len(DAILY)]
    return page(HOME, d=safe_ayah(s, a), moods=MOODS.keys())


@app.route("/mood/<mood>")
def mood(mood):
    items = [x for x in (safe_ayah(s, a) for s, a in MOODS.get(mood, [])) if x]
    return page(MOOD, mood=mood, items=items)


@app.route("/ayah/<int:s>/<int:a>")
def ayah(s, a):
    d = safe_ayah(s, a)
    if not d:
        return page("<div class='card'>الآية غير موجودة أو تعذر الاتصال.</div>"), 404
    return page(AYAH, d=d)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    results, count = [], 0
    try:
        r = requests.get(f"{API}/search/{q}/all/quran-simple", timeout=10).json()
        if r.get("code") == 200:
            count = r["data"]["count"]
            results = r["data"]["matches"][:15]
    except Exception:
        pass
    return page(SEARCH, q=q, results=results, count=count)


if __name__ == "__main__":
    app.run(debug=True)
