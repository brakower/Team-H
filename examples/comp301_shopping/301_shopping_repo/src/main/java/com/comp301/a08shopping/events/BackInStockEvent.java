package com.comp301.a08shopping.events;

import com.comp301.a08shopping.Product;
import com.comp301.a08shopping.Store;

public class BackInStockEvent extends SaleEvent {
  public BackInStockEvent(Product p, Store s) {
    super(p, s);
  }
}
