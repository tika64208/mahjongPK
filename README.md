# 龙岩麻将

规则文档见：[龙岩麻将规则整理](docs/longyan-mahjong-rules.md)。

## 自动麻将 MVP

本仓库包含一个本地命令行 MVP，可让你和 3 个机器人玩一局龙岩麻将核心规则版。

默认 3 个机器人具备不同能力：

- 机器人A：基础策略，保留对子、邻张和金牌。
- 机器人B：会计算向听数，优先让手牌更接近胡牌。
- 机器人C：会计算向听数和有效进张，同向听下优先进张更多的打法。

运行：

```bash
python3 -m longyan_mj.cli
```

使用固定随机种子复现牌局：

```bash
python3 -m longyan_mj.cli --seed 1
```

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

需求与架构：

- [需求分析](docs/requirements.md)
- [架构设计](docs/architecture.md)
- [1000 局自动模拟数据](docs/simulation-results.md)
