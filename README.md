# Y86 Simulator

## 简介

实现一个 Y86-64 指令集模拟器。

```bash
Y86-64-Simulator/
│
├─ test/           # 测试指令文件
│
├─ answer/         # 指令执行结果
│
├─ test.py         # 测试脚本：运行模拟器 + 对比结果
│
└─ code/            # 自定义模拟器代码
```

## 测试方法

运行 `python test.py --bin "python ./code/run.py"`

自定义：
* 如果你的 cpu 可执行文件为 `./cpu`，运行 `python test.py --bin ./cpu`

* 如果你的 cpu 需要解释器，运行 `python test.py --bin "python cpu.py"`

> [!note]
>
> 将你最终用于测试的命令写入 `test.sh`，方便我们最终进行测试。
