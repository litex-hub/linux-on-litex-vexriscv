## Regenerate all the default configurations

Install Java and SBT, then run :

```sh
./generate.py
```


## HOWTO:
This document describes how to configure and use the periperals of your board from Linux.

**Configure/Use the Leds**:

Configure the Leds GPIOs as outputs:
````
$echo 508 > /sys/class/gpio/export
$echo out > /sys/class/gpio/gpiochip508/direction
````
Set the Leds value:
````
$echo 0 > /sys/class/gpio/gpio508/value
$echo 1 > /sys/class/gpio/gpio508/value
````

**Configure/Use the PWM RGB Led**:

````
$ cd /sys/class/pwm/pwmchip0
$ echo 0 > export
$ cd pwm0
$ echo 100 > period
$ echo 50 > duty_cycle
$ echo 1 > enable
````

This should configure the LED with 50% PWM that you can adjust by changing the `duty_cycle` value from `0` to the configured `period`.

**Configure/Use Ethernet**:

1. Manual address:

Verify that the `eth0` ethernet device is present:
`$ ifconfig -a`:
````
eth0      Link encap:Ethernet  HWaddr C6:6A:FB:04:6A:B9
          BROADCAST MULTICAST  MTU:1500  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)

lo        Link encap:Local Loopback
          inet addr:127.0.0.1  Mask:255.0.0.0
          inet6 addr: ::1/128 Scope:Host
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)

sit0      Link encap:IPv6-in-IPv4
          NOARP  MTU:1480  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
````
Configure it:
`$ ifconfig eth0 192.168.1.50`

Verify that you can ping another machine on your network:
`$ ping 192.168.1.100`:
````
PING 192.168.1.100 (192.168.1.100): 56 data bytes
64 bytes from 192.168.1.100: seq=0 ttl=64 time=19.839 ms
64 bytes from 192.168.1.100: seq=1 ttl=64 time=4.585 ms
64 bytes from 192.168.1.100: seq=2 ttl=64 time=8.510 ms
64 bytes from 192.168.1.100: seq=3 ttl=64 time=12.522 ms
^C
--- 192.168.1.100 ping statistics ---
4 packets transmitted, 4 packets received, 0% packet loss
round-trip min/avg/max = 4.585/11.364/19.839 ms
````

2. Automatic address through DHCP:

`$ udhcpc -i eth0`

**Configure/Use the SPI Flash:**

There should be a `/dev/mtd0` that you can read from/write to directly from bash, i.e.,:
```
$ cat /dev/mtd0
```
Or even better, to see the data clearly:

```
$ dd if=/dev/mtd0 count=6 bs=1 status=none | hexdump
```

Before writing you should erase the flash first. This requires `BR2_PACKAGE_MTD` and `BR2_PACKAGE_MTD_JFFS_UTILS` to be enabled in the buildroot config.

```
$ flash_erase /dev/mtd0 0 1
$ echo -ne "\x01\x01" > /dev/mtd0
```

**Configure/Use the SDCard:**

Plug the SDCard, it should be detected with all partitions on it:

`$ ls /dev/mmcblk*`:
````
/dev/mmcblk0    /dev/mmcblk0p1
````

Mount the partition to the directory you want to access it (here /sdcard for example):
```
$ mkdir /sdcard
$ mount /dev/mmcblk0p1 /sdcard/
```

Check that you can read and write on it:
```
$ echo "Hi SDCard" > /sdcard/test
$ cat /sdcard/test
Hi SDCard
```


**Use the Framebuffer**:

When available on the board, the Video Framebuffer will be automatically enabled at startup and will show the tux logo during the boot.
In Linux you can then simply test the Video Framebuffer by filling it with random data with:
```
$ cat /dev/urandom >/dev/fb0
```
