# Customer Success Module – Enhancements 

---

## 📌 Features & Enhancements  

### 1. Stages  
- Inline form view for stages (similar to Tags – no separate form page).  
- Add checkboxes for:  
  - **Achieved stage**  
  - **Lost stage**  
- Only one option (Achieved or Lost) can be selected per stage.  

### 2. Demo Data  
- Provide demo data automatically upon app installation.  

### 3. Automatic Field Population  
- **Phone** and **Email** are auto-filled from the linked **Partner (`partner_id`)**.  
- **Title** and **Customer** are auto-filled from the related **CRM Lead**.  
- If filled automatically → field becomes **read-only**.  
- If no data exists → field remains **editable**.  

### 4. Record Details Page Redesign  
- Two-column layout.  
- Page headline = **Title only** (remove extra header).  
- **Left column:** Customer, Mobile, Email, Health, Renewable Date.  
- **Right column:** Team, Success Partner, Related CRM, Tags.  

### 5. Kanban View & Activity Tracking  
- Inherit `mail.thread` and `mail.activity.mixin`.  
- Add activity tracking icons:  
  - ⏰ for activities  
  - ✉️ for emails  
- Show icons in Kanban cards + Record Details page.  
- Remove field labels in Kanban (display only values, e.g., show “Amir Kamel” instead of “Customer: Amir Kamel”).  

### 6. CRM Lead Integration  
- Related CRM Lead shown as a **smart button** (center of page).  
- Users can only **read** the CRM record (no edit/update/delete/unlink).  
- When a CRM record reaches **Won stage**:  
  - Automatically create a new record in the **first Customer Success stage**.  
  - Auto-fill Title, Partner, Phone, Email.  
  - Notes visible but not editable.  

### 7. Stage-Based Actions & Buttons  
- If at least one **Achieved** stage & one **Lost** stage exist → show two buttons:  
  - ✅ Achieved (green)  
  - ❌ Lost (red)  
- If only Achieved stages exist → show **Achieved button only**.  
- If only Lost stages exist → show **Lost button only**.  
- Remove other default stage buttons.  

### 8. Behavior on Achieved Stage  
- Health = **100%**.  
- Show **green flag widget** in top-right corner.  
- Trigger **success animation** (similar to CRM).  
- Hide stage action buttons (based on config).  

### 9. Behavior on Lost Stage  
- Health = **0%**.  
- Show **red flag widget** in top-right corner.  
- Open **popup window** asking for **reason of loss**.  
- After confirmation:  
  - Save reason as read-only **Lost Reason** field in details page.  
  - Hide stage action buttons (based on config).  

### 10. Dashboard (Postponed)  
- Dashboard feature planned but **postponed for now**.  

---
