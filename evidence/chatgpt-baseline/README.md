# ChatGPT baseline

The same shopper question, asked to ChatGPT twice. The question, word for word:

> I want to buy a phone under 30000 in this Flipkart Big Billion Days sale. Every YouTube 'best phone under 30k' video
> says something different. Which of these YouTubers are being paid, sponsored, given free phones, or earning
> commission on the phones they recommend, and what do the unpaid, independent reviewers actually recommend? Give me
> a table with the video, the reviewer, what they recommended, and the proof of whether they were paid.

| file | what it is |
|---|---|
| `run1-with-firecrawl.txt` / `.json` | Run 1, 8 Oct 2026 02:35 IST, ChatGPT **with the Firecrawl plugin** (flame icon on its steps in `1-question-and-work-log.png`). Full answer text, work log, every link. |
| `run2-no-plugin.txt` / `.json` | Run 2, 9 Oct 2026 05:36 UTC, a temporary chat, **no Firecrawl**: only ChatGPT's built-in web search ("Searched 12 websites", `4-run2-question-and-work-log.png`). |
| `1-…png` to `6-…png` | Screenshots of both chats: question, work log, tables, final pick, and run 2's own limit line. |

Every video either run cited was checked with YouTube's public oEmbed lookup on 9 Oct 2026: all 15 exist.

## What the runs found, next to Unpaid

| | ChatGPT + Firecrawl | ChatGPT, no plugin | Unpaid (`evidence/showcase-2026-10-08/`) |
|---|---|---|---|
| Time | 5 min 4 s | 27 s | 60.7 s to find, open and read 21 videos and 18 transcripts (then labels and prices) |
| Videos cited | 7 (4 sale "under 30k" lists, 3 Gyan Therapy videos: a July advice video and 2 single-phone reviews) | 8 (4 sale lists, 1 from January, 3 single-phone reviews incl. one Hungarian and one of an older phone) | 21 recent reviews whose title names the ₹30k budget |
| What it read | Descriptions, plus one spoken line it mentions (Technology Gyan) | Descriptions only. Its own words: "I also haven't verified the spoken disclosures or YouTube's in-player paid-promotion labels" | Every description, every transcript (Hindi, English, Telugu, Malayalam), YouTube's own labels |
| Shop links | "a large number of amzn.to shopping links" (not followed) | Not followed | 64 followed, 53 carry the creator's affiliate tag |
| Who recommends what | Not counted | Not counted | Picks counted per video, split by reviewers with and without a money tie |
| Quotes checked by code | No | No | Yes: a label shows only if its quote is found word for word |
| Same answer next time | No: the two runs share 0 of their 15 videos | | Yes: `uv run verify` replays the same run |
| Final pick | Moto Edge 70 Fusion, ₹29,999 | A shortlist of 3, no single pick | Motorola Edge 70 Fusion (7 of 9 no-disclosure reviewers), from ₹25,799 |

## Fair notes

- ChatGPT's answers were careful: both said an affiliate link is not the same as a brand paying for the ranking. That's
  the same line Unpaid's labels draw.
- Coverage differs. ChatGPT found 4 sale-list videos that Unpaid's 3 searches didn't, and Unpaid found 21 that ChatGPT
  didn't. Neither covers all of YouTube.
- Run 1 was on 8 Oct and run 2 on 9 Oct, so search results can differ by day. That doesn't explain the zero overlap
  between them, but it's worth knowing.
- The model setting shown was "Medium" in both chats. The exact model behind it isn't shown on the page.
