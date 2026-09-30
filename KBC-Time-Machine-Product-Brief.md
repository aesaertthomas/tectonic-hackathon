# KBC Time Machine — Product Brief

**Status:** Proposed concept, working title. This brief describes what we want to build; it does not claim these capabilities already exist at KBC.

## 1. What we are building

A feature within a banking app that learns a customer's usual financial patterns, notices meaningful changes, and explains what those changes could mean for their future finances. Customers can then add context, explore different scenarios, and connect their habits to personal goals such as buying a car or a home.

The core experience is: **notice a change → explain its possible impact → ask for context → offer a useful next step.**

## 2. The problem

A balance tells customers how much money they have today. A transaction history tells them where their money went. Customers still have to work out whether their habits are changing, whether those changes are sustainable, and how they affect future plans.

We want to make those connections easier to understand while there is still time to make a decision. The feature should recognise positive progress as well as potential pressure on a customer's finances.

## 3. Who it is for

The first version focuses on personal banking customers with sufficient transaction history who want help understanding their spending, saving, and progress toward a goal. It should be useful without requiring them to maintain a detailed manual budget.

Customers with irregular income can use it, but forecasts must reflect that uncertainty. When history is insufficient, the app should invite the customer to enter expectations instead of presenting a confident prediction.

## 4. Core capabilities

| Capability | What it does | Customer benefit |
| --- | --- | --- |
| Learn usual patterns | Establish typical spending by category, recurring payments, income patterns, and saving contributions | Provides a personal baseline |
| Detect meaningful changes | Identify unusual spending, sustained increases, lower income, or growing saving contributions | Draws attention to changes that matter |
| Estimate future impact | Combine current balances, expected income, scheduled bills, and estimated spending | Shows how a change could affect available money |
| Accept customer context | Let customers correct a category or explain a change | Makes future insights more relevant |
| Support personal goals | Capture a goal, target amount, target date, and earmarked savings | Connects daily habits to a desired outcome |
| Suggest next steps | Offer relevant planning tools, saving features, and eligible bank services | Helps customers act on the insight |

## 5. Example: spending increases

The customer usually spends €300–€400 per month on groceries. This month, they spend €600.

The app could say:

> “Your grocery spending was €600 this month. Your usual range is €300–€400. Was this a one-off, or do you expect it to continue?”

The customer can choose **One-off**, **Expected to continue**, **Category is incorrect**, or **Dismiss**.

If the customer explores the impact, the app shows a forecast using their wider financial situation. For illustration: if their usual monthly surplus is €150 and groceries increase from a €350 baseline to €600, their monthly surplus would become a €100 shortfall, assuming everything else stays the same. Over three months, that would mean €300 less available cash.

Only if the account forecast supports it should the app explain that a savings transfer may be needed to cover payments. The warning must account for income, other expenses, accessible balances, and the customer's chosen cash buffer. Repeating an unusual expense a fixed number of times is not enough by itself to justify that warning.

## 6. Example: saving increases

The app notices that the customer has been setting aside more money for several months.

> “You've increased your monthly saving contributions from around €200 to €450. Would you like to connect this to a goal?”

The customer can select **Car**, **Home**, **Emergency fund**, or **Another goal**, or decline to add one. The app must not assume what they are saving for.

For a car goal, the customer enters the amount they want to save and, optionally, a target date. The app estimates their timeline, shows how changing contributions affects it, and offers relevant tools. For a home goal, it can help plan upfront savings and link to an appropriate affordability tool; goal progress alone does not establish mortgage affordability.

Suggestions should explain why they are relevant. Planning and saving actions should be available without requiring the customer to choose a financial product. Product terms, eligibility, and availability need verification before integration.

## 7. What the customer sees

**An overview:** A small set of prioritised insights about spending changes, saving progress, and possible upcoming cash pressure.

**An insight detail view:** The change, the historical comparison, the transactions behind it, and the assumptions used to estimate its impact.

**A scenario view:** A simple forecast over the next one to three months. Customers can compare “this was a one-off” with “this continues,” or adjust expected spending and income. Estimated values must be visually distinguishable from confirmed scheduled payments.

**A goals view:** Each goal's target amount, earmarked savings, remaining amount, estimated completion date, and relevant next steps.

Notifications should be reserved for meaningful, timely insights. Customers can control frequency, snooze an insight, or disable a category of notifications.

## 8. First version: scope

Build one complete flow from transaction data to an understandable insight and a customer action:

1. Categorise transactions and identify recurring income and expenses.
2. Establish a personal baseline using an initial three-to-six-month history window, with the final requirement validated during testing.
3. Detect category spending increases and sustained increases in saving contributions.
4. Generate explainable insight cards with supporting transactions.
5. Show a one-to-three-month cash-flow scenario and its assumptions.
6. Let customers mark changes as one-off, ongoing, or incorrectly categorised.
7. Let customers create a car, home, emergency fund, or custom goal.
8. Suggest a small set of verified tools or services relevant to the confirmed goal.

Automatic money movement, borrowing, investment execution, and specific investment recommendations are outside the first version. The feature may help customers understand a possible surplus, but it does not make future income available to spend or invest today.

## 9. Data and calculation requirements

The feature needs transaction dates, amounts and categories; account balances; recurring or scheduled payments; identifiable income; and customer-entered goals and context.

Transfers between a customer's own accounts must not be counted as new income or ordinary spending. Credit-card purchases and repayments must not be counted twice. Refunds and incomplete months need appropriate treatment. Moving money into savings should not automatically be described as a rise in net wealth.

Forecasts should use transparent calculations. A language model may help explain an insight or interpret customer context, but the monetary amounts and projections must come from a consistent calculation engine.

When accounts, cash spending, or future bills are missing, the app must state the coverage limits. It should not imply that it knows the customer's complete financial position.

## 10. Product principles

- **Explain the evidence:** Customers can see why an insight appeared.
- **Make uncertainty visible:** Forecasts describe possible outcomes under stated assumptions.
- **Ask before inferring intent:** Customers confirm goals and explain changes.
- **Use supportive language:** Messages are calm, specific, and free of judgment.
- **Prioritise relevance:** Small fluctuations should not generate repeated alerts.
- **Keep customers in control:** They can correct data, dismiss insights, and adjust preferences.
- **Connect recommendations to a need:** Suggestions follow the customer's confirmed goal and have a clear rationale.

## 11. How we will measure success

The feature succeeds when customers understand a meaningful change, understand its possible impact, and can choose an appropriate next step.

Measure insight usefulness, correction and dismissal rates, forecast error against actual outcomes, goal creation and continued use, and notification opt-outs. Test whether customers understand the forecast's assumptions and can distinguish estimates from confirmed payments. Product uptake can be a secondary measure, but it should not be the sole measure of usefulness.

## 12. Decisions to validate before development

Confirm transaction and account coverage, history requirements, detection thresholds, handling of irregular income, forecasting accuracy, notification frequency, and the tools or services available for each goal. Determine whether the experience lives in a dedicated section, within Kate, or both.

The first prototype should demonstrate two complete journeys: **an increase in grocery spending with a cash-flow scenario**, and **an increase in saving contributions leading to a confirmed car or home goal**. Use synthetic data until access to real customer data is explicitly established.

## Product promise

**“Understand what's changing in your finances, see where it could lead, and take a useful next step toward what you want.”**
