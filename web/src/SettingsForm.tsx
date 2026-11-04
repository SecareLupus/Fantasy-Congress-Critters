import type { Settings } from "./api";

/** Edit a league's settings (Design-Rulesets §6A.7). The API checks the limits; this only
shapes the values. */
export default function SettingsForm({ value, onChange }: { value: Settings; onChange: (s: Settings) => void }) {
  const slots = value.roster_rules.chamber_slots;
  const num = (s: string) => (s === "" ? 0 : Number(s));
  const set = (patch: Partial<Settings>) => onChange({ ...value, ...patch });
  return (
    <fieldset className="settings">
      <label>
        Budget per legislative year ($)
        <input
          type="number"
          min={1}
          value={value.budget_rules.annual_budget}
          onChange={(e) => set({ budget_rules: { annual_budget: num(e.target.value) } })}
        />
      </label>
      <label>
        Roster limit (critters)
        <input
          type="number"
          min={1}
          max={100}
          value={value.roster_rules.roster_limit}
          onChange={(e) => set({ roster_rules: { ...value.roster_rules, roster_limit: num(e.target.value) } })}
        />
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={!!slots}
          onChange={(e) =>
            set({
              roster_rules: {
                ...value.roster_rules,
                chamber_slots: e.target.checked
                  ? { house: value.roster_rules.roster_limit, senate: value.roster_rules.roster_limit }
                  : null,
              },
            })
          }
        />
        Limit each chamber
      </label>
      {slots && (
        <div className="pair">
          <label>
            House at most
            <input
              type="number"
              min={0}
              value={slots.house}
              onChange={(e) => set({ roster_rules: { ...value.roster_rules, chamber_slots: { ...slots, house: num(e.target.value) } } })}
            />
          </label>
          <label>
            Senate at most
            <input
              type="number"
              min={0}
              value={slots.senate}
              onChange={(e) => set({ roster_rules: { ...value.roster_rules, chamber_slots: { ...slots, senate: num(e.target.value) } } })}
            />
          </label>
        </div>
      )}
      <label>
        Winner
        <select value={value.win_condition} onChange={(e) => set({ win_condition: e.target.value })}>
          <option value="cumulative">Most points</option>
          <option value="head_to_head" disabled>
            Head to head (not built yet)
          </option>
        </select>
      </label>
      <label>
        Drop fee ($, on top of the lost signing fee)
        <input
          type="number"
          min={0}
          value={value.drop_cost.extra_fee}
          onChange={(e) => set({ drop_cost: { ...value.drop_cost, extra_fee: num(e.target.value) } })}
        />
      </label>
      <label>
        Drop penalty (points)
        <input
          type="number"
          min={0}
          step="any"
          value={value.drop_cost.points_penalty}
          onChange={(e) => set({ drop_cost: { ...value.drop_cost, points_penalty: num(e.target.value) } })}
        />
      </label>
    </fieldset>
  );
}
