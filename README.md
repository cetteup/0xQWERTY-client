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

- Age of Empires II Definitive Edition
- Apex Legends
- Battlefield 1
- Battlefield 1942
- Battlefield 2
- Battlefield 2042
- Battlefield 2142
- Battlefield 3
- Battlefield 4
- Battlefield Bad Company 2
- Battlefield V
- Battlefield Vietnam
- Destiny 2
- Dota 2
- Call of Duty 4
- Call of Duty Modern Warfare
- Counter-Strike Global Offensive
- Fortnite
- Hyperscape
- Metro Redux
- ParaWorld
- Portal
- Portal 2
- Rainbox Six Siege
- Rocket League
- Star Wars Battlefront 2
- Stronghold Crusader
- Team Fortress 2
- Trackmania
- Valorant

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
