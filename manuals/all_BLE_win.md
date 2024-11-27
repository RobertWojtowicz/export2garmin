## 2.4. all_BLE_WIN VERSION

### 2.4.1. Preparing host operating system
- It is possible to run Linux as a virtual machine in Windows 11 by installing Hyper-V with powershell:
```
PS> Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```
- After rebooting Windows, install software to connect usb to virtual machine, type command in powershell:
```
PS> winget install usbipd
```
- Describing solution will **only work with USB adapters**, buy cheap USB bluetooth:
  - 5.0/5.1 (tested on RTL8761B chipset, manufacturer Zexmte, works with Miscale and Omron module);
  - 5.3 (tested on ATS2851 chipset, manufacturer Zexmte, works only with Miscale module).
- Bluetooth adapter should have a removable RP-SMA antenna;
- List devices in powershell that you can share:
```
PS> usbipd list
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
1-2    0a12:0001  Generic Bluetooth Radio                                       Not shared
```
- Share USB bluetooth adapter for virtual machine (requires administrator privileges):
```
PS> usbipd bind --busid 1-2
```
- Disable shared device (in this example Generic Bluetooth Adapter) from host system so that there are no bluetooth adapter conflicts, check IP address (network adapter with default gateway):
```
PS> Get-PnpDevice -FriendlyName "Generic Bluetooth Radio" | Disable-PnpDevice -Confirm:$false
PS> Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -ne "Disconnected"} | Select InterfaceAlias, IPv4Address
InterfaceAlias IPv4Address
-------------- -----------
Ethernet 1         {192.168.4.18}
```
- In powershell, create a virtual machine generation 2 (1vCPU, 1024MB RAM, 8GB disk space, default NAT network connection, mount iso with Debian 12):
```
PS> New-VM -Name "export2garmin" -MemoryStartupBytes 1GB -Path "C:\" -NewVHDPath "C:\export2garmin\export2garmin.vhdx" -NewVHDSizeBytes 8GB -Generation 2 -SwitchName "Default Switch"
PS> Add-VMDvdDrive -VMName "export2garmin" -Path "C:\Users\robert\Downloads\debian-12-amd64-netinst.iso"
PS> Set-VMMemory "export2garmin" -DynamicMemoryEnabled $false
PS> Set-VMFirmware "export2garmin" -EnableSecureBoot Off -BootOrder $(Get-VMDvdDrive -VMName "export2garmin"), $(Get-VMHardDiskDrive -VMName "export2garmin"), $(Get-VMNetworkAdapter -VMName "export2garmin")
PS> Set-VM -Name "export2garmin" –AutomaticStartAction Start -AutomaticStopAction ShutDown
```
- Start Hyper-V console from powershell and install Debian 12 (default disk partitioning with minimal components, SSH server is enough):
```
PS> vmconnect.exe 192.168.4.18 export2garmin
```
- After installing system in powershell check IP address of guest to be able to log in easily via SSH:
```
PS> get-vm -Name "export2garmin" | Select -ExpandProperty Networkadapters | Select IPAddresses
IPAddresses
-----------
{172.17.76.18, fe80::215:5dff:fe04:c801}
```

### 2.4.2. Preparing guest operating system
- Log in via SSH with IP address (in this example 172.17.76.18) and install following packages:
```
$ su -
$ apt install -y usbutils usbip sudo
```
- Add a user to sudo, add loading vhci_hcd module on boot, reboot system:
```
$ usermod -aG sudo robert
$ echo "vhci_hcd" | sudo tee -a /etc/modules
$ reboot
```
- Set USB Bluetooth adapter service to start automatically (via host IP address, include "User" name) at system boot, create a file `sudo nano /etc/systemd/system/usbip-attach.service`:
```
[Unit]
Description=usbip attach service
After=network.target

[Service]
Type=simple
User=robert
ExecStart=/usr/sbin/usbip attach --remote=192.168.4.18 --busid=1-2
ExecStop=/usr/sbin/usbip detach --port=0
RemainAfterExit=yes
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
- Activate usbip-attach service and run it:
```
$ sudo systemctl enable usbip-attach.service && sudo systemctl start usbip-attach.service
```
- You can check if export2garmin service works `sudo systemctl status usbip-attach.service` or temporarily stop it with command `sudo systemctl stop usbip-attach.service`;
- Go to next part of instructions, select module:
  - [Miscale - Debian 12](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_BLE.md);
  - [Omron - Debian 12](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Omron_BLE.md);
  - Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
