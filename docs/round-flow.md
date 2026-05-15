# 龙岩麻将一局流程图

本文档描述当前自动龙岩麻将 MVP 中一局牌的核心流程，对应 `longyan_mj.game.MahjongGame.play()` 的实现。

## 1. 流程图

```mermaid
flowchart TD
    A[开始一局] --> B[构建牌墙并洗牌]
    B --> C[开金: 翻出金牌]
    C --> D[发牌: 庄家14张, 其余13张]
    D --> E[开局特殊胡检查]

    E --> E1{有人三金倒?}
    E1 -- 是 --> W[结算胡牌, 本局结束]
    E1 -- 否 --> E2{有人抢金?}
    E2 -- 是 --> W
    E2 -- 否 --> F[进入回合循环]

    F --> G{当前玩家是否需要摸牌?}
    G -- 庄家第一手/碰后 --> H[不摸牌]
    G -- 正常回合 --> I[摸一张牌]

    H --> J{玩家是否处于游金状态?}
    I --> J

    J -- 单游摸到金 --> J1[打金升级双游]
    J1 --> N[轮到下家]
    J -- 单游/双游可胡 --> W
    J -- 否 --> K{是否自摸胡?}

    K -- 是 --> K1{是否选择进入单游?}
    K1 -- 是 --> K2[打出自然将牌, 进入单游]
    K2 --> N
    K1 -- 否 --> W
    K -- 否 --> L{是否暗杠/补杠?}

    L -- 是 --> L1[执行杠牌]
    L1 --> L2[杠后补牌]
    L2 --> J
    L -- 否 --> M[当前玩家出牌]

    M --> O{其他玩家是否明杠?}
    O -- 是 --> O1[执行明杠]
    O1 --> O2[杠后补牌]
    O2 --> J

    O -- 否 --> P{其他玩家是否碰?}
    P -- 是 --> P1[执行碰牌]
    P1 --> P2[碰牌玩家直接出牌]
    P2 --> M

    P -- 否 --> N[轮到下家]
    N --> Q{牌墙是否为空?}
    Q -- 否 --> F
    Q -- 是 --> R[流局, 本局结束]
```

## 2. 时序图

```mermaid
sequenceDiagram
    participant System as 系统
    participant Wall as 牌墙
    participant P0 as 玩家0/庄家
    participant P1 as 玩家1
    participant P2 as 玩家2
    participant P3 as 玩家3
    participant Bot as 机器人策略
    participant Score as 计分模块

    System->>Wall: 构建144张牌并洗牌
    System->>Wall: 翻出金牌
    System->>P0: 发14张
    System->>P1: 发13张
    System->>P2: 发13张
    System->>P3: 发13张

    System->>System: 检查三金倒
    alt 有人三金倒
        System->>Score: 结算三金倒
        Score-->>System: 返回分数
    else 无三金倒
        System->>System: 检查抢金
        alt 有人抢金
            System->>Score: 结算抢金
            Score-->>System: 返回分数
        else 无开局特殊胡
            loop 直到胡牌或流局
                System->>P0: 当前玩家回合

                alt 需要摸牌
                    System->>Wall: 摸牌
                    Wall-->>P0: 返回摸到的牌
                    opt 摸到花牌
                        P0-->>System: 记录花牌
                        System->>Wall: 自动补花
                    end
                else 庄家第一手/碰后出牌
                    System->>P0: 不摸牌, 直接操作
                end

                System->>System: 判断游金状态
                alt 单游/双游胡牌
                    System->>Score: 结算单游/双游
                    Score-->>System: 返回分数
                else 普通自摸检查
                    System->>System: evaluate_win
                    alt 可胡
                        System->>P0: 询问是否胡/是否游金
                        alt 选择胡牌
                            System->>Score: 结算胡牌
                            Score-->>System: 返回分数
                        else 选择游金
                            P0-->>System: 打出自然将牌
                            System->>System: 进入单游状态
                        end
                    else 不胡
                        System->>P0: 检查暗杠/补杠
                        alt 选择杠
                            P0-->>System: 暗杠或补杠
                            System->>Wall: 杠后补牌
                            Wall-->>P0: 返回补牌
                        else 不杠
                            System->>Bot: 请求出牌决策
                            Bot-->>System: 返回出牌
                            P0-->>System: 打出牌

                            System->>P1: 询问是否明杠
                            System->>P2: 询问是否明杠
                            System->>P3: 询问是否明杠
                            alt 有人明杠
                                P1-->>System: 明杠
                                System->>Wall: 杠后补牌
                                Wall-->>P1: 返回补牌
                            else 无人明杠
                                System->>P1: 询问是否碰
                                System->>P2: 询问是否碰
                                System->>P3: 询问是否碰
                                alt 有人碰
                                    P1-->>System: 碰牌
                                    System->>P1: 碰牌后直接出牌
                                else 无人碰
                                    System->>System: 轮到下家
                                end
                            end
                        end
                    end
                end
            end
        end
    end
```

## 3. 当前边界

- 当前流程支持三金倒、抢金、普通自摸、七对、十三幺、单游、双游。
- 当前流程支持碰牌、暗杠、明杠、补杠和杠后补牌。
- 当前已支持 8 张花牌入牌墙、摸花记录和自动补花。
- 当前尚未实现抢杠胡、三游完整状态机、花杠计分、分饼和完整牌局 action log。
