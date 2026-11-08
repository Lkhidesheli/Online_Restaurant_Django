# ონლაინ რესტორანი — Python / Django

ორი გვერდი: კერძების მენიუ და შეკვეთების კალათა.

## გაშვება Windows-ზე

საჭიროა Python 3.12 ან უფრო ახალი ვერსია. პროექტის საქაღალდეში PowerShell-ით:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
```

გახსენი http://127.0.0.1:8000/ . იგივე ნაბიჯებს ასრულებს `start.ps1`.

Linux/macOS-ზე გამოიყენე `.venv/bin/python` Windows-ის `.venv\Scripts\python.exe`-ის ნაცვლად.

## ფუნქციები

- კატეგორიები: Salads, Soups, Chicken-Dishes, Beef-Dishes, Seafood-Dishes, Vegetable-Dishes, Bits&Bites, On-The-Side.
- კომბინირებული ფილტრები: კატეგორია, სიცხარე 0–4, ნიგვზიანი და ვეგეტარიანული — ყველა/კი/არა.
- თითოეულ ქარდზე სურათი, სახელი, სიცხარე, ორივე ნიშანი, ფასი და დამატების ღილაკი.
- კალათაში რაოდენობის შეცვლა 1–99, წაშლა, გასუფთავება და ავტომატური ჯამი.
- კალათა ინახება Django session-ში. ბრაუზერი იღებს მხოლოდ session cookie-ს; პროდუქტის ID და რაოდენობა ინახება სერვერზე SQLite-ში.
- ფასებსა და ჯამს ითვლის Python `Decimal`-ით, API-ის მიმდინარე მონაცემებიდან; ბრაუზერის მიერ გამოგზავნილი ფასი არ მიიღება.
- მუშაობს ჩვეულებრივი Django ფორმებითაც; JavaScript აუმჯობესებს დამატებასა და კალათის განახლებას სრული გადატვირთვის გარეშე.
- CSRF დაცვა, POST მოქმედებები, რაოდენობის სერვერული ვალიდაცია და API-ის შეცდომის ცალკე შეტყობინება.
- მობილურზე მორგებული განლაგება, კლავიატურის ნავიგაცია.

## API

https://restaurant.stepprojects.ge/swagger/index.html

გამოიყენება `GET /api/Products/GetAll` და `GET /api/Categories/GetAll`. ფილტრაციას Python ასრულებს API-ის მონაცემებზე. წარმატებული პროდუქტები ინახება პროცესის cache-ში 60 წამით, კატეგორიები — 5 წუთით. API-ის ველის სახელი `vegeterian` უცვლელია. Baskets API-ის ნაცვლად გამოიყენება მომხმარებლის იზოლირებული Django session. გადახდა და რეალური შეკვეთის გაგზავნა დავალებაში არ შედის.

## სტრუქტურა

- `config/` — Django პარამეტრები, URL-ები, WSGI/ASGI.
- `restaurant/api.py` — გარე API და მონაცემების ვალიდაცია.
- `restaurant/forms.py` — ფილტრებისა და რაოდენობის ვალიდაცია.
- `restaurant/cart.py` — სერვერული კალათა და ჯამები.
- `restaurant/views.py` — გვერდები და POST მოქმედებები.
- `restaurant/templates/` — Django HTML შაბლონები.
- `restaurant/static/` — CSS და დამატებითი JavaScript.
- `restaurant/tests.py` — ავტომატური ტესტები.

## ტესტები

```powershell
.venv\Scripts\python.exe manage.py test
.venv\Scripts\python.exe manage.py check
```

ტესტები ამოწმებს კომბინირებულ ფილტრებს, სიცხარეს 0, „არა“ მნიშვნელობებს, API-დან ფასის აღებას, session იზოლაციას, რაოდენობის საზღვრებს, წაშლას, CSRF დაცვას, POST შეზღუდვასა და ქსელის გათიშვისას კალათის შენარჩუნებას.

## ჰოსტინგი

GitHub Pages Python/Django-ს არ ასრულებს. სერვერზე დააყენე `requirements.txt`, გაუშვი `python manage.py migrate` და `python manage.py collectstatic --noinput`, შემდეგ:

```text
waitress-serve --listen=0.0.0.0:8000 config.wsgi:application
```

გარემოს ცვლადები: `DJANGO_DEBUG=0`, ძლიერი `DJANGO_SECRET_KEY`, რეალური `DJANGO_ALLOWED_HOSTS` და `DJANGO_CSRF_TRUSTED_ORIGINS`. `.env.example` მაგალითია — `.env` ავტომატურად არ იტვირთება; ცვლადები მიუთითე ჰოსტინგის პარამეტრებში. HTTPS ტერმინაციის მქონე სანდო proxy-ს შემთხვევაში `DJANGO_TRUST_PROXY=1`. საჭიროა მუდმივი საცავი SQLite-სთვის, ან PostgreSQL-ზე მორგება. ეს კონფიგურაცია გათვლილია ერთ სერვერზე. განვითარების საიდუმლო, session ბაზა და `.env` Git-ში არ იტვირთება.
