# **Senior Data Engineer \- Home Assignment**

You may use documentation, search engines, coding assistants, and LLMs. We do not expect you to work without modern tools. Please clearly identify where you used AI assistance, and be ready to explain and defend every decision in the interview.

**How to read this assignment.** The bullets under some sections are leading questions: they point at what we care about, not a checklist to complete. We would rather see depth, clear trade-offs, and edge cases you identified yourself than a short answer to every bullet. If you think a bullet is the wrong question, say so and explain why.

# **Scenario**

You have joined a company whose analytics platform looks roughly like this:

* Object storage (S3) is the data lake and holds raw and curated data.

* A cloud data warehouse (Redshift) serves analytics and BI workloads.

* Looker is used by analysts and business users.

* Airflow orchestrates batch pipelines.

* Data arrives from APIs, application databases, and event streams.

* Several teams depend on the platform for business-critical dashboards and metrics.

You inherit the platform from another engineer. Documentation is incomplete, some pipelines carry technical debt, and business users increasingly expect fresher and more trustworthy data.

# **1\. Production Incident: The Dashboard Numbers Changed**

At 09:30, a business stakeholder reports that yesterday's revenue on the dashboard showed \$2.4M earlier this morning but now shows \$2.1M. The dashboard normally becomes stable by 07:00. No deployment was made to the dashboard.

You discover the following:

* The dashboard reads from a Redshift model built from data in S3.

* The upstream source is an API loaded incrementally by date.

* The pipeline succeeded according to Airflow.

* The API occasionally returns late corrections to previous days.

* The pipeline writes partitioned data to S3 and then refreshes the warehouse table.

* There is no documented data-quality SLA.

**Leading questions:**

1. What are your first checks, in order, and why those first?

2. Which hypotheses do you consider, and what evidence eliminates each one?

3. How do you decide whether the current number, the previous number, or both are wrong?

4. What do you tell the stakeholder, and what temporary mitigation would you apply?

5. What would you change permanently so this is prevented, or at least detected before a stakeholder notices?

*There is deliberately no single correct answer. We are interested in your debugging process, prioritization, and understanding of data correctness.*

# 

# **2\. Design a Reliable, Large-Scale Incremental Pipeline**

You need to ingest data from a partner REST API into the data lake and serve it through the warehouse. The source and its consumers have these characteristics:

## **Source**

* Supports date-range queries by event\_date and paginated results.

* Records can be corrected or updated up to 7 days after the original event\_date.

* Requests are rate-limited; a request can partially fail or time out.

* The API does not provide a reliable total count for a query.

* New fields appear in the payload without notice.

## **Scale**

* Roughly 200–300 million records per day (about 1–1.5 TB of raw JSON per day), growing about 50% per year.

* Three years of history must be backfilled before go-live.

## **Consumers and requirements**

* BI dashboards in Looker (through Redshift) need data by 07:00 daily.

* Data scientists query the same curated data directly on the lake with Spark and Athena. Copying it into separate silos per engine is not acceptable.

* Privacy (GDPR) deletion requests for a user must be applied across all history within 30 days.

* Finance must be able to reproduce any reported number exactly as it looked on a past reporting date.

* The pipeline runs daily, and an operator must be able to re-run any historical date range safely.

**Leading questions:**

1. Logical architecture: major components, storage format, and table format. Justify the choices against the requirements above.

2. Extraction window, late corrections, and deletes: how do they reach the lake and the warehouse without full rewrites?

3. Idempotency and failure handling: what makes a re-run, retry, or interrupted run safe, and what state do you keep?

4. Lake-to-warehouse serving: what lives in Redshift, what stays on the lake, and how does it get there?

5. Data validation and observability: how do you know the data is complete and correct, not just that the job succeeded?

6. Cost and performance at this scale: where does the money go, and what are your main levers?

*Show where you would deliberately keep the design simple and where you believe additional complexity is justified.*

# 

# 

# **3\. Data Modeling & SQL**

The company has the following tables:

| Table | Column | Meaning | Notes |
| :---- | :---- | :---- | :---- |
| users | user\_id | User identifier | Unique |
| subscriptions | subscription\_id | Subscription identifier | Unique |
| subscriptions | user\_id | User identifier |  |
| subscriptions | product | Product name | pro / mp |
| subscriptions | start\_date | First active date |  |
| subscriptions | end\_date | First inactive date | NULL means currently active |
| events | event\_ts | Event timestamp | UTC |
| events | user\_id | Logged-in user | NULL for anonymous events |
| events | event\_name | Event name |  |

**Definitions:** An active user on a date is a user with at least one event with a non-null user\_id on that date (UTC). A user is paying on a date if at least one of their subscriptions was active on that date. "Last 30 days" means the 30 complete days ending yesterday.

Write SQL (state your dialect) for:

* **3a.** Daily active paying users for the last 30 days, overall and per product. A user with both products counts once in the overall number.

* **3b.** For each day, the percentage of active users who were paying users.

* **3c.** Users who had more than one overlapping subscription period. Return the user and the overlapping subscription pairs.

For 3c, briefly state your assumptions about boundary dates. For all three, explain how you would validate the result on production data.

# **4\. Set** 

[Set](https://en.wikipedia.org/wiki/Set_\(card_game\)) is a real-time card game consisting of 81 unique cards that vary in four features across three possibilities for each kind of feature:

1. The number of shapes (one, two, or three)  
1. The shape itself (diamond, squiggle, oval)  
1. The Shading (solid, striped, or open)  
1. The color (red, green, or purple)

Each possible combination of features (e.g., a card with three striped green diamonds) appears as a card precisely once in the deck.

**Rules:**  
A set consists of three cards satisfying all of these conditions:

> * They all have the same number or have three different numbers.  
> * They all have the same shape or have three different shapes.  
> * They all have the same shading or have three different shadings.  
> * They all have the same color or have three different colors.

Write a Python program that will:

> * Draw three unique cards  
> * Decide whether the cards form a set  
> * Repeat until a set is found or the deck is empty

The program should have a clear design for each element in the game (e.g., Card, Deck, Feature...) and the matching algorithm.  
Be minded of time and space complexity. 

# **5\. AI / Data Agent Architecture**

The company wants to build a Data Agent for analysts and data scientists. It should answer questions such as:

* Why did daily active users decrease yesterday?

* Which dashboard uses this metric, and what is the SQL behind it?

* What was the source of this number, and is this dataset fresh?

* Compare this week's subscription conversion with the previous four weeks.

* A pipeline failed \- what happened and what data may be affected?

The platform includes S3, Redshift, Looker, Airflow, a data catalog, and existing monitoring and logging. Sensitive data exists in the platform, and the agent must not become a backdoor around existing access controls.

1. What are the major components, and what does the agent have access to?

2. Walk through one question end to end, for example "Why did DAU drop yesterday?"

3. How are permissions enforced, and how do you prevent the agent from exposing data the user cannot already see?

4. Where do you deliberately avoid using an LLM, and why?

5. How would you evaluate whether the agent's answers are correct and trustworthy?

*We are not looking for a specific LLM vendor or framework. Explain the engineering principles behind your design.*

# **Submission**

* A PDF or Markdown document with your reasoning and diagrams. Diagrams may be embedded images or links.

* SQL and code snippets where requested.

* A short closing section: the two or three decisions you are least confident about, and what would change your mind.

* A note on where you used AI assistance.

Please optimize for clarity and practical reasoning rather than length. Depth in the areas you consider most important beats shallow coverage of everything.

**Good luck \- we look forward to discussing your approach.**