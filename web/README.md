# Web

The site: React (Vite, TypeScript) over the API in `pipeline/src/pipeline/api.py`. Pages follow Design-Pages §13:

- **Leagues** (`/`): every league.
- **League** (`/leagues/:id`): standings, the season's progress, and the league's rules.
- **Roster** (`/leagues/:id/rosters/:roster`): a player's critters, budget and points by year; Drop on your own.
- **Market** (`/leagues/:id/market`): priced critters, filterable and sortable, with what each costs bought today and the points they've scored so far; Buy for players in the league.
- **Critter** (`/critters/:bioguide`, optionally `?league=&year=`): points by week, the positions behind power, productivity by kind, top bills, terms and leadership.

Every page takes `?on=DATE` (the "As of" box) and links carry it along, to browse a past season as it stood.

- **Sign in** (`/signin`) and **create an account** (`/signup`, with an invite code; `?invite=CODE` fills it in).
- **Create a league** (`/leagues/new`): any account makes a private league (on an official schedule or its own dates); GameMakers also make official ones. Starts from a preset whose settings can be changed.
- **Manage** (`/leagues/:id/manage`, linked from the league for its game master): the join link for a private league, and a new one to stop the old; the name and settings until the league starts; removing players until it starts.
- **Invites** (`/invites`, for GameMakers): make invite codes and see who used them.

A signed-in player can join an official league from its page, or a private one from its join link; their roster is highlighted in the standings and listed on the home page. In their league's market they buy critters (the Buy button says what it costs and is replaced by the reason when they can't: on the roster, roster or chamber slots full, can't afford), and on their roster they drop them (it says what comes back and what's lost). Each asks to confirm first. Trading always happens today, so it's hidden while browsing with "As of".

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
