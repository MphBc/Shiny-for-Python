from shiny import App, render, ui
import pandas as pd
import matplotlib.pyplot as plt
import os

# Load the dataset with error handling
file_path = r"D:\My\Other\Python\Shiny for python\corporate_stress_dataset\retail_store_sales.csv"
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Dataset not found at {file_path}")

df = pd.read_csv(file_path)

# Ensure required columns exist
required_columns = ["Transaction Date", "Category", "Total Spent", "Payment Method"]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# Data preprocessing
df = df.dropna(subset=["Transaction Date"])
df[['Year', 'Month', 'Day']] = df['Transaction Date'].str.split('-', expand=True)

# Shorten long category labels
category_replacements = {
    'Electric household essentials': 'Electric Essentials',
    'Computers and electric accessories': 'Computers & Accessories'
}
df['Category'] = df['Category'].replace(category_replacements)

data = df.copy()

# Define a consistent color palette
color_palette = ['#4E79A7', '#F28E2C', '#E15759', '#76B7B2', '#59A14F', '#EDC949']

# Define the Shiny UI
app_ui = ui.page_fluid(
    ui.layout_column_wrap(
        ui.card(
            ui.layout_columns(
            ui.card(
            ui.h2("Retail Store Sales"),
            ui.input_radio_buttons(
                "Category_filter",
                "Select Category",
                {"All": "All", **{category: category for category in df['Category'].unique()}},
            ),
            ),
            ui.card(ui.output_plot("donut_chart")),
            col_widths=(4, 8),
         ),
        ),
        ui.card(ui.output_plot("stacked_bar_chart")),
        ui.card(ui.output_plot("bar_chart_month")),
        ui.card(ui.output_plot("bar_chart_day")),
        width=1 / 2,
    ),
)

# Define the server logic
def server(input, output, session):
    @output
    @render.plot
    def donut_chart():
        selected_category = input.Category_filter()

        if selected_category == "All" or selected_category is None:
            counts = df['Category'].value_counts(normalize=True) * 100
        else:
            filtered_df = df[df['Category'] == selected_category]
            counts = filtered_df['Category'].value_counts(normalize=True) * 100

        if counts.empty:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
            ax.set_title("Category Distribution", fontsize=12)
            return fig

        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=["\n".join(label.split()) for label in counts.index],  # Wrap text
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'width': 0.8},
            colors=color_palette[:len(counts)],
        )
        for text in texts + autotexts:
            text.set_fontsize(10)
        title = "Category Distribution" if selected_category == "All" else f"Category Distribution: {selected_category}"
        ax.set_title(title, fontsize=12)

        return fig


    @output
    @render.plot
    def stacked_bar_chart():
        selected_category = input.Category_filter()

        if selected_category == "All" or selected_category is None:
            filtered_df = df
        else:
            filtered_df = df[df['Category'] == selected_category]

        data = filtered_df.groupby(['Category', 'Payment Method'])['Total Spent'].sum().unstack(fill_value=0)
        data = data.sort_values(by=data.columns.tolist(), ascending=False)

        fig, ax = plt.subplots(figsize=(10, 5))
        data.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            color=color_palette[:len(data.columns)],
        )
        ax.set_title("Total Spent by Category and Payment Method" if selected_category == "All" else f"Total Spent: {selected_category}", fontsize=16)
        ax.set_ylabel("Total Spent", fontsize=14)
        ax.legend(title="Payment Method", fontsize=10)
        ax.tick_params(axis='x', labelrotation=45)

        # Wrap long x-axis labels
        ax.set_xticklabels(["\n".join(label.get_text().split()) for label in ax.get_xticklabels()])

        ax.grid(axis='y', linestyle='--', alpha=0.7)
        fig.tight_layout()

        return fig

    @output
    @render.plot
    def bar_chart_day():
        selected_category = input.Category_filter()

        if selected_category == "All" or selected_category is None:
            filtered_df = df
        else:
            filtered_df = df[df['Category'] == selected_category]

        filtered_df['Transaction Date'] = pd.to_datetime(filtered_df['Transaction Date'])
        filtered_df['Day Name'] = filtered_df['Transaction Date'].dt.day_name()

        day_total_spent = filtered_df.groupby('Day Name')['Total Spent'].sum().reset_index()

        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_total_spent['Day Name'] = pd.Categorical(day_total_spent['Day Name'], categories=day_order, ordered=True)
        day_total_spent = day_total_spent.sort_values('Day Name')

        if day_total_spent.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=10)
            ax.set_title("Total Spent by Day of the Week", fontsize=16)
            return fig

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(day_total_spent['Day Name'], day_total_spent['Total Spent'], color=color_palette[0])

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.0f}", ha='center', va='bottom', fontsize=10)

        ax.set_title('Total Spent by Day of the Week', fontsize=16)
        ax.set_ylabel('Total Spent', fontsize=14)
        ax.tick_params(axis='x', labelrotation=45)

        # Wrap long x-axis labels
        ax.set_xticklabels(["\n".join(label.get_text().split()) for label in ax.get_xticklabels()])

        fig.tight_layout()

        return fig
    
    @output
    @render.plot
    def bar_chart_month():
        selected_category = input.Category_filter()

        if selected_category == "All" or selected_category is None:
            filtered_df = data
        else:
            filtered_df = data[data['Category'] == selected_category]

        filtered_df['Transaction Date'] = pd.to_datetime(filtered_df['Transaction Date'])
        filtered_df['Month Name'] = filtered_df['Transaction Date'].dt.month_name()

        month_total_spent = filtered_df.groupby('Month Name')['Total Spent'].sum().reset_index()

        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December']
        month_total_spent['Month Name'] = pd.Categorical(month_total_spent['Month Name'], categories=month_order, ordered=True)
        month_total_spent = month_total_spent.sort_values('Month Name')

        if month_total_spent.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
            ax.set_title("Total Spent by Month", fontsize=16)
            return fig

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(month_total_spent['Month Name'], month_total_spent['Total Spent'], color='lightcoral')

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.0f}", ha='center', va='bottom', fontsize=10)

        title = 'Total Spent by Month' if selected_category == "All" else f'Total Spent by Month: {selected_category}'
        ax.set_title(title, fontsize=16)
        ax.set_ylabel('Total Spent', fontsize=14)
        ax.tick_params(axis='x', labelrotation=45)

        fig.tight_layout()

        return fig

# Create the Shiny app
app = App(app_ui, server)
