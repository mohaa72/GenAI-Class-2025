"""Smart Cash Flow & Invoice Agent"""

obj Business {
    has name: str;
    has balance: float = 0.0;
    has income: float = 0.0;
    has expenses: float = 0.0;

    def add_income(amount: float);
    def add_expense(amount: float, category: str);
    def report;
}


obj Invoice {
    has client: str;
    has amount: float;
    has paid: bool = False;
    has days_overdue: int = 0;

    def pay(biz: Business);
    def overdue_check;
}


# ---------- Implementation ----------

impl Business.add_income(amount: float) {
    self.income += amount;
    self.balance += amount;
    print(f"✅ Invoice from {self.name} PAID: ${amount}");
    print(f"💵 New Balance: ${self.balance}");
}

impl Business.add_expense(amount: float, category: str) {
    self.expenses += amount;
    self.balance -= amount;
    print(f"💸 Expense added: {category} = ${amount}");
    print(f"📉 Balance after expense: ${self.balance}");
}

impl Business.report {
    print("------ 📊 Cash Flow Report ------");
    print(f"Total Income: ${self.income}");
    print(f"Total Expenses: ${self.expenses}");
    print(f"Final Balance: ${self.balance}");

    if self.balance > 0 {
        print("✅ Business is profitable.");
    } elif self.balance == 0 {
        print("⚖️ Business is breaking even.");
    } else {
        print("❌ Business is in deficit. Cut costs!");
    }
}


impl Invoice.pay(biz: Business) {
    if not self.paid {
        self.paid = True;
        biz.income += self.amount;
        biz.balance += self.amount;
        print(f"✅ Invoice from {self.client} PAID: ${self.amount}");
        print(f"💵 New Balance: ${biz.balance}");
    } else {
        print(f"Invoice from {self.client} already paid.");
    }
}

impl Invoice.overdue_check {
    if not self.paid and self.days_overdue > 0 {
        print(f"⚠️ Overdue Invoice! Client: {self.client} Amount: ${self.amount} Days overdue: {self.days_overdue}");
    }
}


# ---------- Run the Agent ----------
with entry {
    biz = Business(name="Smart SME Ltd", balance=200.0);
    print(f"📊 Starting Cash Flow Agent for: {biz.name}");
    print(f"💰 Initial Balance: ${biz.balance}");

    # Create invoices
    invoice1 = Invoice(client="Client A", amount=500);
    invoice2 = Invoice(client="Client B", amount=800);
    print(f"🧾 Created Invoice for {invoice1.client} of ${invoice1.amount}");
    print(f"🧾 Created Invoice for {invoice2.client} of ${invoice2.amount}");

    # Expenses
    biz.add_expense(300, "Office Rent");
    biz.add_expense(700, "Salaries");

    # Client A pays, Client B is overdue
    invoice1.pay(biz);
    invoice2.days_overdue = 30;
    invoice2.overdue_check;

    # Final report
    biz.report;
}
