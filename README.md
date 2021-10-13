<div align="center">
  <br />
  <p>
    <a href="https://rira.wtf"><img src="https://i.imgur.com/BVuDXEM.png" width="500" alt="rira" /></a>
  </p>
  <br />
  <p>
    <a href="https://discord.gg/aMgWPApkyS"><img src="https://img.shields.io/discord/738109119671566447?color=5865F2&logo=discord&logoColor=white" alt="Discord server" /></a>
    <a href="https://github.com/apratimshukla6/RiRa/actions"><img src="https://github.com/apratimshukla6/RiRa/actions/workflows/python-app.yml/badge.svg" alt="Python Application Test" /></a>
    <a href="https://rira.wtf"><img src="https://img.shields.io/github/pipenv/locked/python-version/apratimshukla6/RiRa" alt="Python Version" /></a>
    <a href="https://github.com/apratimshukla6/RiRa/blob/main/LICENSE"><img src="https://img.shields.io/github/license/apratimshukla6/RiRa" alt="LICENSE" /></a>
  </p>
</div>

## About 

RiRa is a minimalistic [Discord](https://discord.com) bot that allows you to play music on your server.

- Play Spotify Tracks.
- Play Youtube Tracks.
- Search music with query.
- Control Volume.
- Built-in queue feature.

**Pending**:
- [ ] Adding Spotify playlists
- [ ] Shuffle queue
- [ ] Range based track removal

## Setup

**Python3 is required.**  
Open `terminal` in project directory and execute:
```shell
pip install pipenv
pipenv install
```

Create `config.toml` in the project directory:
```toml
"token"="your_discord_token_here"
"prefix"="!"
"version"="v0.1"

[music]
"max_volume"=250
"vote_skip"=true
"client"="your_spotify_client_id_here"
"secret"="your_spotify_secret_here"
```

### Other Requirements

- [ffmpeg](https://www.ffmpeg.org/download.html) (`Ensure added to PATH`)
- [opus](https://opus-codec.org/downloads/) (`Ensure added to PATH`)

## Starting up

Open `terminal` in project directory and execute the following:
```shell
pipenv shell
python -m rira
```

The logs will be saved in `rira.log`

## RiRa Commands

<table>
  <tr>
    <th>Command</th>
    <th>Alias</th>
    <th>Task</th>
    <th>Example</th>
  </tr>
  <tr>
    <td>!play</td>
    <td>!p</td>
    <td>To play music</td>
    <td>!p songname or youtube link or spotify url</td>
  </tr>
  <tr>
    <td>!nowplaying</td>
    <td>!np, !current</td>
    <td>Shows currently playing music</td>
    <td>!np</td>
  </tr>
  <tr>
    <td>!queue</td>
    <td>!q, !view</td>
    <td>View the queue</td>
    <td>!q</td>
  </tr>
  <tr>
    <td>!remove</td>
    <td>!r, !del</td>
    <td>Removes music from the queue</td>
    <td>!r 1</td>
  </tr>
  <tr>
    <td>!clear</td>
    <td>!c, !cq</td>
    <td>Clears the queue</td>
    <td>!c</td>
  </tr>
  <tr>
    <td>!pause</td>
    <td>!ps</td>
    <td>Pauses the music</td>
    <td>!ps</td>
  </tr>
  <tr>
    <td>!resume</td>
    <td>!rs</td>
    <td>Resumes the music</td>
    <td>!rs</td>
  </tr>
  <tr>
    <td>!skip</td>
    <td>!fs</td>
    <td>Skips the music</td>
    <td>!fs</td>
  </tr>
  <tr>
    <td>!disconnect</td>
    <td>!dc, !leave</td>
    <td>To make RiRa leave the voice channel</td>
    <td>!dc</td>
  </tr>
  <tr>
    <td>!volume</td>
    <td>!v, !vol</td>
    <td>To change the volume</td>
    <td>!v 250</td>
  </tr>
  <tr>
    <td>!ping</td>
    <td>!pi</td>
    <td>Returns the latency</td>
    <td>!pi</td>
  </tr>
  <tr>
    <td>!credits</td>
    <td>!cr</td>
    <td>Returns the credits</td>
    <td>!cr</td>
  </tr>
</table>

## Links

- [Website](https://rira.wtf)

## Contributing

Before creating an issue, please ensure that it hasn't already been reported/suggested.

The issue tracker is only for bug reports and enhancement suggestions. If you have a question, please ask it in the [Discord server](https://discord.gg/aMgWPApkyS) instead of opening an issue – you will get redirected there anyway.

If you wish to contribute to the RiRa codebase or documentation, feel free to fork the repository and submit a pull request.

## Help

If you don't understand something in the documentation, you are experiencing problems, or you just need a gentle
nudge in the right direction, please don't hesitate to join our [Discord Server] (https://discord.gg/aMgWPApkyS).
