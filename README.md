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
- E mail notifikationer ved nyt match, forespørgsel, accept, afvisning, afhentning, aflevering og nye chatbeskeder, jf. PRD afsnit 22.
- Rapportering af mistænkelige opgaver, jf. PRD afsnit 19.
- Auditlog over alle væsentlige bookinghændelser, jf. PRD afsnit 17.
- Django Admin som internt administrationsinterface, inklusive rapporter og auditlog.

Dermed er MVP fra PRD afsnit 38 dækket, med én bevidst undtagelse: betaling håndteres uden for platformen i den lukkede pilot, som PRD'en åbner for. Stadig udeladt: MitID, forsikring, push og SMS.

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

## Tests

```bash
python manage.py test
```

Testene dækker geometri, routing, pris, matchingmotoren og hele ende til ende flowet fra PRD afsnit 60, inklusive koder, statusskift og ratings.
