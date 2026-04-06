# Manuál: Nasadenie a prevádzka backendovej infraštruktúry

Tento dokument slúži ako edukačná príručka pre nasadenie komplexnej kontajnerizovanej architektúry. Krok za krokom vysvetľuje prípravu servera, inštaláciu potrebných nástrojov, konfiguráciu aplikačného prostredia a nastavenie monitorovacích služieb.

---

## Časť 1: Príprava a zabezpečenie Linux servera

Pred samotným nasadením akejkoľvek aplikácie je dôležité pripraviť čistý operačný systém (v príručke sme pracovali s distribúciou založenou na Ubuntu/Debian). Cieľom tohto kroku je minimalizovať bezpečnostné riziká.

### 1.1 Aktualizácia systému
Základným bezpečnostným pravidlom je pracovať s najnovšími verziami, ktoré obsahujú bezpečnostné záplaty.
```bash
# Aktualizácia zoznamu dostupných aktualizácií
sudo apt update

# Inštalácia najnovších verzií softvéru
sudo apt dist-upgrade -y
```

### 1.2 Vytvorenie dedikovaného používateľa (Non-root user)
Z bezpečnostných dôvodov by sa aplikácie a bežná správa servera **nemali vykonávať pod používateľom `root`**. Vytvoríme si nového používateľa (napr. `deploy`) a pridelíme mu administrátorské práva.

```bash
# Vytvorenie nového používateľa
sudo adduser deploy

# Pridanie používateľa do skupiny 'sudo' pre možnosť vykonávať administrátorské zásahy
sudo usermod -aG sudo deploy

# Prepnutie sa na nového používateľa
su - deploy
```

### 1.3 Konfigurácia Firewallu (UFW - Uncomplicated Firewall)
Na ochranu servera pred neautorizovaným prístupom z internetu nakonfigurujeme firewall tak, aby predvolene blokoval všetku prichádzajúcu komunikáciu a povolil len to, čo potrebujeme.

```bash
# Inštalácia ufw
sudo apt install ufw -y

# Nastavenie predvolených pravidiel
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Povolenie SSH prístupu (aby sme sa po zapnutí firewallu neodrezali od servera)
# UFW profil 'OpenSSH' automaticky otvorí port 22
sudo ufw allow OpenSSH

# Alternatíva pre vyššiu bezpečnosť: Uzamknutie SSH len pre konkrétnu IP adresu administrátora
# sudo ufw allow from <TVOJA_IP_ADRESA> to any port 22

# Zapnutie firewallu a kontrola stavu
sudo ufw enable
sudo ufw status verbose
```

---

## Časť 2: Kontajnerizácia (Docker) a príprava prostredia

Aby sme zabezpečili konzistentnosť prostredia, využijeme Docker. Odporúča sa inštalovať Docker z jeho oficiálnych repozitárov, aby sme mali prístup k najnovším aktualizáciám.

### 2.1 Inštalácia platformy Docker

Pridanie oficiálneho GPG kľúča (slúži na kryptografické overenie pravosti sťahovaných súborov):
```bash
sudo apt update
sudo apt install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Pridanie Docker repozitára medzi zdroje systému:
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null
```

Samotná inštalácia Dockeru a pluginu Docker Compose:
```bash
sudo apt update 
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

Kontrola, či služba beží:
```bash
sudo systemctl status docker
# V prípade potreby manuálne spustenie: sudo systemctl start docker
```

### 2.2 Konfigurácia práv pre Docker
Štandardne vyžaduje Docker na svoju prácu práva administrátora (`sudo`). Pre pohodlnejšiu prácu a automatizáciu (CI/CD pipelines) pridáme nášho používateľa `deploy` do systémovej skupiny `docker`.

```bash
# Pridanie aktuálneho používateľa do skupiny docker
sudo usermod -aG docker $USER

# Upozornenie: Aby sa zmeny prejavili, je potrebné sa odhlásiť a znova prihlásiť
newgrp docker

# Verifikácia funkčnosti
docker run hello-world
```

### 2.3 Príprava spojenia s repozitárom (GitHub SSH)
Na bezpečné a pohodlné sťahovanie zdrojového kódu zo súkromných repozitárov bez nutnosti zadávať heslo si vygenerujeme SSH kľúč.

```bash
# Vygenerovanie SSH kľúča (algoritmus ed25519)
ssh-keygen -t ed25519 -C "deploy@nas-server"

# Zobrazenie verejnej časti kľúča
cat ~/.ssh/id_ed25519.pub
```
*Tento vygenerovaný text je potrebné skopírovať a vložiť do nastavení GitHubu (Settings -> SSH and GPG keys -> New SSH key).*

Následne overíme, či je autentifikácia úspešná:
```bash
# Systém sa spýta na pridanie odtlačku do známych hostiteľov (napíšte 'yes')
ssh -T git@github.com
# Očakávaný výstup: "Hi <username>! You've successfully authenticated..."
```

### 2.4 Príprava adresárovej štruktúry
Vytvoríme si hlavný priečinok pre naše aplikácie a presunieme sa doň. Následne sme pripravení naklonovať náš projekt.
```bash
mkdir ~/apps
cd ~/apps
# git clone git@github.com:TvojeMeno/TvojProjekt.git
```

## Časť 3: Konfigurácia aplikácie a bezpečné nasadenie

Keď máme stiahnutý zdrojový kód našej aplikácie, musíme ho pripraviť na bezpečné lokálne spustenie. To zahŕňa prácu s citlivými premennými, prípravu šifrovacích certifikátov a konfiguráciu webového servera (reverzného proxy).

### 3.1 Správa citlivých údajov (Súbor `.env`)
Nezávisle od toho, v akom jazyku je aplikácia napísaná, citlivé dáta (ako heslá do databázy, API kľúče, porty) **nesmú byť súčasťou zdrojového kódu v Gite**. Používame na to environment premenné.

V koreňovom adresári projektu vytvoríme súbor `.env`:
```bash
# Vytvorenie a úprava súboru v nejakom editore odporúčam vim (naučiť sa vim motions !!!) 
nano .env
```

*Príklad obsahu súboru `.env`:*
```env
# Databáza
POSTGRES_USER=admin
POSTGRES_PASSWORD=heslo
POSTGRES_DB=nazov_db

# Názov kontajnerov (pre lepšiu orientáciu v Docker výpisoch)
CONTAINER_NAME=backend_api

# RabbitMQ (Message Broker)
RABBITMQ_USER=rabbit_admin
RABBITMQ_PASSWORD=rabbit_pass
```
### 3.2 Šifrovanie komunikácie (HTTPS / TLS)
Webové rozhrania a API by mali vždy komunikovať šifrovane. Máme dve možnosti, v závislosti od toho, v akom prostredí systém beží.

#### Možnosť A: Self-signed certifikáty (Pre lokálne siete/IP adresy)
Ak server nemá verejnú doménu a pristupujeme naň iba cez IP adresu, vygenerujeme si certifikát podpísaný sám sebou. Prehliadač síce zobrazí varovanie, ale komunikácia bude šifrovaná.
```bash
mkdir -p nginx/certs
cd nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem
```

#### Možnosť B: Let's Encrypt / Certbot (Pre verejné domény)
Ak máme verejnú IP adresu a zakúpenú doménu (napr. `api.mojadomena.sk`), ktorá smeruje na náš server, môžeme získať bezplatný a dôveryhodný certifikát.
```bash
# Inštalácia nástroja Certbot
sudo apt install certbot -y

# Vygenerovanie certifikátu (vyžaduje dočasne voľný port 80)
sudo certbot certonly --standalone -d api.mojadomena.sk
```
*Tieto certifikáty sa uložia do zložky `/etc/letsencrypt/live/api.mojadomena.sk/`. Aby ich Nginx v Dockeri videl, je nutné túto zložku namapovať ako `volume` v docker-compose.*

---

### 3.3 Architektúra a Orchestrácia (Docker Compose a Siete)
Aplikácia typu mikroslužieb sa zvyčajne neskladá z jedného programu, ale z viacerých prepojených súčastí (FastAPI, Databáza, RabbitMQ, Grafana). Na ich spoločné nasadenie slúži nástroj **Docker Compose**, ktorý je riadený konfiguračným súborom `docker-compose.yml`.

Tento súbor sa zvyčajne delí na 3 hlavné bloky:

1. **`services` (Služby):**
   Definuje samotné kontajnery. Pri každej službe vieme určiť:
   * `image` alebo `build`: Či sa má stiahnuť hotový image z internetu (napr. `postgres:15`), alebo sa má aplikácia skompilovať z našich zdrojových kódov (pomocou priloženého `Dockerfile`).
   * `depends_on`: Určuje poradie štartu (napríklad, API nenabehne, kým nie je databáza pripravená).
   * `healthcheck`: Automatické testy, ktoré Dockru povedia, či služba vo vnútri už reálne funguje a dokáže prijímať požiadavky.

2. **`volumes` (Dátová perzistencia):**
   Kontajnery sú vo svojej podstate *efemérne* (dočasné). Ak sa kontajner s databázou reštartuje, všetky dáta by sa stratili. Preto využívame `volumes` – pevne vyhradené miesto na disku hostiteľského servera, kam si databáza (alebo Loki, Grafana) ukladá svoje súbory. Dáta tak prežijú aj zmazanie kontajnera.

3. **`networks` (Docker Siete a DNS rozlíšenie):**
   V našom návrhu používame vlastnú sieť s názvom `app-network`.
   * **Izolácia:** Do internetu (hostiteľského systému) nevystavujeme žiadne porty databázy, fronty ani samotného API (nepoužívame príkaz `ports: - "8000:8000"` okrem Nginxu). Tieto služby sú pre vonkajší svet neviditeľné.
   * **Interné DNS:** Vďaka sieti `app-network` spolu môžu kontajnery komunikovať jednoducho pomocou ich názvov. FastAPI sa k databáze nepripája cez komplikovanú IP adresu, ale jednoducho ako na `postgres://admin:heslo@db:5432/diploma_db`, pretože Docker interne preloží názov služby `db` na správnu internú IP adresu.

---

### 3.4 Konfigurácia Nginx (Reverzné Proxy)

Z hľadiska vonkajšieho prístupu nasadzujeme model jedného vstupného bodu – **Reverzného proxy servera (Nginx)**. Kontajner Nginx je jediný, ktorý má povolený prístup do internetu (jeho porty sú mapované von z Docker siete).

Jeho úlohou je:
1. Prijať HTTPS požiadavku.
2. Dešifrovať ju pomocou certifikátov.
3. Podľa obsahu URL adresy ju preposlať na správny interný kontajner.

Na to slúži konfiguračný súbor `default.conf` (ktorý následne skopírujeme do Nginx kontajnera pomocou jeho vlastného Dockerfile).

*Príklad konfigurácie Nginx `default.conf`:*
```nginx
server {
    # Nginx počúva na porte 10443 (vnútornom) a zapína SSL šifrovanie
    listen 10443 ssl;
    server_name _; 

    # Cesty k certifikátom (ktoré sme vygenerovali/namapovali v predchádzajúcom kroku)
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    # Smerovanie pre hlavné API
    location / {
        # Prepošle požiadavku na internú DNS adresu kontajnera fastapi na porte 8000
        proxy_pass http://fastapi:8000;
        
        # Uchovanie pôvodných hlavičiek pre aplikáciu (aby API vedelo, od koho požiadavka prišla)
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Smerovanie pre monitorovací panel (Grafana)
    location /grafana/ {
        # Prepošle požiadavky smerujúce na /grafana/ do kontajnera grafana
        proxy_pass http://grafana:3000;
        proxy_set_header Host $host;
    }
}
```

### 3.5 Spustenie systému
Keď máme pripravené súbory (kód, `.env`, sieťové nastavenia a certifikáty), môžeme spustiť samotnú orchestráciu:

```bash
# Súčasné skompilovanie vlastných obrazov (API, Workery, Nginx) a ich spustenie na pozadí
docker compose up -d --build

# Zobrazenie logov konkrétneho kontajnera (napríklad Nginxu, či úspešne naštartoval)
docker compose logs -f nginx

# Overenie stavu všetkých kontajnerov (či nemajú stav 'restarting' alebo 'exited')
docker compose ps -a
```
*Nezabudnite po zmene portu povoliť prístup na firewalle:*
```bash
sudo ufw allow 10443/tcp
```

---

## 4: Pozorovateľnosť systému (Monitorovanie a Logovanie)

V prostredí mikroslužieb, kde beží viacero nezávislých kontajnerov (API, databáza, RabbitMQ, workery), je takmer nemožné hľadať chyby manuálne. Preto zavádzame tzv. **Observability stack**, ktorý pozostáva zo zberu metrík a centralizácie logov.

### 4.1 Zber metrík (Prometheus a Pushgateway)
Na sledovanie "zdravia" systému (koľko dát sa stiahlo, ako dlho trval beh, či nastali chyby) využívame časové rady dát. 

*   **Prometheus:** Slúži ako hlavná databáza pre metriky. V pravidelných intervaloch sa pýta našich služieb na ich aktuálny stav (tzv. *pull* model).

*Príklad konfigurácie Promethea `prometheus.yml`:*

```prometheus
 global:
  # ako často sa budú extrahovať metriky
  scrape_interval: 30s

 scrape_configs:
  # názov pod ktorým budú metriky evidované
  - job_name: 'pushgateway'
    static_configs:
      # endpoint na ktorom sú vystavované metriky
      - targets: ['pushgateway:9091']

  - job_name: 'node-exporter'
    static_configs:
      - targets: [ 'node-exporter:9100' ]

  - job_name: 'cadvisor'
    static_configs:
      - targets: [ 'cadvisor:8080' ]

  - job_name: 'rabbitmq'
    static_configs:
      - targets: [ 'rabbitmq-exporter:9419' ]
```

*   **Pushgateway:** Keďže naše Data Gathering workery sú jednorazové skripty (zobudia sa, stiahnu dáta a vypnú sa), Prometheus by ich nemusel stihnúť zachytiť. Preto workery svoje metriky na konci behu "pretlačia" (push) do Pushgateway kontajnera, odkiaľ si ich Prometheus neskôr prevezme.

### 4.2 Centralizácia logov (Loki a Promtail)
Aby sme nemuseli do každého kontajnera vstupovať cez terminál (`docker logs`), posielame všetky výpisy na jedno miesto.
*   **Promtail:** Malý agent, ktorý beží na serveri, číta štandardné výstupy (stdout/stderr) všetkých bežiacich Docker kontajnerov a posiela ich ďalej.

*Príklad konfigurácie Promtail `promtail-config.yaml`:*

```promtail
 server:
  # Port, na ktorom Promtail vystavuje svoje vlastné metriky
  http_listen_port: 9080
  grpc_listen_port: 0
  health_check_target: false

# Keď Promtail číta logy z kontajnerov, ukladá si do tohto súboru informáciu 
# o tom, po ktorý riadok už prečítal. Ak sa náhodou Promtail reštartuje alebo vypne, vďaka tomuto súboru 
# po zapnutí nezačne čítať všetky logy odznova, ale bude plynulo pokračovať tam, kde prestal.
positions:
  filename: /tmp/positions.yaml

# interný endpoint pre prijímanie dát
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    # súbory z ktorých promtail číta
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    # odstraňuje / z názvu kontajneru, aby to bolo bez / pri vizualizácii
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
```
  
* **Loki:** Databáza optimalizovaná na ukladanie textových logov.

*Príklad konfigurácie Loki `loki-config.yaml`:*

```loki
# pre viacero inštancií (projektov), pričom každá inštancia by potrebovala vlastný token 
 auth_enabled: false

# Port, na ktorom počúva a prijíma logy od Promtailu.
server:
  http_listen_port: 3100

#  Koreňový adresár vo vnútri kontajnera, do ktorého si Loki bude ukladať všetky svoje súbory.
common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  # Beží na jendom server
  replication_factor: 1
  # Ukladá informácie o bežiacich inštanciách iba do RAM pamäte, neukladá ich do externej databázy. 
  ring:
    kvstore:
      store: inmemory


schema_config:
  configs:
    - from: 2020-10-24
      # Akú technológiu má použiť na indexy. boltdb je rýchla malá lokálna databáza.
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      # Nastavuje rotáciu. Aby index nebol po roku obrovský a pomalý, Loki ho každých 24 hodín uzavrie a vytvorí nový s predponou index_.
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
```

### 4.3 Vizualizácia (Grafana)
Grafana slúži ako vizuálny panel (Dashboard) pre administrátora. Pripája sa na Prometheus (pre grafy) a Loki (pre textové logy).
Vďaka konfigurácii Nginxu (z predošlej kapitoly) je Grafana dostupná na adrese `https://ip-adresa:10443/grafana/`.

V Grafane si následne vieme vytvoriť grafy, ktoré nám ukazujú:
1.  Počet úspešných / zlyhaných behov providerov.
2.  Stav imputácie dát (či systém beží na reálnych alebo doplnených dátach).
3.  Záťaž procesora a pamäte jednotlivých kontajnerov.

---

## Časť 5: Automatizácia úloh (Cron) a Workery

Základom ETL systému (Extract, Transform, Load) je pravidelné spúšťanie zberu dát. V Linuxe sa na to využíva plánovač úloh **Cron**.

*Poznámka: Nastavenie premennej `PYTHONPATH=/app` je kritické pre správne fungovanie relatívnych importov v Pythone, aby systém našiel všetky tvoje moduly.*

### 5.1 Nastavenie Cronu na serveri
Ak príkaz zbehol úspešne, pridáme ho do plánovača úloh, aby sa vykonával automaticky.

```bash
# Otvorenie editora pre crontab aktuálneho používateľa
crontab -e
```

Na koniec súboru pridáme nasledujúci riadok:
```bash
# Aký interpretr sa má použiť
SHELL=/bin/sh
# Zoznam adresárov, v ktorých má systém hľadať spustiteľné programy.
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
# Koreňový adresár projektu.
PYTHONPATH=/app

# Formát: MINÚTA HODINA DEŇ_V_MESIACI MESIAC DEŇ_V_TÝŽDNI PRÍKAZ
00 9 * * * python /app/DataGathering/app.py >> /var/log/data_gathering.log 2>&1
```
Tento zápis zabezpečí spustenie o 9:00 a zároveň presmeruje všetky výpisy a prípadné chyby (`2>&1`) do logovacieho súboru na hostiteľskom serveri pre spätnú kontrolu.

---

## Časť 7: Aktualizácia (Upgrade) PostgreSQL na novú verziu (15 -> 18)

Aktualizácia databázy medzi verziami v prostredí Dockeru vyžaduje špecifický postup. PostgreSQL pri týchto prechodoch mení vnútornú štruktúru uloženia dát na disku. Ak by ste iba zmenili verziu v `docker-compose.yml`, nový kontajner by odmietol naštartovať pre nekompatibilitu súborov.

Tento proces pozostáva z logického exportu dát, zmazania starého volume a následného importu dát do novej, čistej databázy.

### 7.1 Krok za krokom: Migrácia na PostgreSQL 18

Nasledujúce príkazy sú spúšťané priamo v priečinku, kde sa nachádza `docker-compose.yml`.

```bash
# 1. Vytvorenie kompletnej zálohy (Dump) zo starej bežiacej databázy
# Parameter -F c znamená vytvorenie komprimovaného "custom" formátu, ideálneho pre obnovu
docker exec -t postgres_db pg_dump -U admin -d nazov_db -F c -f /tmp/upgrade_backup.dump

# Skopírovanie vytvorenej zálohy z vnútra kontajnera bezpečne na hostiteľský server
docker cp postgres_db:/tmp/upgrade_backup.dump ./upgrade_backup.dump

# 2. Zastavenie a zmazanie starého databázového kontajnera
# API a ostatné služby môžu zatiaľ bežať
docker compose stop db
docker compose rm -f db

# 3. Zmazanie starého volume
# Dôležité: Toto fyzicky zmaže staré dáta. Uistite sa, že súbor ./upgrade_backup.dump má veľkosť väčšiu ako 0 bytov!
# (Názov volume zistíte príkazom: docker volume ls | grep db)
docker volume rm nazov_projektu_db_data

# 4. Úprava súboru docker-compose.yml
# V tomto kroku otvoríme konfiguráciu zmeníme verziu obrazu na 18 a upravíme mapovanie dát. Novšie verzie Postgresu namapujeme volume o úroveň vyššie a pomocou premennej `PGDATA` povieme databáze, nech si vytvorí vlastný podadresár `data`.
vim docker-compose.yml

Blok databázy bude vyzerať takto:

services:
  db:
    image: postgres:18
    environment:
      - PGDATA=/var/lib/postgresql/data  # Definuje presnú cestu pre uloženie dát
    volumes:
      - postgres_data:/var/lib/postgresql  # Volume sa mapuje o úroveň vyššie!


# 5. Spustenie novej verzie databázy
# Keďže sme starý volume zmazali, Docker vytvorí nový, úplne prázdny volume a inicializuje čistú databázu v18
docker compose up -d db

# 6. Počkáme pár sekúnd, kým databáza plne naštartuje, a nahráme zálohu do nového kontajnera
docker cp ./upgrade_backup.dump postgres_db:/tmp/upgrade_backup.dump

# 7. Obnova dát do novej databázy
# Prepínač -1 (jednotka) zabezpečí, že sa celá obnova vykoná ako jedna transakcia. 
# Ak nastane chyba, celá obnova sa bezpečne vráti späť (rollback).
docker exec -t postgres_db pg_restore -U admin -d nazov_db -1 /tmp/upgrade_backup.dump

# 8. Vyčistenie dočasných súborov
docker exec -t postgres_db rm /tmp/upgrade_backup.dump
rm ./upgrade_backup.dump
```

### 7.2 Kontrola úspešnosti migrácie
Po úspešnej obnove je vhodné skontrolovať logy databázy a pripojiť sa do nej, aby sme overili, že skutočne bežíme na novej verzii.

```bash
# Kontrola logov pre prípadné chyby
docker compose logs db

# Zistenie aktuálnej verzie priamo z bežiacej databázy
docker exec -t postgres_db psql -U admin -d nazov_db -c "SELECT version();"
```
*Očakávaný výstup by mal obsahovať text podobný:* `PostgreSQL 18.x on x86_64-pc-linux-musl...`