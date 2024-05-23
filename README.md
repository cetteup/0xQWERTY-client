# 0xQWERTY-client

[![License](https://img.shields.io/github/license/cetteup/0xQWERTY-client)](/LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/cetteup/0xQWERTY-client)](https://github.com/cetteup/joinme.click-launcher/commits/main)
[![CodeFactor report](https://img.shields.io/codefactor/grade/github/cetteup/0xQWERTY-client)](https://www.codefactor.io/repository/github/cetteup/0xqwerty-client)
[![Discord](https://img.shields.io/discord/1032672744183181382?label=Discord)](https://discord.gg/dN6N4PRZHc)

Automatically press keys in-game when Twitch viewers redeem channel point rewards

## Features

- define keys to press per reward and game in a simple YAML config
- automatically sets up channel point rewards on Twitch
- only triggers keypress if relevant game for reward is open in the foreground
- automatically mark redemptions as fulfilled if key was pressed (optional)
- automatically refund all redemptions, e.g. for testing (optional)

## Supported games

Adding support for additional games is quite simple. If your favorite game is missing, reach out [on Discord](https://discord.gg/dN6N4PRZHc).

| Game                                         | Minimum client version¹ |
|----------------------------------------------|-------------------------|
| 7 Days To Die                                | v1.0.5                  |
| Age of Empires II Definitive Edition         | v1.0.0                  |
| Apex Legends                                 | v1.0.0                  |
| Battlefield 1                                | v1.0.0                  |
| Battlefield 1942                             | v1.0.0                  |
| Battlefield 2                                | v1.0.0                  |
| Battlefield 2042                             | v1.0.0                  |
| Battlefield 2142                             | v1.0.0                  |
| Battlefield 3                                | v1.0.0                  |
| Battlefield 4                                | v1.0.0                  |
| Battlefield Bad Company 2                    | v1.0.0                  |
| Battlefield Hardline                         | v1.3.0                  |
| Battlefield V                                | v1.0.0                  |
| Battlefield Vietnam                          | v1.0.0                  |
| Call of Duty                                 | v1.0.5                  |
| Call of Duty  2                              | v1.0.5                  |
| Call of Duty 4                               | v1.0.0                  |
| Call of Duty Modern Warfare                  | v1.0.0                  |
| Call of Duty Modern Warfare II               | v1.0.5                  |
| Call of Duty United Offensive                | v1.0.5                  |
| Call of Duty World at War                    | v1.0.5                  |
| Counter-Strike                               | v1.0.5                  |
| Counter-Strike 2                             | v1.3.0                  |
| Counter-Strike Condition Zero                | v1.0.5                  |
| Counter-Strike Global Offensive              | v1.0.0                  |
| Counter-Strike Source                        | v1.0.5                  |
| Day of Defeat                                | v1.0.5                  |
| Day of Defeat Source                         | v1.0.5                  |
| DCS World                                    | v1.0.5                  |
| Destiny 2                                    | v1.0.0                  |
| Dota 2                                       | v1.0.0                  |
| Escape from Tarkov                           | v1.2.0                  |
| Fortnite                                     | v1.0.0                  |
| Half-Life                                    | v1.0.5                  |
| Half-Life 2 (incl. Episode One, Episode Two) | v1.0.5                  |
| Half-Life 2 Deathmatch                       | v1.0.5                  |
| Half-Life 2 Lost Coast                       | v1.0.5                  |
| Half-Life Source                             | v1.0.5                  |
| Heroes of the Storm                          | v1.0.5                  |
| Hyperscape                                   | v1.0.0                  |
| League of Legends                            | v1.0.5                  |
| Left 4 Dead                                  | v1.0.5                  |
| Left 4 Dead 2                                | v1.0.5                  |
| Metro Redux                                  | v1.0.0                  |
| Overwatch (incl. Overwatch 2)                | v1.0.5                  |
| ParaWorld                                    | v1.0.0                  |
| Path of Exile                                | v1.2.0                  |
| Portal                                       | v1.0.0                  |
| Portal 2                                     | v1.0.0                  |
| PUBG: BATTLEGROUNDS                          | v1.1.0                  |
| Quake II/Quake II RTX                        | v1.0.7                  |
| Rainbox Six Siege                            | v1.0.0                  |
| Rocket League                                | v1.0.0                  |
| StarCraft II                                 | v1.0.5                  |
| Star Wars Battlefront 2                      | v1.0.0                  |
| Star Wars: Squadrons                         | v1.0.7                  |
| Stronghold Crusader                          | v1.0.0                  |
| Team Fortress                                | v1.0.5                  |
| Team Fortress 2                              | v1.0.0                  |
| The Sims 3                                   | v1.0.5                  |
| The Sims 4                                   | v1.0.5                  |
| Trackmania                                   | v1.0.0                  |
| Unreal                                       | v1.0.7                  |
| Unreal II: The Awakening                     | v1.0.7                  |
| Unreal Tournament                            | v1.0.7                  |
| Unreal Tournament 2003                       | v1.0.7                  |
| Unreal Tournament 2004                       | v1.0.7                  |
| Unreal Tournament 3                          | v1.0.7                  |
| Valorant                                     | v1.0.0                  |
| Warhammer Vermintide 2                       | v1.0.5                  |
| War Thunder                                  | v1.0.5                  |
| World of Tanks                               | v1.0.5                  |
| World of Warcraft                            | v1.2.0                  |

¹ refers to the minimum launcher version supporting all features relevant to the game

## Example config

```yaml
logLevel: info
autoFulfill: true
refund: false
rewards:
  - id: '80d76c25-6dd4-412c-91f7-329121ae54d3' # An existing reward created by 0xQWERTY
    title: Get out of the vehicle!
    cost: 1000
    actions:
      Battlefield 2:
        type: keypress
        value: e
      Call of Duty Modern Warfare:
        type: keypress
        value: f
  - title: Reload my gun!   # Rewards without an id will be created
    cost: 500
    actions:
      Counter-Strike Global Offensive:
        type: keypress
        value: r
      Valorant:
        type: keypress
        value: r
  - title: Jump!
    cost: 200
    actions:
      Rocket League:
        type: keypress
        value: space
```

## Downloads

* https://github.com/cetteup/0xQWERTY-client/releases/latest

License
-------

This is free software under the terms of the MIT license.
