# 🚀 CRM, Customer Success & Time Off Module Enhancements #5  

---

##### 📈 CRM App Enhancements (Need to be Assign)  

###### ✅ Urgent  
1. **Yes/No Field with Won Stage Behavior**  
   - Add a **Yes/No field** in CRM records.  
   - This field appears **only when the record reaches the Won stage**.  
   - Once chosen (Yes or No), the field becomes **readonly**.  
   - If **Yes** → automatically create a record in **Customer Success** with the same CRM data.  
   - If **No** → make the field readonly and prevent creating a related Customer Success record.  

2. **Create Project Button in CRM**  
   - Add a **Create Project button** (green) in CRM records.  
   - Base it on the **same function from the Sales module**.  
   - After project creation:  
     - Hide the button.  
     - Show a **Smart Button** linking to the related Project.  

3. **Smart Button Synchronization in CSM**  
   - In Customer Success (CSM), show a **Smart Button for Project** in each record.  
   - By default → the button appears but is **disabled**.  
   - When the related CRM record creates a Project:  
     - Enable the button in CSM.  
     - Button opens the same related Project.  
   - Use a **compute function** to update dynamically whenever the CRM record changes.  

4. **Survey Button in CSM**  
   - Add a button **“Survey”** in Customer Success records.  
   - Should behave like **“Ask Feedback”** in the **Appraisal app**.  
   - Since Community Edition lacks this code, retrieve the function logic from other sources.

##### 📈 CRM App Enhancements (Assigned to **Omar**)

###### ✅ Urgent (Old Task)
5. **Stage Tracking per Record**  
   - Add a **Notebook Page** per CRM record containing a table:  
     - Stage Name  
     - Start Date (when record entered stage)  
     - End Date (when record left stage)  
     - Difference (duration in that stage).  

6. **Average Stage Duration & Graphs**  
   - Add a **Float field** to calculate **average duration** across stages.  
   - Show **Average Duration** in views.  
   - Use this field for generating graphs.  

> NOTE: Use "log code.txt file" and "the photo" shared in the group as reference.  

---

##### 📊 Customer Success App Enhancements  

###### ⚠️ Optional (Old Task)
1. **Dashboard Analytics UI/UX**  
   - Fix empty analytics boxes → show a placeholder or clean UI when no data.  
2. **Team Leader Restricted Dashboard**  
   - Each Team Leader can only see **their clients** and **record counts**.  

---

##### 🆕 Time Off Portal App Enhancements (Assigned to **Amir**)  

###### ✅ Urgent  (Old Task)
1. **Third Menu in Time Off Portal**  
   - Add a **third menu** in the Time Off Portal app.  
   - Display the same data & behaviors of **Approves and Refuses** in the waiting list of the original Time Off app.  
   - Ensure the design is **clean and user-friendly**.  
