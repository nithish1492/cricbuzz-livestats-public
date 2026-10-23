from utils.cricbuzz import extract_match_records

def test_live_parser():
    payload={"typeMatches":[{"matchType":"International","seriesMatches":[{"seriesAdWrapper":{"seriesId":1,"seriesName":"Example","matches":[{"matchInfo":{"matchId":2,"seriesId":1,"seriesName":"Example","matchDesc":"1st T20I","matchFormat":"T20","startDate":"1792243800000","team1":{"teamName":"India"},"team2":{"teamName":"Australia"},"venueInfo":{"ground":"Ground","city":"Delhi"}}}]}}]}]}
    rows=extract_match_records(payload)
    assert len(rows)==1
    assert rows[0]["team1"]=="India"
    assert rows[0]["external_id"]=="2"
