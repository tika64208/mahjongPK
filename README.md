# 龙岩麻将

规则文档见：[龙岩麻将规则整理](docs/longyan-mahjong-rules.md)。

## 自动麻将 MVP

本仓库包含一个本地命令行 MVP，可让你和 3 个机器人玩一局龙岩麻将核心规则版。

当前规则核心已支持开金、抢金、碰牌、暗杠、明杠、补杠、杠后补牌、自摸、三金倒、七对、十三幺、单游和双游 MVP。

默认 3 个机器人具备不同能力：

- 机器人A：基础策略，保留对子、邻张和金牌。
- 机器人B：会计算向听数，优先让手牌更接近胡牌。
- 机器人C：专家策略，会计算向听、真实剩余进张、胡牌价值、碰牌收益、防守风险和金牌保留价值。

机器人能力通过 `AbilityConfig` 配置，后续可映射为账号已购买能力：

- `shanten`：向听计算。
- `effective_draws`：有效进张。
- `remaining_tiles`：剩余牌统计。
- `hand_value`：胡牌价值评估。
- `pong_ev`：碰牌收益评估。
- `defense`：防守风险评估。
- `gold_strategy`：金牌策略。
- `style_control`：风格控制，可偏激进、防守或高分。
- `opponent_tenpai`：对手听牌概率判断。
- `danger_refined`：危险牌精细评分。
- `kong_ev`：杠牌收益评估，专家机器人可用它控制明杠动作。
- `youjin_strategy`：游金/双游/三游路线预留。
- `monte_carlo`：轻量模拟收益估计。
- `explanation`：出牌解释和训练提示。

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
- [机器人能力测试方案](docs/ability-benchmark-plan.md)
