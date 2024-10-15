import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import re
from coinstat.helpers import get_token_amount, update_holdings, save_user_data, load_user_data, handle_address, add_tokens, group_holdings, save_report_csv, plot_holdings
from tokeninsight.helpers import load_coin_ratings, calculate_final_scores, display_final_scores, show_ratings

# Initialize the Ollama LLM
llm = Ollama(model="llama3.1")

def plot_radar_chart(overall_scores: Dict[str, float], username: str, diagram_dir: str) -> str:
    """
    Create an improved radar chart of the user's overall portfolio rating.
    """
    categories = [
        'Token Performance',
        'Team Partners & Investors',
        'Token Economics',
        'Roadmap Progress',
        'Security Score'
    ]
    
    values = [
        overall_scores.get('token_performance', 0),
        overall_scores.get('team_partners_investors', 0),
        overall_scores.get('token_economics', 0),
        overall_scores.get('roadmap_progress', 0),
        overall_scores.get('security', 0)
    ]

    # Number of variables
    num_vars = len(categories)

    # Compute angle for each category
    angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
    angles += angles[:1]  # Repeat the first angle to close the polygon

    # Extend the values to close the polygon
    values += values[:1]

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 8))
    ax = plt.subplot(111, polar=True)

    # Draw the shape
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)

    # Set the labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    # Set y-axis limits and labels
    ax.set_ylim(0, 1)
    ax.set_yticks(np.arange(0.2, 1.2, 0.2))
    ax.set_yticklabels([f'{x:.1f}' for x in np.arange(0.2, 1.2, 0.2)])

    # Add gridlines
    ax.set_rgrids(np.arange(0.2, 1.2, 0.2), angle=0, fontsize=8)

    # Add value annotations
    for angle, value, category in zip(angles[:-1], values[:-1], categories):
        ax.text(angle, value, f'{value:.2f}', ha='center', va='center')

    # Remove radial lines
    ax.set_rlabel_position(0)
    ax.spines['polar'].set_visible(False)
    ax.grid(True)

    # Add title
    plt.title(f'{username} Overall Portfolio Rating', size=20, y=1.1)

    # Adjust layout and save
    plt.tight_layout()
    radar_chart_filename = os.path.join(diagram_dir, f'{username}_portfolio_radar_chart.png')
    plt.savefig(radar_chart_filename, dpi=300, bbox_inches='tight')
    plt.close()

    return radar_chart_filename

# Add the save_final_report function
def save_final_report(overall_scores: Dict[str, float], holdings_df: pd.DataFrame, final_scores: List[Dict], file_path: str) -> None:
    """
    Save the final report as an Excel file.
    """
    metrics_df = pd.DataFrame({
        'Metric': [
            'Token Performance',
            'Team Partners & Investors',
            'Token Economics',
            'Roadmap Progress',
            'Security Score'
        ],
        'Score': [
            overall_scores.get('token_performance', 0),
            overall_scores.get('team_partners_investors', 0),
            overall_scores.get('token_economics', 0),
            overall_scores.get('roadmap_progress', 0),
            overall_scores.get('security', 0)
        ]
    })

    overall_score = metrics_df['Score'].mean()

    # Add 'Counted in Rating' column
    rated_symbols = set(score['symbol'] for score in final_scores)
    holdings_df['Counted in Rating'] = holdings_df['symbol'].isin(rated_symbols)

    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        holdings_df.to_excel(writer, sheet_name='Holdings', index=False)

        workbook = writer.book
        metrics_sheet = writer.sheets['Metrics']
        holdings_sheet = writer.sheets['Holdings']

        # Add overall score
        metrics_sheet.write('D1', 'Overall Score')
        metrics_sheet.write('D2', overall_score)

        # Insert the images into the Excel file with proper sizing and positions
        if 'plot_file' in overall_scores and os.path.exists(overall_scores['plot_file']):
            metrics_sheet.insert_image('A7', overall_scores['plot_file'], {'x_scale': 0.5, 'y_scale': 0.5})
        if 'radar_plot_file' in overall_scores and os.path.exists(overall_scores['radar_plot_file']):
            metrics_sheet.insert_image('F7', overall_scores['radar_plot_file'], {'x_scale': 0.5, 'y_scale': 0.5})

        # Auto-fit columns
        for sheet in [metrics_sheet, holdings_sheet]:
            for i, col in enumerate(sheet.get_worksheet().table):
                max_length = max(len(str(cell.value)) for cell in col)
                sheet.set_column(i, i, max_length + 2)

    print(f"Report saved to {file_path}")

# Helper functions from AI.py
def extract_score(data_string):
    match = re.search(r': ([\d.]+%|Missing Data \(High Risk\))', data_string)
    return match.group(1) if match else "N/A"

def prepare_asset_data(holdings, rating_scores, underlying_technology_security, token_performance, ecosystem_development, team_partners_investors, token_economics, roadmap_progress):
    asset_data = {}
    for holding in holdings:
        asset_data[holding] = {
            'Rating Score': extract_score(next((s for s in rating_scores if s.startswith(holding)), '')),
            'Underlying Technology Security': extract_score(next((s for s in underlying_technology_security if s.startswith(holding)), '')),
            'Token Performance': extract_score(next((s for s in token_performance if s.startswith(holding)), '')),
            'Ecosystem Development': extract_score(next((s for s in ecosystem_development if s.startswith(holding)), '')),
            'Team, Partners & Investors': extract_score(next((s for s in team_partners_investors if s.startswith(holding)), '')),
            'Token Economics': extract_score(next((s for s in token_economics if s.startswith(holding)), '')),
            'Roadmap Progress': extract_score(next((s for s in roadmap_progress if s.startswith(holding)), ''))
        }
    return asset_data

def plot_pie_chart(data: List[Dict], username: str, diagram_dir: str) -> str:
    """
    Create a pie chart of the user's portfolio distribution.

    Input:
        data (List[Dict]): List of dictionaries containing token data
        username (str): Name of the user
        diagram_dir (str): Directory to save the chart

    Output:
        str: Filename of the saved pie chart
    """
    df = pd.DataFrame(data)
    df = df[df['balanceUSD'] > 0]  # Filter out zero balances
    plt.figure(figsize=(10, 8))
    wedges, texts, autotexts = plt.pie(df['balanceUSD'], labels=df['symbol'], autopct='%1.1f%%', startangle=140)
    plt.title(f'{username} Portfolio Distribution')
    plt.setp(autotexts, size=8, weight="bold")
    plt.tight_layout()
    pie_chart_filename = os.path.join(diagram_dir, f'{username}_portfolio_pie_chart.png')
    plt.savefig(pie_chart_filename, dpi=300, bbox_inches='tight')
    plt.close()
    return pie_chart_filename

# Questionnaire and options
questionnaire = [
    "1. What is your age group?",
    "2. How would you describe your cryptocurrency investment knowledge?",
    "3. How long is your investment horizon for cryptocurrencies?",
    "4. How would you react if your cryptocurrency portfolio lost 20% of its value in a month?",
    "5. What is your primary investment goal with cryptocurrencies?",
    "6. How much of your total investment portfolio are you comfortable allocating to cryptocurrencies?",
    "7. When considering a cryptocurrency investment, what is more important to you?",
    "8. How would you describe your reaction to cryptocurrency market volatility?",
    "9. Have you previously invested in cryptocurrencies?",
    "10. How would you rate your current financial stability?",
    "11. What is your annual income range?",
    "12. How would you respond to a high-risk, high-return cryptocurrency investment opportunity?",
    "13. How do you feel about using leverage (borrowing money) to increase potential returns in cryptocurrency investments?",
    "14. How much time do you spend monitoring your cryptocurrency investments?",
    "15. How would you feel if a cryptocurrency investment underperformed for an extended period?",
    "16. What is your experience with diversifying your cryptocurrency investments?",
    "17. How would you prioritize your financial goals with cryptocurrencies?",
    "18. What proportion of your investments do you hold in high-risk cryptocurrencies?",
    "19. How would you describe your approach to new cryptocurrency trends (e.g., DeFi, NFTs)?",
    "20. How do you handle financial losses outside of cryptocurrency investments?"
]

options = [
    ["A. Under 30", "B. 30-40", "C. 41-50", "D. Over 50"],
    ["A. Extensive (I understand the market and regularly invest)", "B. Moderate (I have some knowledge and occasionally invest)", "C. Basic (I know some fundamental concepts)", "D. Limited (I know very little about cryptocurrencies)"],
    ["A. More than 15 years", "B. 10-15 years", "C. 5-10 years", "D. Less than 5 years"],
    ["A. I would buy more assets as they are cheaper now", "B. I would hold and wait for the market to recover", "C. I would be concerned but would not make any changes", "D. I would sell my assets to avoid further losses"],
    ["A. High growth and returns", "B. Growth with some income", "C. Balanced growth and preservation", "D. Capital preservation and safety"],
    ["A. More than 75%", "B. 50-75%", "C. 25-50%", "D. Less than 25%"],
    ["A. Potential returns", "B. Balance between returns and safety", "C. Stability with some returns", "D. Safety and security of my capital"],
    ["A. Excited by potential opportunities", "B. Cautious but not overly worried", "C. Concerned but managing", "D. Very concerned and uncomfortable"],
    ["A. Yes, frequently", "B. Yes, several times", "C. Yes, once or twice", "D. No, never"],
    ["A. Very stable, with a high disposable income", "B. Stable, with some disposable income", "C. Moderately stable, with limited disposable income", "D. Unstable, with very limited disposable income"],
    ["A. Over $200,000", "B. $100,000 - $200,000", "C. $50,000 - $100,000", "D. Below $50,000"],
    ["A. I would invest a significant amount", "B. I would invest a moderate amount", "C. I would invest a small amount", "D. I would avoid it"],
    ["A. Comfortable and willing", "B. Open to considering it", "C. Hesitant but might consider it", "D. Uncomfortable and unwilling"],
    ["A. Daily", "B. Weekly", "C. Monthly", "D. Rarely"],
    ["A. Unfazed and willing to stay invested", "B. Concerned but willing to wait for recovery", "C. Anxious and considering changes", "D. Ready to sell and avoid further loss"],
    ["A. Extensive, I manage a diversified portfolio", "B. Moderate, I have some diversification", "C. Basic, I understand the concept", "D. Limited, I do not diversify much"],
    ["A. Growing wealth aggressively", "B. Growing wealth moderately", "C. Balancing growth and income", "D. Preserving wealth and ensuring stability"],
    ["A. Over 75%", "B. 50-75%", "C. 25-50%", "D. Less than 25%"],
    ["A. Very proactive and willing to invest", "B. Open but cautious", "C. Skeptical but curious", "D. Uninterested and avoidant"],
    ["A. I view them as opportunities for future gains", "B. I accept them and move on", "C. I find them stressful but manageable", "D. I find them very distressing"]
]

# Function to present a question and get a valid answer
def ask_question(question, options):
    print(question)
    for option in options:
        print(option)
    while True:
        answer = input("Your answer (A/B/C/D): ").upper()
        if answer in ['A', 'B', 'C', 'D']:
            return answer
        else:
            print("Invalid input. Please enter A, B, C, or D.")

def conduct_risk_assessment():
    answers = []
    for i, question in enumerate(questionnaire):
        answer = ask_question(question, options[i])
        answers.append(answer)
    return answers

# Function to analyze risk tolerance
def analyze_risk_tolerance(answers):
    score = sum([4 - ord(answer) + ord('A') for answer in answers])
    if score > 60:
        risk_level = "High"
    elif score > 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    return risk_level, score

def check_risk_alignment(personal_risk, portfolio_risk):
    risk_levels = {"low": 1, "medium": 2, "high": 3}
    
    personal_risk_value = risk_levels.get(personal_risk.lower())
    portfolio_risk_value = risk_levels.get(portfolio_risk.lower())
    
    if personal_risk_value is None or portfolio_risk_value is None:
        return "Invalid risk level provided", None

    if personal_risk_value == portfolio_risk_value:
        return "Yes", None
    elif personal_risk_value > portfolio_risk_value:
        return "No", "Increase risk"
    else:
        return "No", "Decrease risk"

def parse_holdings_input(input_string):
    return [token.strip() for token in input_string.strip('[]').split(',')]

def parse_percentages_input(input_string):
    percentages = re.findall(r'(\w+):\s*([\d.]+)%', input_string)
    return [f"{token}: {percentage}%" for token, percentage in percentages]

# Templates and prompts
greeting_template = """
You are a Robotic Cryptocurrency Portfolio Manager and Robotic Advisor specializing in managing digital asset portfolios. Your role is to provide expert investment guidance focused exclusively on cryptocurrency assets, tailored to clients' risk tolerance levels. Your advice should exclude other financial products such as DeFi products or bonds.
As a professional in the cryptocurrency investment field, you possess in-depth knowledge of blockchain technology, cryptocurrency markets, and the technical and financial characteristics of various tokens. Your expertise enables you to provide clear, professional, and concise explanations tailored to each client's risk profile.
Your job is to recommend a reallocation suggestion to clients after receiving and analyze the information of clients. The recommendation output is done in the last prompt as final output.

You only need to greet your client in this prompt without any request questions to clients.

Your role: Financial AI Bot
Output/My role: Your client

Client's name: {client_name}

Your response:
"""

client_profile_template = """
Analyze the following client risk profile:
Personal risk: {personal_risk} {risk_score}
Portfolio risk: {port_risk}
Alignment: {alignment}
Suggested Adjustment on portfolio risk: {adjustment}
Percentage of portfolio analyzed: {included_percentage}
Tokens not analyzed: {missing_tokens}

Based on the above information, provide a concise output using ONLY the following format:

Client Risk Tolerance: [personal_risk level] ([score])
Current Portfolio Risk: [port_risk]
Alignment: [Yes/No]
Adjustment on portfolio: [Increase/Decrease Risk/None]
Portfolio Analysis Coverage: [included_percentage]%
Unanalyzed Tokens: [list of missing_tokens]

IMPORTANT: 
- Do not include any additional explanations or text.
- The Client Risk Tolerance should include both the risk level and the score in parentheses.
- The Adjustment should only state whether to Increase, Decrease, or make No change to the portfolio risk.
- Ensure each line contains only the requested information.
- Portfolio Analysis Coverage should be a percentage.
- Unanalyzed Tokens should list the tokens not included in the risk analysis.
"""

categorize_assets_template = """
Categorize the following assets by risk using the provided rating scores:

Holdings and Scores:
{holdings_and_scores}


Output format:
[Asset]: [Risk Category] (Score: [score])

IMPORTANT INSTRUCTIONS:
- Provide ONLY the categorization for each asset in the list.
- Use EXACTLY the output format specified above for each asset.
- Do NOT include any additional explanations, introductions, or conclusions.
- For assets with "Missing Data", categorize as High Risk and state "(Insufficient Data)" instead of the score.
- Ensure each asset is on a new line.
- Do not add any extra spaces or punctuation.
- The risk categories and scores are already provided, so do not recalculate them.


Your response should contain ONLY the asset categorizations in the specified format, sorted alphabetically by asset symbol.
"""

analyze_allocation_template = """
Analyze the following asset allocation:

Holdings, Scores, and Percentages:
{holding_percentage_and_risk}


IMPORTANT INSTRUCTIONS:
- List each asset using the following exact format:
  [symbol]: percentage% (Risk Category).
- Ensure each asset is on a new line.
- Do not add any additional explanations or conclusions.
- Sort the output by percentage in descending order.
- Do not modify any values; use the percentages and risk categories as provided.
- Do not change any data inside the input 


Your response should contain ONLY the asset allocations in the specified format.
"""

strategic_diversification_template = """
Analyze the portfolio and suggest an overall reallocation strategy based on the following information:

Current Portfolio Composition:
{current_portfolio_composition}


Overall Portfolio Risk: {overall_portfolio_risk}
Target Risk Profile: {target_risk}
Target adjustment: {adjustment}
Asset allocation on 3 risk categories: {risk_formatted_portfolio_allocations}

TASK:
Provide a broad reallocation strategy to align the portfolio with the target risk profile. Focus on general directions for high-risk, medium-risk, and low-risk assets without mentioning specific tokens.

Consider the following in your analysis:
1. The current distribution of high-risk, medium-risk, and low-risk assets
2. The overall portfolio risk compared to the target risk profile
3. General diversification principles

Output Format:
1. Risk Alignment Assessment:
   [Brief assessment of how the current portfolio risk aligns with the target risk profile]

2. Suggested Reallocation Direction:
   High-Risk Assets: [Increase/Decrease/Maintain]
   Medium-Risk Assets: [Increase/Decrease/Maintain]
   Low-Risk Assets: [Increase/Decrease/Maintain]

3. Rationale:
   [Provide a brief explanation for the suggested changes, focusing on how they will help align the portfolio with the target risk profile]

4. Additional Considerations:
   [Mention any other important factors to consider in the reallocation process, such as maintaining a certain level of diversification]

IMPORTANT:
- Do not mention or suggest specific tokens or assets.
- Focus on broad categories of risk (high, medium, low) and their overall allocation in the portfolio.
- Ensure the suggestions aim to bring the overall portfolio risk closer to the target risk profile.
- Consider the current risk distribution when making suggestions.
"""

outlier_analysis_template = """
Analyze the following outliers in the portfolio holdings:

{outliers}

Overall Rating Score for each token (in list format): {holdings_and_score}

For each outlier token, provide an analysis using this format:

Token Name: [Token Symbol]
Overall Rating Score: [Overall Rating Score]
Outlier Metric(s):
- [Metric Name]: [Score]

Example:
**USDT: Overall Rating Score: 70.88**

Outlier Metric(s):
- token_economics: 49.33%

Analysis:.....

Analysis:
- Explain why this metric is considered an outlier (i.e., how it's significantly lower than the overall rating score).
- Discuss the potential risks this outlier represents for the token in the metric aspect
- Analyze how this outlier might negatively impact the overall performance and risk profile of the token.

Potential Impact on Portfolio:
- Describe how this outlier might increase risk or potentially decrease performance in the overall portfolio.
- Suggest any specific risk mitigation strategies or actions related to this token based on the outlier analysis.

IMPORTANT:
- Please do not evaluate the overall rating score again, i.e do not give any risk level (low, medium or high)to the score /
    The overall rating score is used to compared with the outliers score for the user interface
- Provided outlier and its metrics must be lower than the overall rating score.
- Clearly state the potential risks associated with each outlier.
- Be concise but insightful in your analysis, emphasizing the negative implications of the outlier.
- Do not discuss any potential advantages or positive aspects of the outliers.
- Do not add any metrics or scores that are not provided in the input.
- Remember that all outliers in this context represent potential risks, not advantages.

Provide your analysis for each outlier token in the specified format, focusing on risk assessment and mitigation strategies.
"""

# Create prompts
greeting_prompt = PromptTemplate(input_variables=["client_name"], template=greeting_template)
client_profile_prompt = PromptTemplate(input_variables=["personal_risk", "port_risk", "risk_score", "alignment", "adjustment", "included_percentage", "missing_tokens"], template=client_profile_template)
categorize_assets_prompt = PromptTemplate(input_variables=["holdings_and_scores"], template=categorize_assets_template)
analyze_allocation_prompt = PromptTemplate(input_variables=["holding_percentage_and_risk"], template=analyze_allocation_template)
strategic_diversification_prompt = PromptTemplate(input_variables=["current_portfolio_composition", "overall_portfolio_risk", "target_risk", "adjustment", "risk_formatted_portfolio_allocations"], template=strategic_diversification_template)
outlier_analysis_prompt = PromptTemplate(input_variables=["outliers", "holdings_and_score"], template=outlier_analysis_template)

# Create chains
greeting_chain = LLMChain(llm=llm, prompt=greeting_prompt)
client_profile_chain = LLMChain(llm=llm, prompt=client_profile_prompt, output_key="clientProfile")
categorize_assets_chain = LLMChain(llm=llm, prompt=categorize_assets_prompt)
analyze_allocation_chain = LLMChain(llm=llm, prompt=analyze_allocation_prompt)
strategic_diversification_chain = LLMChain(llm=llm, prompt=strategic_diversification_prompt)
outlier_analysis_chain = LLMChain(llm=llm, prompt=outlier_analysis_prompt)

# Function from outlier.py
def find_outliers_in_holdings(data_file, holdings):
    fundamental_columns = [
        'token_performance',
        'team_partners_investors', 
        'token_economics', 
        'roadmap_progress',
        'security'
    ]

    def find_outliers_with_original_score(row):
        overall_rating = float(row['rating_score'])
        outliers = {}

        for column in fundamental_columns:
            if pd.notna(row[column]):
                value = float(row[column].strip('%'))
                diff = overall_rating - value
                if diff >= 20:
                    outliers[column] = row[column]

        return outliers

    outliers_list = []
    df = pd.read_csv(data_file)
    for symbol in holdings:
        row = df[df['symbol'] == symbol]
        if not row.empty:
            outliers = find_outliers_with_original_score(row.iloc[0])
            if outliers:
                outliers_list.append((symbol, outliers))

    if not outliers_list:
        return "No outliers detected in your portfolio. All fundamental ratings are within 20 points of the overall rating score."
    else:
        print('The outliers analysis')
        return outliers_list

# Additional helper functions
def prepare_outlier_data(outliers):
    outlier_data = []
    for token, metrics in outliers:
        outlier_info = f"{token}:\n"
        for metric, score in metrics.items():
            outlier_info += f"- {metric}: {score}\n"
        outlier_data.append(outlier_info)
    return "\n".join(outlier_data)

def analyze_outliers(outliers):
    outlier_data = prepare_outlier_data(outliers)
    return outlier_data

def calculate_risk_allocations(holding_percentage_and_risk):
    risk_allocations = {'High': 0, 'Medium': 0, 'Low': 0}
    
    for holding in holding_percentage_and_risk:
        parts = holding.split()
        percentage = float(parts[1].rstrip('%'))
        risk = parts[2].strip('()')
        
        risk_allocations[risk] += percentage
    
    risk_formatted_portfolio_allocations = [
        f'High risk allocation: {risk_allocations["High"]:.2f}%',
        f'Medium risk allocation: {risk_allocations["Medium"]:.2f}%',
        f'Low risk allocation: {risk_allocations["Low"]:.2f}%'
    ]
    
    return risk_formatted_portfolio_allocations

def AI_analysis(user_name, portfolio_risk, client_holdings, holding_percentage_and_risk, included_percentage, missing_tokens, holdings_and_scores, df):
    # Get client name
    client_name = user_name
    
    # Run greeting chain
    greeting_result = greeting_chain.run(client_name=client_name)
    print(greeting_result)
    
    # Conduct risk assessment
    print("\nPlease complete the following risk assessment questionnaire:")
    risk_assessment_results = conduct_risk_assessment()
    
    # Analyze risk tolerance
    personal_risk_level, risk_score = analyze_risk_tolerance(risk_assessment_results)
    print(f"\nRisk assessment completed. Your risk tolerance level is: {personal_risk_level}({risk_score})")

    # Run client profile chain
    port_risk = portfolio_risk.lower()
    
    # Check alignment
    alignment, adjustment = check_risk_alignment(personal_risk_level, port_risk)
    
    # Use these values in your client profile chain
    client_profile_result = client_profile_chain.run(
        port_risk=port_risk,
        personal_risk=personal_risk_level,
        risk_score=risk_score,
        alignment=alignment,
        adjustment=adjustment if adjustment else "None",
        included_percentage=included_percentage,
        missing_tokens=", ".join(missing_tokens) if missing_tokens else "None"
    )

    print(client_profile_result)

    # Run the asset categorization chain
    categorization_result = categorize_assets_chain.run(holdings_and_scores=holdings_and_scores)
    print("\nAsset Categorization:")
    print(categorization_result)

    # Run the asset allocation analysis chain
    allocation_result = analyze_allocation_chain.run(
        holding_percentage_and_risk=holding_percentage_and_risk
    )
        
    print("\nAsset Allocation Analysis:")
    print(allocation_result)

    risk_formatted_portfolio_allocations = calculate_risk_allocations(holding_percentage_and_risk)

    strategic_diversification_result = strategic_diversification_chain.run(
        current_portfolio_composition=allocation_result,
        overall_portfolio_risk=port_risk,
        target_risk=personal_risk_level,
        adjustment=adjustment if adjustment else "None",
        risk_formatted_portfolio_allocations=risk_formatted_portfolio_allocations
    )
    print("\nStrategic Diversification Suggestions:")
    print(strategic_diversification_result)

    print("Outlier Analysis:")
    outlier_list = find_outliers_in_holdings(df, client_holdings)
    final_outliers = analyze_outliers(outlier_list)
    outlier_analysis_result = outlier_analysis_chain.run(
        outliers=final_outliers,
        holdings_and_scores=holdings_and_scores)

    print(outlier_analysis_result)

def main():
    # Define relative paths
    script_dir = os.path.dirname(__file__)
    user_dir = os.path.join(script_dir, "user")
    report_dir = os.path.join(user_dir, "report")
    diagram_dir = os.path.join(user_dir, "diagram")
    json_dir = os.path.join(user_dir, "json")
    blockchains_file = os.path.join(script_dir, "coinstat", "blockchains.csv")
    coin_ratings_file = os.path.join(script_dir, "tokeninsight", "final_coin_rating.csv")

    # Create necessary directories
    for directory in [report_dir, diagram_dir, json_dir]:
        os.makedirs(directory, exist_ok=True)

    # Get user input and process data
    user_name = input("Enter your name: ").strip().lower()
    user_file = os.path.join(json_dir, f"{user_name}.json")

    if os.path.exists(user_file):
        print(f"Welcome back, {user_name}!")
        user_data = load_user_data(user_file)
        if input("Do you want to update your current portfolio? (yes/no): ").strip().lower() == 'yes':
            if input("Do you want to add new tokens? (yes/no): ").strip().lower() == 'yes':
                add_tokens(user_data, blockchains_file)
            user_data = update_holdings(user_data)
            save_user_data(user_file, user_data)
    else:
        print(f"New user detected: {user_name}")
        user_data = {'name': user_name, 'tokens': []}
        add_tokens(user_data, blockchains_file)
        save_user_data(user_file, user_data)

    # Load coin ratings
    coin_ratings = load_coin_ratings(coin_ratings_file)
    
    # Calculate final scores
    final_scores = calculate_final_scores(user_data['tokens'], coin_ratings)
    
    # Display final scores and get overall scores
    overall_scores = display_final_scores(final_scores, user_data['tokens'])

    # Process user data and prepare for AI analysis
    grouped_holdings = group_holdings(user_data['tokens'])
    total_portfolio_value = sum(item['balanceUSD'] for item in grouped_holdings)

    holding_percentage_and_risk = []
    for item in grouped_holdings:
        percentage = (item['balanceUSD'] / total_portfolio_value) * 100
        holding_percentage_and_risk.append(f"{item['symbol']}: {percentage:.2f}%")

    holdings_df = pd.DataFrame(grouped_holdings).sort_values(by='balanceUSD', ascending=False)
    
    # Prepare data for AI analysis
    client_holdings = holdings_df['symbol'].tolist()
    included_tokens = set(coin_ratings['symbol'])
    missing_tokens = [token for token in client_holdings if token not in included_tokens]
    included_percentage = (len(client_holdings) - len(missing_tokens)) / len(client_holdings) * 100

    holdings_and_scores = [f"{row['symbol']}: Rating Score: {row['rating_score']:.2f}" 
                           for _, row in coin_ratings[coin_ratings['symbol'].isin(client_holdings)].iterrows()]

    # Determine portfolio risk
    portfolio_risk = calculate_portfolio_risk(holdings_df)

    # Run AI analysis
    AI_analysis(user_name, portfolio_risk, client_holdings, holding_percentage_and_risk, 
                included_percentage, missing_tokens, holdings_and_scores, coin_ratings_file)

    # Generate and save charts
    plot_file = plot_pie_chart(grouped_holdings, user_name, diagram_dir)
    radar_plot_file = plot_radar_chart(overall_scores, user_name, diagram_dir)
    overall_scores['plot_file'] = plot_file
    overall_scores['radar_plot_file'] = radar_plot_file

    print(f"Pie chart saved as: {plot_file}")
    print(f"Radar chart saved as: {radar_plot_file}")

    # Save the final report
    report_file_path = os.path.join(report_dir, f"{user_name}_portfolio_report.xlsx")
    save_final_report(overall_scores, holdings_df, final_scores, report_file_path)
    print(f"Portfolio report saved as: {report_file_path}")

# Implement this function to calculate portfolio risk
def calculate_portfolio_risk(holdings_df):
    print(f"Debug: Holdings DataFrame in risk calculation:\n{holdings_df}")

    if holdings_df.empty:
        print("Warning: Holdings DataFrame is empty. Cannot calculate risk.")
        return "unknown"

    if 'balanceUSD' not in holdings_df.columns:
        print("Error: 'balanceUSD' column not found in holdings DataFrame.")
        return "unknown"

    if 'risk_category' not in holdings_df.columns:
        print("Error: 'risk_category' column not found in holdings DataFrame.")
        return "unknown"

    total_value = holdings_df['balanceUSD'].sum()
    if total_value == 0:
        print("Warning: Total portfolio value is zero. Cannot calculate risk.")
        return "unknown"

    risk_scores = {'High': 3, 'Medium': 2, 'Low': 1}
    weighted_risk = sum(
        risk_scores.get(row['risk_category'], 2) * (row['balanceUSD'] / total_value)
        for _, row in holdings_df.iterrows()
    )

    print(f"Debug: Calculated weighted risk: {weighted_risk}")

    if weighted_risk > 2.5:
        return "high"
    elif weighted_risk > 1.5:
        return "medium"
    else:
        return "low"

# Add error handling
if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"Error: Required file not found. {e}")
    except pd.errors.EmptyDataError:
        print("Error: One of the data files is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")