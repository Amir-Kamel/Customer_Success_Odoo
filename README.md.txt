# Customer Success Module - Task Assignments

## Assigned Tasks

### Amir
- Edit the menu:
  - Add a **Configurations** submenu containing *Teams*, *Tags*, and *Stages*.
  - Rename the **Records** menu to **Pipeline**.
- Add a **Team Leader** field to the *Teams* module (relation with `res.users`).
- Restrict the available users in the **Assigned User** field (renamed to **Success Partner**) in the *Pipeline* module based on the chosen team.
- When selecting a related CRM record, automatically update the **Title** and **Customer** fields with data from the chosen CRM record.
- Automatically populate **Phone** and **Email** fields from the linked `partner_id`.
- Create a **Tags** module and connect it to the *Customer Success* model, similar to how tags work in CRM.

---

### Mahmoud
- Fix the **Health Bar** (UI/UX only: make it increase and decrease properly).
- After fixing, display the health bar inside record details (with percentage shown).
- Remove the **Stage** field from details view and replace it with **Workflow Flags** at the top right of the page.
- Add a **Star Rating** field:
  - Show stars in *Kanban cards*.
  - Show stars in *Record Details* (use `priority` widget or selection field).
- Add a **CRM button** at the top center of the page, linking to the related CRM record.

---

### Mina
- Modify the **Last Feedback** field:
  - Rename it to **Feedback**.
  - Move it to the bottom of the page inside a new *tab sheet*.
  - Convert it to an **HTML field**.
- Add an **Avatar** for the Success Partner:
  - In *Kanban view*: remove the label "Assigned:" and instead display the avatar beside the Success Partner’s name.
- Inherit `mail.thread` and `mail.activity.mixin`, then add activity tracking in *Kanban cards*.
- Redesign the **Record Details page**:
  - Use a **two-column layout**.
  - Page headline should display only the *Title* field (remove extra header).
  - **Left column:** Customer, Mobile, Email, Health, Renewable Date.  
  - **Right column:** Team, Success Partner (Assigned User), Related CRM, Tags.

---

## Postponed Tasks
- Implement a **Dashboard** (to be planned later).
