package com.comp301.a08shopping;

import com.comp301.a08shopping.events.*;

import java.util.List;
import java.util.*;

public class CustomerImpl implements Customer {
  private final String name;
  private double budget;
  private final ArrayList<ReceiptItem> receiptItems = new ArrayList<>();

  public CustomerImpl(String customerName, double customerBudget) {
    if (customerName == null || customerBudget < 0) throw new IllegalArgumentException();
    else {
      name = customerName;
      budget = customerBudget;
    }
  }

  public void update(StoreEvent event) {
    if (event instanceof BackInStockEvent)
      System.out.println(
          event.getProduct().getName() + " is back in stock at " + event.getStore().getName());
    else if (event instanceof OutOfStockEvent)
      System.out.println(
          event.getProduct().getName() + " is now out of stock at " + event.getStore().getName());
    else if (event instanceof PurchaseEvent)
      System.out.println(
          "Someone purchased "
              + event.getProduct().getName()
              + " at "
              + event.getStore().getName());
    else if (event instanceof SaleEndEvent)
      System.out.println(
          "The sale for "
              + event.getProduct().getName()
              + " at "
              + event.getStore().getName()
              + " has ended");
    else if (event instanceof SaleStartEvent)
      System.out.println(
          "New sale for "
              + event.getProduct().getName()
              + " at "
              + event.getStore().getName()
              + "!");
  }

  public String getName() {
    return name;
  }

  public double getBudget() {
    return budget;
  }

  public void purchaseProduct(Product product, Store store) {
    if (product == null || store == null) throw new IllegalArgumentException();
    else if (store.getSalePrice(product) > budget) throw new IllegalStateException();
    else {
      budget = budget - store.getSalePrice(product);
      store.purchaseProduct(product);
      ReceiptItem receipt =
          new ReceiptItemImpl(product.getName(), store.getSalePrice(product), store.getName());
      receiptItems.add(receipt);
    }
  }

  public List<ReceiptItem> getPurchaseHistory() {
    return (List<ReceiptItem>) receiptItems.clone();
  }
}
