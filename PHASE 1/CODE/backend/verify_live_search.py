import urllib.request
import json

url = "http://127.0.0.1:8000/api/v1/search/query"

# Fetch indexed video list
try:
    v_req = urllib.request.Request("http://127.0.0.1:8000/api/v1/summary/stats")
    with urllib.request.urlopen(v_req) as v_resp:
        stats = json.loads(v_resp.read().decode("utf-8"))
        print("[Live Verification] System stats:", stats)
except Exception as err:
    print("Stats error:", err)

def test_query(q, vid=None, top_k=10):
    payload = {"query": q, "topK": top_k, "similarityThreshold": 0.20}
    if vid:
        payload["videoId"] = vid
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("\n--- Live Test: Query 'handbag' (All Videos) ---")
res_all = test_query("handbag", vid=None, top_k=10)
a_all = res_all.get("analytics", {})
print(f"Candidates: {a_all.get('candidatesRetrieved')}")
print(f"Accepted: {a_all.get('acceptedResults')}")
print(f"Grouped: {a_all.get('groupedTracks')}")
print(f"Returned: {a_all.get('finalReturnedResults')} Result Cards")
print(f"Object Results Count: {len(res_all.get('objectResults', []))}")

# Test with a specific videoId if available
videos_req = urllib.request.Request("http://127.0.0.1:8000/api/v1/developer/videos")
try:
    with urllib.request.urlopen(videos_req) as resp:
        v_list = json.loads(resp.read().decode("utf-8"))
        if v_list:
            v_id = v_list[0].get("videoId")
            print(f"\n--- Live Test: Query 'handbag' (Scoped to '{v_id}') ---")
            res_scoped = test_query("handbag", vid=v_id, top_k=10)
            a_scoped = res_scoped.get("analytics", {})
            print(f"Candidates: {a_scoped.get('candidatesRetrieved')}")
            print(f"Accepted: {a_scoped.get('acceptedResults')}")
            print(f"Grouped: {a_scoped.get('groupedTracks')}")
            print(f"Returned: {a_scoped.get('finalReturnedResults')} Result Cards")
            print(f"Object Results Count: {len(res_scoped.get('objectResults', []))}")
            assert len(res_scoped.get("objectResults", [])) <= 10, "Over-retrieval bug detected!"
            print("\nSUCCESS: Scoped search result cards strictly bounded by topK=10!")
except Exception as e:
    print("Scoped test notice:", str(e))
