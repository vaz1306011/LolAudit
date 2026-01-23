# LolAudit

[中文](README.md) | [English](README_EN.md) | [日本語](README_JP.md)

**League of Legends** client helper tool that provides auto match acceptance, auto re-queue, and simple UI operations to reduce repetitive actions in ranked or normal games.

## [Download](https://github.com/vaz1306011/LolAudit/releases/latest)

## Features ✨

- **One-click Queue**: Start queueing from the lobby based on the selected mode.
- **Auto Accept Match**: Automatically accepts a match after the configured delay when a match is found.
- **Auto Re-queue**: Automatically re-queues if the queue exceeds the expected time.
- **Select Ban Champion**: Automatically selects the ban champion based on your previous choice.
- **Auto Lock Champion**: Automatically locks the champion before the timer ends.

## Requirements 📦

- **OS**:
  - Windows 10/11
  - macOS
- **Python**: 3.10+
- **Dependencies**:
  - [PySide6](https://pypi.org/project/PySide6/)

## Screenshots

  <tr>
    <td><img alt="" src="./.readme/in-room.png"></td>
    <td><img alt="" src="./.readme/matching.png"></td>
  <tr>
  <tr>
    <td><img alt="" src="./.readme/champ-select.png"></td>
  <tr>
</table>

## Installation ⚙️

1. Clone the repository:
   ```bash
   git clone https://github.com/vaz1306011/LolAudit.git
   cd LolAudit
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   pipenv install
   ```
3. Run the app:
   ```bash
   python lol_audit.pyw
   ```

## Usage 🖥️

- **One-click Queue**: Click the "One-click Queue" button to start queueing with the selected mode.
- **Stop Queue**: You can stop queueing at any time while matching.
- **Settings**:
  - `Auto Accept`: Automatically accept the match after the configured delay.
  - `Auto Re-queue`: Automatically re-queues if the queue exceeds the expected time.
  - `Select Ban Champion`: Automatically selects the ban champion based on your previous choice.
  - `Auto Lock Champion`: Automatically locks the champion before the timer ends.

## Notes ⚠️

- This program is for academic and personal practice only. Using it may violate Riot Games' Terms of Service. Use at your own risk.
- Do not use in official matches or competitive environments.
