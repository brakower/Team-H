package com.comp301.a08shopping.events;

import com.comp301.a08shopping.Product;
import com.comp301.a08shopping.Store;

public class SaleEvent implements StoreEvent {
  private final Product product;
  private final Store store;

  public SaleEvent(Product p, Store s) {
    if (p == null || s == null) throw new IllegalArgumentException();
    else {
      product = p;
      store = s;
    }
  }

  public Product getProduct() {
    return product;
  }

  public Store getStore() {
    return store;
  }
}
