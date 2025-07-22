# Chart of Accounts (COA) Models & Database Schema

This document describes the updated, multi-level Chart of Accounts (COA) models and database schema implemented in `accounting/models.py` as per `coa_implementation_plan.md`.

---

## Hierarchical Structure

- **AccountCategory**: Top-level group (e.g., Asset, Liability, Equity, Income, Expense, Contra-accounts)
- **AccountGroup**: Mid-level group (e.g., Current Assets, Non-Current Assets, etc.), supports parent-child nesting for up to 5 levels
- **Account**: Leaf-level ledger/account (e.g., Cash, Inventory, Receivable), linked to AccountGroup, supports sub-ledger relationships

---

## Models & Fields

### 1. AccountCategory
- `company`: ForeignKey to Company (multi-tenant support)
- `code`: CharField, unique per company
- `name`: CharField
- `description`: TextField (optional)
- `is_active`: Boolean
- **Meta**: `unique_together` on (company, code)

### 2. AccountGroup
- `company`: ForeignKey to Company
- `category`: ForeignKey to AccountCategory
- `code`: CharField, unique per company
- `name`: CharField
- `parent`: ForeignKey to self (optional, for nesting)
- `description`: TextField (optional)
- `is_active`: Boolean
- **Meta**: `unique_together` on (company, code)

### 3. Account
- `company`: ForeignKey to Company
- `group`: ForeignKey to AccountGroup (multi-level COA hierarchy)
- `code`: CharField, unique per company
- `name`: CharField
- `description`: TextField (account metadata/details)
- `type`: CharField, choices: Asset, Liability, Equity, Income, Expense, Contra-Account (main account type)
- `parent`: ForeignKey to self (optional, for sub-ledger relationships, e.g., customer/vendor sub-accounts)
- `is_group`: Boolean (mark as grouping node, non-posting)
- `is_default`: Boolean (system-wide default account mapping, e.g., Sales Revenue, Retained Earnings)
- `is_active`: Boolean (enable/disable account)
- `balance_side`: CharField, choices: Debit/Credit (normal balance side)
- `account_type`: CharField (sub-classification, e.g., COGS, Admin Expense, Bank, Receivable)
- `created_at`: DateTimeField (audit/history tracking)
- `updated_at`: DateTimeField (audit/history tracking)
- **Meta**: `unique_together` on (company, code)

---

## Relationships & Hierarchy

- **AccountCategory** (1) → (M) **AccountGroup**
- **AccountGroup** (1) → (M) **Account**
- **AccountGroup** supports parent-child nesting for multi-level grouping
- **Account** supports parent-child for sub-ledger (e.g., AR by customer)

---

## Comments & Usage

- All models are multi-tenant (company-specific)
- Unique codes enforced per company for all levels
- `is_group` and `parent` fields allow flexible hierarchy and grouping
- `is_default` enables system-wide mapping for default accounts (e.g., for auto-posting)
- `balance_side` and `account_type` support financial reporting and validation
- Designed for integration with all ERP modules (Sales, Purchase, Inventory, Manufacturing, HR, Banking)

---

## Example Hierarchy

- **AccountCategory**: Asset
  - **AccountGroup**: Current Assets
    - **AccountGroup**: Cash & Bank
      - **Account**: Cash-in-Hand
      - **Account**: Bank Account 1
    - **AccountGroup**: Receivables
      - **Account**: Accounts Receivable
  - **AccountGroup**: Non-Current Assets
    - **Account**: Land
    - **Account**: Buildings

---

## Migration

- Run Django makemigrations/migrate to apply these schema changes.
- Update integration logic in other modules to use the new COA structure for account mapping.

---

## 🧠 Advanced Auto-Posting Utilities

### 1. Multi-Line, Multi-Account Posting
- Use `auto_post_journal_multi(company, lines, ...)` to post a batch of debit/credit lines in a single journal entry.
- Each line is a dict: `{ 'account': <Account>, 'debit': <amount>, 'credit': <amount>, 'description': <optional> }`
- Example:
  ```python
  from accounting.utils import auto_post_journal_multi
  lines = [
      {'account': acc_receivable, 'debit': 1000, 'description': 'Invoice receivable'},
      {'account': acc_revenue, 'credit': 1000, 'description': 'Sales revenue'}
  ]
  entry = auto_post_journal_multi(company, lines, reference='INV-001', user=request.user, journal_type='sales')
  ```

### 2. Context-Aware Posting
- Use `auto_post_context(company, context_type, context_obj, ...)` for business event-driven posting.
- Example for sales invoice:
  ```python
  from accounting.utils import auto_post_context
  entry = auto_post_context(company, 'sales', invoice_obj, user=request.user)
  ```
- The utility will post the correct debits/credits based on the context (e.g., sales, purchase, payroll).
- Extend `auto_post_context` to support more business events as needed.

### 3. Validation
- All posting utilities use `validate_account_for_posting()` to ensure only active, non-group accounts are used.

---

For more, see `accounting/utils.py` and the API documentation.

For further details, see `accounting/models.py`