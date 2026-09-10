# Risikovurdering: misbrug af PåVejen

Version 1, pilotperioden. Vurderingen dækker misbrug og ansvarsrisici ved C2C transportmatching, jf. PRD afsnit 18, 19, 20, 37, 47 og 48. Skalaen for sandsynlighed og konsekvens er lav, mellem og høj, vurderet for en lille, geografisk afgrænset pilot.

Vurderingen skelner mellem aktive værn, som systemet selv håndhæver, og passive værn, som informerer, dokumenterer og afskrækker.

## 1. Transport af ulovlige eller forbudte genstande

Sandsynlighed: mellem. Konsekvens: høj, både strafferetligt og for platformens omdømme.

Aktive værn i drift:

- Automatisk screening af opgavetekster mod forbudte kategorier ved oprettelse og redigering. Match opretter en åben rapport til admin og logges i auditloggen. Der blokeres ikke alene på automatik, jf. PRD afsnit 26, men admin kan annullere opgaven og suspendere brugeren.
- Rapportér funktion, hvor chauffører kan anmelde mistænkelige opgaver.
- Obligatorisk bekræftelse ved oprettelse af enhver opgave af, at varen ikke er en forbudt genstand.

Passive værn:

- Vilkårssiden med en udtømmende liste over forbudte genstande.
- Auditlog med bruger, tidspunkt og indhold, som kan udleveres til myndigheder.
- Afhentnings og afleveringskoder, der binder fysiske hændelser til identificerbare konti.

Kendte huller: screeningen er nøgleordsbaseret og kan omgås med omskrivninger. Billeder screenes ikke. Opgradering til AI baseret moderation er planlagt i fase 5.

## 2. Svindel mellem parterne

Eksempler: varen afleveres aldrig, falsk skadesanmeldelse, aftale om betaling uden om platformen, som fjerner dokumentationen.

Sandsynlighed: mellem. Konsekvens: mellem.

Aktive værn:

- Afhentningskode og afleveringskode, så statusskift kræver fysisk udveksling mellem parterne.
- Betalingsreservation, der først frigives efter bekræftet aflevering.
- Konflikthåndtering, hvor betalingen sættes på pause, og admin afgør sagen på baggrund af chat, koder og auditlog.
- Gensidige ratings, der først reelt tæller, når leveringer er gennemført.

Passive værn:

- Al kommunikation holdes i platformens chat, hvilket giver dokumentation ved konflikt.
- Vilkårenes ansvarsfordeling og den maksimale vareværdi på 5.000 kr., som begrænser tabets størrelse.

Kendte huller: ingen identitetsverificering ud over e mail i piloten. MitID i fase 4 reducerer risikoen for falske konti væsentligt.

## 3. Skade, bortkomst og tyveri af varer

Sandsynlighed: mellem. Konsekvens: mellem, begrænset af værdiloftet.

Aktive værn: værdiloft på 5.000 kr. håndhævet i modelvalidering, konflikthåndtering med betalingspause.

Passive værn: vilkårenes tydelige ansvarsfraskrivelse: platformen er formidler, ikke transportør, og dækker ikke skader i piloten. Kravet om ærlig værdi og beskrivelse ligger hos afsenderen, forsvarlig håndtering hos chaufføren.

Kendte huller: ingen forsikring. Integreret transportforsikring er en go live blokering for offentlig lancering, jf. PRD afsnit 48, men accepteres i en lille lukket pilot med informerede deltagere.

## 4. Persontransport og kommerciel kørsel i forklædning

Risikoen er, at platformen utilsigtet formidler taxakørsel eller professionel fragt, som kræver tilladelser.

Sandsynlighed: lav i piloten. Konsekvens: høj, regulatorisk.

Aktive værn: opgavetyperne er begrænset til genstande. Persontransport findes ikke som kategori.

Passive værn: vilkår og positionering, prisen er kompensation for besvær, ikke erhvervsindtægt. Ikke mål listen i PRD afsnit 8 fastholdes.

Kendte huller: en chauffør med meget høj aktivitet kan reelt drive erhverv. Overvågning af aktivitetsniveau pr. chauffør bør tilføjes før offentlig lancering, sammen med skattevejledning, jf. PRD afsnit 47.

## 5. Misbrug af personoplysninger og chikane

Sandsynlighed: lav. Konsekvens: høj for den ramte.

Aktive værn: præcise adresser deles først efter accepteret booking. Telefon og e mail vises ikke direkte. Kun bookingens parter kan se bookingen, håndhævet i views.

Passive værn: GDPR principper i PRD afsnit 35, auditlog over adgang til væsentlige hændelser.

Kendte huller: sletning og eksport af egne data er ikke selvbetjent endnu og håndteres manuelt i piloten.

## 6. Ratingmanipulation og falske konti

Sandsynlighed: mellem ved vækst, lav i piloten. Konsekvens: mellem.

Aktive værn: én rating pr. part pr. booking, håndhævet med unik constraint. Ratings kræver en reel gennemført booking.

Passive værn: auditlogging af hele bookingforløbet gør kunstige transaktionsmønstre synlige.

Kendte huller: gensidig samtidig offentliggørelse af ratings, jf. PRD afsnit 16, er ikke implementeret. Anti fraud signalerne fra PRD afsnit 37, fx mange konti fra samme enhed, kommer efter piloten.

## 7. Platformens eget ansvar

Risikoen er, at platformen anses som part i transporten eller som arbejdsgiver.

Sandsynlighed: lav. Konsekvens: høj.

Passive værn: vilkårenes eksplicitte formidlerrolle, dokumenteret vilkårsaccept med tidsstempel ved kontooprettelse og pr. opgave, betaling håndteret som reservation med planlagt outsourcing til reguleret udbyder i fase 3.

Handlingsregel: juridisk vurdering af C2C transport, platformsansvar, skat og betalingsregler er en go live blokering før offentlig lancering, jf. PRD afsnit 48. Denne vurdering er ikke en erstatning for juridisk rådgivning.

## Opfølgning

Ejeren gennemgår vurderingen efter piloten og ved hver væsentlig funktionsudvidelse. Alle åbne rapporter fra screening og brugere skal behandles i admin inden 48 timer i pilotperioden.
