# モニタリング

## top
CPU利用率

```bash
$ top
top - 21:33:48 up 3 days, 17:32,  3 users,  load average: 0.00, 0.00, 0.00
Tasks: 123 total,   1 running, 121 sleeping,   1 stopped,   0 zombie
%Cpu(s):  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0
MiB Mem :    924.9 total,     90.0 free,    611.9 used,    223.0 buff/cach
MiB Swap:      0.0 total,      0.0 free,      0.0 used.    158.7 avail Mem

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+
     67 root       0 -20       0      0      0 I   0.0   0.0   0:00.00
     68 root       0 -20       0      0      0 I   0.0   0.0   0:00.00
     72 root       0 -20       0      0      0 I   0.0   0.0   0:00.00
     73 root      20   0       0      0      0 S   0.0   0.0   0:00.24
     74 root       0 -20       0      0      0 I   0.0   0.0   0:00.00
     76 root       0 -20       0      0      0 I   0.0   0.0   0:00.09
    115 root      19  -1   97456  28708  27556 S   0.0   3.0   0:01.81
```

上記はCPU稼働率0%の状態。

## free
メモリ利用率のモニタリング。
--human(-h)オプションによってhuman-readableに、人間が読みやすいように単位を付けて表示する。
```bash
$ free --human
               total        used        free      shared  buff/cache   available
Mem:           924Mi       611Mi        90Mi       0.0Ki       223Mi       158Mi
Swap:             0B          0B          0B
```

上記は941MiBのメモリが搭載されており、userdから611MiB使われていることが分かる。

## stress

CPU稼働率を疑似的に上昇させる。

