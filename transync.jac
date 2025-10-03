"""TRANSYNC: Transport Real-time Architecture for Networked Synchronization and Customer Loyalty"""

import random;

obj Project {
    has active: bool = True;

    def run;
}
obj Transync(Project) {
    has fleet_balance: float = 0.0;
    has income: float = 0.0;
    has expenses: float = 0.0;
    has overdue: bool = False;
    has customers: dict[str,int] = {};  # Loyalty points per customer

    def init;
    override def run;
    def add_passenger(fare: float, client: str);
    def add_expense(amount: float, description: str);
    def mark_overdue(client: str, amount: float, days: int);
    def generate_report;
}


with entry {
    print("Starting Transync Fleet Tracker for: Supermetro Sacco");
    system = Transync();
    system.run();
}


impl Project.run {
    raise NotImplementedError("Subclasses must implement this method.");
}


impl Transync.init {
    self.fleet_balance = 0.0;
    self.income = 0.0;
    self.expenses = 0.0;
    self.overdue = False;
    self.customers = {};
}

impl Transync.run {
    print(f"Initial Fleet Balance: ${self.fleet_balance}");

    self.add_passenger(100.0, "Passenger A");
    self.add_passenger(80.0, "Passenger B");
    self.add_passenger(50.0, "Passenger C");

    self.add_expense(50.0, "Fuel");
    self.add_expense(30.0, "Maintenance");

    self.mark_overdue("Passenger B", 80.0, 5);

    self.generate_report();
}

impl Transync.add_passenger(fare: float, client: str) {
    self.fleet_balance += fare;
    self.income += fare;

    # Track loyalty points (20% of fare per ride)
    if client not in self.customers {
        self.customers[client] = 0;
    }
    self.customers[client] += int(fare * 0.2);

    print(f"Passenger boarded: {client}, Fare: ${fare}");
    print(f"Loyalty Points for {client}: {self.customers[client]} points");
    print(f"New Fleet Balance: ${self.fleet_balance}");
}

impl Transync.add_expense(amount: float, description: str) {
    self.fleet_balance -= amount;
    self.expenses += amount;
    print(f"Expense added: {description} = ${amount}");
    print(f"Balance after expense: ${self.fleet_balance}");
}

impl Transync.mark_overdue(client: str, amount: float, days: int) {
    self.overdue = True;
    print(f"Overdue Fare! Client: {client} Amount: ${amount} Days overdue: {days}");
}

impl Transync.generate_report {
    print("------ Fleet Report ------");
    print(f"Total Income: ${self.income}");
    print(f"Total Expenses: ${self.expenses}");
    print(f"Final Balance: ${self.fleet_balance}");

    if self.fleet_balance < 0 {
        print("Fleet running at a deficit. Improve efficiency!");
    } else {
        print("Fleet is profitable. Keep up the good work!");
    }

    print(" Loyalty Points Summary:");
    for client in self.customers.keys() {
        print(f"   - {client}: {self.customers[client]} points");
    }
}
