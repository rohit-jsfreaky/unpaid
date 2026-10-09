# Unpaid: for the SerpApi India Hackathon 2026 judges

**Pitch:** Every "best phone under ₹30,000" video says something different. Unpaid reads all of them, including what
reviewers say out loud, and shows who disclosed a brand deal, a free unit or a commission, and what the reviewers
with nothing to disclose recommend.

- Repo: https://github.com/rohit-jsfreaky/unpaid (start with the [README](README.md))
- Video (2:17, the app running locally): https://youtu.be/neUM6Qp4lko
- Track: Commerce & Market Intelligence
- Auth: none. No login, and no API keys needed to judge: the real runs replay from `evidence/`.

## At a glance: criteria → where to look

| criterion | where |
|---|---|
| Idea strength | README "The problem": 21 recent reviews, 10 different #1 picks, 9 disclosed money ties hidden in descriptions, links and speech |
| Originality | Price tools in this space compare prices. Unpaid asks whether the advice to buy was paid for, and ranks picks by reviewers with nothing to disclose. README "What I built" |
| vs plain chat | `evidence/chatgpt-baseline/README.md`: ChatGPT with Firecrawl took 5 min 4 s for 7 videos; without it, 27 s for 8, and it says it didn't check spoken disclosures. The two runs share 0 videos. README "The numbers" → Baseline |
| Technical complexity | `engine/src/unpaid/proof.py` (AI finds, code proves), `links.py` (affiliate tags by following redirects), `uses.py` (feature claims in 4 languages), `agent.py` (LLM reads, code plans), `serpapi.py` (record/replay with receipts) |
| Usefulness | The report: `web/app/app/r/[id]/`. Best product for your must-haves, who is paid, today's prices, every quote with a "Watch at" link |
| Meaningful SerpApi usage | README "How Unpaid uses SerpApi": 4 engines, every fact comes from them; `engine/src/unpaid/youtube.py`, `collect.py`, `prices.py` |

## The verified production run

"best phone under 30k for camera and battery, big billion days", recorded live on 8 Oct 2026, 17:19 UTC
(`evidence/showcase-2026-10-08/`):

1. The LLM reads the question: phone, ₹30,000, Big Billion Days, must-haves camera + battery.
2. Code plans 3 YouTube searches (2 English, 1 Hindi) → 38 videos → 21 recent reviews whose title names the budget
   (17 dropped, each with a reason).
3. 21 videos opened, 18 transcripts read (Hindi 12, English 3, Telugu 2, Malayalam 1): 42 searches, 60.7 s.
4. 64 description links followed, 53 carry a creator's affiliate tag.
5. Labels: Earns commission 8, Brand-sponsored 1 (Trakin Tech, `#Collab … #MotorolaIndia`), No disclosure found 12.
   One commission label comes from Telugu speech at 8:04.
6. Picks: Motorola Edge 70 Fusion is #1 with both groups (7 of 9 no-disclosure reviewers, 8 of 9 with a money tie).
   Realme P4 Power: 6 of 9 vs 3 of 9.
7. Must-haves: camera → Motorola Edge 70 Fusion, battery → Realme P4 Pro (by no-disclosure reviewers).
8. Google Shopping: Edge 70 Fusion from ₹25,799 (Zepto, 12 sellers).

A second run proves any product works: "best earbuds under 3000 for gym and bass" (`evidence/earbuds-2026-10-09/`,
6 reviews, 5 with a money tie, 19 searches).

## 60-second judge path

1. `cd engine && uv sync && uv run verify`: 22 PASS lines with no keys. Each one is a claim from the README, checked
   from the saved data.
2. **Run the attacks:** `uv run pytest -q -k "quote or trap or denial or tagged or sponsor or guard or leak or refuses or prove_uses"`:
   12 attack tests (fake quotes, "not sponsored" traps, untagged links, the wrong sponsor, budget overrun, key leaks).
3. `uv run unpaid serve`, then in another terminal `cd web && npm ci && npm run dev` → http://localhost:3000.
4. **Open Unpaid** → click the phone question under **Try:** and watch the recorded run play back.
5. Report → **Reviews** → **Telugu Techno Spring**: the spoken commission line, its English meaning, "Watch at 8:04".
6. **How we label**: the rules and the accuracy table (the same numbers `verify` printed).

## What each sponsor does here

| SerpApi engine | job | file |
|---|---|---|
| `youtube` | find recent review videos in English and Hindi; YouTube's own "Earns commission" / "N products" labels | `engine/src/unpaid/youtube.py` (`search`, `parse_search`), `collect.py` |
| `youtube_video` | the full description: sponsor lines, `#Collab`, shop links | `youtube.py` (`video`), `links.py` |
| `youtube_video_transcript` | what the reviewer said, with timestamps, in the language they spoke | `youtube.py` (`transcript`) |
| `google_shopping` | today's price per seller for the top picks | `engine/src/unpaid/prices.py` |
| `account.json` | searches left, for the budget guard | `engine/src/unpaid/serpapi.py` |

Without SerpApi there are no videos, descriptions, transcripts or prices, so there is no report.

## What is real and what is demo

- **Real:** every video, quote, link check and price in the app and the README comes from live SerpApi calls on
  8–9 Oct 2026. Each saved file keeps SerpApi's search id, `json_endpoint` and time (`verify` checks every saved file).
- **Replay:** judges without keys see those real runs replayed, with the same events and the same report. A question
  that was never recorded says so and needs keys (`.env.example`) to run live. It never spends on its own.
- **Not demo data anywhere.** No invented videos, quotes or prices.

## What it proves, and what it does not

**Proves:**
- Every label shown has a receipt: a quote found word for word, a followed link with the creator's tag, or YouTube's
  own label.
- On 21 hand-checked videos: 100% precision for Brand-sponsored and Earns commission, 89% commission recall (one
  spoken Malayalam line missed, left unfixed and published).
- What the no-disclosure reviewers pick, compared with everyone, on the same videos.

**Does not prove:**
- That a reviewer with "No disclosure found" is independent, or that a paid reviewer is wrong.
- Accuracy beyond the 21-video phone run. The answer key was labelled by Claude Code agents and re-checked row by
  row, not by a human expert.
- Anything about videos outside the 21-day window or the 3 searches the free plan allows.

## Known issues

- One missed commission (CallMeShazzam Vines, spoken in Malayalam). That video counts as "No disclosure found" and its
  quote is on the camera card.
- Auto-captions garble some names. One #1 pick reads "Lava VAT Curve".
- 3 of 21 videos had no transcript from SerpApi. They're labelled from the description only and marked "No captions".
- Twin-model lines ("M56 and F56 both have a good camera") are dropped on purpose, so a few real opinions are lost.
- Coverage: ChatGPT (with Firecrawl) cited 4 sale-list videos our 3 searches didn't find
  (`evidence/chatgpt-baseline/`). The free plan limits how many searches we run per question.

## Build log

- **7 Oct:** probed SerpApi (5 calls): YouTube search in EN + HI with commission labels, a full video, a Hindi
  transcript. Facts in `CLAUDE.md`.
- **8 Oct:** picked the idea. Engine: SerpApi client with record/replay and budget guard, YouTube parsers, showcase
  recorded (42 searches, 60.7 s). LLM extraction + code proof + link checks → labels. Answer key (21 videos).
  Board + Google Shopping prices. Agent (question → plan) + streaming API.
- **9 Oct:** web app (landing + dashboard + live check + report). Must-haves ("best for camera / battery") proved the
  same way. Any product: per-product features, earbuds run recorded live. CI green (engine + web).
  Question normalising so "Best phone…?" replays the recorded "best phone…". README, this page, zero-context test.
  ChatGPT baseline saved (run 1 with Firecrawl from 8 Oct, run 2 without it on 9 Oct).
