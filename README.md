# Algorithmic Trading Strategy with Heikin Ashi Candlestick Charts and Zerodha API

This project provides a Python code implementation of an algorithmic trading strategy that utilizes Heikin Ashi candlestick charts and integrates with the Zerodha API for automated trading on the Indian stock market.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Usage](#usage)
- [Disclaimer](#disclaimer)
- [Requirements](#requirements)
- [Installation](#installation)
- [License](#license)

## Introduction

Algorithmic trading involves using computer algorithms to automate trading decisions. This project combines Heikin Ashi candlestick charts with the Zerodha API to create an automated trading strategy. Heikin Ashi charts are a type of candlestick chart that smoothens price data, making trends and patterns easier to identify. The Zerodha API allows you to access real-time market data and execute trades programmatically.

## Features

- Automated trading strategy using Heikin Ashi candlestick charts.
- Integration with the Zerodha API for real-time market data and trade execution.
- Dynamic identification of potential buy/sell opportunities based on various conditions.
- Automatic position management, including stop-loss orders and order modifications.
- Continuous execution with a user-defined interval between each trading cycle.

## Usage

1. **Configuration:**
   - Make sure you have an active Zerodha account and obtain your API key.
   - Update the `'access_token.txt'` path and other necessary configurations in the code.

2. **Setting Up Dependencies:**
   - Install the required Python packages by running: `pip install kiteconnect pandas numpy talib`.

3. **Running the Code:**
   - Run the Python script using: `python Heikin_ashi_strategy.py`.
   - The script will execute the trading strategy at regular intervals.
   - Ensure you have the necessary funds and permissions for trading on the Zerodha account.

## Disclaimer

- Trading in financial markets carries a risk of loss. The provided code is for educational and illustrative purposes only. It does not constitute financial advice, and any trading decisions made based on this code are at your own risk.
- Make sure to thoroughly understand the strategy and modify it according to your risk tolerance and financial goals.
- Test the strategy in a simulated environment before using real funds.

## Requirements

- Python 3.x
- Zerodha account and API key
- Required Python packages: kiteconnect, pandas, numpy, talib

## Installation

Follow these steps to set up and run the trading strategy:

1. **Clone the Repository:**

```
git clone https://github.com/neevan0842/Heikin_Ashi_Zerodha.git
```
2. **Install Dependencies:**
```
pip install kiteconnect pandas numpy talib
```

3. **Configuration:**
- Configure your Zerodha API credentials by setting your `api_key` and updating the `'access_token.txt'` path.
- Customize other parameters according to your preferences.

4. **Run the Script:**
- Execute the trading strategy by running the following command:
  ```
  python3 Heikin_Ashi_Zerodha.py
  ```
- The script will run the algorithmic trading strategy at regular intervals, utilizing the Heikin Ashi candlestick charts and Zerodha API for automated trading.

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute the code for personal and commercial purposes. Refer to the [LICENSE](LICENSE.txt) file for more details.

---

