import mysql.connector as bk
import re
import bcrypt
import random

# MySQL database connection Setup
bankConnect = bk.connect(
    host="localhost",
    user="root",
    password="temitope2703@",
    database="bankapp_db",
    auth_plugin='mysql_native_password'
)
bankAppLink = bankConnect.cursor()
print("Successfully Connected")

# Registration Database Tables creation name as (customerDataTable)
bankAppLink.execute("""
    CREATE TABLE IF NOT EXISTS customerDataTable (
        ID INT AUTO_INCREMENT PRIMARY KEY,
        fullName VARCHAR(100),
        lastName VARCHAR(100),
        age INT,
        occupation VARCHAR(100),
        address VARCHAR(255),
        email VARCHAR(100) UNIQUE,
        phoneNumber VARCHAR(18),
        password VARCHAR(255)
    )
""")

# Account Database Tables creation name as (customerAcctTable)
bankAppLink.execute("""
    CREATE TABLE IF NOT EXISTS customerAcctTable (
        ID INT AUTO_INCREMENT PRIMARY KEY,
        customerID INT,
        accountNumber VARCHAR(15) UNIQUE,
        Balance DECIMAL(10, 2) DEFAULT 0.0,
        FOREIGN KEY (customerID) REFERENCES customerDataTable(ID)
    )
""")

# Loan Database Tables creation name as (customerLoanTable)
bankAppLink.execute("""
    CREATE TABLE IF NOT EXISTS customerLoanTable (
        loanID INT AUTO_INCREMENT PRIMARY KEY,
        customerID INT,
        loanAmount DECIMAL(10, 2),
        interestRate DECIMAL(4, 2),
        loanTerm INT,  -- in months
        monthlyPayment DECIMAL(10, 2),
        remainingBalance DECIMAL(10, 2),
        FOREIGN KEY (customerID) REFERENCES customerDataTable(ID)
    )
""")

# Savings Plan Database Tables creation name as (customerSavingsPlanTable)
bankAppLink.execute("""
    CREATE TABLE IF NOT EXISTS customerSavingsPlanTable (
        planID INT AUTO_INCREMENT PRIMARY KEY,
        customerID INT,
        planName VARCHAR(100),
        targetAmount DECIMAL(10, 2),
        currentAmount DECIMAL(10, 2),
        interestRate DECIMAL(4, 2),
        FOREIGN KEY (customerID) REFERENCES customerDataTable(ID)
    )
""")

# Function to generate an account number
def createAccountNum():
    accountNumber = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return accountNumber

# Function to register a new customer
def customerInfo(fullName, lastName, age, occupation, address, email, phoneNumber, password):
    # Verify phone number
    if not phoneNumber.startswith("+234") or len(phoneNumber) != 14:
        raise ValueError("Phone number must start with +234 and be accompanied with 10 digits")
        
    # Email verification
    regexEmail = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regexEmail, email):
        raise ValueError("Invalid Email Address. Please ensure the email has a single '@' symbol, a domain name, and a valid top-level domain (e.g., '.com', '.org').")

    # Verify password
    passwordRegex = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{10,}$'
    if not re.match(passwordRegex, password):
        raise ValueError("Password must be at least 10 characters long, start with a capital letter, include letters, numbers, and symbols")

    # Encrypt password (using hash bcrypt)
    passwordHashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert customer data into the customerDataTable database
    bankData = "INSERT INTO customerDataTable (fullName, lastName, age, occupation, address, email, phoneNumber, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    decodePassword = passwordHashed.decode('utf-8')
    bankValues = (fullName, lastName, age, occupation, address, email, phoneNumber, decodePassword)
    bankAppLink.execute(bankData, bankValues)
    bankConnect.commit()

    # Creating an account for the customer
    customerID = bankAppLink.lastrowid
    accountNumber = createAccountNum()
    bankData = "INSERT INTO customerAcctTable (customerID, accountNumber, Balance) VALUES (%s, %s, %s)"
    bankValues = (customerID, accountNumber, 0.0)
    bankAppLink.execute(bankData, bankValues)
    bankConnect.commit()
    
    print(f"Customer registered successfully. Welcome to NexBanking, {fullName}!")
    print("Your Customer ID is:", customerID)
    print("Your Account Number is:", accountNumber)
    return customerID

# Customer login Function
def login(email, password):
    bankData = "SELECT ID, password FROM customerDataTable WHERE email = %s"
    bankAppLink.execute(bankData, (email,))
    outcome = bankAppLink.fetchone()
    if outcome and bcrypt.checkpw(password.encode('utf-8'), outcome[1].encode('utf-8')):
        print("Login successful!")
        return outcome[0]
    else:
        print("Login failed! Please check your email and password.")
        return None

# Function to check account balance
def checkBalance(customerID):
    bankData = "SELECT accountNumber, Balance FROM customerAcctTable WHERE customerID = %s"
    bankAppLink.execute(bankData, (customerID,))
    outcome = bankAppLink.fetchone()
    if outcome:
        print("Account Number:", outcome[0])
        print("Balance: ₦", outcome[1])
    else:
        print("This customer has no account with us. Please create one today.")

# Function to deposit money
def deposit(customerID, amount):
    bankData = "UPDATE customerAcctTable SET Balance = Balance + %s WHERE customerID = %s"
    bankAppLink.execute(bankData, (amount, customerID))
    bankConnect.commit()
    print("Deposited ₦", amount, "successfully.")

# Function to withdraw money
def withdraw(customerID, amount):
    bankData = "SELECT Balance FROM customerAcctTable WHERE customerID = %s"
    bankAppLink.execute(bankData, (customerID,))
    balance = bankAppLink.fetchone()[0]
    if balance >= amount:
        bankData = "UPDATE customerAcctTable SET Balance = Balance - %s WHERE customerID = %s"
        bankAppLink.execute(bankData, (amount, customerID))
        bankConnect.commit()
        print("Withdrew ₦", amount, "successfully.")
    else:
        print("Insufficient funds!")

# Function to transfer money between accounts
def transferMoney(senderID, receiverAccountNumber, amount):
    bankData = "SELECT Balance FROM customerAcctTable WHERE customerID = %s"
    bankAppLink.execute(bankData, (senderID,))
    senderBalance = bankAppLink.fetchone()[0]

    if senderBalance >= amount:
        bankData = "SELECT customerID FROM customerAcctTable WHERE accountNumber = %s"
        bankAppLink.execute(bankData, (receiverAccountNumber,))
        receiver = bankAppLink.fetchone()
        
        if receiver:
            receiverID = receiver[0]
            bankData = "UPDATE customerAcctTable SET Balance = Balance - %s WHERE customerID = %s"
            bankAppLink.execute(bankData, (amount, senderID))
            
            bankData = "UPDATE customerAcctTable SET Balance = Balance + %s WHERE customerID = %s"
            bankAppLink.execute(bankData, (amount, receiverID))
            
            bankConnect.commit()
            print(f"Transferred ₦{amount} successfully to account number {receiverAccountNumber}.")
        else:
            print("Receiver account not found!")
    else:
        print("Insufficient funds for transfer!")

# Function to get customer details
def getCustomerDetails(customerID):
    bankData = "SELECT * FROM customerDataTable WHERE ID = %s"
    bankAppLink.execute(bankData, (customerID,))
    customerDetails = bankAppLink.fetchone()
    if customerDetails:
        print("Customer Details:")
        print("ID:", customerDetails[0])
        print("Full Name:", customerDetails[1])
        print("Last Name:", customerDetails[2])
        print("Age:", customerDetails[3])
        print("Occupation:", customerDetails[4])
        print("Address:", customerDetails[5])
        print("Email:", customerDetails[6])
        print("Phone Number:", customerDetails[7])
    else:
        print("Customer not found.")

# Function to get account details
def getAccountDetails(customerID):
    bankData = "SELECT * FROM customerAcctTable WHERE customerID = %s"
    bankAppLink.execute(bankData, (customerID,))
    accountDetails = bankAppLink.fetchone()
    if accountDetails:
        print("Account Details:")
        print("ID:", accountDetails[0])
        print("Customer ID:", accountDetails[1])
        print("Account Number:", accountDetails[2])
        print("Balance: ₦", accountDetails[3])
    else:
        print("Account not found.")

# Function to apply for a loan
def applyForLoan(customerID, loanAmount, interestRate, loanTerm):
    monthlyPayment = (loanAmount * (interestRate / 100 / 12)) / (1 - (1 + interestRate / 100 / 12) ** (-loanTerm))
    remainingBalance = loanAmount + (monthlyPayment * loanTerm) - loanAmount
    bankData = "INSERT INTO customerLoanTable (customerID, loanAmount, interestRate, loanTerm, monthlyPayment, remainingBalance) VALUES (%s, %s, %s, %s, %s, %s)"
    bankValues = (customerID, loanAmount, interestRate, loanTerm, monthlyPayment, remainingBalance)
    bankAppLink.execute(bankData, bankValues)
    bankConnect.commit()
    print("Loan applied successfully.")
    print(f"Loan Amount: ₦{loanAmount}, Monthly Payment: ₦{monthlyPayment:.2f}, Loan Term: {loanTerm} months")

# Function to repay loan
def repayLoan(customerID, amount):
    bankData = "SELECT remainingBalance FROM customerLoanTable WHERE customerID = %s"
    bankAppLink.execute(bankData, (customerID,))
    remainingBalance = bankAppLink.fetchone()[0]
    if remainingBalance > 0:
        newBalance = remainingBalance - amount
        if newBalance < 0:
            newBalance = 0
        bankData = "UPDATE customerLoanTable SET remainingBalance = %s WHERE customerID = %s"
        bankAppLink.execute(bankData, (newBalance, customerID))
        bankConnect.commit()
        print(f"Repayment of ₦{amount} made successfully. Remaining Balance: ₦{newBalance:.2f}")
    else:
        print("No outstanding loan balance.")

# Function to create a savings plan
def createSavingsPlan(customerID, planName, targetAmount, interestRate):
    bankData = "INSERT INTO customerSavingsPlanTable (customerID, planName, targetAmount, currentAmount, interestRate) VALUES (%s, %s, %s, %s, %s)"
    bankValues = (customerID, planName, targetAmount, 0.0, interestRate)
    bankAppLink.execute(bankData, bankValues)
    bankConnect.commit()
    print(f"Savings plan '{planName}' created successfully with a target of ₦{targetAmount}.")

# Function to deposit into a savings plan
def depositSavings(customerID, planID, amount):
    bankData = "SELECT currentAmount FROM customerSavingsPlanTable WHERE customerID = %s AND planID = %s"
    bankAppLink.execute(bankData, (customerID, planID))
    currentAmount = bankAppLink.fetchone()[0]
    newAmount = currentAmount + amount
    bankData = "UPDATE customerSavingsPlanTable SET currentAmount = %s WHERE customerID = %s AND planID = %s"
    bankAppLink.execute(bankData, (newAmount, customerID, planID))
    bankConnect.commit()
    print(f"Deposited ₦{amount} into savings plan. New Balance: ₦{newAmount:.2f}")

# Welcome message
def welcome_message():
    message = """
    
    Welcome to NexBanking!

    Thank you for choosing NexBanking. Here’s how to get started:

    Key Features:
    - **Registration:** Sign up easily with your personal details to create a new account.
    - **Login:** Securely log in to access your account anytime, anywhere.
    - **Deposit:** Quickly deposit money into your account with a few taps.
    - **Withdrawal:** Easily withdraw money from your account when you need it.
    - **Transfer Money:** Transfer money between your accounts or to other people securely.
    - **Check Balance:** View your account balance in real-time.
    - **View Account Details:** Access detailed information about your accounts.
    - **Apply for Loans:** Get financial support through our loan services.
    - **Repay Loans:** Manage your loan repayments effortlessly.
    - **Create Savings Plans:** Set and achieve your savings goals.
    - **Deposit into Savings Plans:** Grow your savings with regular deposits.

    Getting Started:
    1. **Create Your Account:** Sign up with your personal details.
    2. **Create Password:** Choose your preferred Secure Password.
    
    Contact Us:
    - **Customer Support:** Reach out to our support team anytime at +234-814-680-1974 or support@nexbanking.com.
   

    Get Started Now:
    - [Create Account Now] | [Log In]

    Stay Connected:
    - Follow Us on Social Media: [Facebook](NexBanking) | [Twitter](NexBankingNg) | [Instagram](NexbankingINsta)

    Best regards,
    The NexBanking Team
    """
    return message

print(welcome_message())

# Nexbanking application section
def nexBank():
    CustomerAccountID = None  # store initial logged-in customer ID
    while True:
        print("\n*** Welcome to NexBanking ***")
        print("1. Register")
        print("2. Login")
        print("3. Check Balance")
        print("4. Deposit Money")
        print("5. Withdraw Money")
        print("6. Transfer Money")
        print("7. View Customer Details")
        print("8. View Account Details")
        print("9. Apply for Loan")
        print("10. Repay Loan")
        print("11. Create Savings Plan")
        print("12. Deposit into Savings Plan")
        print("13. Exit")
        print("**********************************")

        choice = input("Enter your choice: ")

        if choice == '1':
            # Registration Section
            fullName = input("Enter Full Name: ")
            lastName = input("Enter Last Name: ")
            age = int(input("Enter Age: "))
            occupation = input("Enter Occupation: ")
            address = input("Enter Full Address: ")
            email = input("Enter Email: ")
            phoneNumber = input("Enter Phone Number: ")
            password = input("Create Password: ")

            try:
                customerID = customerInfo(fullName, lastName, age, occupation, address, email, phoneNumber, password)
                CustomerAccountID = customerID
                print("You are now logged in. Your Customer ID is:", CustomerAccountID)
            except ValueError as ve:
                print(ve)
                
        elif choice == '2':
            # Login logic
            email = input("Enter Email: ")
            password = input("Enter Password: ")
            CustomerAccountID = login(email, password)
            if CustomerAccountID:
                print("You are now logged in. Your Customer ID is:", CustomerAccountID)
            
        elif choice == '3':
            # Check balance logic
            if CustomerAccountID:
                checkBalance(CustomerAccountID)
            else:
                print("Please log in first.")
            
        elif choice == '4':
            # Deposit money logic
            if CustomerAccountID:
                amount = float(input("Amount to deposit: "))
                deposit(CustomerAccountID, amount)
            else:
                print("Please log in first.")
            
        elif choice == '5':
            # Withdraw money logic
            if CustomerAccountID:
                amount = float(input("Amount to withdraw: "))
                withdraw(CustomerAccountID, amount)
            else:
                print("Please log in first.")
            
        elif choice == '6':
            # Transfer money logic
            if CustomerAccountID:
                receiverAccountNumber = input("Enter Receiver's Account Number: ")# receiver must be in the database already
                amount = float(input("Amount to transfer: "))
                transferMoney(CustomerAccountID, receiverAccountNumber, amount)
            else:
                print("Please log in first.")
        
        elif choice == '7':
            # View Customer Details
            if CustomerAccountID:
                getCustomerDetails(CustomerAccountID)
            else:
                print("Please log in first.")

        elif choice == '8':
            # View Account Details
            if CustomerAccountID:
                getAccountDetails(CustomerAccountID)
            else:
                print("Please try and log in first.")
        
        elif choice == '9':
            # Apply for Loan
            if CustomerAccountID:
                loanAmount = float(input("Enter Loan Amount: "))
                interestRate = float(input("Enter Interest Rate (e.g., 5 for 5%): "))
                loanTerm = int(input("Enter Loan Term (in months): "))
                applyForLoan(CustomerAccountID, loanAmount, interestRate, loanTerm)
            else:
                print("Please log in first.")
        
        elif choice == '10':
            # Repay Loan
            if CustomerAccountID:
                amount = float(input("Amount to repay: "))
                repayLoan(CustomerAccountID, amount)
            else:
                print("Please log in first.")
        
        elif choice == '11':
            # Create Savings Plan
            if CustomerAccountID:
                planName = input("Enter Savings Plan Name: ")
                targetAmount = float(input("Enter Target Amount: "))
                interestRate = float(input("Enter Interest Rate (e.g., 5 for 5%): "))
                createSavingsPlan(CustomerAccountID, planName, targetAmount, interestRate)
            else:
                print("Please log in first.")
        
        elif choice == '12':
            # Deposit into Savings Plan
            if CustomerAccountID:
                planID = int(input("Enter Savings Plan ID: "))
                amount = float(input("Amount to deposit: "))
                depositSavings(CustomerAccountID, planID, amount)
            else:
                print("Please log in first.")
            
        elif choice == '13':
            # To exit Nexbank Application
            print("Thank You for Banking with NexBanking; you have exited NexBanking service for now!")
            print("Logout Confirmation: You have successfully logged out.")
            print("We Value Your Feedback: Rate Your Experience and Give Feedback! ")
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

# Starting NexBank application
nexBank()

