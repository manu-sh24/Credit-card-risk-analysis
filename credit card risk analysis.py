#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# In[2]:


pwd


# In[3]:


# Read the data.
dataP2P = pd.read_csv('Master_Loan_Summary.csv')


# In[5]:


dataP2P.head()


# In[6]:


# HELPER FUNCTIONS
def change_dtype(dtype , df , col_names):
    """ 
    Set dtype of columns given to the dtype given.
    Input: dtype= Desired Datatype
           df = DataFrame
           col_names = Names of columns we want to change the datatype of.   
    """
    for col in col_names:
        df[col] = df[col].astype(dtype)
def find_late_payment_statistics(df,col_name):
    """
    Find the percentage of people who made late payments based on due date categorisation.
    Input: df = DataFrame for analysis.
           col_name = The columns which contains days past due date.  
    Output: A dictionary containing the percentage of people who paid on time, late by 30,45 and 60 days.
    """
    temp_dict = {'Paid on time':0,'30 days late':0 , '45 days late':0 , '60 days late':0}
    total = len(df)
    temp_dict['Paid on time'] = round((len(df[(df[col_name]==0)])/total) * 100 , 2)
    temp_dict['30 days late'] = round((len(df[(df[col_name]>0) & (df[col_name]<=30)])/total) * 100,2)
    temp_dict['45 days late'] = round((len(df[(df[col_name]>30) & (df[col_name]<=45)])/total) * 100,2)
    temp_dict['60 days late'] = round((len(df[(df[col_name]>45) & (df[col_name]<=60)])/total) * 100 , 2)
    return temp_dict        


# In[7]:


# Change the columns to appropriate datatype and extract month and rows.
change_dtype('datetime64' , dataP2P , ['origination_date','last_payment_date','next_payment_due_date'])
dataP2P['Year'] = dataP2P['origination_date'].apply(lambda x: x.year)
dataP2P['Month'] = dataP2P['origination_date'].apply(lambda x: x.month)

# For our observations we will take customers with similar account balance i.e less than 2000.
dataP2P = dataP2P[(dataP2P['amount_borrowed']<2000) & (dataP2P['days_past_due']<=60)]


# In[8]:


# Find late payment statistics.
P2P_stat = find_late_payment_statistics(dataP2P, 'days_past_due')

# Plotting the values
plt.figure(figsize=(12,12))
sns.barplot(x = list(P2P_stat.keys()) , y = list(P2P_stat.values()))
plt.title('Percentage of late payments as per days past due.')


# In[9]:


# Actual Percentage
P2P_stat


# In[10]:


# Define columns for data-frame and percentage of type of customers.
col = ['Date_Issued', 'Due_Date',  'Date_Paid', 'Balance_Days','Customer_Type','No_of_Customers','Rate','Principal' , 'Interest_Per_Person','Total_Interest' , 'Total_Principal']
percentage_of_customers = {'>15':.62 , '30':.11 , '45':.08 , '60':.16}


# In[11]:


def calculate_interest_on_revolving_balance(date_issued , due_date , date_paid , amount , rate , si = True, period = 4, balance_date = "01", decrement_rate = 5):
    """
    Function to calculate interest on revolving balance.
    Input:
    date_issued: Date the loan was issued.
    due_date: Due date for the loan.
    date_paid: Date the loan was paid.
    amount: Principal amount.
    rate: Yearly rate of interest.
    si: Boolean column to determine if Simple interest or compound interest will be calculated.
    period : compounding period
    balance_date : balance date in string.
    decrement_rate: The percentage of loan the customer pays back every month in percentage.
    Output: Total interest due.
    
    """
    # Initialize values
    total_days = 0
    days = 0
    counter = 0
    interest = 0
    decrement_rate = decrement_rate/100
    rate = rate/12
    
    # Convert the dates to pd.DateTime.
    date_issued = pd.to_datetime(date_issued)
    date_paid = pd.to_datetime(date_paid)
    due_date = pd.to_datetime(due_date)
    
    # If paid on time no interest is generated
    if date_paid == due_date:
        return 0,0
    
    # Generate next_balance date
    month = date_issued.month
    year = date_issued.year
    current_balance_date = get_next_balance_date(month,year , balance_date=balance_date)
    
    # Set next balance date as current balance date.
    next_balance_date = current_balance_date
    while(date_paid>next_balance_date):
        if counter == 0:
            # If due date falls after the current balance date, we need to subtract the current balance date from due date.
            if (due_date>current_balance_date):
                # It means I have no outstanding balance in current month.
                days = 0
                interest = 0
            else:
                days = (current_balance_date - due_date).days
                total_days += days
                amount = amount * (1-decrement_rate)
                
                # Calculate interest
                if si == True:
                    interest = calculate_si_for_one(amount , days, rate)
                else:
                    interest = calculate_compound_interest(rate ,amount , days/365 , period=period )
                    
                # Set current balance date as next balance date and find next balance date.   
                current_month = current_balance_date.month
                current_year = current_balance_date.year    
                current_balance_date = next_balance_date
                next_balance_date = get_next_balance_date(current_month , current_year , balance_date = balance_date)
                counter += 1
        else:
            # Find days due.
            days = (next_balance_date - current_balance_date).days
            
            # Total days due
            total_days += days
            
            # Calculate interest.
            if si == True:
                interest += calculate_si_for_one(amount , days, rate)
            else:
                interest += calculate_compound_interest(rate ,amount , days/365 , period=period )
                        
                
            # Set current balance date as next balance date and update next balance date. 
            amount = amount * (1-decrement_rate)
            current_balance_date = next_balance_date
            current_month = current_balance_date.month
            current_year = current_balance_date.year
            next_balance_date = get_next_balance_date(current_month , current_year , balance_date = balance_date)
            

    # Check for remaining due days in current_balance_date
    if (date_paid> current_balance_date):
        # Find days due for the last month.
        days = (date_paid-current_balance_date ).days
        # Total days due
        total_days += days

        # Amount due.
        amount = amount * (1-decrement_rate)

        # Calculate interest.
        if si == True:
            interest += calculate_si_for_one(amount , days, rate)
        else:
            interest += calculate_compound_interest(rate ,amount , days/365 , period=period )
            
    return interest , total_days

def generate_ledger_si(start_date,late_days, creditfree_days = 15, rate = 15 , type_of_customer = ">15", percentage_of_customers = percentage_of_customers, amount = 1000 , total_customers=1000 ):
    
    """
    This function will create a ledger with the kind of customer given and calculate the interest charged based on the days
    past due date.
    Input:
    start_date: The date when the first loan was issued.
    late_days: The number of days a person makes payment past the due date.
    creditfree_days: 15 as provided in the question.
    rate: Yearly rate of interest.
    type_of_customer: Type of customer.
    percentage_of_customers: Dictionary containing the percentage of customers of each kind.
    amount: Principal Balance.
    Totat_Customers: Total Number of Customers.
    Output:
    Dataframe containing the ledger of a particular kind of customer.
    
    """
    counter = 0
    
    # Initialize the parameters needed to find the interest
    temp_dict = dict.fromkeys(col)
    start_date = pd.to_datetime(start_date)
    due_date = start_date + np.timedelta64(creditfree_days , 'D')
    date_paid =  due_date + np.timedelta64(late_days, 'D')
    start_date , due_date , date_paid
    interest_for_one , balance_days = calculate_interest_on_revolving_balance(start_date , due_date , date_paid , amount, rate) 
    no_of_customers = find_number_of_customers(type_of_customer , percentage_of_customers , total_customers  )
    total_principal = no_of_customers * amount 
    
    # Plug values into first row
    temp_dict['Date_Issued'] = start_date
    temp_dict['Due_Date'] = due_date
    temp_dict['Date_Paid'] = date_paid
    temp_dict['Customer_Type'] = type_of_customer
    temp_dict['Rate'] = rate
    temp_dict['Principal'] = amount
    temp_dict['Balance_Days'] = balance_days
    temp_dict['No_of_Customers'] = no_of_customers
    temp_dict['Interest_Per_Person'] = interest_for_one
    temp_dict['Total_Interest'] = calculate_interest_for_all(no_of_customers , interest_for_one)
    temp_dict['Total_Principal'] = total_principal
    # Populate the df
    initialized_df = pd.DataFrame([temp_dict])
    
    # Set previous date
    current_date_issued = start_date
    current_due_date = due_date
    current_date_paid = date_paid
    while(counter == 0):
            # Create a temp_row to append it.
            temp_row = dict.fromkeys(col)
            next_date_issued = current_date_paid + np.timedelta64(1,'D')
            next_due_date = next_date_issued+ np.timedelta64(creditfree_days,'D')
            next_date_paid = next_due_date+ np.timedelta64(late_days,'D')
            balance_days = calc_balance_days(next_date_issued , next_due_date , next_date_paid)
            no_of_customers = find_number_of_customers(type_of_customer , percentage_of_customers , total_customers)
            interest_for_one = calculate_si_for_one(amount ,balance_days, rate)
            total_principal = no_of_customers * amount 
            
            # Append the row
            temp_row['Date_Issued'] = next_date_issued
            temp_row['Due_Date'] = next_due_date
            temp_row['Date_Paid'] = next_date_paid
            temp_row['Customer_Type'] = type_of_customer
            temp_row['Rate'] = rate
            temp_row['Principal'] = amount
            temp_row['Balance_Days'] = balance_days
            temp_row['No_of_Customers'] = no_of_customers
            temp_row['Interest_Per_Person'] = interest_for_one
            temp_row['Total_Interest'] = calculate_interest_for_all(no_of_customers , interest_for_one)
            temp_row['Total_Principal'] = no_of_customers * amount
            
            # Set the current rows as next rows
            current_date_issued = next_date_issued
            current_due_date = next_due_date
            current_date_paid = next_date_paid
            
            #Append the df
            initialized_df = initialized_df.append([temp_row], ignore_index = True)
            
            #Condition to break while loop
            if next_due_date.year == 2020:
                counter += 1
    return initialized_df
    
    
def str2date(month):
    """
    It will convert a date given in string to proper format so that it can be used in Pandas Timestamp function.
    Eg: "1" will return "01".
    Input:
    month: The date in string.
    Output: The month in proper format.
    """
    if len(month)==1:
        month = "0" + month
    return month  

def get_next_balance_date(month , year, balance_date="01"):
    """
    It will generate the next balance date which will be used in calculating the days past due.
    Input:
    month: Current month of loan issued(Integer).
    year: Current year of loan issued(Integer).
    balance_date: The date at which the balance amount is generated(String).
    Output: 
    The next balance date in Timestamp format.
    
    """
    if month<12:
        return pd.to_datetime(str(year) + "-" + str2date(str(month+1))+ "-" + balance_date)
    else:
        return pd.to_datetime(str(year+1) + "-" + str2date(str(1))+ "-" + balance_date)
    
def calc_balance_days(date_issued,due_date , date_paid , balance_date = "01"):
    """
    This function will calculate the number of days a person is due based date_issued and date_paid.
    Input: 
    date_issued: Date the loan was issued.
    date_paid: Date the loan was paid back.
    Output:
    The number of days past due in integer.
    """
    
    # Convert the values to pandas.DateTime
    date_issued = pd.Timestamp(date_issued)
    date_paid = pd.Timestamp(date_paid)
    due_date = pd.Timestamp(due_date)
    
    # Set the balance days = 0.
    balance_days = 0
    
    # Check if bill was paid on time.
    if due_date == date_paid:
        return balance_days
    
    # First check if due date is after the balance date.
    # If I take credit on 1/01/19 I will get the balance 01/02/19
    counter = 0
    issued_month = date_issued.month
    issued_year = date_issued.year
    prev_balance_date = next_balance_date =get_next_balance_date(issued_month , issued_year)
   
    while(date_paid>next_balance_date):
        if counter == 0:
            balance_days = (next_balance_date - due_date).days
            counter +=1
        else:
            balance_days += (next_balance_date - prev_balance_date).days
        # Increment the month:
        prev_balance_date = next_balance_date
        next_balance_date = get_next_balance_date(next_balance_date.month , next_balance_date.year)
        
    # Final step
    balance_days += (date_paid - prev_balance_date).days
    return balance_days

# Calculate Simple Interest-day-wise
def calculate_si_for_one(principal , balance_days , rate):
    """
    Function which calculates Simple Interest based on yearly interest.
    Input:
    Principal: Principal amount.
    balance_days: Number of days past due.
    rate: Yearly rate of interest.
    Output:
    Simple interest
    """
    si = principal * balance_days * (rate/100) * (1/365)
    return si

def calculate_interest_for_all(number_of_customers , interest_for_one):
    """
    Calculates interest for all the customers based on the number of customers.
    """
    return number_of_customers * interest_for_one

def find_number_of_customers(type_of_customer , dict_customer_percentage , total_customers):
    """
    Find the number of customers of a given type.
    """
    return dict_customer_percentage[type_of_customer] * total_customers


# In[12]:


# Create the ledger for different customers.
percentage_of_customers = {'>15':.62 , '30':.11 , '45':.08 , '60':.16}
customer_15 = generate_ledger_si("2017-12-17", late_days=0 , rate=180, percentage_of_customers= percentage_of_customers)
customer_30 = generate_ledger_si("2017-12-17", late_days=30 ,type_of_customer='30' , rate=180, percentage_of_customers= percentage_of_customers)
customer_45 = generate_ledger_si("2017-12-17", late_days=45, type_of_customer='45', rate=180, percentage_of_customers= percentage_of_customers)
customer_60 = generate_ledger_si("2017-12-17", late_days=60, type_of_customer='60', rate=180, percentage_of_customers= percentage_of_customers)

# # As we don't issue another loan to customers who paid 60 days after due date we remove them.
customer_60 = pd.DataFrame(customer_60[:1])

# Concatenate them to a dataframe.
si_df = pd.concat([customer_15, customer_30 , customer_45, customer_60] , ignore_index=True)


# In[13]:


# Display the dataframe.
si_df


# ## Profit generated in 1 year is?
# 

# In[14]:


principal_invested = si_df['Total_Principal'].sum()
interest_earned = si_df['Total_Interest'].sum()

# Calculate the money lost due to .03% of the customers who never paid back.
money_lost = .03 * 1000 * 1000

# Calculate the amount went in generating cards for every customer.
cost_of_cards = 25 * 1000

# The money paid to the credit company by the organization for issuing the card.
money_per_card = 10 * 1000

# Money paid to the bank by the credit card company for the principal.
money_paid_to_bank = .065 * 1000 * 1000

# Calculate total principal.
total_principal = money_lost + principal_invested + cost_of_cards + money_paid_to_bank

# Calculate total returns.
returns = principal_invested + money_per_card + interest_earned

# Calculate the profit/loss %.
diff = returns - total_principal
calc_percentage = diff/total_principal * 100

if calc_percentage<0:
    print('The credit card company could not break even.')
    print('It incurred a loss of ' , round(calc_percentage,2) , '%.')
    print('Loss suffered is ', diff)
else:
    print('The credit card company made a profit.')
    print('It made a profit of  ' , round(calc_percentage,2) , '%.')
    print('Profit made is ', diff)

