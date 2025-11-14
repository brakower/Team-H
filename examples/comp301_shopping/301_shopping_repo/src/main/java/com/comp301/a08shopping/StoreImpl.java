package com.comp301.a08shopping;

import com.comp301.a08shopping.events.StoreEvent;
import com.comp301.a08shopping.events.BackInStockEvent;
import com.comp301.a08shopping.events.OutOfStockEvent;
import com.comp301.a08shopping.events.PurchaseEvent;
import com.comp301.a08shopping.events.SaleEndEvent;
import com.comp301.a08shopping.events.SaleStartEvent;
import com.comp301.a08shopping.exceptions.OutOfStockException;
import com.comp301.a08shopping.exceptions.ProductNotFoundException;

import java.util.List;
import java.util.*;

public class StoreImpl implements Store {
  private final String storeName;
  private final ArrayList<StoreObserver> storeObservers = new ArrayList<>();
  private final ArrayList<Product> products = new ArrayList<>();
  private final ArrayList<Integer> productInventory = new ArrayList<>();
  private final ArrayList<Double> discountValues = new ArrayList<>();

  public StoreImpl(String name) {
    if (name == null) throw new IllegalArgumentException();
    else storeName = name;
  }

  public String getName() {
    return storeName;
  }

  public void addObserver(StoreObserver observer) {
    if (observer == null) throw new IllegalArgumentException();
    else storeObservers.add(observer);
  }

  public void removeObserver(StoreObserver observer) {
    storeObservers.remove(observer);
  }

  public List<Product> getProducts() {
    return (List<Product>) products.clone();
  }

  public Product createProduct(String name, double basePrice, int inventory) {
    if (name == null || inventory < 0) throw new IllegalArgumentException();
    Product prod = new ProductImpl(name, basePrice, inventory);
    products.add(prod);
    productInventory.add(inventory);
    discountValues.add(0.0);
    return prod;
  }

  public ReceiptItem purchaseProduct(Product product) {
    if (product == null) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else if (productInventory.get(products.indexOf(product)) == 0) throw new OutOfStockException();
    else {
      int prevInventory = productInventory.get(products.indexOf(product));
      productInventory.set(products.indexOf(product), prevInventory - 1);
      if (productInventory.get(products.indexOf(product)) == 0)
        notify(new OutOfStockEvent(product, this));
      notify(new PurchaseEvent(product, this));
    }
    return new ReceiptItemImpl(product.getName(), getSalePrice(product), storeName);
  }

  public void restockProduct(Product product, int numItems) {
    if (product == null || numItems < 0) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    if (productInventory.get(products.indexOf(product)) == 0)
      notify(new BackInStockEvent(product, this));
    productInventory.set(products.indexOf(product), numItems);
  }

  public void startSale(Product product, double percentOff) {
    if (product == null || percentOff < 0 || percentOff > 1) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else {
      discountValues.set(products.indexOf(product), percentOff);
      notify(new SaleStartEvent(product, this));
    }
  }

  public void endSale(Product product) {
    if (product == null) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else {
      discountValues.set(products.indexOf(product), 0.0);
      notify(new SaleEndEvent(product, this));
    }
  }

  public int getProductInventory(Product product) {
    if (product == null) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else return productInventory.get(products.indexOf(product));
  }

  public boolean getIsInStock(Product product) {
    if (product == null) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else return !(this.getProductInventory(product) == 0);
  }

  public double getSalePrice(Product product) {
    if (product == null) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else {
      double unRounded =
          product.getBasePrice() * (1.0 - discountValues.get(products.indexOf(product)));
      return (double) Math.round(unRounded * 100) / 100;
    }
  }

  public boolean getIsOnSale(Product product) {
    if (product == null) throw new IllegalArgumentException();
    else if (!products.contains(product)) throw new ProductNotFoundException();
    else return (getSalePrice(product) < product.getBasePrice());
  }

  private void notify(StoreEvent event) {
    for (StoreObserver o : storeObservers) o.update(event);
  }
}
