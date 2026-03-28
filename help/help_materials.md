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