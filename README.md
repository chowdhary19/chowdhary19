<div align="center">

<table border="0">
<tr>
<td width="130" align="center">
<img src="https://github.com/chowdhary19/pub_pri/blob/main/linkedIN%20avatar.png" width="112" height="112" style="border-radius:50%;border:2px solid #39d353;" alt="Yuvraj Singh Chowdhary"/>
</td>
<td>

### YUVRAJ SINGH CHOWDHARY
**Founding Systems Engineer** — Runtime AI Infrastructure · Financial Operating Systems · Distributed Control Planes

</td>
</tr>
</table>

<img src="./assets/banner-header.svg" width="100%" alt="terminal banner: founding systems engineer, runtime AI infrastructure, financial operating systems, distributed control planes"/>

[![Email](https://img.shields.io/badge/Email-chowdharyyuvrajsingh%40gmail.com-0d1117?style=for-the-badge&logo=gmail&logoColor=39d353)](mailto:chowdharyyuvrajsingh@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-connectyuvraj-0d1117?style=for-the-badge&logo=linkedin&logoColor=58a6ff)](https://www.linkedin.com/in/connectyuvraj/)
[![GitHub](https://img.shields.io/badge/GitHub-chowdhary19-0d1117?style=for-the-badge&logo=github&logoColor=c9d1d9)](https://github.com/chowdhary19)
[![Synvolv](https://img.shields.io/badge/Synvolv-synvolv.com-0d1117?style=for-the-badge&logoColor=a78bfa)](https://synvolv.com/)
[![Remote](https://img.shields.io/badge/Remote-US%2FUK%20overlap%20·%20based%20in%20India-0d1117?style=for-the-badge&logoColor=f2cc60)](#)
[![Profile Views](https://komarev.com/ghpvc/?username=chowdhary19&style=for-the-badge&color=39d353&label=PROFILE+VIEWS)](https://github.com/chowdhary19)

</div>

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ whoami`

<img src="./assets/terminal-boot.svg" width="100%" alt="terminal session: whoami, north_star.md, status.sh, echo PHILOSOPHY"/>

I don't really do the personal-website-with-a-headshot-and-a-mission-statement thing. I do this instead — a terminal, because that's genuinely where I live most of the day.

Short version: I design and build the infrastructure that sits underneath AI products and trading operations — the layer between "the product works in a demo" and "the product survives contact with production." Request-path gateways. Policy evaluators. Provider orchestration. Usage ledgers. Reconciliation engines. Risk monitors. Audit trails. The stuff nobody screenshots for a launch post and everybody suddenly cares about the day it's missing.

Right now I'm the founding engineer building **[Synvolv](https://synvolv.com/)** — a runtime control plane that sits between AI products and the model providers they call, so that routing, budgets, policy, and provider spend are decided *before* they happen instead of reconciled after the invoice lands. In parallel, I built the operating backbone underneath **Blockhouse Capital's** trading desk — the unglamorous plumbing that keeps exchange connectivity, reconciliation, and risk visibility honest while real capital is actually moving. Before founder-mode, I spent a stretch at **Canonical** making sure other people's Linux infrastructure boots correctly on day one, because someone has to.

I don't ship demos. I ship the thing the demo was pretending to be.

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ git log --oneline --graph --decorate --all`

```text
* 4c9a2f1 (HEAD -> main, origin/synvolv) feat(gateway): ship OpenAI-compatible control plane to live traffic
* 8e1d0a3 feat(policy): enforce tenant budgets before provider spend commits
* 1f77b2c feat(routing): normalize every major model provider behind one contract
* 6b0d5e2 feat(ledger): make cost attribution a first-class citizen, not an afterthought
|
* d3b6e90 (origin/blockhouse) feat(quant-os): stand up trading desk operating layer from zero
* a02c88f feat(reconciliation): make exchange state and ledger state agree, always
* 77fe410 fix(risk): catch what fragmented CEX/DEX/broker data was quietly hiding
* 9c14f88 feat(reporting): give investors a control room instead of a spreadsheet
|
* 60021ab (tag: canonical-oss) feat(linux): ship Ubuntu cloud image validation upstream
* 2a417cd chore(ci): reduce release-day surprises for people I've never met
|
* 0000001 Initial commit — I just code.
```

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ cat architecture/gateway.md`

The pitch is simple: an AI product should not be able to spend money it doesn't have permission to spend, call a provider it isn't allowed to call, or run a request that violates policy — and it shouldn't need a rewrite to get that. Point an existing OpenAI-compatible client at the gateway, and every request now passes through a control plane before a single token leaves the building.

<img src="./assets/gateway-flow.svg" width="100%" alt="architecture diagram: client apps route through a runtime control plane (authn, policy evaluator, routing and fallback mesh, budget ledger, audit trail) before reaching OpenAI, Anthropic, Gemini, or a custom endpoint"/>

<div align="center"><sub><i>policy evaluated, budget checked, route decided — before a single token leaves the building.</i></sub></div>
<br/>

Under the hood, that box in the middle is doing the same job a payments processor does for money — except the currency is model tokens, and the fraud it's catching is a runaway agent loop instead of a stolen card. Auth and tenant identity resolve first. Policy gets evaluated against live budget state. The router picks a provider and model, with fallback baked in for when an upstream has a bad day. Every decision — allowed, throttled, rerouted, blocked — gets written to an audit trail that can answer "what happened and why" without anyone needing to SSH into anything at 2am.

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ ls -la ~/systems --sort=impact`

```text
drwxr-x---  founder  founder   synvolv-gateway/       # runtime control plane for live LLM traffic
drwxr-x---  founder  founder   blockhouse-quant-os/   # operating backbone for a live trading desk
drwxr-x---  founder  founder   canonical-oss/         # upstream Linux infra validation, Canonical
-rw-r--r--  founder  founder   .still-coding          # never modified, always open
```

<details>
<summary><b>$ cat synvolv-gateway/README.md</b></summary>
<br/>

The problem: teams wire an LLM provider into a product, and from that moment every prompt is an unmonitored operational and financial liability. No budget ceiling. No policy layer. No idea which feature, tenant, or workflow is actually driving spend until the bill shows up.

**Synvolv** is the fix — an OpenAI-compatible gateway an existing app can adopt with a config change, not a rewrite. Underneath it: policy evaluation, tenant budgets, provider routing and fallback, model normalization across every major provider, and a cost ledger that knows what a request is worth before the response even comes back. It's built to sit in the hot path of production traffic without anyone noticing it's there — until the day it stops a runaway workflow from doing real damage.

I own this end to end — architecture, backend, the control-plane UX operators actually use, and the design-partner conversations that keep it honest against how AI infra actually breaks once it leaves a notebook.

</details>

<details>
<summary><b>$ cat blockhouse-quant-os/README.md</b></summary>
<br/>

Blockhouse runs real capital across CEX, DEX, and broker venues, which means the "boring" stuff — reconciliation, margin visibility, execution monitoring, knowing exactly what you hold and what you owe, right now — is the whole game.

I built the operating layer underneath the desk: normalized account and position state across fragmented venues, real-time investor reporting, and exception handling for the stuff that silently goes wrong — failed fills, funding anomalies, delisting risk, ADL exposure. Plus the daily control room the team actually watches instead of a stack of dashboards nobody trusts.

```text
$ grep -r "financial-infra" ~/systems/blockhouse-quant-os/
CEX/DEX APIs · Broker APIs · IBKR · Order & Fill Pipelines · Account/Subaccount State
Execution Monitoring · Portfolio & PnL Systems · Margin/Liquidation Checks
ADL & Delisting Surveillance · DEX Signing · Replay Protection · Investor Reporting
```

This isn't a trading strategy. It's the infrastructure that makes running one, with other people's money, something you can actually defend.

</details>

<details>
<summary><b>$ cat canonical-oss/README.md</b></summary>
<br/>

Before founder-mode, I spent time making sure other people's infrastructure boots correctly in the first place — validating Ubuntu cloud and server images across provisioning, boot diagnostics, networking behavior, and package health at Canonical. Open-source, async-first, globally distributed team, code review as a way of life.

It's where I actually learned what "infrastructure" means: invisible when it works, extremely loud when it doesn't.

</details>

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ ls stack/`

**`ai-runtime/ + languages/`**
<br/>
<img src="https://skillicons.dev/icons?i=py,go,rust,ts,js&theme=dark&perline=5" alt="Python, Go, Rust, TypeScript, JavaScript"/>

**`backend + data/`**
<br/>
<img src="https://skillicons.dev/icons?i=nodejs,express,django,fastapi,graphql,postgres,mysql,mongodb,redis&theme=dark&perline=9" alt="Node.js, Express, Django, FastAPI, GraphQL, PostgreSQL, MySQL, MongoDB, Redis"/>

**`cloud + reliability/`**
<br/>
<img src="https://skillicons.dev/icons?i=docker,kubernetes,aws,githubactions,nginx,terraform,grafana,prometheus&theme=dark&perline=8" alt="Docker, Kubernetes, AWS, GitHub Actions, Nginx, Terraform, Grafana, Prometheus"/>

**`operator-surfaces + growth/`**
<br/>
<img src="https://skillicons.dev/icons?i=react,nextjs,tailwind,figma,vercel,cloudflare,supabase&theme=dark&perline=7" alt="React, Next.js, Tailwind CSS, Figma, Vercel, Cloudflare, Supabase"/>

<br/>

<img src="./assets/skills-ticker.svg" width="100%" alt="scrolling ticker: gateway, policy engine, routing mesh, budget ledger, audit trail, control plane, reconciliation, risk monitor, go, python, rust, kafka, clickhouse, kubernetes, postgresql, ownership"/>

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ cat manifesto.txt`

- I don't ship demos. I ship the thing the demo was pretending to be.
- Uptime isn't a KPI I report on. It's a personality trait.
- I have read more provider API docs than I'd like to admit in a public document.
- If you're debugging a weird request at 2am, there's a decent chance one of my systems already logged exactly why.
- "0→1" isn't a resume word for me — it's just what happens when nobody else has built the thing yet, so I do.
- I don't do meetings about infrastructure. I do infrastructure.
- I just code. That's it. That's the whole bio.

<img src="./assets/section-divider.svg" width="100%" alt=""/>

## `$ ./github-stats.sh --live`

<div align="center">

<img height="168" src="https://github-readme-stats.vercel.app/api?username=chowdhary19&show_icons=true&hide_border=true&bg_color=0d1117&title_color=a78bfa&text_color=c9d1d9&icon_color=39d353&border_color=21262d&count_private=true" alt="Yuvraj's GitHub stats"/>
<img height="168" src="https://github-readme-stats.vercel.app/api/top-langs/?username=chowdhary19&layout=compact&hide_border=true&bg_color=0d1117&title_color=a78bfa&text_color=c9d1d9&border_color=21262d" alt="Top languages"/>

<img src="https://github-readme-streak-stats.herokuapp.com/?user=chowdhary19&hide_border=true&background=0D1117&stroke=21262D&ring=39D353&fire=F2CC60&currStreakLabel=A78BFA&sideLabels=C9D1D9&dates=8B949E&currStreakNum=C9D1D9&sideNums=C9D1D9" alt="GitHub streak stats"/>

<img src="https://github-readme-activity-graph.vercel.app/graph?username=chowdhary19&bg_color=0d1117&color=39d353&line=a78bfa&point=ffffff&area=true&area_color=39d353&hide_border=true" width="100%" alt="Contribution activity graph"/>

<img src="https://github-profile-trophy.vercel.app/?username=chowdhary19&theme=onedark&no-frame=true&column=4&margin-w=8&margin-h=8&row=2" alt="GitHub trophies"/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/chowdhary19/chowdhary19/output/snake-dark.svg"/>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/chowdhary19/chowdhary19/output/snake.svg"/>
  <img alt="a snake eating my own contribution graph, which is somehow the most honest metaphor on this page" src="https://raw.githubusercontent.com/chowdhary19/chowdhary19/output/snake-dark.svg" width="100%"/>
</picture>

</div>

<img src="./assets/footer-signoff.svg" width="100%" alt="still building. always building. made in a terminal, not a design tool."/>

<div align="center">

> "Strive not to be a success, but rather to be of value." — Albert Einstein

[![Email](https://img.shields.io/badge/-Email-39d353?style=flat-square&logo=gmail&logoColor=0d1117)](mailto:chowdharyyuvrajsingh@gmail.com)
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-58a6ff?style=flat-square&logo=linkedin&logoColor=0d1117)](https://www.linkedin.com/in/connectyuvraj/)
[![Synvolv](https://img.shields.io/badge/-Synvolv-a78bfa?style=flat-square)](https://synvolv.com/)

</div>
