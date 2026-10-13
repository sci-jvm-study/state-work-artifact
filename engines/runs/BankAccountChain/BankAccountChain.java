// Same class body as BankAccount.java (see that file for full provenance/
// license). deposit()/withdraw() copied verbatim. Longer call sequence
// (6 calls instead of 3) to genuinely exercise the withdrawal-counter
// limit (numberOfWithdrawals >= 5), which the shorter BankAccount.java
// driver couldn't reach.
public class BankAccountChain {

    private int balance;
    private int numberOfWithdrawals;

    public BankAccountChain(int amount) {
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

    public static void classify(int initial, int a1, int a2, int a3, int a4, int a5, int a6) {
        BankAccountChain acct = new BankAccountChain(initial);
        acct.deposit(a1);
        acct.withdraw(a2);
        acct.withdraw(a3);
        acct.withdraw(a4);
        acct.withdraw(a5);
        acct.withdraw(a6);
    }

    public static void main(String[] args) {
        classify(1000, 50, 30, 20, 10, 5, 5);
    }
}