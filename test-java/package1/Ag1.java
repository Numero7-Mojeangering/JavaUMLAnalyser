package package1;

import java.util.ArrayList;

public class Ag1 {
    private double d1;
    private double d2;
    private ArrayList<Double> test;

    public Ag1() {
        d1 = 0;
        test = new ArrayList<Double>();
    }

    public void addTest(double zr)
    {
        test.add(Double.valueOf(zr));
    }

    public double getD1() {
        return d1;
    }

    public double getD2() {
        return d2;
    }

    public void setD2(double d) {
        this.d2 = d;
    }

    public void setD1(double d) {
        this.d1 = d;
    }
}


class Test {

}