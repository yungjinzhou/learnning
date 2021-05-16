Since these are absolute counters, you would have to regularly retrieve these metrics and then do the calculation yourself. So, if you want the number over the next minute, you would have to get the numbers, wait a minute, and get the numbers again. SNMP would not update those numbers too often so you may not be able to get these every second anyway.

Once you have the raw user, nice, system, idle, interrupts counters you can get the total number of ticks by summing these up. Even the MIB description says that adding them up is expected.

$ snmptranslate -Td .1.3.6.1.4.1.2021.11.52
UCD-SNMP-MIB::ssCpuRawSystem
...
    This object may sometimes be implemented as the
    combination of the 'ssCpuRawWait(54)' and
    'ssCpuRawKernel(55)' counters, so care must be
    taken when summing the overall raw counters."
Then, regardless of how long it has been since you took the measurements, the total number of ticks over that period is total1 - total0. And the idle percentage would be (idle1-idle0)/(total1-total0).

You are asking "how do you know how many ticks per second it is typically" but as you can see, you don't need to know that.




利用ceilometer组件，用snmp收集硬件信息时，得到cpu参数为以tick time为计数的值，上面是转换方法。
