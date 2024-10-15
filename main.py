import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple
from coinstat.helpers import get_token_amount, update_holdings, save_user_data, load_user_data, handle_address, add_tokens, group_holdings, save_report_csv, plot_holdings
from tokeninsight.helpers import load_coin_ratings, calculate_final_scores, display_final_scores, show_ratings

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

def main() -> None:
    """
    Main function to run the portfolio analysis and report generation.
    """
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

    # Calculate final scores and generate reports
    coin_ratings = load_coin_ratings(coin_ratings_file)
    final_scores = calculate_final_scores(user_data['tokens'], coin_ratings)
    
    # Display final scores and get overall scores
    overall_scores = display_final_scores(final_scores, user_data['tokens'])

    print("Debug: overall_scores in main function:")
    print(overall_scores)
    
    grouped_holdings = group_holdings(user_data['tokens'])
    total_portfolio_value = sum(item['balanceUSD'] for item in grouped_holdings)

    for item in grouped_holdings:
        item['percentage'] = (item['balanceUSD'] / total_portfolio_value)

    overall_scores['Total Portfolio USD Balance'] = total_portfolio_value

    holdings_df = pd.DataFrame(grouped_holdings).sort_values(by='balanceUSD', ascending=False)

    # Generate and save charts
    plot_file = plot_pie_chart(grouped_holdings, user_name, diagram_dir)
    radar_plot_file = plot_radar_chart(overall_scores, user_name, diagram_dir)
    overall_scores['plot_file'] = plot_file
    overall_scores['radar_plot_file'] = radar_plot_file

    # Save the final report
    report_file_path = os.path.join(report_dir, f"{user_name}_portfolio_report.xlsx")
    save_final_report(overall_scores, holdings_df, final_scores, report_file_path)


if __name__ == "__main__":
    main()