# 小程序模式说明

当前仓库已增加微信小程序本地单机模式，目录为 `miniprogram/`。

## 1. 如何运行

1. 打开微信开发者工具。
2. 选择“导入项目”。
3. 项目目录选择仓库根目录。
4. `project.config.json` 已配置：

```json
{
  "compileType": "miniprogram",
  "miniprogramRoot": "miniprogram/"
}
```

5. 进入后会打开 `pages/game/game`，可以直接开始一局。

## 2. 当前支持

小程序端当前是本地单机 MVP，支持：

- 1 名真人玩家 + 3 个机器人。
- 144 张牌牌墙：136 张基础牌 + 8 张花牌。
- 开金，且金牌不会翻到花牌。
- 摸到花牌自动补花。
- 普通自摸、七对、十三幺、三金倒。
- 起手抢金。
- 单游、双游 MVP。
- 碰牌。
- 暗杠、明杠、补杠、杠后补牌。
- 抢杠胡、杠分即时结算、杠上开花标记。
- 基础机器人出牌、碰牌、杠牌。
- 玩家手牌、花牌、牌墙、金牌、得分和日志展示。

## 3. 当前边界

- 小程序端还不是联网房间模式。
- 小程序端当前使用本地 JS 规则核心，不调用 Python 引擎。
- 机器人是基础策略版，尚未完整迁移 Python 里的全部专家能力。
- 尚未实现三游完整状态机、花杠计分、分饼和完整 action log。
- 当前小程序端适合单机试玩和 UI 验证；正式多端版建议改成“服务端 Python 规则核心 + 小程序客户端渲染”。

## 4. 目录结构

```text
miniprogram/
  app.js
  app.json
  app.wxss
  sitemap.json
  core/
    tiles.js       牌定义、牌墙、展示
    evaluator.js   胡牌、抢金、游金辅助判断
    bot.js         基础机器人策略
    game.js        小程序端牌局状态机
  pages/
    game/
      game.js
      game.json
      game.wxml
      game.wxss
```

## 5. 后续演进建议

小程序 MVP 跑通后，下一步建议补：

- 结构化 action log。
- 服务端 API：`GET /games/{id}`、`POST /games/{id}/actions`。
- 小程序只提交动作和渲染状态，规则校验回到服务端。
- 机器人能力配置由服务端下发，避免客户端可篡改。
