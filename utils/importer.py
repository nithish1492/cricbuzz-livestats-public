from .cricbuzz import fetch_live_matches, extract_match_records, sync_matches, fetch_series_list, extract_series_records, sync_series, fetch_scorecard, sync_scorecard
def import_live_matches():
    payload=fetch_live_matches(); return sync_matches(extract_match_records(payload)),payload
def import_series():
    payload=fetch_series_list(); return sync_series(extract_series_records(payload)),payload
def import_scorecard(match_id):
    payload=fetch_scorecard(match_id); return sync_scorecard(match_id,payload),payload
