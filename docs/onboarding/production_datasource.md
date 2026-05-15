## Production Step 2 — Create an Open Dental Datasource

After creating your production institution you need to create a sync that
connects NexHealth to your practice's Open Dental database.

### Create the Sync

1. In the developer portal (production mode), navigate to the Institutions page.

2. Click "Create new sync" in the top right corner.

3. Select "Open Dental" as the system you are syncing with.

4. The portal will display your unique product key and a download link for
   the NexHealth Synchronizer installer. Copy the product key — you will
   need it in the next step.

### Install the Synchronizer on the Practice Server

NOTE: This step must be performed on-site (or remotely) at the dental practice.
You will need access to their Windows server and an IT contact or admin at the
practice. If you need help coordinating this, contact NexHealth support at
support@nexhealth.com — they can assist with guided Synchronizer installs.

The Synchronizer must be installed on the Windows machine where the practice's
Open Dental database is running. This is typically a server at the practice
location itself.

1. Download the installer from: https://nexhealth.com/download

2. Run the installer on the practice's Windows server.
   The machine must have Windows administrative privileges.

3. Enter your product key when prompted and let the installer complete.

4. If the installer fails to open, first install the Visual C++ runtime:
     https://aka.ms/vs/17/release/vc_redist.x64.exe
   Then re-run the Synchronizer installer.

5. After installation, the Synchronizer will prompt you to select which
   locations to monitor. Select the location(s) that will be connected
   to your application.

### Verify the Sync

Back in the developer portal, the institution's sync status should update to
reflect that the Synchronizer is connected. Allow a few minutes for the initial
data sync — providers, locations, operatories, and patients will populate.

Once your sync is active, continue to the production_api_key section.