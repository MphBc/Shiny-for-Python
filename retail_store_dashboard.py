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

data1 = data[data['Quantity'] > 0]

#-------- Global variant --------#

def calculate_dynamic_shared_max(filtered_df):
    # Calculate total spent by month
    filtered_df['Month Name'] = filtered_df['Transaction Date'].dt.month_name()
    month_total_spent = filtered_df.groupby('Month Name')['Total Spent'].sum()

    # Calculate total spent by day
    filtered_df['Day Name'] = filtered_df['Transaction Date'].dt.day_name()
    day_total_spent = filtered_df.groupby('Day Name')['Total Spent'].sum()

    # Calculate the shared maximum across both datasets
    shared_max = max(month_total_spent.max(), day_total_spent.max())
    return shared_max

# Define a consistent color palette
color_palette = ['#4E79A7', '#F28E2C', '#E15759', '#76B7B2', '#59A14F', '#EDC949']

app_ui = ui.page_fluid(
    ui.tags.style(
        """
        .nav-box {
            display: flex;
            flex-direction: column;
            width: 100%;
            background-color: #4A4947;
        }
        .nav-title {
            text-align: center;
            color: white;
            font-size: 45px;
            font-weight: bold;
            padding: 10px;
        }
        .nav-panel-text {
            font-size: 18px;
            font-weight: bold;
            color: #495057;
            padding: 5px 10px;
        }
        .value-box {
            text-align: center;
        }
        .value-box h3 {
            margin: 0;
            font-size: 20px;
            font-weight: bold;
            color: #495057;
        }
        .value-box p {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        .custom-card-header {
            text-align: center;
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        table {
            width: 100%;
            table-layout: fixed;
        }
        th, td {
            text-align: center;
            padding: 8px;
        }
        th {
            font-weight: bold;
        }
        .equal-height-card {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .equal-height-card .card-body {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .equal-height-card .card-body .plot-container {
            flex: 1;
        }
        """
    ),
    ui.tags.div(
        ui.tags.h1("Retail Store Sales Dashboard", class_="nav-title"),
        class_="nav-box"
    ),
    ui.page_navbar(
        ui.nav_panel(
            ui.tags.span("Overview", class_="nav-panel-text"),
            ui.page_fluid(
                ui.layout_column_wrap(
                    ui.tags.div(
                        ui.value_box(
                            "Total Quantity",
                            ui.output_ui("quantity")
                        ),
                        class_="value-box"
                    ),
                    ui.tags.div(
                        ui.value_box(
                            "Total Spend",
                            ui.output_ui("price")
                        ),
                        class_="value-box"
                    ),
                    ui.tags.div(
                        ui.value_box(
                            "Percent Change (YoY)",
                            ui.output_ui("yoy")
                        ),
                        class_="value-box"
                    ),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header(
                            ui.tags.h3(
                                "Total Spent by Category and Payment Method",
                                class_="custom-card-header"
                            )
                        ),
                        ui.output_plot("stacked_bar_chart"),
                        class_="equal-height-card"
                    ),
                    ui.card(
                        ui.card_header(
                            ui.tags.h3(
                                "Latest Data",
                                class_="custom-card-header"
                            )
                        ),
                        ui.output_table("top_customers"),
                        class_="equal-height-card"
                    ),
                    col_widths=(9, 3),
                    height="100%"
                ),
            ),
        ),
        ui.nav_panel(
            ui.tags.span("Sales", class_="nav-panel-text"),
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
                        col_widths=(4, 8)
                    ),
                ),
                ui.card(ui.output_plot("bar_chart_avg_price")),
                ui.card(ui.output_plot("bar_chart_month")),
                ui.card(ui.output_plot("bar_chart_day")),
                width=1/2
            ),
        ),
    ),
    class_="nav-box",
)

#---------------------- PART1 ----------------------#
# Define the server logic
def server(input, output, session):
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

        ax.set_ylabel("Total Spent", fontsize=14)
        ax.set_xlabel("")  # Remove x-axis label
        # ax.legend(title="Payment Method", fontsize=10)
        
        # Move the legend outside the plot area
        ax.legend(
            title="Payment Method",
            fontsize=10,
            bbox_to_anchor=(1.05, 1),  # Move legend outside to the right
            loc='upper left',          # Anchor point for the legend
            borderaxespad=0.           # Padding between legend and axes
        )
        ax.tick_params(axis='x', labelrotation=45)

        # Wrap long x-axis labels
        ax.set_xticklabels(["\n".join(label.get_text().split()) for label in ax.get_xticklabels()])

        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Remove the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        fig.tight_layout()

        return fig

    @render.ui
    def price():
        Total_spend = data['Total Spent'].sum
        return Total_spend

    @render.ui
    def price():
        # Ensure 'Total Spent' is numeric and handle missing values
        if data['Total Spent'].isnull().any():
            data['Total Spent'] = data['Total Spent'].fillna(0)  # Replace NaN with 0

        # # Convert 'Total Spent' to numeric, replacing non-numeric values with 0
        # data['Total Spent'] = pd.to_numeric(data['Total Spent'], errors='coerce').fillna(0)

        # Calculate total spend as an integer
        total_spend = int(data['Total Spent'].sum())
        return f"{total_spend:,.2f} $"  # Format with commas and currency symbol
    
    @render.ui
    def quantity():
        # Check for missing or non-numeric values
        if data['Quantity'].isnull().any():
            data['Quantity'] = data['Quantity'].fillna(0)  # Replace NaN with 0

        data['Quantity'] = data['Quantity'].astype(int)
        total_quantity = data['Quantity'].sum()
        return f"{total_quantity:,}"  # Format as currency
    
    @render.ui
    def yoy():
        # Convert 'Transaction Date' to datetime if not already done
        if not pd.api.types.is_datetime64_any_dtype(data['Transaction Date']):
            data['Transaction Date'] = pd.to_datetime(data['Transaction Date'])

        # Extract the year from the transaction date
        data['Year'] = data['Transaction Date'].dt.year

        # Handle missing or zero values in 'Total Spent'
        data['Total Spent'] = data['Total Spent'].fillna(0)

        # Group by year and calculate the total spent for each year
        yearly_total_spent = data.groupby('Year')['Total Spent'].sum().reset_index()

        # Check if there are enough years of data for YoY analysis
        if len(yearly_total_spent) < 2:
            return "Insufficient data for Year-over-Year analysis."

        # Calculate Year-over-Year (YoY) percentage change
        yearly_total_spent['YoY Change (%)'] = yearly_total_spent['Total Spent'].pct_change() * 100

        # Extract the data for the last year
        last_year_data = yearly_total_spent.iloc[-1]

        # Handle cases where YoY Change is NaN
        last_year_yoy_change = last_year_data["YoY Change (%)"]
        if pd.isna(last_year_yoy_change):
            return "No YoY Change Available"

        # Format the YoY Change value to 2 decimal places
        last_year_yoy_change = round(last_year_yoy_change, 2)

        return f"{last_year_yoy_change}%"



    @output
    @render.table
    def top_customers():
        # Calculate the total spend per customer
        top_customers = data.groupby('Customer ID')['Total Spent'].sum().reset_index()

        # Sort by total spend in descending order
        top_customers = top_customers.sort_values(by='Total Spent', ascending=False).head(10)

        # # Convert 'Total Spent' to numeric, replacing non-numeric values with 0
        # top_customers['Total Spent'] = pd.to_numeric(top_customers['Total Spent'], errors='coerce').fillna(0)

        # Optionally, format the 'Total Spent' column to include commas for thousands
        top_customers['Total Spent'] = top_customers['Total Spent'].apply(lambda x: f"{x:,.2f}")

        # Return the data as a DataFrame
        return top_customers


#---------------------- PART2 ----------------------#

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
            ax.set_title("Category Distribution", fontsize=14)
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
            text.set_fontsize(12)  # Consistent font size for labels and percentages
        title = "Category Distribution" if selected_category == "All" else f"Category Distribution: {selected_category}"
        ax.set_title(title, fontsize=14)  # Consistent title font size

        return fig


    @output
    @render.plot
    def bar_chart_avg_price():
        # Calculate the adjusted price per unit by dividing Price Per Unit by Quantity
        data1['Adjusted Price Per Unit'] = data1['Price Per Unit'] / data1['Quantity']

        # Group the data by 'Category' and calculate the average Price Per Unit for each category
        category_avg_price = data1.groupby('Category')['Adjusted Price Per Unit'].mean().reset_index()

        # Rename the columns for clarity
        category_avg_price.columns = ['Category', 'Average Price Per Unit']

        # Sort the DataFrame by 'Average Price Per Unit' in descending order
        category_avg_price_sorted = category_avg_price.sort_values(by='Average Price Per Unit', ascending=False)

        # Find the category with the highest value
        max_value_category = category_avg_price_sorted.iloc[0]['Category']

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 5))

        # Highlight the highest value bar
        bars = ax.bar(
            category_avg_price_sorted['Category'], 
            category_avg_price_sorted['Average Price Per Unit'], 
            color=[
                'orange' if category == max_value_category else 'teal'
                for category in category_avg_price_sorted['Category']
            ],
            width=0.5
        )

        # Add labels to each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,  # Position at the center of the bar
                height,  # Height of the bar
                f"{height:.2f}",  # Display the value formatted to 2 decimal places
                ha='center', va='bottom', fontsize=10  # Consistent font size for bar labels
            )

        # Wrap long x-axis labels
        wrapped_labels = ["\n".join(label.split()) for label in category_avg_price_sorted['Category']]
        ax.set_xticks(range(len(wrapped_labels)))
        ax.set_xticklabels(wrapped_labels, rotation=45, ha='right', fontsize=12)  # Consistent font size for x-axis labels

        # Remove the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Chart details
        ax.set_title('Average Price Per Unit by Category', fontsize=14, pad=20)  # Consistent title font size
        ax.set_ylabel('Average Price Per Unit', fontsize=12)  # Consistent y-axis label font size
        ax.tick_params(axis='y', labelsize=12)  # Consistent y-axis tick label font size

        return fig

    @output
    @render.plot
    def bar_chart_month():
        selected_category = input.Category_filter()

        # Filter the data based on the selected category
        if selected_category == "All" or selected_category is None:
            filtered_df = data
        else:
            filtered_df = data[data['Category'] == selected_category]

        filtered_df['Transaction Date'] = pd.to_datetime(filtered_df['Transaction Date'])
        filtered_df['Month Name'] = filtered_df['Transaction Date'].dt.month_name()

        month_total_spent = filtered_df.groupby('Month Name')['Total Spent'].sum().reset_index()

        # Ensure months are in the correct order
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December']
        month_total_spent['Month Name'] = pd.Categorical(month_total_spent['Month Name'], categories=month_order, ordered=True)
        month_total_spent = month_total_spent.sort_values('Month Name')

        if month_total_spent.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
            ax.set_title("Total Spent by Month", fontsize=14)
            return fig

        # Calculate the shared maximum for the y-axis
        shared_max = calculate_dynamic_shared_max(filtered_df)

        # Find the month with the maximum total spent
        max_value_month = month_total_spent.loc[month_total_spent['Total Spent'].idxmax(), 'Month Name']

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(
            month_total_spent['Month Name'],
            month_total_spent['Total Spent'],
            color=[
                'orange' if month == max_value_month else '#48A6A7'
                for month in month_total_spent['Month Name']
            ],
        )

        # Add labels to each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,  # Position at the center of the bar
                height + (shared_max * 0.02),  # Move label slightly above the bar
                f"{height:,.0f}",  # Display the value formatted with commas
                ha='center', va='bottom', fontsize=8  # Adjust font size and alignment
            )

        # Set the y-axis limit using the shared maximum
        ax.set_ylim(0, shared_max * 1.15)  # Add extra padding for labels

        # Chart details
        ax.set_title('Total Spent by Month', fontsize=14)  # Consistent title font size
        ax.set_ylabel('Total Spent', fontsize=12)  # Consistent y-axis label font size
        ax.tick_params(axis='x', labelrotation=45, labelsize=12)  # Consistent x-axis tick label font size
        ax.tick_params(axis='y', labelsize=12)  # Consistent y-axis tick label font size

        # Remove the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        fig.tight_layout()

        return fig

    @output
    @render.plot
    def bar_chart_day():
        selected_category = input.Category_filter()

        # Filter the data based on the selected category
        if selected_category == "All" or selected_category is None:
            filtered_df = data
        else:
            filtered_df = data[data['Category'] == selected_category]

        filtered_df['Transaction Date'] = pd.to_datetime(filtered_df['Transaction Date'])
        filtered_df['Day Name'] = filtered_df['Transaction Date'].dt.day_name()

        day_total_spent = filtered_df.groupby('Day Name')['Total Spent'].sum().reset_index()

        # Ensure days are in the correct order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_total_spent['Day Name'] = pd.Categorical(day_total_spent['Day Name'], categories=day_order, ordered=True)
        day_total_spent = day_total_spent.sort_values('Day Name')

        if day_total_spent.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
            ax.set_title("Total Spent by Day of the Week", fontsize=14)
            return fig

        # Calculate the shared maximum for the y-axis
        shared_max = calculate_dynamic_shared_max(filtered_df)

        # Find the day with the maximum total spent
        max_value_day = day_total_spent.loc[day_total_spent['Total Spent'].idxmax(), 'Day Name']

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(
            day_total_spent['Day Name'],
            day_total_spent['Total Spent'],
            color=[
                'orange' if day == max_value_day else '#9ACBD0'
                for day in day_total_spent['Day Name']
            ],
            width=0.5
        )

        # Add labels to each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:,.0f}", ha='center', va='bottom', fontsize=8)  # Consistent font size for bar labels

        # Set the y-axis limit using the shared maximum
        ax.set_ylim(0, shared_max * 1.1)  # Add 10% padding

        # Chart details
        ax.set_title('Total Spent by Day of the Week', fontsize=14, pad=20)  # Consistent title font size
        ax.set_ylabel('Total Spent', fontsize=12)  # Consistent y-axis label font size
        ax.tick_params(axis='x', labelrotation=45, labelsize=12)  # Consistent x-axis tick label font size
        ax.tick_params(axis='y', labelsize=12)  # Consistent y-axis tick label font size

        # Remove the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        fig.tight_layout()

        return fig

# Create the Shiny app
app = App(app_ui, server)
