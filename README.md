<div align="center">
  <img src="./assets/hero-terminal.svg" width="100%" alt="Yuvraj Singh Chowdhary — founder and infrastructure engineer — in an animated terminal scanner">
</div>

<p align="center">
  <a href="https://synvolv.com/"><code>synvolv</code></a>
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://cal.com/heyyuvraj/chat"><code>schedule a call</code></a>
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="mailto:chowdharyyuvrajsingh@gmail.com"><code>email</code></a>
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://www.linkedin.com/in/connectyuvraj/"><code>linkedin</code></a>
</p>

<br>

## `$ cat /home/yuvraj/about`

Most people try to place me in one box.

Backend. Infrastructure. AI. Quant. Blockchain. Founder.

The honest answer is that I keep following a system until I reach the layer that can actually fail the business.

I have built web products and automations, DeFi and signing flows, exchange and broker integrations, order and fill state machines, portfolio and cash reconciliation, risk monitors, Linux release tooling, distributed backends, AI gateways, policy engines, usage ledgers, internal terminals and operator control planes.

Not because I collect stacks. I do not.

Each problem simply pulled me one layer deeper.

A feature became a service. The service became a queue. The queue became a state machine. The state machine touched money. Money required a ledger. The ledger disagreed with an exchange. The exchange required reconciliation. Reconciliation required an operator. The operator needed a control plane. The control plane sat in the hot path. The hot path had to become fast enough to disappear.

From the outside that looks like breadth. From inside my head it is one obsession:

```text
make the important state explicit
keep the system honest under pressure
own the path after the endpoint returns 200 OK
```

I like starting from zero. Empty repository, ugly first diagram, incomplete requirements, a customer describing the problem with the wrong nouns — that is usually where my best work begins.

I am not the engineer who needs the problem to arrive pre-cut into tickets. I would rather understand the business, find the real invariant, build the first working system, operate it, watch where reality disagrees with the design and then rebuild the part that was pretending.

That is also why I became a founder. Sometimes the missing layer is too important to remain a side project.

<br>

<div align="center">
  <img src="./assets/systems-overview.svg" width="100%" alt="An animated terminal systems map showing Yuvraj's work across product, blockchain, quantitative finance, infrastructure and AI runtime systems">
</div>

<br>

## `$ less /var/log/the-long-way-here.log`

I started by building whatever I could get my hands on.

Small products taught me speed. You learn quickly when there is nobody else to blame for the database, the deployment, the broken onboarding and the page that looked perfect on your machine. Automation taught me the first serious lesson: a boring five-minute task becomes infrastructure the moment a team quietly depends on it.

Blockchain and DeFi changed the cost of being careless.

A bad retry is not merely noisy. A signing boundary is not an implementation detail. A stale nonce, loose replay protection or confused chain state can turn a small software mistake into irreversible truth. That work made me respect state transitions, ownership and the difference between an action being accepted and an action being correct.

Then I moved closer to markets and financial operations.

Exchanges do not agree with one another. Broker APIs lag. Orders are accepted before they are settled. Fills arrive out of order. Balances drift. Rate limits become architecture. Funding, collateral, margin and liquidation risk continue moving while your worker is restarting.

So I built the layer around the APIs: normalized account state, order and fill pipelines, exchange-specific recovery, cash checks, reconciliation, portfolio views, execution monitoring, market-event surveillance, risk alerts, investor reporting and the internal control room people could actually use when the data stopped being polite.

That period made one thing permanent in the way I think:

> If two systems can disagree about money, reconciliation is not an afterthought. It is part of the product.

Linux and platform work taught me a different kind of discipline. A fix that lives in one engineer's shell history is not a fix. A test that passes only in the environment where it was written is not a test. Cloud images, boot failures, package behavior, CI, diagnostics, release validation and regression triage made me less impressed by clever code and much more impressed by systems that can reproduce and explain themselves.

Then AI infrastructure brought almost every earlier lesson into the same request path.

Provider differences. Streaming. Rate limits. Tenant isolation. Fallbacks. Variable cost. Usage attribution. Policy. Retry semantics. Tail latency. Audit. Operators. The bill arriving long after the engineering decision that created it.

It felt familiar.

So I built the control layer I wanted to exist.

<br>

## `$ ./inspect --builder --all-layers`

I am an infrastructure engineer in the broad, old-fashioned meaning of the word.

I care about the things underneath a product, between its components and immediately after it fails.

I can work at the request edge where every allocation matters, then move into the ledger where every mutation needs a reason, then into the operator surface where the system must explain what happened without asking somebody to grep six services at 3 AM.

I have designed and shipped:

```text
request paths        gateways, middleware, streaming, routing, rate control
financial state      ledgers, reconciliation, cash, PnL, margin, exposure
market connectivity  CEX / DEX / broker adapters, orders, fills, account state
control systems      policy engines, budgets, permissions, audit, operator actions
data systems         transactional models, event pipelines, analytical read paths
reliability          retries, idempotency, backpressure, recovery, observability
platform work        Linux tooling, CI, release validation, containers, deployment
product surfaces     terminals, control rooms, dashboards, onboarding, internal tools
```

The languages change. The shape of the work does not.

I use Go when the service needs to stay simple and fast. Python when the problem is data-heavy, operational or moving quickly. TypeScript when the operator surface and the backend need to evolve together. Rust when the boundary genuinely earns the extra strictness. PostgreSQL, Redis, ClickHouse, Kafka, RabbitMQ, containers, Linux, cloud services, traces and metrics are tools I know well, but none of them are my identity.

My actual skill is keeping the whole path in view.

```text
user intent
  -> identity and authorization
  -> current state
  -> policy
  -> money / risk
  -> execution
  -> side effects
  -> evidence
  -> recovery
  -> operator decision
```

A lot of software is locally correct and globally wrong. Every service returns success. Every dashboard is green. The customer still lost money, the balance still drifted, the retry still duplicated the action or the provider bill still destroyed the margin.

I build against that class of failure.

<br>

## `$ cat /srv/synvolv/WHY`

[**Synvolv**](https://synvolv.com/) is what happened when that systems instinct met production AI.

I founded it because AI teams had model SDKs, gateways, logs and monthly spend reports, but very little authority during the only moment that matters: while the request is still alive and the outcome can still be changed.

I architected the gateway and control plane from an empty repository.

The path handles OpenAI-compatible ingress, provider normalization, streaming, tenant identity, budgets, policy snapshots, model access, routing, health-aware fallback, metering, cost attribution, audit evidence and the operator controls around all of it.

I built one of the fastest AI gateway control paths I know of in production: about **456 microseconds of average measured gateway overhead** on our path while still making real policy and routing decisions.

That speed matters because infrastructure should not become the tax for using infrastructure. The control layer has to be fast enough to disappear, explicit enough to dispute and complete enough to operate.

Synvolv is one thing I am building. It is not the only thing I know how to build. It is the clearest current expression of how I work:

```text
understand the whole system
put authority before the irreversible action
leave evidence after it
make the operator stronger
remove latency until the layer feels inevitable
```

<details>
<summary><strong>production receipts</strong></summary>
<br>

```text
17M+        LLM requests / month across scaled design partners
~456 us     average measured gateway overhead
200+        models across major providers and custom endpoints
< 5 min     OpenAI-compatible integration path

$65M        AUM supported by quant operating infrastructure I built with the team
12          investor clients supported during the operating build-out
20+         exchanges covered by market-event and delisting surveillance
```

The numbers are useful because real systems should leave evidence. They are not the biography.

</details>

<br>

## `$ cat ~/.notes-from-systems-that-fought-back`

```text
01  The happy path proves the demo. The recovery path proves the product.

02  A retry is a new state transition, not a second chance to forget the first one.

03  "Real-time" is a promise about freshness, ordering and recovery — not a WebSocket.

04  A ledger is the answer you can still defend after two systems disagree.

05  Tail latency is where a clean architecture stops being polite.

06  If a control cannot change the outcome, it is a report.

07  An automatic decision without evidence is tomorrow's argument.

08  The operator is part of the system. Design for the person carrying the pager.

09  Fast code with slow recovery is not a fast system.

10  A provider saying accepted does not mean the business state is correct.

11  Hidden state becomes visible during the worst possible incident.

12  The best infrastructure is boring only because somebody did the hard thinking early.
```

I care about performance, but not benchmark theatre. I care about speed when it changes capacity, tail behavior, unit economics or the way a product feels.

I care about correctness, but not the kind that ends when the tests turn green. Correct means the retry is safe, the ledger reconciles, the failure is visible, the decision can be explained and the next operator has a clean move.

I care about architecture, but I am suspicious of diagrams that do not include deployment, backfill, migration, alerting and recovery.

And I care about taste. Sharp names. Fewer knobs. Explicit ownership. Small hot paths. Useful logs. Honest metrics. No magic state. No ritual that only one engineer remembers.

The best compliment somebody can give my work is not that it looks clever.

It is that the system is real, understandable and hard to accidentally betray.

<br>

## `$ git log --all --author=yuvraj --stat`

These panels are generated inside this repository from the profile owner's real public GitHub history.

No visitor-counter theatre. No trophy wall. No third-party statistics service waiting to disappear. A scheduled GitHub Action queries the account, builds the contribution and activity SVGs, then commits them back into the repository.

<div align="center">
  <img src="./assets/github-contributions.svg" width="100%" alt="Live terminal-styled GitHub contribution history generated by this repository">
</div>

<div align="center">
  <img src="./assets/github-activity.svg" width="100%" alt="Recent public GitHub activity generated by this repository">
</div>

<br>

## `$ ./connect --problem-has-teeth`

I am most useful when the prototype worked and reality has started asking better questions.

Bring me the gateway that must disappear under load. The financial workflow that technically works but nobody trusts. The exchange integration with six definitions of account state. The AI product whose usage is growing faster than its unit economics. The queue that is fine until the same message arrives twice. The internal operation held together by a spreadsheet, a Slack channel and one person's memory.

I will trace the whole path, find the real invariant and build the missing layer.

```text
call      https://cal.com/heyyuvraj/chat
email     chowdharyyuvrajsingh@gmail.com
linkedin  https://www.linkedin.com/in/connectyuvraj/
company   https://synvolv.com/
```

```text
yuvraj@production:~$ █
```
