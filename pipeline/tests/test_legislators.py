from datetime import date

from pipeline.legislators import party_periods


def test_term_without_switch_is_one_period():
    term = {"start": "2023-01-03", "end": "2029-01-03", "party": "Independent", "caucus": "Democrat"}
    assert party_periods(term) == [(date(2023, 1, 3), date(2029, 1, 3), "Independent", "Democrat")]


def test_mid_term_switch_splits_the_term_and_the_switch_day_goes_to_the_new_party():
    # Manchin: the source ends the Democratic affiliation on the day the new one starts.
    term = {"start": "2019-01-03", "end": "2025-01-03", "party": "Independent",
            "party_affiliations": [
                {"start": "2019-01-03", "end": "2024-05-31", "party": "Democrat"},
                {"start": "2024-05-31", "end": "2025-01-03", "party": "Independent", "caucus": "Democrat"},
            ]}
    assert party_periods(term) == [
        (date(2019, 1, 3), date(2024, 5, 30), "Democrat", None),
        (date(2024, 5, 31), date(2025, 1, 3), "Independent", "Democrat"),
    ]


def test_affiliation_ending_the_day_before_the_next_is_kept():
    # Sinema: the source ends the Democratic affiliation the day before.
    term = {"start": "2019-01-03", "end": "2025-01-03", "party": "Independent",
            "party_affiliations": [
                {"start": "2019-01-03", "end": "2022-12-08", "party": "Democrat"},
                {"start": "2022-12-09", "end": "2025-01-03", "party": "Independent", "caucus": "Democrat"},
            ]}
    assert [p[:2] for p in party_periods(term)] == [
        (date(2019, 1, 3), date(2022, 12, 8)), (date(2022, 12, 9), date(2025, 1, 3))]
