# 🚀 Customer Success, CRM & Time Off Module Enhancements #4

---

##### 🆕 Time Off App Enhancements (Assigned to **Amir**)

###### ✅ Urgent
- **Separated Menus for Time Off Types**  
  - Split **Configurations → Time Off Types** into **two menus**:  
    - **Absence Types**  
    - **Work Time Types**  
  - Rename menus based on type.  
- **New Record Behavior**  
  - When pressing **New** from Absence menu → auto-fill field as Absence.  
  - When pressing **New** from Work Time menu → auto-fill field as Work Time.  

###### ⚠️ Optional
- **Double Approval Check**  
  - If a user in the approvers list presses **Approve** or **Refuse** more than once → raise an error.  
  - Implement this check via **model function**.  
- **Restricted Validation for Time Off Types**  
  - Only **Admins** and **Time Officers** can change status to **Validate1**.  
  - Ensure it appears only for them.  

---

##### ⏱️ Time Approval App Enhancements (Assigned to **Amir**)

> App Reference: [OHRMS Holidays Approval](https://apps.odoo.com/apps/modules/18.0/ohrms_holidays_approval)

###### ✅ Urgent
- **Filter by Time Off Type**  
  - Filter displayed records in **time off field** by type:  
    - Absence  
    - Work Time  
  - Display either:  
    - Type in brackets beside each entry, **OR**  
    - Two separate fields (Absence-only, Work Time-only).  
- **Separate Approval Creation**  
  - Create **two approval types**:  
    - One for **Absence**  
    - One for **Work Time**  

---

##### 📊 Customer Success App Enhancements

###### ⚠️ Optional
- **Dashboard Analytics UI/UX**  
  - Fix empty analytics boxes → show a placeholder or clean UI when no data.  
- **Team Leader Restricted Dashboard**  
  - Each Team Leader can only see **their clients** and **record counts**.  

---

##### 📈 CRM App Enhancements (Assigned to **Omar**)

###### ✅ Urgent
- **Stage Tracking per Record**  
  - Add a **Notebook Page** per CRM record containing a table:  
    - Stage Name  
    - Start Date (when record entered stage)  
    - End Date (when record left stage)  
    - Difference (duration in that stage).  
- **Average Stage Duration & Graphs**  
  - Add a **Float field** to calculate **average duration** across stages.  
  - Show **Average Duration** in views and use it to generate graphs.  

> NOTE: Use "log code.txt file" and "the photo" that have sent on our group as a reference for you