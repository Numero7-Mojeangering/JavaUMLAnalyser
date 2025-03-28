
package package1;

public class Main extends SuperMain {
    private int test;
    private Ag1 ag1;
    private Ag2 ag2;

    public Main()
    {
        test = 6;
        ag1 = null;
        ag2 = new Ag2();
    }

    public Ag2 getAg2()
    {
        return ag2;
    }

    public int getTest()
    {
        return test;
    }

    public Ag1 getAg1()
    {
        return ag1;
    }
}