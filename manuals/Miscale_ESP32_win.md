## 2.4. Miscale_ESP32_WIN VERSION

### 2.4.1. Preparing host operating system
- It is possible to run Linux as a virtual machine in Windows 11 by installing Hyper-V with powershell:
```
PS> Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```
- Check host IP address (network adapter with default gateway), create a virtual switch in bridge mode:
```
PS> Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -ne "Disconnected"} | Select InterfaceAlias, IPv4Address
InterfaceAlias IPv4Address
-------------- -----------
Ethernet 1         {192.168.4.18}
PS> New-VMSwitch -Name "bridge" -NetAdapterName "Ethernet 1"
```
- In powershell, create a virtual machine generation 2 (1vCPU, 1024MB RAM, 8GB disk space, bridge network connection, mount iso with Debian 12):
```
PS> New-VM -Name "export2garmin" -MemoryStartupBytes 1GB -Path "C:\" -NewVHDPath "C:\export2garmin\export2garmin.vhdx" -NewVHDSizeBytes 8GB -Generation 2 -SwitchName "bridge"
PS> Add-VMDvdDrive -VMName "export2garmin" -Path "C:\Users\robert\Downloads\debian-12-amd64-netinst.iso"
PS> Set-VMMemory "export2garmin" -DynamicMemoryEnabled $false
PS> Set-VMFirmware "export2garmin" -EnableSecureBoot Off -BootOrder $(Get-VMDvdDrive -VMName "export2garmin"), $(Get-VMHardDiskDrive -VMName "export2garmin"), $(Get-VMNetworkAdapter -VMName "export2garmin")
PS> Set-VM -Name "export2garmin" –AutomaticStartAction Start -AutomaticStopAction ShutDown
```
- Start Hyper-V console from powershell and install Debian 12 (default disk partitioning with minimal components, SSH server is enough):
```
PS> vmconnect.exe 192.168.4.18 export2garmin
```
- After installing system in powershell check IP address of guest to be able to log in easily via SSH, you will also need this address to configure connection parameters MQTT in ESP32 (**"mqtt_server"**):
```
PS> get-vm -Name "export2garmin" | Select -ExpandProperty Networkadapters | Select IPAddresses
IPAddresses
-----------
{192.168.4.118, fe80::215:5dff:fe04:c801}
```

### 2.4.2. Preparing guest operating system
- Log in via SSH with IP address (in this example 192.168.4.118) and install following package:
```
$ su -
$ apt install -y sudo
```
- Add a user to sudo (in this example robert), reboot system:
```
$ usermod -aG sudo robert
$ reboot
```
- Go to next part of instructions:
  - [Miscale - Debian 12](https://github.com/RobertWojtowicz/export2garmin/blob/master/manuals/Miscale_ESP32.md);
  - Back to [README](https://github.com/RobertWojtowicz/export2garmin/blob/master/README.md).

## If you like my work, you can buy me a coffee
<a href="https://www.buymeacoffee.com/RobertWojtowicz" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>