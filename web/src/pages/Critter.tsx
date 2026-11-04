import { Link, useParams, useSearchParams } from "react-router-dom";
import { useApi, useAsOf, type Critter as CritterData, type Week } from "../api";
import { billName, chamberName, congressUrl, day, dollars, dollarsCents, label, partyLetter, pct, pts, seat } from "../format";
import Loading from "../Loading";

function WeeklyChart({ weeks }: { weeks: Week[] }) {
  const max = Math.max(1, ...weeks.map((w) => (w.power ?? 0) + (w.productivity ?? 0)));
  const height = 120;
  const width = 6 * weeks.length;
  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label="Points by week">
      {weeks.map((w, i) => {
        const power = ((w.power ?? 0) / max) * height;
        const prod = ((w.productivity ?? 0) / max) * height;
        return (
          <g key={w.week}>
            <title>
              {w.state === "upcoming"
                ? `Week ${w.week} (${day(w.start)}): still to come`
                : `Week ${w.week} (${day(w.start)} – ${day(w.end)}): ${pts(w.power)} power + ${pts(w.productivity)} productivity${w.state === "final" ? ", final" : ""}`}
            </title>
            {w.state === "upcoming" ? (
              <rect x={i * 6 + 1} y={height - 2} width={4} height={2} className="upcoming" />
            ) : (
              <>
                <rect x={i * 6 + 1} y={height - power} width={4} height={power} className="power" />
                <rect x={i * 6 + 1} y={height - power - prod} width={4} height={prod} className="productivity" />
              </>
            )}
          </g>
        );
      })}
    </svg>
  );
}

export default function Critter() {
  const { bioguide } = useParams();
  const { query } = useAsOf();
  const [params] = useSearchParams();
  const league = params.get("league");
  const year = params.get("year");
  const { data, error } = useApi<CritterData>(`/api/critters/${bioguide}${query({ league, year })}`);
  if (!data) return <Loading error={error} />;
  const card = data.card;
  const b = data.breakdown;
  const total = data.power + data.productivity;
  return (
    <>
      {data.league && (
        <p className="crumbs">
          <Link to={`/leagues/${data.league.league_id}${query()}`}>{data.league.name}</Link> ·{" "}
          <Link to={`/leagues/${data.league.league_id}/market${query({ year: data.year })}`}>Market</Link>
        </p>
      )}
      <div className="critter-head">
        <img
          src={`https://unitedstates.github.io/images/congress/225x275/${data.bioguide_id}.jpg`}
          alt=""
          onError={(e) => (e.currentTarget.style.display = "none")}
        />
        <div>
          <h1>{data.name}</h1>
          {card && (
            <p className="muted">
              {chamberName(card.chamber)} · {card.party ?? "No party"} · {partyLetter(card.party)}-{seat(card)}
            </p>
          )}
          {data.owners.length > 0 && <p>Owned by {data.owners.join(", ")}</p>}
        </div>
      </div>

      <h2>
        {data.year}{" "}
        <span className="muted small">
          ({data.congress}th Congress, session {data.session}
          {data.league ? `, scored with ${data.league.name}'s ruleset` : ""})
        </span>
      </h2>
      <div className="stats">
        <div>
          <span className="stat">{pts(total)}</span>
          <span className="muted">points through {day(data.counted_through)}</span>
        </div>
        <div>
          <span className="stat">{pts(data.power, 0)}</span>
          <span className="muted">power</span>
        </div>
        <div>
          <span className="stat">{pts(data.productivity, 0)}</span>
          <span className="muted">productivity</span>
        </div>
        <div>
          <span className="stat">{pct(b?.participation)}</span>
          <span className="muted">roll calls voted</span>
        </div>
        {data.price && (
          <div>
            <span className="stat">{dollars(data.price.session_cost)}</span>
            <span className="muted">
              Session Cost: {dollarsCents(data.price.signing_fee)} to sign, {dollarsCents(data.price.weekly_fee)} a week
            </span>
          </div>
        )}
      </div>
      {data.price && (
        <p className="muted small">
          Priced for {pts(data.price.projected_power + data.price.projected_productivity, 0)} projected points (
          {pts(data.price.projected_power, 0)} power + {pts(data.price.projected_productivity, 0)} productivity) × a
          market multiplier of {data.price.multiplier.toFixed(2)}.
        </p>
      )}
      <WeeklyChart weeks={data.weekly} />
      <p className="legend small">
        <span className="swatch power" /> power <span className="swatch productivity" /> productivity · {data.ended} of{" "}
        {data.weeks} weeks ended, {data.final} final
      </p>

      {b && (
        <div className="split">
          <section>
            <h3>Power: positions held</h3>
            <p className="muted small">
              Each seat is worth its value over a full session, paid by the week for the days held and multiplied by that
              week's roll-call participation.
            </p>
            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th>Position</th>
                    <th>Role</th>
                    <th>Held</th>
                    <th className="num">Value / session</th>
                  </tr>
                </thead>
                <tbody>
                  {b.positions.map((p) => (
                    <tr key={`${p.category}-${p.committee_code ?? p.name}-${p.start_date}`}>
                      <td>
                        {p.name}
                        {p.category === "SUBCOMMITTEE_SEAT" && <span className="muted"> (subcommittee)</span>}
                      </td>
                      <td>{p.role ? label(p.role) : ""}</td>
                      <td className="small nowrap">
                        {day(p.start_date)} – {p.end_date >= data.as_of ? "now" : day(p.end_date)}
                      </td>
                      <td className="num">{pts(p.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section>
            <h3>Productivity by kind</h3>
            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th>Credit</th>
                    <th className="num">Items</th>
                    <th className="num">Points</th>
                  </tr>
                </thead>
                <tbody>
                  {b.categories.map((c) => (
                    <tr key={c.category}>
                      <td>{label(c.category)}</td>
                      <td className="num">{c.items}</td>
                      <td className="num">{pts(c.points)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
      {b && b.bills.length > 0 && (
        <section>
          <h3>Top bills</h3>
          <div className="scroll">
            <table>
              <thead>
                <tr>
                  <th>Bill</th>
                  <th>Title</th>
                  <th>Credit for</th>
                  <th className="num">Points</th>
                </tr>
              </thead>
              <tbody>
                {b.bills.map((bill) => (
                  <tr key={bill.bill_id}>
                    <td className="nowrap">
                      <a href={congressUrl(bill.bill_id)} target="_blank" rel="noreferrer">
                        {billName(bill.bill_id)}
                      </a>
                      {bill.sponsor && <span className="tag">sponsor</span>}
                    </td>
                    <td>{bill.title}</td>
                    <td className="small">{bill.categories.map(label).join(", ")}</td>
                    <td className="num">{pts(bill.points, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <div className="split">
        <section>
          <h3>Terms</h3>
          <div className="scroll">
            <table>
              <tbody>
                {data.terms.map((t) => (
                  <tr key={t.start_date}>
                    <td>{chamberName(t.chamber)}</td>
                    <td>{seat(t)}</td>
                    <td>{t.party}</td>
                    <td className="small">
                      {day(t.start_date)} – {day(t.end_date)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        {data.leadership.length > 0 && (
          <section>
            <h3>Leadership</h3>
            <div className="scroll">
              <table>
                <tbody>
                  {data.leadership.map((l) => (
                    <tr key={`${l.title}-${l.start_date}`}>
                      <td>{l.title}</td>
                      <td className="small">
                        {day(l.start_date)} – {l.end_date ? day(l.end_date) : "now"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </>
  );
}
