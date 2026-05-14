## Step 2a — Mac Users: Install Parallels (Windows Virtual Machine)

NOTE: Installing Parallels and setting up a Windows environment takes
approximately 20-30 minutes. Please set aside enough time before starting.

Open Dental is an on-premises EHR that only runs on Windows. Mac users need
to install Parallels Desktop to simulate a Windows environment.

1. Download the Parallels trial installer from:
   https://www.parallels.com/products/desktop/trial/

2. Run the Parallels installer and click "Install Parallels Desktop".

3. Once complete, open the Parallels Desktop application.

4. Walk through the Parallels setup process and grant any permissions it requests.

You will now have a Windows 11 desktop environment running inside your Mac.
All remaining Open Dental and synchronizer steps take place inside that
Windows environment.

### Install a Required Dependency

The NexHealth synchronizer requires a Visual C++ runtime that may be missing
from the virtual environment. Install it now before moving on:

1. Inside Parallels, open Microsoft Edge and complete any initial setup steps.
2. Navigate to: https://aka.ms/vs/17/release/vc_redist.x64.exe
3. Run the downloaded installer and follow each step. Click "Close" when done.

Your Parallels Windows environment is now fully configured.
Next: install Open Dental inside this Windows environment (open_dental section).