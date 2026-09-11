# PåVejen

C2C matchingplatform, der matcher private personer, som alligevel skal køre en bestemt rute, med andre private, der skal have noget transporteret på eller tæt ved ruten.

Kerneprincippet er:

Ting, der skal flyttes, matches med mennesker, der alligevel skal samme vej.

Dette er den første fungerende prototype, jf. PRD afsnit 40 og 57. Den beviser den tekniske kerne: opret en tur fra A til B, opret et transportbehov fra C til D, og lad systemet afgøre, om det giver mening at kombinere dem.

## Hvad platformen kan

- Opret bruger, login og profilside med rating, verificeringsniveau og gennemførte leveringer.
- Opret, rediger og annuller ture med startsted, destination, afgang, maksimal omvej og ledig kapacitet.
- Gentagne ture, jf. PRD afsnit 23: angiv ugedage, tidspunkt, omvej og kapacitet én gang, så materialiseres kommende ture automatisk, og nye opgaver matches mod dem.
- Opret, rediger og annuller transportbehov med afhentning, aflevering, deadline, størrelse, vægt, cirka værdi og billede.
- Automatisk matching med matchscore, omvejsberegning og prisforslag, både når en opgave og når en tur oprettes.
- Send forespørgsel, accepter eller afvis booking.
- Afhentningskode og afleveringskode, der bekræfter statusskift i transportflowet.
- Privat chat pr. booking med systembeskeder ved statusændringer.
- Gensidig rating efter aflevering. Bookingen afsluttes, når begge har vurderet.
- Notifikationer pr. e mail og web push ved nyt match, forespørgsel, accept, afvisning, afhentning, aflevering, konflikt og nye chatbeskeder, jf. PRD afsnit 22. Push slås til på profilsiden, VAPID nøgler genereres automatisk og gemmes i databasen, og døde abonnementer ryddes op af sig selv.
- PWA: manifest, service worker og appikon, så PåVejen kan installeres på hjemmeskærmen, jf. PRD fase 4. På iPhone er det samtidig forudsætningen for push.
- Betalingslivscyklus, jf. PRD afsnit 13 og 14: betalingen reserveres ved accept og frigives efter aflevering, med 15 % platformsgebyr. Udbyderen er "manual" i piloten, og abstraktionen er klar til Stripe Connect i fase 3.
- Konflikthåndtering, jf. PRD afsnit 20: begge parter kan markere et problem, hvorefter betalingen sættes på pause, og administrator afgør sagen i Django Admin.
- Annullering af accepterede bookinger før afhentning, hvor tur og opgave genåbnes til matching.
- Konflikter afgøres i ét trin i admin: refundér til afsenderen eller frigiv til chaufføren, hvorefter booking, opgave, betaling, chat, auditlog og notifikationer opdateres samlet.
- Vilkår med ansvarsfordeling og forbudte genstande. Accept dokumenteres med tidsstempel ved kontooprettelse, og hver opgave kræver bekræftelse af, at varen er lovlig.
- Automatisk screening af opgavetekster mod forbudte kategorier. Match flages som åben rapport til admin og logges, uden at der blokeres alene på automatik, jf. PRD afsnit 26.
- Rapportering af mistænkelige opgaver, jf. PRD afsnit 19.
- Auditlog over alle væsentlige booking og betalingshændelser, jf. PRD afsnit 17.
- Django Admin som internt administrationsinterface, inklusive betalinger, rapporter og auditlog.

Dermed er MVP fra PRD afsnit 38 dækket. Pengestrømmen afvikles fortsat uden om platformen i den lukkede pilot, men hele flowet og gebyrmodellen er på plads. Stadig udeladt: rigtig betalingsudbyder, MitID, forsikring, push og SMS.

Demodata: `python manage.py seed_demo` opretter to brugere, ture, en gentagen tur, en opgave med matches og en aktiv booking. Login jesper eller martin med kodeordet demo1234.

## Teknisk

- Python 3.11+ og Django 5.2, SQLite som database.
- Django apps under `apps/`: accounts, core, trips, transport, matching, bookings, messaging og ratings, jf. PRD afsnit 31 og 58.
- Matchingmotoren ligger i `apps/matching/services.py` som en separat serviceklasse, jf. PRD afsnit 34.
- Routing er abstraheret i `apps/core/routing.py`. Prototypen bruger luftlinje gange en vejfaktor. En rigtig routing API kan sættes ind uden ændringer i matchingmotoren, jf. PRD afsnit 11.
- Geocoding i `apps/core/geocoding.py`: først et lokalt opslagsværk over danske byer, derefter DAWA, Danmarks Adressers Web API fra Dataforsyningen, som slår rigtige adresser og bynavne op uden API nøgle. Ukendte steder kan stadig angives med manuelle koordinater.
- E mail sendes til konsollen i udvikling. I drift sættes SMTP via miljøvariablerne `DJANGO_EMAIL_BACKEND`, `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`, `DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD` og `PAAVEJEN_BASE_URL` til links i mails.
- Prisforslag i `apps/core/pricing.py`: grundbeløb + omvej + tid + størrelse, jf. PRD afsnit 12.
- Matchscore vægtes med rute 40 %, tidspunkt 25 %, omvej 15 %, kapacitet 10 % og brugerhistorik 10 %, jf. PRD afsnit 10.

## Kom i gang

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Åbn derefter http://127.0.0.1:8000/ og opret to brugere. Lad den ene oprette turen Kolding → Sønderborg og den anden opgaven Kolding → Aabenraa. Systemet finder matchet, beregner omvejen og foreslår en pris.

## Drift

Appen er klar til en lille pilotdeploy: whitenoise serverer statiske filer, og med `DJANGO_DEBUG=0` aktiveres HTTPS redirect, sikre cookies og HSTS. Sæt `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, SMTP variablerne og `PAAVEJEN_BASE_URL`, kør `collectstatic` og `migrate`, og servér med en WSGI server som gunicorn.

Risikovurderingen for misbrug, inklusive aktive og passive værn og kendte huller, ligger i `docs/RISIKOVURDERING.md`. Juridisk vurdering er fortsat en go live blokering før offentlig lancering, jf. PRD afsnit 48.

## Tests

```bash
python manage.py test
```

Testene dækker geometri, routing, pris, matchingmotoren og hele ende til ende flowet fra PRD afsnit 60, inklusive koder, statusskift og ratings.
