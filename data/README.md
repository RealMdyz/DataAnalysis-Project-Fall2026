# Data

**Source:** Amazon Reviews'23 — McAuley Lab, UC San Diego
Official page: https://amazon-reviews-2023.github.io/

Raw and processed data are **not** committed to GitHub (see `.gitignore`).
Everything here must be rebuildable from the scripts in `src/`.

<div dir="rtl">

## منشأ داده

| مورد | توضیح |
|---|---|
| سازنده | آزمایشگاه McAuley، دانشگاه UC San Diego |
| مقاله‌ی مرجع | Hou و همکاران (۲۰۲۴)، arXiv:2403.03952 |
| بازه‌ی زمانی کل داده | مه ۱۹۹۶ تا سپتامبر ۲۰۲۳ |
| حجم کل | حدود ۵۷۱ میلیون نقد، ۵۴ میلیون کاربر، ۴۸ میلیون محصول، ۳۳ دسته |
| دسته‌ی ما (Toys_and_Games) | حدود ۱۶٫۳ میلیون نقد، ۸٫۱ میلیون کاربر، ۸۹۰ هزار محصول |
| نوع داده | **مشاهده‌ای** |
| مجوز | مجوز صریحی برای داده منتشر نشده (MIT مخزن گیت‌هاب فقط برای کد است)؛ استفاده‌ی آموزشی، بدون بازنشر، با ارجاع به مقاله |

### نوع داده: مشاهده‌ای

نقدها را خود کاربران به انتخاب خودشان نوشته‌اند و هیچ دخالت یا آزمایش کنترل‌شده‌ای (مثل آزمون A/B) در کار نبوده است. ممکن است عامل سومی مثل قیمت یا کیفیت کلی محصول هم‌زمان روی یک جنبه (مثلاً باتری) و روی امتیاز اثر بگذارد. بنابراین نتایج این پروژه **ارتباط** را نشان می‌دهند، نه **علیت**؛ خروجی نهایی اولویت‌بندی بهبود بر پایه‌ی شواهد است، نه تضمین افزایش امتیاز.

### واحد مشاهده

- فایل نقدها: هر ردیف یک نقد است، یعنی یک کاربر درباره‌ی یک محصول در یک زمان.
- فایل اطلاعات محصول: هر ردیف یک محصول است.
- پس از ادغام، اطلاعات هر محصول به تعداد نقدهایش تکرار می‌شود؛ آماره‌های سطح محصول (مثل میانگین قیمت) باید در سطح محصول حساب شوند، نه نقد.

### واحد محصول: `parent_asin`

نسخه‌های مختلف یک محصول (رنگ، اندازه) شناسه‌ی `asin` جدا ولی `parent_asin` مشترک دارند. از دید صاحب محصول همه یک محصول‌اند و فایل اطلاعات محصول هم با `parent_asin` کلیدگذاری شده است. استفاده از `asin` نقدهای یک محصول را تکه‌تکه می‌کند و تعداد نقد هر بازه را کم می‌کند.

### سوگیری نمونه (خودگزینی)

نقدنویس‌ها نماینده‌ی همه‌ی خریداران نیستند؛ کسانی بیشتر نقد می‌نویسند که تجربه‌ی خیلی خوب یا خیلی بد داشته‌اند. نتایج فقط به جامعه‌ی نقدنویس‌ها تعمیم‌پذیر است.

### محدودیت‌های شناخته‌شده‌ی تولید داده

1. **قیمت** مربوط به زمان جمع‌آوری داده (حدود ۲۰۲۳) است، نه زمان نوشتن نقد.
2. **میانگین امتیاز و تعداد امتیاز** محصول در لحظه‌ی جمع‌آوری ثبت شده‌اند و اطلاعات آینده را در خود دارند (خطر نشت).
3. **بعضی محصولات اطلاعات محصول ندارند**، چون تعداد محصولات از روی نقدها شمرده شده است.
4. نام برخی فیلدها در مستندات رسمی ناهمسان است (مثلاً `helpful_vote` و `helpful_votes`)؛ نام واقعی پس از دانلود بررسی می‌شود.

</div>

## Files
Downloaded with `python src/download_data.py`. Exact URLs, sizes and SHA-256
hashes are in `download_manifest.json`.

| File | Content | Size | Downloaded (UTC) |
|---|---|---|---|
| `raw/Toys_and_Games.jsonl.gz` | User reviews (16,260,406 lines) | 1.95 GB | 2026-10-14 |
| `raw/meta_Toys_and_Games.jsonl.gz` | Product metadata (890,874 lines) | 0.66 GB | 2026-10-14 |

## Subset rules
1. **Remote-controlled products** (task 3, locked before modeling): a product is
   kept if any entry of its `categories` list matches `subset.category_regex` in
   `configs/config.yaml`. Scan results: `reports/phase1/category_scan.json`
   (`python src/scan_category.py`).
2. Spare parts / accessories are **kept** (task 4); vehicles vs parts becomes a
   subgroup comparison in phase 4. Subset built with `python src/build_subset.py`
   -> `processed/meta_rc.parquet` (71,046 products) and
   `processed/reviews_rc.parquet` (862,444 reviews); 0 unparseable lines.
3. **Report units** (task 10, locked before modeling): 3-month calendar windows,
   a product-window needs >= 20 reviews, analysis period 2015-01-01 to 2023-03-31
   (see `window` in `configs/config.yaml` and `notebooks/06_window_feasibility.ipynb`).

## Folder layout
```
data/
  raw/        <- original downloads (ignored by git)
  processed/  <- subsets and cleaned files (ignored by git)
```
