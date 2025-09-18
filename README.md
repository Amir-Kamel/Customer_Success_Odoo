# 🚀 Customer Success & Employee Module Enhancements #3

---

## 🔎 Search View Grouping (✅ Done)

- Added **default group-by options** in the Customer Success search view:
  - Tags
  - Team
  - Partners
  - Assigned User

---

## 🔒 Security Handling (Assigned to **Omar**)

Implement a **3-level security system**:

- **Assigned User**
  - Can view & edit **only their assigned records**.
  - ❌ Cannot delete any records.
- **Team Leader**
  - Can view, edit, and delete records **within their own team only**.
- **Admin**
  - Full access to **all teams, records, and actions**.

---

## ⚠️ Warning Notifications on Stage Removal (Assigned to **Mahmoud**)

- When a record is **removed from the "Won" stage in CRM**, a **warning message** should be sent in the **Customer Success module**.
- The warning message should include the **record title** that was removed.
- Implement this using **Activities**, as discussed in the meeting.

---

## 🆕 Employee & Time Off Module Enhancements (Assigned to **Amir**)

**Objective**: Allow multiple approvers for employee time-off requests.

### Current Behavior
- Field under **Work Information → Time Off** is `many2one` (single approver).

### New Requirement
- Change to `many2many` → multiple approvers must **all approve** before leave is granted.
- Approval must require **all selected approvers**, not just one or some.

### Implementation Ideas
1. **Inheritance Approach**
   - Replace the type of field with a `many2many`.
   - Check and update approval logic so all assigned users must approve.

2. **New Field Approach**
   - Add a new `many2many` field for time-off approvers.
   - Hide the original field.
   - Update **Time Off → Configurations → Time Off Types** logic.
   - Extend the last two approval functions to include the new field behavior.

-----------------------------------
