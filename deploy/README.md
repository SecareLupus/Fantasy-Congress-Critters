# Deploying

One Linux server runs everything with Docker Compose ([compose.yml](compose.yml)):

- **db**: Postgres 17. Not reachable from outside.
- **app**: the image built from the repo's [Dockerfile](../Dockerfile): the API and the built site (`critters serve`), and the `critters` commands.
- **caddy**: the only service with open ports (80, 443). It gets and renews the HTTPS certificate for `DOMAIN` and passes requests to the app.

Two systemd timers run the jobs:

- **Daily update**, 10:00 UTC ([update.sh](update.sh)): `critters update`.
- **Nightly backup**, 04:00 UTC ([backup.sh](backup.sh)): a database dump and the official roster snapshots, kept for 30 days on the server and copied off it with rclone.

Each job pings a health check that emails you if it fails or doesn't run.

What the server needs: an update takes about a minute and 650 MB of memory at its peak; one Congress loaded, scored and priced is about 250 MB of database; downloads are about 500 MB a Congress. A server with 2 CPUs, 4 GB of memory and 40 GB of disk is plenty.

## First setup

### 1. The server

Ubuntu 24.04 LTS on any VPS. As root, or with sudo:

1. Make a user with your SSH key, then turn off password and root login in `/etc/ssh/sshd_config` (`PasswordAuthentication no`, `PermitRootLogin no`).
2. Turn on automatic security updates: `apt install unattended-upgrades`.
3. Open only SSH and the web ports: `ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable`. Docker opens the ports it publishes on its own, and only Caddy publishes any.
4. Install Docker Engine with the Compose plugin ([docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu/)), and rclone (`apt install rclone`).

### 2. The code and settings

```bash
sudo git clone https://github.com/SecareLupus/Fantasy-Congress-Critters.git /srv/critters
sudo mkdir -p /srv/critters/data && sudo chown -R 1000:1000 /srv/critters/data   # the app runs as uid 1000
cd /srv/critters/deploy
sudo cp .env.example .env && sudo chmod 600 .env && sudo nano .env
```

In `.env`, set `DOMAIN`, a `POSTGRES_PASSWORD` from `openssl rand -hex 24` (letters and digits only: it goes in a URL), and the health check and backup settings from steps 6 and 7.

Point the domain's DNS A record (and AAAA, for IPv6) at the server before starting, so Caddy can get the certificate.

### 3. Start it

```bash
sudo docker compose up -d --build
curl https://$DOMAIN/api/health        # {"ok":true}
```

### 4. Load the Congress

Copy the official roster snapshots from the machine that has been running `critters update`. They are the only record of when committee seats changed, and nothing else can recreate them:

```bash
rsync -a data/raw/rosters/official/ SERVER:/srv/critters/data/raw/rosters/official/   # from your machine
sudo chown -R 1000:1000 /srv/critters/data                                           # on the server
```

Then load, score and price the Congress in session. `run` starts a one-off app container:

```bash
alias critters='sudo docker compose run --rm app critters'
critters league preset save standard --file presets/standard.toml --by <you>
critters download --congress 119
critters load --congress 119
critters score --congress 119
critters price --session 2
critters update
```

It takes about five minutes. For a new Congress, see "A new Congress" below.

### 5. The first GameMaker

```bash
critters invite create --by <you> --role gamemaker --note "me"
```

Sign up at `https://DOMAIN/signup?invite=CODE`. From then on, make leagues and invite players on the site (Invites in the header).

### 6. Health checks

At [healthchecks.io](https://healthchecks.io) (free), or anything that takes the same pings, make two checks: "critters update" (period 1 day, grace 2 hours) and "critters backup" (period 1 day, grace 2 hours). Put their ping URLs in `.env` as `HEALTHCHECK_UPDATE_URL` and `HEALTHCHECK_BACKUP_URL`. The update's last 10 KB of output goes with its ping, so a failure email says what broke.

Also add an uptime check on `https://DOMAIN/api/health`, which answers only when the app can reach the database.

### 7. Backups

Set up somewhere off the server: a Backblaze B2 bucket or S3. Add it to rclone with `sudo rclone config` (as root, since the timers run as root), then set `BACKUP_REMOTE` in `.env`, e.g. `b2:critters-backups`. Run a backup once:

```bash
sudo ./backup.sh
```

### 8. The timers

```bash
sudo cp systemd/critters-* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now critters-update.timer critters-backup.timer
systemctl list-timers 'critters-*'
```

The units expect the repo at `/srv/critters`; change `ExecStart` if it isn't.

## Day to day

- **Logs:** `sudo docker compose logs -f app`. Update runs are in `journalctl -u critters-update`.
- **Data status:** `critters status`.
- **Run an update now:** `sudo systemctl start critters-update`.
- **Accounts:** `critters account list`, and `critters account update NAME --reset-password` for a forgotten password.
- **A new version:** `cd /srv/critters && sudo git pull && cd deploy && sudo docker compose up -d --build`. The schema updates itself when the app starts.

## Restoring

```bash
sudo ./restore.sh backups/critters-STAMP.dump backups/rosters-STAMP.tar.gz
```

This replaces the database and puts the roster snapshots back, stopping the app while it runs. For a backup that's only on the remote, fetch it first: `sudo rclone copy b2:critters-backups/critters-STAMP.dump backups/`. Restore once on purpose, early, to know it works.

## A new Congress

On January 3, the new Congress needs loading and pricing before its leagues can trade. Pricing session 1 reads the last Congress's latest run. Committee rosters are posted weeks later, so seats are projected until then (pipeline/README.md, "Pricing"):

```bash
critters download --congress 120
critters load --congress 120
critters score --congress 120
critters price --session 1
```

For the first 30 days, `critters update` also keeps updating the old Congress so its last week settles.
