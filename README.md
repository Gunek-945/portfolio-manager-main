This project is a comprehensive tool for analyzing cryptocurrency portfolios, generating custom ratings, and providing insights based on various data sources and metrics, including security scores.

## Features

- Fetch and process blockchain data from CoinStats API
- Retrieve and update token ratings from TokenInsight
- Incorporate security scores from Certik
- Perform backtesting using a Buy and Hold strategy
- Generate custom rating scores based on various metrics including performance, team, token economics, roadmap progress, and security
- Create visualizations including pie charts and radar charts for portfolio analysis
- Produce detailed Excel reports of portfolio performance and ratings
- Interactive user interface for portfolio management and updates

## Directory Structure


PORTFOLIO_MANAGER/
├── coin_rating_model/          # Module for coin rating and analysis
│   ├── data/                   # Data storage for coin rating model
│   │   ├── backtest_results.csv    # Results from backtesting
│   │   ├── coin_stats.csv          # Statistical data about coins
│   │   └── data/                   # Additional data files
│   ├── coinstatcoins.py        # Script for coin statistics
│   ├── HODL.py                 # Implementation of HODL strategy
│   ├── merge.py                # Data merging utilities
│   ├── model.py                # Main rating model implementation
│   └── token_ratings.csv       # CSV file with token ratings
├── coinstat/                   # Module for coin statistics
│   ├── __pycache__/            # Python cache files
│   ├── __init__.py             # Module initialization
│   ├── blockchains.csv         # List of supported blockchains
│   ├── get_data.py             # Script to fetch coin data
│   └── helpers.py              # Helper functions for coinstat module
├── security/                   # Module for security analysis
│   ├── __init__.py             # Module initialization
│   ├── certik.py               # Integration with Certik security scores
│   ├── merge.py                # Merging security data
│   └── security_scores.csv     # CSV file with security scores
├── tokeninsight/               # Module for token insights
│   ├── __pycache__/            # Python cache files
│   ├── __init__.py             # Module initialization
│   ├── coin_rating_raw.csv     # Raw coin rating data from TokenInsight
│   ├── coin_rating_updated.csv # Updated ratings after removing 2 feature columns
│   ├── combine_with_new_token_rating.py  # Script to update ratings
│   ├── updated_coin_rating_with_security.csv  # Ratings merged with security scores
│   ├── final_coin_rating.csv   # Final ratings after coin_rating_model updates
│   ├── get_data.py             # Script to fetch raw TokenInsight data
│   ├── helpers.py              # Helper functions for tokeninsight module
# CSV Workflow: 
# 1. coin_rating_raw.csv (from get_data.py)
# 2. coin_rating_updated.csv (from combine_with_new_token_rating.py)
# 3. updated_coin_rating_with_security.csv (after merge.py in security/)
# 4. final_coin_rating.csv (after updates in coin_rating_model/)
└── user/                       # User-related files and outputs
    ├── diagram/                # Generated diagrams and charts
    ├── json/                   # User data in JSON format
    ├── report/                 # Generated user reports
    ├── LICENSE                 # Project license file
    ├── main.py                 # Main script to run the portfolio manager
    ├── README.md               # Project documentation and instructions

## Installation

Clone the repository:

```bash
git clone https://github.com/iMarioChow/portfolio_manager.git
```

Navigate to the project directory:

```bash
cd portfolio_manager
```

Install required packages:

```bash
pip install requests pandas matplotlib openpyxl xlsxwriter numpy
```

## Usage

Run the main script:

```bash
python main.py
```

1. Enter your name when prompted. 
2. If you are a returning user, you will be asked if you want to update your portfolio.
3. If updating, the script will fetch updated token holdings from the blockchain networks.
4. You'll be asked if you want to add new tokens to your portfolio. If yes, provide the token addresses.
5. The script will display your total portfolio value and token holdings.
6. A rating report will be generated and displayed using Token Insight data.
7. Pie charts and hexagon diagrams will be generated to visualize your portfolio holdings.

## Workflow

1. **Data Preparation**:
   - Run `get_data.py` in the `coin_rating_model` folder to generate `blockchains.csv`. This file contains manually input data about EVM compatibility for each chain.
   - Run `get_data.py` in the `token_insight` folder to generate `coin_rating.csv`. This file contains token ratings from Token Insight.

2. **Portfolio Management**:
   - Run `main.py` to start the portfolio manager.
   - For new users:
     - Input your name and wallet addresses.
     - The script will check holdings across all chains listed in `blockchains.csv`.
     - Holdings are saved in `user/json/[user_name].json`.
   - For returning users:
     - Choose to update existing portfolio or add new tokens.
     - Updating will refresh balances for existing addresses.
     - Adding new tokens requires inputting new addresses.

3. **Report Generation**:
   - After portfolio update or creation, an Excel report is generated in `user/report/`.
   - The report includes holdings and a portfolio score.

4. **Visualization**:
   - Pie charts and hexagon diagrams are generated in `user/diagram/` to visualize the portfolio.

## Data Files

- `blockchains.csv`: Contains blockchain networks and their connection IDs.
- `coin_rating.csv`: Contains Token Insight ratings for various tokens.
- `[user_name].json`: Stores the user's token holdings and other relevant data.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
