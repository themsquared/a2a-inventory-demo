# a2a-inventory-demo

**Problem:** The Agent2Agent (A2A) protocol just passed its one-year mark under Linux Foundation governance. The announcement says it's "production-ready," cites 150+ supporting organizations, and names active production deployments across supply chain, financial services, insurance, and IT operations. None of that is independently counted — it's the foundation and its vendors describing their own ecosystem. An [Ask HN thread](https://hn.svelte.dev/item/48582679) asking "is anyone using A2A?" got 92 points and a top reply calling the whole premise wrong.

**Value proposition:** You can't see anyone's private production traffic from the outside. But A2A ships with its own discovery mechanism — a `.well-known/agent-card.json` file an agent publishes so other agents can find it — and that file, when published, is public by construction. It's the one signal of real-world A2A adoption that isn't filtered through a vendor's press release. This repo scans GitHub's public code index for it and reports who's actually publishing one.

**What it found (2026-10-16 run, captured in `captures/latest-scan.json`):** 634 distinct repositories publish a `.well-known/agent.json` or `.well-known/agent-card.json` file. 247 distinct GitHub accounts are behind them. **One account — `CSOAI-ORG`, a single person's user account (Nicholas Templeman / Council of AI) — accounts for 371 of those 634 repos: 58.5%.** The account programmatically generates near-identical single-tool "ai-mcp" repos (`gdpr-compliance-ai-mcp`, `recipe-finder-ai-mcp`, `iso-27001-ai-mcp`, dozens more), each wrapping one MCP tool behind a boilerplate agent card pointing at `mcp.meok.ai`. The next-largest account, `inference-gateway` (a small real open-source LLM gateway project), has 6. Every other account in the top 10 has 2–4. There is no Salesforce, Box, MongoDB, PayPal, Atlassian, or any other commonly-cited 2025 A2A launch partner publishing a public agent card of their own.

**This is not proof A2A has no real users.** Enterprise production deployments are typically internal and wouldn't publish a public discovery file at all — that's exactly why the Linux Foundation's "150+ organizations" and "production deployments" claims can't be falsified from outside, and exactly why "we looked and couldn't verify it independently" is the honest finding here, not "it's fake." What the data does show: the public, falsifiable surface of A2A adoption is dominated by one account's templated content farm, and the organic long tail behind it is overwhelmingly solo projects, course exercises, and one-off experiments — not the broad enterprise base the anniversary framing implies.

## Quickstart (~2 minutes)

```bash
git clone https://github.com/themsquared/a2a-inventory-demo
cd a2a-inventory-demo
export GITHUB_TOKEN=$(gh auth token)   # or any PAT with no scopes — public code search only
python3 scripts/scan.py
```

Requires Python 3.9+ and a GitHub token (GitHub's code search API requires authentication even for public repos; no scopes are needed). No other dependencies — stdlib only.

Expected output: a deduped repo count, a distinct-owner count, and the top 10 owners by repo count, written to `captures/latest-scan.json`. Numbers will drift as new repos get created and old ones get deleted — that's expected and part of the point; re-run it before citing a number.

## How it works

`scripts/scan.py` queries GitHub's code search API (`GET /search/code`) for two filenames that carry the same job under two spec eras:

- `path:.well-known filename:agent-card.json` — the current A2A spec's discovery file name.
- `path:.well-known filename:agent.json` — the original pre-Linux-Foundation name, still used by agents built against the earlier spec or by libraries that haven't updated their templates.

It paginates each query up to GitHub's 1,000-result code-search cap, dedupes by repository, and looks up each top account's GitHub account type (`User` vs `Organization`) via the Users API — the distinction matters here because "an organization with 371 repos" and "one person with 371 repos" are very different adoption signals.

## Honest limitations

- **This measures public GitHub repos only.** It cannot see private repos, internal deployments, or agents hosted without a public source repo at all (the agent card itself is usually served from a live URL, not just committed to a repo — a repo-based search undercounts anyone who deploys without committing the card to version control, and overcounts template/tutorial repos nobody ever deployed).
- **GitHub code search indexing has known gaps and lag** — it doesn't claim to be exhaustive, and the API's own 1,000-result cap means very large query results (we hit it on both queries) are undercounted, not overcounted.
- **A templated or auto-generated repo is not proof of non-use** — it's possible some of the CSOAI-ORG repos are deployed and serving real traffic at `mcp.meok.ai`. We did not probe those endpoints (out of scope, and probing 371 third-party services without a clear research justification felt like the wrong use of this demo). The finding is about the *shape* of public A2A adoption evidence, not a claim about what any one deployment does.
- **"150+ organizations supporting the standard" and "production deployments" are different claims than this repo tests.** The Linux Foundation's figure is about standards-body membership and named vendor integrations (Google, Microsoft, AWS, and others shipping A2A support in their platforms), which this scan doesn't contradict. What it contradicts is any reading of that figure as "150+ independent organizations have deployed their own interoperable A2A agents," which is not what a search for the protocol's own discovery artifact shows.

## Topics

`ai-agents` `a2a` `agent2agent` `mcp` `interoperability` `github-search`
