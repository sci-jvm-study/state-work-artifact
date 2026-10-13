// Extracted from jpf-symbc's own example suite,
// src/examples/sequences/BankAccount.java. Origin:
// https://github.com/SymbolicPathFinder/jpf-symbc -- Apache License 2.0
// (per-file NASA/jpf-symbc header confirmed). deposit()/withdraw() copied verbatim: financial-account bookkeeping with
// stateful logic across multiple calls (a balance and a withdrawal counter persist between calls), so the branching is driven
// by field state across a sequence of calls.
public class BankAccount {

    private int balance;
    private int numberOfWithdrawals;

    public BankAccount(int amount) {
        balance = amount;
    }

    public void deposit(int amount) {
        if (amount > 0)
            balance = balance + amount;
    }

    public void withdraw(int amount) {
        if (amount > balance) {
            return;
        }
        if (numberOfWithdrawals >= 5) {
            return;
        }
        balance = balance - amount;
        numberOfWithdrawals++;
    }

    public static void classify(int initial, int amount1, int amount2, int amount3) {
        BankAccount acct = new BankAccount(initial);
        acct.deposit(amount1);
        acct.withdraw(amount2);
        acct.withdraw(amount3);
    }

    public static void main(String[] args) {
        classify(100, 50, 30, 20);
    }
}