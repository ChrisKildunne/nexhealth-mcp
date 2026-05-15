## Step 3 — Install the NexHealth Synchronizer

The NexHealth synchronizer connects Open Dental to the NexHealth platform,
allowing appointments created through the API to appear in the EHR in real time.

### Get Your Product Key

1. Log in to your NexHealth developer portal.
2. Navigate to the Institutions page.
3. Click "Create new sync" in the top right corner.
4. Select "Open Dental" as the system you are syncing with.
5. You will see your product key and a download link for the installer.

### Install the Synchronizer

Perform these steps inside Windows (inside Parallels if you are on a Mac):

1. Download the installer from: https://nexhealth.com/download
2. Run the installer inside your Windows environment.
3. Enter your product key when prompted and let the installer complete.

### Troubleshooting

If the installer fails to open, install the Visual C++ dependency manually:
  https://aka.ms/vs/17/release/vc_redist.x64.exe
Then reattempt the synchronizer installation.

Once complete, Open Dental is fully connected to NexHealth.
Next: store your API key (api_key section).