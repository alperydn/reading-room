# Reading Room veri şeması

Sayfa üç JSON bloğuyla beslenir. `scripts/build_page.py` bunları şablona yerleştirir; elle düzenlemek gerekirse aşağıdaki biçime uy.

## data.json

```json
{
  "chapters": [
    {"title": "BÖLÜM BAŞLIĞI", "author": "Yazar Adı", "page": 24,
     "blocks": [
       {"t": "h1", "h": "<span class=\"pg\" data-p=\"24\"></span>BÖLÜM BAŞLIĞI<sup data-p=\"24\">∗</sup>"},
       {"t": "h2", "h": "<b>Yazar Adı</b>"},
       {"t": "c",  "h": "[1806]"},
       {"t": "p",  "h": "Paragraf metni… <i>italik</i> …"}
     ]}
  ],
  "notes": {"24": [{"m": "∗", "h": "Dipnot metni"}]}
}
```

| Alan | Anlamı |
|---|---|
| `chapters[].title` | İçindekiler'de ve üst çubukta görünen ad. Büyük harfle yazılmışsa sayfa kendisi başlık düzenine çevirir. |
| `chapters[].author` | Varsa bölümün yazarı (derlemelerde). Boş bırakılabilir. |
| `chapters[].page` | Bölümün başladığı kitap sayfası. Sayfa bilgisi yoksa `null`. |
| `blocks[].t` | `h1` bölüm başlığı, `h2` yazar/alt başlık, `c` ortalanmış küçük satır (tarih, ders adı), `p` paragraf. |
| `blocks[].h` | Bloğun HTML'i. Yalnızca `<i>`, `<b>`, `<sup>`, `<span class="pg">` kullan. |
| `notes["N"]` | N numaralı kitap sayfasının dipnotları. `m` işaret (`1`, `∗`), `h` dipnot HTML'i. |

**Sayfa işareti:** `<span class="pg" data-p="N"></span>` kitap sayfası N'nin başladığı yere konur. Paragrafın ortasına düşebilir. "Sayfaya git" bu işaretleri kullanır; hiç işaret yoksa o alan gizlenir.

**Dipnot işareti:** `<sup data-p="N">1</sup>`. N, işaretin geçtiği sayfa. Sayfa, dipnotu `notes` içinde N, N±1, N±2 anahtarlarında arar; böylece sayfa kayması tolere edilir. Sayfa bilgisi olmayan kaynaklarda N yerine bölüm sırası kullanılır.

**Kaçış:** `build_page.py`, `</` dizisini `<\/` yapar; elle yerleştiriyorsan sen yap.

## gloss.json

```json
{"diyalektik": "Karşıtların çatışmasıyla ilerleyen düşünme ya da gelişme yolu.",
 "aklın hilesi": "Hegel'e göre aklın, insanların kişisel tutkularını kendi amacına araç olarak kullanması."}
```

- Kitabın zor ve tekrar eden 100–200 terimi. Her tanım 1–2 kısa cümle, kitabın bağlamında.
- Çok sözcüklü terimler olabilir.
- Anahtarlar küçük harf. Türkçede `I→ı`, `İ→i` (build_page.py bunu `locale` ayarına göre yapar).
- Sayfa Türkçe ekleri soyarak eşleştirir (`kavramların` → `kavram`). Ünsüz yumuşaması yakalanmaz (`diyalektiği` → `diyalektik` bulunmaz); bu tür sık geçen biçimleri ayrı anahtar olarak ekle.

## config.json

```json
{
  "title": "Hukuka Giriş",
  "lang": "tr",
  "book": "\"Hukuka Giriş\" (ders kitabı, Türkçe)",
  "storePrefix": "hg_",
  "locale": "tr",
  "hidden": [0, 14],
  "persona": "Sen Türkçe hukuk metinleri okuyan birine yardım eden sabırlı bir öğretmensin.",
  "audience": "hukuk bilgisi olmayan",
  "termHint": "Hukukî bir terimse bu metindeki teknik anlamını kısaca belirt.",
  "smallWords": ["ve", "ile", "bir", "üzerine", "olarak", "mu", "için", "de", "da"]
}
```

Yalnızca `title` zorunlu; diğerlerinin genel varsayılanları şablonda vardır. `lang` arayüz ve yapay zekâ cevaplarının dilidir (`tr` ya da `en`); `persona`, `audience`, `termHint` ve sözlük tanımları bu dilde yazılır. `locale` kitap metninin dilidir ve verilmezse `lang` kullanılır. İkisi farklıysa sayfa kitap dilinden arayüz diline çeviri düğmeleri gösterir; `"translate": false` ile kapatılır.

İngilizce arayüz örneği:

```json
{
  "title": "Leviathan",
  "lang": "en",
  "book": "\"Leviathan\" (Thomas Hobbes, 1651)",
  "storePrefix": "lev_",
  "persona": "You are a patient teacher helping someone read early modern political philosophy.",
  "audience": "a reader with no background in philosophy",
  "termHint": "If it is a philosophical term, briefly note the sense Hobbes gives it."
}
``` `storePrefix` her kitapta farklı olmalı, yoksa iki Reading Room sayfası aynı tarayıcıda birbirinin konumunu ezer.
