package com.comp301.a08shopping;

public class ProductImpl implements Product {
  private final String name;
  private final double basePrice;
  private int inventory;
  private double discount;

  public ProductImpl(String n, double baseP, int copies) {
    if (baseP <= 0) throw new IllegalArgumentException();
    else {
      name = n;
      basePrice = baseP;
      inventory = copies;
      discount = 0;
    }
  }

  public ProductImpl(String n, double baseP) {
    this(n, baseP, 0);
  }

  public String getName() {
    return name;
  }

  public double getBasePrice() {
    return basePrice;
  }

  public void setInventory(int copies) {
    inventory = copies;
  }

  public void setDiscount(double percentOff) {
    discount = percentOff;
  }

  public int getInventory() {
    return inventory;
  }

  public double getDiscount() {
    return discount;
  }
}
