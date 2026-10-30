# Account churn data

`data/accounts.csv` has one row per customer account (3000 rows).

| Column | Meaning |
|---|---|
| account_id | Unique account id |
| signup_month | Month the account signed up (2025-01 to 2025-12) |
| plan | basic, pro or team |
| seats | Number of paid seats |
| onboarding_completed | yes if the account finished the guided onboarding |
| support_tickets_90d | Support tickets opened in the 90 days observed |
| price_increase_notice | yes if the account received the July 2025 price-increase notice |
| churned | yes if the account cancelled during the observation window |

Docs for context are in `docs/`.
