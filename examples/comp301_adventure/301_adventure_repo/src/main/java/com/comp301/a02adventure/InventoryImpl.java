package com.comp301.a02adventure;

import java.util.*;

public class InventoryImpl implements Inventory {
  private List<Item> theList;

  public InventoryImpl() {
    theList = new ArrayList<>();
  }
  ;

  public boolean isEmpty() {
    return theList.isEmpty();
  }

  public int getNumItems() {
    return theList.size();
  }

  public List<Item> getItems() {
    return new ArrayList<Item>(theList);
  }

  public void addItem(Item item) {
    theList.add(item);
  }

  public void removeItem(Item item) {
    theList.remove(item);
  }

  public void clear() {
    theList.clear();
  }

  public void transferFrom(Inventory other) {
    theList.addAll(other.getItems());
    other.clear();
  }
}
