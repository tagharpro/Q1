<p align="center">
  <img src="assets/icon.png" width="120" alt="Q1 Browser logo">
</p>

<h1 align="center">Q1 Browser 🧭</h1>

<p align="center">
  یک مرورگر دسکتاپ حرفه‌ای برای ویندوز — بر پایه Chromium / Qt WebEngine<br>
  با تب‌ها، بوکمارک، تاریخچه، دانلود، حالت خصوصی و <b>دستیار هوش مصنوعی داخلی</b>.
</p>

<p align="center">
  <a href="https://github.com/tagharpro/Q1/releases">
    <img src="https://img.shields.io/badge/Download-Windows-blue" alt="Download not available yet">
  </a>
</p>

---

## ✅ دانلود و نصب (ویندوز)

نسخه‌ی آماده‌ی ویندوز به‌صورت **یک فایل ZIP** در خود مخزن موجود است:

> 👉 **[Q1Browser-Windows.zip](https://github.com/tagharpro/Q1/blob/v1.0.1-windows/dist/Q1Browser-Windows.zip)** (حدود ۱۳٫۵ MB)

### روش نصب

1. فایل `Q1Browser-Windows.zip` را دانلود کنید.
2. آن را Extract کنید.
3. پوشه‌ی `Q1Browser-WebView2-Windows` را باز کنید.
4. روی `Q1Browser.exe` دوبار کلیک کنید.
5. سیستم‌عامل ممکن است از شما تأیید بگیرد؛ **More info → Run anyway** را بزنید.
   (فایل امضای دیجیتال تجاری ندارد، چون پروژه‌ی متن‌باز/شخصی است.)

این نسخه **پورتابل** است، بدون نصب اجرا می‌شود و فقط به **WebView2 Runtime** (روی ویندوز ۱۱ و اکثر ویندوز ۱۰ نصب است) نیاز دارد.
اگر اجرا نشد، WebView2 Runtime را از [مایکروسافت](https://developer.microsoft.com/microsoft-edge/webview2/) نصب کنید.

---

## ✨ امکانات

- ✅ **تب‌های متعدد** — باز، بستن، جابه‌جایی (مثل اکثر مرورگرها)
- ✅ **نوار آدرس هوشمند** — آدرس بنویسید یا مستقیم جستجو کنید
- ✅ **دکمه‌های Back / Forward / Reload / Stop / Home**
- ✅ **بوکمارک و تاریخچه** — با ذخیره‌ی محلی
- ✅ **مدیریت دانلودها** — پنجره‌ی دانلود با نوار پیشرفت
- ✅ **حالت خصوصی (Private Tab)** — یک پروفایل جدا برای مرور بدون ذخیره در تاریخچه
- ✅ **پنجره‌های جدید / باز شدن لینک‌ها در تب جدید**
- ✅ **صفحه‌ی جدید تب (New Tab)** با جستجو و دسترسی سریع
- ✅ **تنظیمات** — صفحه‌ی اصلی، موتور جستجو، بازیابی تب‌ها، پاک‌سازی داده‌ها
- ✅ **پیاده‌سازی بر پایه‌ی Chromium از طریق Qt WebEngine** (پشتیبانی HTML5/JS/CSS)

## 🤖 دستیار هوش مصنوعی داخلی

Q1 Browser یک پنل AI داخلی دارد. این پنل با هر سروری که **OpenAI-compatible** باشد کار می‌کند؛
یعنی می‌توانید از **Ollama** (رایگان و آفلاین)، **LM Studio**، **vLLM**، **Groq** یا **OpenAI** استفاده کنید.

### راه‌اندازی سریع با Ollama (رایگان، آفلاین)

1. [Ollama](https://ollama.com) را نصب کنید.
2. مدل را دانلود کنید:
   ```bash
   ollama pull llama3.2
   ```
3. سرویس را اجرا کنید:
   ```bash
   ollama serve
   ```
4. در Q1 Browser: **Toolbar → AI Assistant** را فعال کنید، سپس در **Settings → AI** مطمئن شوید:
   - Base URL: `http://127.0.0.1:11434/v1`
   - Model: `llama3.2`
   - API Key: خالی (برای Ollama لازم نیست)

حالا از پنل هوش مصنوعی سؤال بپرسید! جواب‌ها به‌صورت **Streaming** نمایش داده می‌شوند.

---

## 🛠 اجرا از سورس (برای توسعه)

پیش‌نیاز: **Python 3.11+** و **Qt WebEngine** (برای ویندوز راحت‌ترین راه، استفاده از wheel است).

```bash
git clone https://github.com/tagharpro/Q1.git
cd Q1

python -m venv .venv
# windows
.venv\Scripts\activate
# linux/mac
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

## 📦 ساخت نسخه‌ی ویندوز (WebView2)

برای ساخت نسخه‌ی کوچک و Portable با موتور Edge WebView2:

```bash
# python-embed = CPython embeddable wheel (از PyPI)
# webview_wheels = pywebview, pythonnet, bottle, typing_extensions, proxy_tools
# vc-dir       = پوشه‌ای که msvcp140.dll های مایکروسافت را دارد

python tools/package_webview2_windows.py \
  --pyembed-dir /tmp/pyembed \
  --wheel-dir /tmp/webview_wheels \
  --launcher /tmp/buildwin/Q1Browser.exe \
  --vc-dir /path/to/vc-runtime
```

خروجی: `dist/Q1Browser-Windows.zip`

---

## 📁 ساختار پروژه

```
Q1/
├─ run.py               # نقطه‌ی اجرا
├─ q1_browser/
│  ├─ main.py           # QApplication & WebEngine setup
│  ├─ browser_window.py # پنجره، تولبار، منو، تب‌ها
│  ├─ browser_tab.py    # یک تب مرورگر
│  ├─ pages.py          # باز کردن لینک‌ها در تب جدید
│  ├─ ai_panel.py       # دستیار هوش مصنوعی داخلی
│  ├─ download_center.py# مدیر دانلود
│  ├─ dialogs.py        # تنظیمات/بوکمارک/تاریخچه
│  ├─ settings.py       # تنظیمات ماندگار
│  └─ storage.py        # ذخیره‌ی بوکمارک و تاریخچه
├─ windows_app/         # نسخه‌ی WebView2 (Windows portable)
├─ assets/              # آیکون و New Tab
├─ build.py             # ساخت بیلد PyInstaller (نسخه‌ی Qt)
├─ tools/               # اسکریپت‌های بسته‌بندی (Qt و WebView2)
└─ ci/                  # وردفلو GitHub Actions برای بیلد خودکار ویندوز
```

## 📄 مجوز

این پروژه به‌صورت متن‌باز در گیت‌هاب شما منتشر می‌شود. قبل از استفاده‌ی تجاری،
مجوز مورد نظر خودتان را انتخاب کنید (به‌طور پیش‌فرض `MIT` پیشنهاد می‌شود).
