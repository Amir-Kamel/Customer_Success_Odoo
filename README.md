# 🚀 CRM, Customer Success & Time Off Module Enhancements #6  

---

### 🕒 DH Portal Time Off Website App (Assigned to **Amir**)  

###### ✅ Done  
1. **Portal Access Error Message**  
   - Fixed the error message appearing on the website when portal users try to access waiting-for-approval pages without internal rights.  
   - Example of the error:  
     ```
     Uh-oh! Looks like you have stumbled upon some top-secret records.
     Sorry, andrew (id=8) doesn't have 'read' access to: - User (res.users)
     ```
   > **Note:** Need to discuss the **portal access limitation issue** — since portal users can’t have rules or groups, this approach might not be functional.  

---

### 📈 CRM Module (Assigned to **Mahmoud**)  

###### ✅ Urgent  
1. **Return to Won Stage Notification**  
   - When a CRM record returns again to the **Won stage**, if the related record in CSM still exists (not deleted):  
     - Automatically add an **activity notification** in the related CSM record.  
     - The activity should notify that the CRM record has **returned to the Won stage**.  
   - This is similar to the previous task but reverses the logic (previously triggered when leaving the Won stage).  

---

### 📊 Customer Success Module (Assigned to **Mina**)  

###### ✅ Urgent  
1. **Survey Wizard Integration**  
   - Take the **wizard view** and add a new field of type **Survey (survey_id)**.  
   - Add this field inside the wizard view and integrate it into the logic.  
   - Use the **“Share” button function** from the Survey app.  
   - Once a survey type/template is chosen:  
     - Automatically update all related data (e.g., survey links, metadata).  
   - Later, implement logic to connect all survey participations related to a record by:  
     - Adding a new field in all survey participations to link them to their **related CSM record**.  
   - **Note:** Complete the first part (integration and data sync) successfully before proceeding to the second part (participation linking).  

---

### 📊 Customer Success App Enhancements  

###### ⚠️ Optional  
1. **Dashboard Analytics UI/UX**  
   - Fix empty analytics boxes → show a placeholder or clean UI when no data.  
2. **Team Leader Restricted Dashboard**  
   - Each Team Leader can only see **their clients** and **record counts**.  

---

### 🔗 CRM & Customer Success Integration (Assigned to **Mahmoud** - If Not Finished)  

###### ✅ Urgent  
1. **Yes/No Field with Won Stage Behavior**  
   - Add a **Yes/No field** in CRM records.  
   - This field appears **only when the record reaches the Won stage**.  
   - Once chosen (Yes or No), the field becomes **readonly**.  
   - If **Yes** → automatically create a record in **Customer Success** with the same CRM data.  
   - If **No** → make the field readonly and prevent creating a related Customer Success record.  

---

### 📈 CRM App Enhancements (Assigned to **Omar** - To Continue)  

###### ✅ Urgent  
1. **Stage Tracking per Record**  
   - Add a **Notebook Page** per CRM record containing a table with:  
     - Stage Name  
     - Start Date (when record entered stage)  
     - End Date (when record left stage)  
     - Difference (duration in that stage).  

2. **Average Stage Duration & Graphs**  
   - Add a **Float field** to calculate the **average duration** across stages.  
   - Display **Average Duration** in views.  
   - Use it to generate **graphs** for performance tracking.  

> **Note:** Use `log code.txt` file and the reference photo shared in the group for implementation details.  

---

### 💼 CRM Module (Assigned to **Amir**)  

###### ✅ Urgent  
1. **Sub Opportunity Feature**  
   - Add a **“Sub Opportunity” button** in CRM records.  
   - Allows creating **multiple child opportunities** from a parent record.  
   - Each child record:  
     - Has only **one parent**.  
     - Automatically inherits **team**, **team members**, **responsible users**, **phone**, and **email** from the parent.  
     - Allows entering a **new title** for the child opportunity.  
   - In each child record, display a **Parent Opportunity field** showing the originating record.  

---
