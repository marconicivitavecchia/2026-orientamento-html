# 2026 Orientamento HTML

Laboratorio di informatica per l'orientamento, IIS Marconi di Civitavecchia.

## Di cosa si tratta

Un laboratorio di circa 35 minuti pensato per una ventina di studenti di terza media, uno per computer, aiutati da due o tre tutor. I ragazzi non scrivono HTML da zero: partono da una pagina già pronta (`index.html`) e la personalizzano con cinque sfide a gradini, dal nome ai colori, dall'elenco degli hobby all'immagine, fino ai bottoni che cambiano lo sfondo. Si usa HTML perché è ciò che si fa davvero a scuola, così non si creano false aspettative. La parte finale, la pubblicazione delle pagine online, è facoltativa e si può saltare senza che l'attività perda di senso.

## Prima del laboratorio

Prepara i computer in anticipo: su ogni postazione copia sul desktop `index.html` e la cartella `immagini`, che contiene già alcune foto pronte all'uso. Trovi lo zip `template.zip` con già tutti i file pronti.

Se vuoi aggiungere altre foto, scarica foto libere da diritti (Pexels, Unsplash, Pixabay o Wikimedia Commons sono buone fonti) e passale allo script `prepara_immagini.sh`, che le ridimensiona e ne sistema i nomi, per esempio con `./prepara_immagini.sh foto-scaricate immagini`; richiede ImageMagick e funziona su Linux e macOS, su Windows dentro WSL. Apri l'editor sul file e il browser sulla stessa pagina, affiancati, e se prevedi la consegna online tieni aperto anche il questionario. Dividi le postazioni tra i tutor e consegna a ciascuno la propria scheda.

## Durante il laboratorio

Fai svolgere l'attività seguendo la scheda per gli studenti e la scheda per i tutor, che contengono le sfide, la scaletta dei 35 minuti, gli errori più frequenti e come aiutare senza fare al posto dei ragazzi. Non servono altre istruzioni.

## Consegna e pubblicazione (facoltativo)

A fine laboratorio ogni ragazzo copia il codice dall'editor (Ctrl+A, Ctrl+C) e lo incolla nel questionario online insieme a un nome o a un soprannome. Il modulo ha due sole domande, in quest'ordine: nome o soprannome (risposta breve) e codice della pagina (paragrafo). Non deve richiedere l'accesso con un account Google e deve consentire più invii, così chi sbaglia può rimandare e vale l'ultima versione con lo stesso nome. Metti in conto circa tre minuti in più nella scaletta.

Per creare il sito scarica le risposte del modulo in formato CSV e lancia:

```
python3 pubblica_pagine.py risposte.csv --immagini immagini --logo logo.png
```

Serve Python 3.8 o successivo e non c'è nulla da installare. Lo script crea la cartella `sito` con una pagina per ogni ragazzo e un `index.html` con l'elenco e una casella di ricerca, dove compare il logo della scuola se lo passi con `--logo`. Alla fine segnala le pagine da guardare a mano prima di pubblicare, per esempio quelle che caricano script da altri siti o reindirizzano altrove: controllale e, se serve, escludile con `--escludi nome-del-file`. Se arrivano nuove risposte, riscarica il CSV e rilancia lo script, che rigenera tutto.

Copia poi la cartella `sito` dove preferisci, per esempio nella cartella pubblica del tuo account su studenti.marconicloud.it, e crea con un generatore a scelta il QR code del link da dare ai ragazzi, che cercheranno il proprio nome nell'elenco.

## Dati dei ragazzi

Si tratta di minorenni: invita i ragazzi a non scrivere cognome, indirizzo o altri dati personali nella pagina. Non mettere mai il CSV o gli html nella cartella `sito` in un repository: il `.gitignore` di questo progetto li esclude proprio per evitarlo. Dopo qualche settimana cancella la cartella dal server, le risposte del modulo e il CSV scaricato.