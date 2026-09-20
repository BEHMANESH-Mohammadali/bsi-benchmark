# bsi-benchmark

ابزار بنچمارک برای سنجش این‌که یک چارچوب تحلیل ساختاریافته — امروز فقط **BSI** (Behmanesh Structural Index) به‌طور end-to-end سیم‌کشی شده — نسبت به تولید خام (raw) روی متون علمی چه تفاوتی در کیفیت و دقت تحلیل ایجاد می‌کند.

## این ابزار دقیقاً چه می‌کند؟

مقایسه‌ای زنده بین تحلیلِ تولیدشده با یک پرامپت خام (`raw`) و تحلیلِ تولیدشده با پرامپت یک framework مشخص (امروز: BSI) روی همان مقاله، سپس داوری آن دو توسط یک LLM مستقل. داور خودش معیارهای مقایسه را انتخاب می‌کند (بدون لنگر شدن روی واژگان اختصاصی framework، مثلاً D1–D7/EIG در BSI)، و نتیجه همیشه با فیلد `criteria_source` مشخص می‌کند که داوری واقعاً توسط مدل انجام شده (`"llm"`) یا به روش heuristic بازگشتی (`"heuristic_fallback"`) — که به‌صورت شناخته‌شده به نفع framework مورد آزمایش سوگیری دارد.

### وضعیت واقعی «عمومی‌بودن» برای framework دیگر

یک رجیستری افزونه (`frameworks/registry.py`) و دستور `frameworks` وجود دارد که هدفش این است که framework از هستهٔ ابزار جدا شود و BSI فقط یکی از چند framework ثبت‌شده باشد، نه چیزی hardcode‌شده. **اما این هنوز کل مسیر را framework-agnostic نکرده**: خودِ ROADMAP.md صراحتاً می‌گوید این رجیستری فقط یک seam ایجاد می‌کند تا framework دوم بدون دست‌زدن به کد BSI اضافه شود؛ بازنویسی واقعی `compare`/`self-compare` برای پذیرفتن هر framework دلخواه (نه فقط یک فایل پرامپت به نام «bsi») یک تغییر بزرگ‌تر و پرریسک‌تر است که هنوز انجام نشده. در عمل، امروز `compare` دقیقاً دو حالت پرامپت دارد: `raw` و `bsi` (فایلی که به `--bsi-prompt-file` می‌دهید) — هر پرامپتی می‌توانید در آن فایل بگذارید، ولی معماری و کد هنوز صریحاً حول این دو نام ساخته شده‌اند.

> ریپازیتوری به‌طور کامل روی اندروید و در Termux توسعه داده می‌شود.

---

## فهرست

- [پیش‌نیازها](#پیش‌نیازها)
- [نصب در Termux](#نصب-در-termux)
- [پیکربندی (متغیرهای محیطی)](#پیکربندی-متغیرهای-محیطی)
- [دستورات اصلی](#دستورات-اصلی)
- [پرووایدرهای پشتیبانی‌شده](#پرووایدرهای-پشتیبانی‌شده)
- [اجرای بنچمارک در حالت‌های مختلف](#اجرای-بنچمارک-در-حالت‌های-مختلف)
- [بازداوری (rejudge) بدون تولید مجدد تحلیل‌ها](#بازداوری-rejudge-بدون-تولید-مجدد-تحلیل‌ها)
- [استخراج و بررسی نتایج](#استخراج-و-بررسی-نتایج)
- [ثبت و تجمیع نتایج](#ثبت-و-تجمیع-نتایج)
- [استقرار اسکریپت اصلاح‌شده در Termux](#استقرار-اسکریپت-اصلاح‌شده-در-termux)
- [نکات و مشکلات شناخته‌شده](#نکات-و-مشکلات-شناخته‌شده)

---

## پیش‌نیازها

- Termux (Android)
- Python 3.11+
- کلید API حداقل یکی از generatorهای واقعی (لیست کامل در بخش دستورات)

## نصب در Termux

```bash
pkg update && pkg upgrade -y
pkg install -y python git

git clone https://github.com/ibstrade11-source/bsi-benchmark.git
cd bsi-benchmark

pip install -e .
```

نصب، دستور `bsi-benchmark` را در PATH قرار می‌دهد (تعریف‌شده در `pyproject.toml` به‌عنوان `project.scripts`)؛ نیازی به `python -m ...` نیست.

## پیکربندی (متغیرهای محیطی)

کلیدهای API را در `~/.bashrc` قرار دهید (فقط کلید generatorهایی که واقعاً استفاده می‌کنید لازم است):

```bash
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."
export GEMINI_API_KEY="..."
export GROQ_API_KEY="..."
export OPENROUTER_API_KEY="..."
export GAPGPT_API_KEY="..."

# اختیاری — مدل پیش‌فرض Groq را override می‌کند؛
# اگر ست شده و می‌خواهید مقدار پیش‌فرض (openai/gpt-oss-20b) استفاده شود، unset کنید:
# unset GROQ_MODEL
```

```bash
source ~/.bashrc
```

> ⚠️ اگر `GROQ_MODEL` به‌اشتباه روی مدلی با سقف توکن پایین‌تر ست شده باشد، حتی درخواست‌های کوتاه هم با خطای rate limit مواجه می‌شوند.

---

## دستورات اصلی

| دستور | کاربرد |
|---|---|
| `run` | فقط واکشی مقالات برای یک query و اجرای یک evaluator سطح-دیتاست (امروز فقط `basic` موجود است: صرفاً شمارش مقالات) |
| `evaluate` | نمرهٔ یک تحلیل از‌پیش‌تولیدشده (فایل JSON با schema به نام `AnalyzedDataset`) را با evaluator `bsi` می‌سنجد و D1–D7 + امتیاز BSI + `grounding_ratio` + `tag_coverage` را چاپ می‌کند — برای یک تحلیل تکی، نه بنچمارک خودکار |
| `compare` | بنچمارک خودکار اصلی: واکشی مقاله(ها)، فراخوانی یک یا چند generator زیر یک یا چند حالت پرامپت (raw/bsi)، داوری هر ترکیب، تولید گزارش مقایسه |
| `self-compare` | ثبت مقایسهٔ خوداظهاریِ یک تحلیل‌گر روی یک مقاله؛ معیارها را خودِ تحلیل‌گر انتخاب می‌کند، برندهٔ هر معیار از دو امتیاز raw/bsi مشتق می‌شود نه جداگانه اظهار می‌شود |
| `stats` | تجمیع چند رکورد **self-compare** (نه رکوردهای compare) با فاصلهٔ اطمینان ۹۵٪ bootstrap، Cohen's d_z جفت‌شده، و آزمون تقریبی Wilcoxon signed-rank — بدون وابستگی به scipy/numpy (برای اجرا روی Termux) |
| `frameworks` | فهرست framework‌های ثبت‌شده در رجیستری — امروز فقط `bsi` |

راهنمای کامل هر دستور:

```bash
bsi-benchmark compare --help
```

---

## پرووایدرهای پشتیبانی‌شده

همهٔ پرووایدرهای زیر در `providers/registry.py` ثبت و در `pipeline/runner.py` با یک parser واقعی سیم‌کشی شده‌اند (یعنی همه از طریق `--provider <name>` در `compare`/`run` قابل‌استفاده‌اند):

| پرووایدر | منبع | متن کامل خودکار (`--fetch-full-text`) |
|---|---|---|
| `arxiv` | arXiv | ✅ دانلود PDF + استخراج متن با `pypdf`؛ id‌های قدیمی‌سبک و نسخه‌های withdraw‌شده هم مدیریت می‌شوند |
| `openalex` | OpenAlex | ❌ فقط چکیده (از `abstract_inverted_index` بازسازی می‌شود) |
| `crossref` | Crossref | ❌ فقط چکیده |
| `europepmc` | Europe PMC | ❌ فقط چکیده |
| `semantic_scholar` | Semantic Scholar | ❌ فقط چکیده |
| `mock` | — | برای هر query یک آیتم fixture برمی‌گرداند؛ فقط برای smoke test آفلاین — خروجی `compare` روی `mock` هرگز به‌عنوان benchmark evidence ذخیره نمی‌شود (CLI صراحتاً خطا می‌دهد) |
| `single_article` | — | همیشه همان یک مقالهٔ ثابت (میکروبیوم دهانی/سن زیستی) را برمی‌گرداند، صرف‌نظر از query — برای تست‌های reproducible بدون تماس شبکه‌ای |

برای پرووایدرهایی غیر از `arxiv`، متن کامل را باید دستی با `--full-text-file` بدهید (بخش بعد).

---

## اجرای بنچمارک در حالت‌های مختلف

### ۱) اجرای آفلاین / smoke test (بدون تماس با API واقعی)

```bash
bsi-benchmark compare \
  --provider mock \
  --query "epistemology" \
  --generators mock \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/smoke_test
```

> خروجی این حالت هرگز به‌عنوان نتیجهٔ معتبر ذخیره نمی‌شود؛ فقط برای تست لوله‌کشی کد است.

### ۲) اجرای زنده با یک generator، بدون داور جداگانه (self-judging)

```bash
bsi-benchmark compare \
  --provider openalex \
  --query "environmental policy climate change mitigation" \
  --limit 1 \
  --generators groq \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/env_run1
```

### ۳) اجرای زنده با داور مجزا (برای کاهش سوگیری)

```bash
bsi-benchmark compare \
  --provider arxiv \
  --query "philosophy epistemology" \
  --limit 1 \
  --generators groq \
  --judge openrouter \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/philosophy_run
```

### ۴) با استخراج خودکار متن کامل مقاله (فقط arXiv)

```bash
bsi-benchmark compare \
  --provider arxiv \
  --query "behavioral economics decision making" \
  --limit 1 \
  --generators groq \
  --judge openrouter \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/econ_run \
  --fetch-full-text \
  --fresh
```

روی هر provider دیگری، این فلگ فقط یک هشدار چاپ می‌کند و به حالت چکیده‌محور برمی‌گردد (abstract-only)، اجرا را متوقف نمی‌کند.

### ۵) تأمین دستی متن کامل (برای هر provider غیر از arxiv)

```bash
bsi-benchmark compare \
  --provider openalex \
  --query "..." \
  --limit 1 \
  --generators groq \
  --judge openrouter \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --full-text-file ./article_fulltext.txt \
  --output results/manual_fulltext_run
```

اگر هم `--full-text-file` و هم `--fetch-full-text` داده شوند، `--full-text-file` اولویت دارد.

### ۶) ادامه‌ی اجرا (resume) به‌جای شروع از صفر

بدون `--fresh`، سلولی که تحلیلش قبلاً با موفقیت تولید شده هرگز دوباره تولید نمی‌شود؛ فقط سلولی که داوری‌اش گم، خطادار یا heuristic بوده (`criteria_source != "llm"`) دوباره داوری می‌شود:

```bash
bsi-benchmark compare \
  --provider arxiv \
  --query "philosophy epistemology" \
  --limit 1 \
  --generators groq \
  --judge groq \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/philosophy_run
```

برای شروع کاملاً تازه — چک‌پوینت و گزارش قبلی حذف نمی‌شوند، با پسوند timestamp آرشیو می‌شوند:

```bash
bsi-benchmark compare \
  ... \
  --output results/philosophy_run \
  --fresh
```

### ۷) خوداظهاری (self-compare)

```bash
bsi-benchmark self-compare \
  --input examples/self_compare_example.json \
  --output results/self_compare/philosophy_self
```

فایل ورودی باید معیارها و امتیاز raw/bsi هر معیار را داشته باشد (نمونه‌ی شکل مورد انتظار: `examples/self_compare_example.json`، راهنمای اعلانی که باید به تحلیل‌گر داد: `examples/self_compare_prompt.md`).

### ۸) تنظیم دما، حداکثر توکن و نسخهٔ پرامپت (فقط برای ثبت در متادیتا)

این مقادیر توسط ابزار اعمال نمی‌شوند — فقط در `run_metadata` رکورد می‌شوند تا provenance نتیجه کامل بماند:

```bash
bsi-benchmark compare \
  --provider arxiv --query "..." --limit 1 \
  --generators groq --judge openrouter \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --temperature 0.3 \
  --max-tokens 4000 \
  --prompt-version v3.4.2 \
  --output results/custom_run
```

### ۹) نمرهٔ یک تحلیل از‌پیش‌تولیدشده (بدون فراخوانی هیچ LLM)

```bash
bsi-benchmark evaluate --input examples/sample_analyzed_dataset.json
```

خروجی برای هر آیتم: D1 تا D7، امتیاز نهایی BSI، `grounding_ratio` و `tag_coverage`.

### ۱۰) فقط واکشی مقالات (بدون تحلیل/داوری)

```bash
bsi-benchmark run --provider crossref --query "quantum decision making"
```

---

## بازداوری (rejudge) بدون تولید مجدد تحلیل‌ها

کلید چک‌پوینتِ تحلیل‌ها (`cell_key`: مقاله+generator+mode) از کلید داوری (`judge_key`: مقاله+generator) مستقل است. پس اگر تحلیل‌های raw/BSI قبلاً موفق تولید شده باشند ولی داوری‌شان نامعتبر بوده، کافی‌ست **همان دستور compare را با همان `--output` و بدون `--fresh`** دوباره بزنید — تحلیل‌های کش‌شده تکرار نمی‌شوند و فقط داوری اجرا می‌شود.

### بازداوری با همان داور (retry روی خطای موقت)

```bash
bsi-benchmark compare \
  --provider arxiv --query "philosophy epistemology" --limit 1 \
  --generators groq --judge groq \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/philosophy_run
```

### بازداوری با داور متفاوت (وقتی داور اول شکست خورده یا می‌خواهید نتیجه را با مدل دیگری صحت‌سنجی کنید)

```bash
bsi-benchmark compare \
  --provider arxiv --query "philosophy epistemology" --limit 1 \
  --generators groq --judge openrouter \
  --bsi-prompt-file MASTER_PROMPT_BSI_v3.4.2.md \
  --output results/philosophy_run
```

> یک داوری که واقعاً از یک LLM آمده و خطا نداشته (`criteria_source == "llm"`, بدون `error`/`judge_error`) هرگز بازنویسی نمی‌شود؛ فقط داوری‌های گمشده، خطادار یا heuristic دوباره تلاش می‌شوند.

---

## استخراج و بررسی نتایج

### آمار توصیفی روی رکوردهای self-compare

> ⚠️ دستور `stats` فقط روی رکوردهای **self-compare** کار می‌کند، نه روی خروجی `compare`. این دو داده‌ی کاملاً متفاوتی‌اند: `compare` نتیجهٔ یک داور LLM مستقل است، `self-compare` خوداظهاریِ یک تحلیل‌گر است. برای بررسی نتایج `compare` به بخش بعدی (خواندن مستقیم JSON) مراجعه کنید.

```bash
bsi-benchmark stats \
  --input results/self_compare/*.json \
  --output out/self_compare_agg
```

خروجی شامل میانگین اختلاف (bsi − raw)، فاصلهٔ اطمینان ۹۵٪ (bootstrap) و p تقریبی Wilcoxon است — این آمار همهٔ معیارهای همهٔ رکوردها را در یک نمونه ادغام می‌کند؛ معیارهای داخل یک رکورد (همان مقاله/همان تحلیل‌گر) مستقل از هم نیستند، پس N ظاهری از تعداد مشاهدات مستقل واقعی بزرگ‌تر است (این هشدار در خروجی خودِ دستور هم چاپ می‌شود).

### خواندن مستقیم یک نتیجهٔ compare (JSON)

```bash
cat results/philosophy_run.json | python -m json.tool
```

فیلدهای کلیدی برای بررسی:

- `criteria_source` → باید `"llm"` باشد؛ `"heuristic_fallback"` یعنی داوری واقعی رخ نداده.
- `total_scores` (نه صرفاً `winner`) → معیار قابل‌اعتمادتر، چون فیلد `winner` بدون اعتبارسنجی جداگانه است.
- `has_full_text` / `full_text_fetch_error` (در `input_quality` هر مقاله) → مشخص می‌کند تحلیل روی چکیده انجام شده یا متن کامل.
- `retrieval_status` / `retrieval_validation` → آیا مقالهٔ بازگشتی با query تطابق عنوانی معتبر داشته (برای query‌های شبیه عنوان مقاله) یا رد شده.

### استخراج فقط نتایج معتبر (فیلتر heuristic fallback) با jq

```bash
pkg install -y jq   # در صورت نبودن jq در Termux

find results/ -maxdepth 1 -name '*.json' -exec sh -c \
  'jq -e "[.results[].cells[]?.judge_result.criteria_source] | any(. == \"llm\")" "$1" >/dev/null 2>&1 && echo "$1"' _ {} \;
```

---

## ثبت و تجمیع نتایج

### ۱) اعتبارسنجی و curate کردن نتایج (نسخهٔ اصلاح‌شده)

نسخهٔ قبلی `scripts/validate_and_curate_result.py` سه اشکال داشت که در سندباکس پیدا و رفع شدند:

1. اسکن غیربازگشتی (`glob("*.json")`) بود، پس فایل‌های داخل `results/self_compare/` یا هر زیرپوشهٔ دیگر اصلاً دیده نمی‌شدند.
2. گیت ورودی فقط رکوردهای self-compare را قبول می‌کرد (`article`+`analyst_model`)؛ گزارش‌های `compare` (schema متفاوت: `results`+`run_metadata`) همیشه رد می‌شدند — یعنی پوشهٔ `compare/` در مخزن نتایج هرگز توسط این اسکریپت پر نمی‌شد، برخلاف چیزی که README خودِ آن مخزن ادعا می‌کند.
3. منطق اعتبارسنجی (`walk()` به‌دنبال `judge_result.criteria_source`) برای schema رکوردهای compare نوشته شده بود، در حالی که یک رکورد self-compare اصلاً هرگز کلید `judge_result` ندارد (schema آن یک لیست تخت `criteria` با `raw_score`/`bsi_score` است — نگاه کنید `self_compare/models.py`). پس این اعتبارسنجی روی self-compare عملاً هیچ‌کاره بود؛ تنها گیت واقعی همان چک کلید بالادستی در بند ۲ بود.

نسخهٔ اصلاح‌شده (فایل ضمیمه — `validate_and_curate_result.py`):

- به‌صورت بازگشتی کل `results/` را می‌گردد (`rglob`)، فایل‌های `*.checkpoint.json` و هر چیزی داخل خودِ پوشه‌های مقصد را نادیده می‌گیرد؛
- هر فایل را بر اساس schema واقعی‌اش به `compare` یا `self` طبقه‌بندی می‌کند؛
- رکورد self-compare را دقیقاً با همان `SelfComparisonIO().load()` که خودِ دستور `self-compare` استفاده می‌کند اعتبارسنجی می‌کند (نه یک اعتبارسنج دوم و جدا که ممکن است از آن واگرا شود)؛ نبودِ `raw_analysis_text`/`bsi_analysis_text` رد نمی‌کند، فقط به‌عنوان «غیرقابل‌راستی‌آزمایی مستقل» هشدار می‌دهد — دقیقاً همان رفتار خودِ CLI؛
- گزارش compare را با بازسازی واقعی دیتاکلاس‌های `ComparisonReport`/`ComparisonResult`/`ComparisonCell` و استفاده از `.complete`/`.incomplete_reasons` خودِ کتابخانه اعتبارسنجی می‌کند — همان تعریفِ «قابل‌انتشار» که در بقیهٔ کد هم استفاده می‌شود، نه یک کپی دستی که ممکن است با آن ناسازگار شود؛
- در `compare/` و `self_compare/` **داخل یک مخزن جداگانه** (متغیر محیطی `BSI_BENCHMARK_RESULTS_REPO`) curate می‌کند؛ اگر این متغیر ست نشده باشد، به‌جای شکست خوردن، با یک هشدار به `results/curated/` همین مخزن سورس سقوط می‌کند (fallback)، تا اسکریپت پیش از پیکربندی مخزن جدا هم قابل‌اجرا بماند.

اعتبارسنجی end-to-end در سندباکس: یک رکورد واقعی self-compare (تولیدشده با خودِ CLI)، یک رکورد self-compare در زیرپوشه (برای تست اسکن بازگشتی)، و دو گزارش synthetic compare-cli (یکی با `criteria_source: "llm"` معتبر، یکی با داوری heuristic ناقص) ساخته شد؛ اجرای اسکریپت هر ۴ مورد را درست دسته‌بندی/رد کرد، commit در مخزن مقصد جداگانه درست ثبت شد، اجرای دوم به‌درستی «Nothing new to commit» داد (idempotent)، و حالت fallback بدون متغیر محیطی هم بدون خطا کار کرد.

```bash
export BSI_BENCHMARK_RESULTS_REPO=~/bsi-benchmark-results-bsi
git clone https://github.com/ibstrade11-source/bsi-benchmark-results-bsi.git \
  "$BSI_BENCHMARK_RESULTS_REPO"   # فقط بار اول

python scripts/validate_and_curate_result.py
```

### ۲) ساختار مخزن نتایج جدا

نتایج نهایی هر framework در یک مخزن **مجزا** از سورس نگهداری می‌شوند (`bsi-benchmark-results-bsi`) تا خواندن/زیپ‌کردن سورس تحت‌تأثیر قرار نگیرد و هر framework آینده مخزن نتایج خودش را داشته باشد:

```
compare/        هر نتیجهٔ معتبر compare-cli: یک جفت .json + .md
self_compare/   هر رکورد معتبر self-compare: همان جفت json+md
scripts/
    rebuild_csvs.py                       ۸ گزارش CSV را از compare/*.json می‌سازد
    generate_report.py, build_report.sh   گزارش نهایی یک‌جا (۸ جدول) را از همان CSVها می‌سازد
BENCHMARK_REPORT_8_TABLES.md          خروجی خوانای generate_report.py
```

پس از هر ثبت نتیجهٔ تازه در آن مخزن:

```bash
cd ~/bsi-benchmark-results-bsi
bash scripts/build_report.sh
```

دیدن پیام پایانی `===== BUILD REPORT COMPLETE =====` یعنی هر ۸ جدول CSV و گزارش نهایی با موفقیت و از روی داده‌های واقعی بازسازی شدند.

هر ردیف CSV بر اساس نام فایل و وجود `judge_result` معتبر یکی از این وضعیت‌ها را می‌گیرد: `VALID`، `TEST` (نام فایل شامل الگوهایی مثل `smoke_test`/`mock`)، `ARCHIVED` (نام فایل شامل `archived`)، `UNJUDGED` (بدون `judge_result` معتبر). این طبقه‌بندی مستقل از اعتبارسنجی `validate_and_curate_result.py` است.

---

## استقرار اسکریپت اصلاح‌شده در Termux

جایگزینی مستقیم نسخهٔ رفع‌اشکال‌شدهٔ `validate_and_curate_result.py` روی دستگاه:

```bash
cd ~/bsi-benchmark

# نسخهٔ فعلی را قبل از جایگزینی پشتیبان بگیرید
cp scripts/validate_and_curate_result.py scripts/validate_and_curate_result.py.bak

# فایل اصلاح‌شده را (که همراه این README ارسال شده) در همین مسیر کپی کنید، مثلاً از Downloads:
cp /sdcard/Download/validate_and_curate_result.py scripts/validate_and_curate_result.py

# اجرای آزمایشی بدون مخزن نتایج جدا (fallback به results/curated/) —
# برای اطمینان از رفتار صحیح روی نتایج واقعیِ خودتان، قبل از commit واقعی:
unset BSI_BENCHMARK_RESULTS_REPO
python scripts/validate_and_curate_result.py

# اجرای واقعی، با مخزن نتایج جداگانه:
export BSI_BENCHMARK_RESULTS_REPO=~/bsi-benchmark-results-bsi
python scripts/validate_and_curate_result.py
```

اگر خروجی اجرای آزمایشی (fallback) برای رکوردهای شناخته‌شدهٔ شما درست بود (`CURATED (self): ...` و/یا `CURATED (compare): ...` به تعداد درست، بدون `INVALID` غیرمنتظره)، می‌توانید `results/curated/` تستی را حذف کنید و با `BSI_BENCHMARK_RESULTS_REPO` ست‌شده دوباره اجرا کنید:

```bash
rm -rf results/curated
```

---

## نکات و مشکلات شناخته‌شده

- **Retry عمومی**: تمام generatorها (از جمله Gemini) از طریق لایهٔ مشترک `network/retry.py` یک مکانیزم retry با exponential backoff (حداکثر ۳ تلاش، تأخیر `delay * 2**n`) روی هر استثنای شبکه‌ای و روی پاسخ‌های ۵xx/۴۲۹ دارند — منطق جداگانه‌ای به‌ازای هیچ generator خاصی (از جمله Gemini) پیاده‌سازی نشده؛ همه از همین لایهٔ مرکزی رد می‌شوند.
- **سقف توکن Groq (TPM)**: مدل پیش‌فرض `openai/gpt-oss-20b` سقف ۸۰۰۰ توکن‌بر‌دقیقه دارد. سیستم برای متن مقاله (نه پرامپت داور) با بودجه‌های فشرده‌سازیِ پلکانی تلاش مجدد می‌کند؛ برای پرامپت داور، `max_tokens` جدا و کوچک‌تر رزرو می‌شود تا جای کافی برای گلاسری+RAW+BSI بماند.
- **محدودیت جغرافیایی Gemini**: بدون VPN در برخی شبکه‌ها مسدود است؛ حتی با VPN، اگر کشور خروجی در اتحادیه اروپا باشد ممکن است خطای `"User location is not supported"` بدهد.
- **GapGPT** سهمیهٔ رایگان روزانهٔ تکرارشونده ندارد — فقط یک اعتبار اولیهٔ یک‌باره در زمان ثبت‌نام.
- **`mock` و `single_article`** فقط برای تست هستند؛ خروجی `compare` با generator `mock` صریحاً به‌عنوان benchmark evidence رد می‌شود (CLI با کد خطا متوقف می‌شود).
- **`--fetch-full-text`** فقط روی `--provider arxiv` کار می‌کند؛ روی provider دیگر فقط هشدار می‌دهد و به چکیده برمی‌گردد.
- همیشه پیش از اعتماد به یک نتیجه، فیلد `criteria_source` را بررسی کنید.

---

## ساختار پروژه (خلاصه)

```
bsi-benchmark/
├── src/bsi_benchmark/
│   ├── cli.py
│   ├── benchmark/          # BenchmarkRunner ('run' command)
│   ├── comparison/         # ComparisonSpec, CrossModelRunner, judge.py, checkpoint.py, glossary.py
│   ├── evaluation/         # EvaluationEngine ('evaluate' command, D1-D7 scoring)
│   ├── frameworks/         # FrameworkRegistry — 'bsi' امروز تنها ورودی
│   ├── generation/         # generatorها: anthropic, openai, deepseek, gemini, groq, openrouter, gapgpt, bsi_api, local, mock
│   ├── providers/          # arxiv, openalex, crossref, europepmc, semantic_scholar, mock, single_article
│   ├── parsers/            # پارسر متناظر هر provider
│   ├── pipeline/           # PipelineRunner: واکشی+پارس+retrieval-validation+limit
│   ├── network/            # HttpClient, retry.py (backoff عمومی)
│   ├── self_compare/       # I/O و رندر رکوردهای self-compare
│   ├── models/             # Article, Analysis
│   └── export/, reporting/, common/, errors/, utils/, datasets/
├── scripts/
│   ├── validate_and_curate_result.py
│   ├── run_benchmark.sh
│   └── run_self_compare_with_llm.py
├── examples/                # self_compare_example.json, sample_analyzed_dataset.json, ...
├── tests/
└── results/
    └── self_compare/
```

---

## لایسنس

MIT — طبق فایل `LICENSE` (نویسنده: Mohammadali Behmanesh).

---

> **پیش از commit در مخزن عمومی**: این README بر اساس دو فایل zip ارسالی (سورس + نتایج) در تاریخ نگارش تطبیق داده شده، نه یک اتصال زنده به HEAD مخزن. جزئیات فنیِ قابل‌تغییر — نام دقیق فلگ‌های CLI، فهرست providerها/generatorها، رفتار دقیق `validate_and_curate_result.py` — را یک‌بار با آخرین commit مخزن مقایسه کنید؛ اگر از زمان این zip چیزی commit شده، همان بخش‌ها را به‌روزرسانی کنید.
