package com.comp301.a02adventure;

public class ItemImpl implements Item {
  private String name;

  public ItemImpl(String name) {
    if (name == null) throw new IllegalArgumentException();
    this.name = name;
  }

  public String getName() {
    return name;
  }

  @Override
  public boolean equals(Object other) {
    if (other == null) {
      return false;
    } else if (this.getClass() != other.getClass()) {
      return false;
    } else if (this.getName() != ((ItemImpl) other).getName()) {
      return false;
    } else return true;
  }

  @Override
  public String toString() {
    return name;
  }
}
