---
name: reading-room
description: "Reading Room: Bir PDF, EPUB, DOCX ya da uzun metni; sözlüklü, yapay zekâ ile basitleştir/özetle/açıkla destekli, içindekiler, bölüm gizleme ve tema ayarları olan etkileşimli bir okuma odası sayfasına dönüştürür. Turns a book or long text (PDF, EPUB, DOCX, TXT) into an interactive reading room web page with glossary, AI simplify/summarize/explain, table of contents and themes. Interface in Turkish or English."
metadata:
  display-name: "Reading Room"
  version: "1.4.1"
---

# Reading Room

Kullanıcının verdiği kitabı rahat okunan, etkileşimli tek bir HTML sayfasına dönüştür. Sayfanın kodu hazır: `assets/sablon.html`. **Kodu sıfırdan yazma**; yalnızca veriyi üret ve şablonu `scripts/build_page.py` ile doldur.

Klasördeki dosyalar:

| Dosya | Ne işe yarar |
|---|---|
| `assets/sablon.html` | Sayfanın kabuğu (CSS + HTML + JS). Yer tutucular: `{{TITLE}}`, `{{CONFIG_JSON}}`, `{{DATA_JSON}}`, `{{GLOSS_JSON}}`. |
| `scripts/pdf_to_json.py` | PDF → `data.json` (sayfa no, dipnot, italik/kalın, bölüm). |
| `scripts/text_to_json.py` | TXT / MD / DOCX / EPUB → `data.json` (DOCX/EPUB için pandoc). |
| `scripts/build_page.py` | `data.json` + `gloss.json` + `config.json` → tek HTML; şemayı denetler. |
| `references/veri-semasi.md` | Üç JSON dosyasının ayrıntılı şeması. Veriyi elle düzeltmen gerekirse oku. |

Bu skill'in yolunu `SKILL_DIR` olarak düşün; script'leri oradan çalıştır, çıktıları çalışma klasörüne yaz.

## 1. Önce sor

Kullanıcı belirtmediyse tek seferde sor (soru aracı varsa onunla):
- Hangi dosya? (Ekli değilse yüklemesini ya da klasörünü bağlamasını iste.)
- Varsayılan olarak gizlenecek bölümler var mı? (Önsöz, kaynakça, dizin, belirli yazarlar.) Gizlenenler İçindekiler'den açılabilir kalır.
- Okurun düzeyi ve amacı (sözlük tanımlarının ve yapay zekâ cevaplarının sadeliği için).

**Arayüz dili:** Sayfa Türkçe (`tr`) ya da İngilizce (`en`) olabilir. Yabancı dilde bir kitabı Türkçe arayüzle kurmak, okura çeviri desteği de verir (aşağıda `translate`). Kullanıcı söylemediyse onunla konuştuğun dili seç; ayrıca sorma. Kitabın dili arayüz dilinden farklı olabilir (ör. İngilizce kitap, Türkçe arayüz). Kullanıcıyla İngilizce konuşuyorsan bu talimatları uygula ama ona İngilizce yanıt ver.

## 2. Metni çıkar

**PDF:**
```bash
pip install pdfplumber   # yoksa
python3 $SKILL_DIR/scripts/pdf_to_json.py kitap.pdf --inspect          # önce tanı
python3 $SKILL_DIR/scripts/pdf_to_json.py kitap.pdf -o data.json [--lang en] [--offset N] [--from P] [--chapters bolumler.json]
```
Script şunları yapar: tekrarlayan üst/alt bilgiyi siler, kitap sayfa numarasını (PDF sırası değil) üst/alt bilgiden tahmin eder ve her sayfa başına `<span class="pg">` koyar, satır sonu tirelemesini birleştirir, italik/kalını font adından yakalar, sayfa altındaki küçük puntolu blokları dipnot olarak ayırır, büyük puntolu satırları bölüm başlığı sayar. Sonunda stderr'e bir rapor yazar.

Raporu oku ve gerekirse düzelt:
- **`sayfa_ofseti`** tutarsızsa ya da "bulunamadı" diyorsa kitabın birkaç sayfasına bakıp `--offset` ver (kitap sayfası = PDF sırası + offset).
- **Bölümler** yanlışsa (başlık bulunamadı, fazla bölüm çıktı) içindekiler sayfasından bir `bolumler.json` hazırla: `[{"title": "…", "author": "…", "page": 24}, …]` ve `--chapters` ile ver.
- **Kapak ve ön sayfalar** gerekmiyorsa `--from` ile atla.
- `dipnot_isareti` ile `eslesen_isaret` çok farklıysa dipnot düzeni alışılmadık demektir; birkaç sayfayı elle kontrol et.
- **Metin katmanı yoksa** (taranmış PDF) script durur. Kullanıcıya OCR gerektiğini söyle (`ocrmypdf` kurulabiliyorsa uygula).

**EPUB / DOCX / TXT / MD:**
```bash
python3 $SKILL_DIR/scripts/text_to_json.py kitap.epub -o data.json
```
Bu kaynaklarda kitap sayfası olmadığından sayfa işareti konmaz; "Sayfaya git" kendiliğinden gizlenir.

**Kontrol et:** `data.json`'dan üç dört bölümü örnekle oku. Kopmuş paragraf, kaçmış dipnot, yanlış yere düşmüş sayfa işareti, metne karışmış üst bilgi olmasın. Küçük hataları JSON'da doğrudan düzelt (şema: `references/veri-semasi.md`).

## 3. Sözlüğü yaz (gloss.json)

Metni okuyarak kitabın zor ve tekrar eden **100–200 terimini** seç. Her birine kitabın bağlamında, okurun düzeyine uygun 1–2 kısa cümlelik tanım yaz. Terimler kitabın dilinde, tanımlar **arayüz dilinde** olsun. Çok sözcüklü terimler ("aklın hilesi") de olabilir. Anahtarları küçük harfle yaz. Tanımları kendin yaz; başka sözlüklerden kopyalama.

## 4. Ayarları yaz (config.json)

```json
{
  "title": "Kitap Adı",
  "lang": "tr",
  "book": "\"Kitap Adı\" (Yazar; Türkçe çeviri)",
  "storePrefix": "ka_",
  "locale": "tr",
  "hidden": [0, 12],
  "persona": "Sen Türkçe <alan> metinleri okuyan birine yardım eden sabırlı bir öğretmensin.",
  "audience": "<alan> bilgisi olmayan",
  "termHint": "<Alana özgü> bir terimse bu metindeki özel anlamını kısaca belirt."
}
```
- `storePrefix`: kitaba özgü kısa önek. Aynı tarayıcıdaki başka okuma odalarıyla çakışmasın.
- `hidden`: varsayılan gizli bölümlerin `data.json`'daki sırası (0'dan). Hepsi görünsün isteniyorsa `[]`.
- `lang`: arayüzün ve yapay zekâ cevaplarının dili, `tr` ya da `en`.
- `persona` / `audience` / `termHint`: yapay zekâ istemlerini kitabın alanına uyarla (felsefe, hukuk, tıp, edebiyat…). **`lang` dilinde yaz.** `audience` Türkçede "… birinin rahatça anlayacağı" kalıbına girer ("hukuk bilgisi olmayan"), İngilizcede tam bir isim öbeğidir ("a reader with no legal background"). Vermezsen şablondaki genel varsayılanlar kullanılır.
- `locale`: kitap metninin dili (`tr`, `en`, `de`…); büyük/küçük harf ve sözlük eşleştirmesi buna göre yapılır. Vermezsen `lang` kullanılır. Ek soyma yalnızca Türkçe ve İngilizce için var.
- `translate`: kitabın dili arayüz dilinden farklıysa (`locale` ≠ `lang`) çeviri kendiliğinden açılır; kapatmak için `false`, zorla açmak için `true`.
- `smallWords`: başlıklarda küçük kalacak bağlaçlar. Türkçe ve İngilizce kitaplar için `locale`'e göre hazır; kitap başka dildeyse o dilin listesini ver.

## 5. Sayfayı üret

```bash
python3 $SKILL_DIR/scripts/build_page.py --data data.json --gloss gloss.json --config config.json -o "<kitap>-reading-room.html"
```
Script şemayı denetler; HATA varsa düzelt, UYARI'ları değerlendir.

## 6. Dene

Playwright varsa sayfayı aç ve şunları dene, ekran görüntüsüne bak:
- Sayfa konsol hatası olmadan yükleniyor; bölüm sayısı doğru; varsayılan gizli bölümler gizli.
- Sözlükteki bir kelimeye tıklayınca kutu açılıyor ve tanım görünüyor.
- Bir dipnot işareti doğru metni gösteriyor.
- "Sayfaya git" doğru yere götürüyor (sayfa işareti varsa).

## 7. Teslim et

**claude.ai'de, artifact araçları varsa** (`publish_files` / `publish_version`):
1. İlk yayından önce `guide` (topic: pages) oku.
2. Sayfayı **yeni bir artifact** olarak yayınla (`publish_files`, `index.html`). Başlık: "<Kitap adı> — Reading Room", ikon: "Book". Yayın sonucu `sample` yeteneğinin bildirilmediği uyarısını verir; bu beklenen bir durum.
3. Yapay zekâ özellikleri `claude.use('sample')` ile çalışır. Yayından **sonra** `declare_capabilities` ile `{"sample": {}}` bildir (`base_version`: yayın sonucundaki `version`). Bildirim yapılmazsa sayfa açılır ama yapay zekâ düğmeleri devre dışı kalır.

**Artifact araçları yoksa** (Claude Code, API, başka ortamlar): HTML dosyasını kullanıcıya teslim et. Dosya tarayıcıda tek başına açılır; sözlük, dipnot, içindekiler, temalar ve konum hatırlama çalışır. Yapay zekâ düğmeleri bu ortamda devre dışı kalır ve seçilen metni kopyalama seçeneği sunar. Kullanıcıya bunu bir cümleyle söyle. Sayfaya API anahtarı gömme.

Teslim mesajı kısa olsun: kaç bölüm, varsayılan olarak hangilerinin gizli olduğu ve gizlenenlerin İçindekiler'den göz simgesiyle açılabildiği.

**Telif:** Kullanıcının kendi kopyasından ürettiği sayfa ona özeldir. Kitap telifliyse sayfayı herkese açık paylaşmaması gerektiğini bir cümleyle hatırlat.

## Sonradan değişiklikler

- Veri değişikliği (yazım hatası, bölüm adı, yeni terim): JSON'u düzelt, `build_page.py`'yi yeniden çalıştır, aynı artifact'e yeniden yayınla (claude.ai'de `list_files` → `base_version`).
- Kullanıcı okuma sayfasına dokunulmamasını istediyse özet, sunum notu gibi çıktıları **ayrı bir doküman** olarak üret.
- Şablonda olmayan özellikleri (ör. sesli okuma) kullanıcı istemedikçe ekleme.

## Sayfanın özellikleri (şablonda hazır)

- Üst çubuk: İçindekiler, o anki bölüm adı, "Bulunduğum yeri özetle", görünüm ayarları; aşağı kayınca gizlenir; ilerleme çizgisi.
- Arayüz dili: Türkçe ya da İngilizce (`lang`).
- Çeviri (kitap dili arayüz dilinden farklıysa): kelimeye dokununca bağlamdaki karşılığı (ör. İngilizce kitapta "Türkçesi"), "Cümleyi çevir" düğmesi ve seçim çubuğunda "Çevir". Yapay zekâ yoksa seçili metni Google Çeviri'de açan bağlantı çıkar.
- Görünüm: 4 tema (Sepya, Krem, Yeşil, Gece), yazı boyutu, satır aralığı, satır genişliği, Kitap/Sade yazı tipi; ayar değişince okunan yer korunur.
- Kelimeye dokununca açılır kutu: sözlük tanımı, "Bu cümledeki anlamı" (yapay zekâ), "Cümleyi basitleştir".
- Metin seçince alt çubuk: Basitleştir / Özetle / Açıkla → yan panelde akan cevap, takip sorusu, "Daha da basit anlat", "Örnek ver".
- Dipnot işaretine dokununca dipnot metni.
- İçindekiler: bölüm listesi, "Sayfaya git", göz simgesiyle bölüm gizle/göster, "Tümünü göster", "Varsayılana dön".
- Okuma konumu, ayarlar ve gizli bölümler tarayıcı belleğinde hatırlanır.
