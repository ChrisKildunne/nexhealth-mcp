# Troubleshooting: Sandbox Environment

This guide covers common questions and issues developers encounter when working
in the NexHealth sandbox environment. For general API error codes, see troubleshoot.md.

---

## How do I add an additional sandbox location or sync integration?

**Short answer:** You are typically limited to one integrated location in the sandbox.

By default, NexHealth allows developers one complimentary integrated location in
the sandbox environment. We recommend using Open Dental for this integration.

**If the "Create new sync" button is greyed out** in the top right corner of your
institution page in the developer portal, it means you have already created your
one complimentary integrated location.

**To request an additional sync:**
Reach out to developers@nexhealth.com. Additional syncs are handled on a
case-by-case basis — explain your use case and the team will let you know
if it can be accommodated.

**Steps to find the Create new sync button:**
1. Log in to your developer portal at https://developers.nexhealth.com
2. Navigate to the Institutions page
3. Select your institution
4. Look for the "Create new sync" button in the top right corner
5. If it is greyed out, your complimentary sync has already been used

---

---

*More sandbox troubleshooting topics will be added here as common issues are identified.*

## Why are the reads/writes showing "read" only?

**Short answer:** This indicates the connection between NexHealth and your database
has been severed — NexHealth can read from the database but can no longer write to it.

This is most commonly seen after a server restart, a database outage, or when the
NexHealth synchronizer service stops running.

**Things to check:**

1. **Is the server online?**
   Confirm the Windows server (or Parallels VM if on Mac) running Open Dental
   is powered on and accessible.

2. **Is the database up and running?**
   Open Dental runs on MySQL. Confirm the MySQL service is running on the server.
   In Windows, open Task Manager or Services and look for MySQL.

3. **Is the NexHealth synchronizer running?**
   This is the most common cause. Check that the NexHealth Synchronizer service
   is active:
   - On Windows, press `Win + R`, type `services.msc`, and press Enter
   - Look for **NexHealth Synchronizer** in the list
   - If it shows as Stopped, right-click and select **Start**
   - If it fails to start, try restarting the machine and checking again

Once all three are confirmed running, the reads/writes status should return to
normal within a few minutes as the synchronizer re-establishes its connection.

**If the issue persists** after confirming all three, reach out to
developers@nexhealth.com with a description of what you see in the Services panel.

