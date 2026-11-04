# Web

The site: React (Vite, TypeScript) over the API in `pipeline/src/pipeline/api.py`. Pages follow Design-Pages §13:

- **Leagues** (`/`): every league.
- **League** (`/leagues/:id`): standings, the season's progress, and the league's rules.
- **Roster** (`/leagues/:id/rosters/:roster`): a player's critters, budget and points by year.
- **Market** (`/leagues/:id/market`): priced critters, filterable and sortable, with what each costs bought today and the points they've scored so far.
- **Critter** (`/critters/:bioguide`, optionally `?league=&year=`): points by week, the positions behind power, productivity by kind, top bills, terms and leadership.

Every page takes `?on=DATE` (the "As of" box) and links carry it along, to browse a past season as it stood.

It is read-only for now: players still join, buy and drop with the `critters league` commands. Accounts (invite code and password) and trading from the site come next.

## Development

Start Postgres and the API, then the dev server, which forwards `/api` to the API:

```bash
docker compose up -d db
cd pipeline && uv run critters serve --reload
```

```bash
cd web && npm install && npm run dev   # http://localhost:5173
```

## Production

`npm run build` writes `web/dist`, which `critters serve` serves alongside the API from one port.
