package com.comp301.a08shopping.events;

import com.comp301.a08shopping.Product;
import com.comp301.a08shopping.Store;

public class OutOfStockEvent extends SaleEvent {
  public OutOfStockEvent(Product p, Store s) {
    super(p, s);
  }
}
