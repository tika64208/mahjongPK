# 机器人能力胜率影响测试方案

## 1. 测试目标

评估每个机器人能力、能力组合和专家能力包对实际牌局表现的影响，为后续能力购买、会员权益、机器人难度和训练提示定价提供数据依据。

核心问题：

- 单个能力能提升多少胜率和平均得分？
- 哪些能力组合存在明显协同效果？
- 专家机器人中哪些能力最关键？
- 哪些能力更适合作为免费能力、单独售卖能力、能力包或会员能力？

## 2. 当前能力列表

| 能力 ID | 名称 | 当前作用 |
| --- | --- | --- |
| `basic_tile_efficiency` | 基础牌效 | 保留对子、邻张、金牌。 |
| `shanten` | 向听计算 | 判断出牌后离胡牌还有几步。 |
| `effective_draws` | 有效进张 | 计算可改善手牌的牌种数量。 |
| `remaining_tiles` | 剩余牌统计 | 结合牌河和明牌计算真实剩余有效张数。 |
| `hand_value` | 胡牌价值评估 | 偏好高分路线。 |
| `pong_ev` | 碰牌收益评估 | 判断碰牌是否划算。 |
| `defense` | 防守风险评估 | 高压局面减少危险出牌。 |
| `gold_strategy` | 金牌策略 | 提高金牌和金牌路线价值。 |
| `style_control` | 风格控制 | 调整激进、防守、高分等权重。 |
| `opponent_tenpai` | 对手听牌判断 | 估算对手听牌概率。 |
| `danger_refined` | 危险牌精细评分 | 细分熟张、生张、字牌、中张风险。 |
| `kong_ev` | 杠牌收益评估 | 当前保留杠潜力，后续接完整杠动作。 |
| `youjin_strategy` | 游金策略 | 当前提高金牌路线价值，后续接游金状态机。 |
| `monte_carlo` | 轻量模拟 | 用剩余有效张/牌墙估算短期收益。 |
| `explanation` | 出牌解释 | 生成出牌建议和原因，不直接提升 AI 胜率。 |

## 3. 测试类型

### 3.1 单能力增益测试

目的：评估某个能力单独加入后，相比基础机器人提升多少。

对照组：

```text
baseline = basic_tile_efficiency
```

实验组：

```text
baseline + shanten
baseline + effective_draws
baseline + remaining_tiles
baseline + hand_value
baseline + pong_ev
baseline + defense
baseline + gold_strategy
baseline + style_control
baseline + opponent_tenpai
baseline + danger_refined
baseline + kong_ev
baseline + youjin_strategy
baseline + monte_carlo
baseline + explanation
```

注意：

- 部分能力依赖其他能力才有意义，例如 `effective_draws` 通常需要配合 `shanten`。
- 单能力测试仍要保留，用于确认“单卖是否有感知价值”。

### 3.2 能力包测试

目的：评估更符合商品设计的能力组合。

建议能力包：

| 能力包 | 能力 ID |
| --- | --- |
| 免费基础包 | `basic_tile_efficiency` |
| 牌效包 | `shanten`, `effective_draws` |
| 读牌包 | `shanten`, `effective_draws`, `remaining_tiles` |
| 高分路线包 | `hand_value`, `gold_strategy`, `youjin_strategy` |
| 碰牌判断包 | `shanten`, `pong_ev` |
| 防守包 | `defense`, `opponent_tenpai`, `danger_refined` |
| 模拟包 | `shanten`, `effective_draws`, `remaining_tiles`, `monte_carlo` |
| 训练提示包 | `explanation`, `shanten`, `effective_draws`, `remaining_tiles` |
| 专家包 | 全部能力 |

### 3.3 专家移除测试

目的：从专家能力包中移除一个能力，观察表现下降多少，判断能力的重要性。

对照组：

```text
expert = 全部能力
```

实验组：

```text
expert - shanten
expert - effective_draws
expert - remaining_tiles
expert - hand_value
expert - pong_ev
expert - defense
expert - gold_strategy
expert - style_control
expert - opponent_tenpai
expert - danger_refined
expert - kong_ev
expert - youjin_strategy
expert - monte_carlo
expert - explanation
```

解释：

- 如果移除某能力后胜率明显下降，说明它是专家包的关键能力。
- 如果移除后几乎无影响，该能力可能更适合训练、解释、差异化体验，而不是胜率型卖点。

### 3.4 能力组合协同测试

目的：识别能力之间的协同价值。

重点组合：

| 组合 | 观察点 |
| --- | --- |
| `shanten` + `effective_draws` | 牌效能力是否明显优于只算向听。 |
| `effective_draws` + `remaining_tiles` | 理论进张变成真实剩余进张后的收益。 |
| `defense` + `opponent_tenpai` + `danger_refined` | 完整防守包收益。 |
| `hand_value` + `gold_strategy` + `youjin_strategy` | 高分路线收益。 |
| `remaining_tiles` + `monte_carlo` | 轻量模拟是否提升决策。 |
| `pong_ev` + `hand_value` | 碰牌是否会影响高分路线。 |

## 4. 实验设计

### 4.1 固定座位法

每次测试让实验机器人坐固定座位，例如机器人C，其余三个座位使用固定基准机器人。

优点：

- 对比简单。
- 容易观察实验机器人胜率。

缺点：

- 座位、庄家顺序可能有偏差。

建议：

- 每个能力至少跑 4 组，让实验机器人轮流坐 0、1、2、3 号位。
- 统计四个座位的平均表现。

### 4.2 同种子配对法

每个实验使用同一批 seed：

```text
baseline seeds = 1..N
test seeds = 1..N
```

优点：

- 降低随机牌墙差异带来的噪声。
- 更适合比较能力增益。

### 4.3 推荐局数

| 阶段 | 局数 | 用途 |
| --- | ---: | --- |
| 快速检查 | 100 | 确认逻辑无异常。 |
| 初步评估 | 1000 | 粗略判断能力强弱。 |
| 产品定价参考 | 5000 | 比较稳定的能力评分。 |
| 正式报告 | 10000+ | 降低随机误差。 |

当前 Python 引擎中专家机器人较耗时，建议先用 1000 局跑出方向，再优化 benchmark 脚本性能。

## 5. 统计指标

每个实验组记录：

| 指标 | 说明 |
| --- | --- |
| 总局数 | 实验局数。 |
| 胜场 | 实验机器人胡牌次数。 |
| 胜率 | 胜场 / 总局数。 |
| 非流局胜率 | 胜场 / 非流局局数。 |
| 总分 | 实验机器人累计分数。 |
| 平均每局得分 | 总分 / 总局数。 |
| 平均出牌数 | 一局平均出牌次数。 |
| 流局率 | 流局 / 总局数。 |
| 胡牌类型分布 | 普通自摸、七对、三金倒等。 |
| 平均胡牌倍数 | 胡牌价值变化。 |
| 平均计算耗时 | 能力带来的性能成本。 |

## 6. 能力评分公式

建议先采用 100 分制。

```text
能力评分 =
  胜率提升分
+ 平均得分提升分
+ 胡牌质量提升分
+ 稳定性分
- 性能成本扣分
```

### 6.1 胜率提升分

```text
胜率提升 = 实验组胜率 - 基准组胜率
```

| 胜率提升 | 分数 |
| --- | ---: |
| <= 0% | 0 |
| 0% - 1% | 10 |
| 1% - 3% | 25 |
| 3% - 6% | 40 |
| 6% - 10% | 55 |
| > 10% | 65 |

### 6.2 平均得分提升分

```text
得分提升 = 实验组平均每局得分 - 基准组平均每局得分
```

| 得分提升 | 分数 |
| --- | ---: |
| <= 0 | 0 |
| 0 - 0.1 | 5 |
| 0.1 - 0.3 | 10 |
| 0.3 - 0.6 | 15 |
| > 0.6 | 20 |

### 6.3 胡牌质量提升分

可用平均胡牌倍数或高分胡牌占比计算。

| 表现 | 分数 |
| --- | ---: |
| 无提升 | 0 |
| 高分胡牌略增 | 5 |
| 高分胡牌明显增加 | 10 |

### 6.4 稳定性分

观察多批 seed 的方差。

| 表现 | 分数 |
| --- | ---: |
| 波动大 | 0 |
| 波动中等 | 3 |
| 波动小 | 5 |

### 6.5 性能成本扣分

```text
耗时倍率 = 实验组平均耗时 / 基准组平均耗时
```

| 耗时倍率 | 扣分 |
| --- | ---: |
| <= 1.5x | 0 |
| 1.5x - 3x | -3 |
| 3x - 6x | -6 |
| > 6x | -10 |

## 7. 输出报告格式

建议 benchmark 输出 Markdown 和 JSON 两份。

### 7.1 Markdown 表格

```text
| 实验组 | 能力 | 胜率 | 胜率提升 | 平均分 | 得分提升 | 流局率 | 平均轮数 | 能力评分 |
```

### 7.2 JSON 结构

```json
{
  "games": 1000,
  "baseline": {
    "win_rate": 0.193,
    "avg_score": -0.17
  },
  "experiments": [
    {
      "name": "shanten",
      "abilities": ["basic_tile_efficiency", "shanten"],
      "win_rate": 0.245,
      "win_rate_delta": 0.052,
      "avg_score": 0.05,
      "score_delta": 0.22,
      "ability_score": 58
    }
  ]
}
```

## 8. 初步预期

| 能力 | 预计胜率影响 | 备注 |
| --- | --- | --- |
| `shanten` | 高 | 算向听是质变。 |
| `effective_draws` | 高 | 与向听配合明显。 |
| `remaining_tiles` | 中高 | 越到中后盘越有价值。 |
| `hand_value` | 中 | 可能提高得分，不一定提高胜率。 |
| `pong_ev` | 中 | 减少乱碰。 |
| `defense` | 中 | 当前启发式，需与听牌判断配合。 |
| `gold_strategy` | 中高 | 龙岩麻将金牌价值高。 |
| `style_control` | 低到中 | 更偏体验和差异化。 |
| `opponent_tenpai` | 中 | 与防守包协同。 |
| `danger_refined` | 中 | 与防守包协同。 |
| `kong_ev` | 待复测 | 已接入杠流程，需用新大样本重新评估胜率影响。 |
| `youjin_strategy` | 当前中低 | 完整游金状态机实现后会更重要。 |
| `monte_carlo` | 当前中 | 轻量版；完整模拟后潜力高。 |
| `explanation` | 不直接提升 AI 胜率 | 主要用于训练、提示和复盘商品。 |

## 9. 后续实现建议

新增 benchmark 模块：

```text
longyan_mj/benchmark.py
```

建议命令：

```bash
python3 -m longyan_mj.benchmark --games 1000 --mode single
python3 -m longyan_mj.benchmark --games 1000 --mode packs
python3 -m longyan_mj.benchmark --games 1000 --mode ablation
```

当前脚本已支持：

- `--mode single`：单能力增益测试。
- `--mode packs`：能力包测试。
- `--mode ablation`：专家移除测试。
- `--games`：每组局数。
- `--seed-start`：起始 seed。
- `--output-dir`：Markdown/JSON 报告输出目录。

建议先实现：

1. 单能力增益测试。
2. 能力包测试。
3. 专家移除测试。
4. Markdown/JSON 报告输出。
5. 性能耗时统计。
