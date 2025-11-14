package com.comp301.a02adventure;

public class CellImpl implements Cell {
  private String cellName;
  private Position cellPos;
  private String cellDes;
  private Inventory cellChest;
  private boolean hasVisited;

  public CellImpl(int x, int y, String name, String description) {
    cellPos = new PositionImpl(x, y);
    if (name == null || description == null) throw new IllegalArgumentException();
    cellName = name;
    cellDes = description;
    hasVisited = false;
    cellChest = null;
  }

  public CellImpl(int x, int y) {
    this(x, y, "", "");
  }

  public String getName() {
    return cellName;
  }

  public String getDescription() {
    return cellDes;
  }

  public Position getPosition() {
    return cellPos;
  }

  public Inventory getChest() {
    return cellChest;
  }

  public boolean getIsVisited() {
    return hasVisited;
  }

  public boolean hasChest() {
    return !(cellChest == null);
  }

  // SETTER METHODS
  public void setName(String name) {
    if (name == null) throw new IllegalArgumentException();
    cellName = name;
  }

  public void setDescription(String description) {
    if (description == null) throw new IllegalArgumentException();
    cellDes = description;
  }

  public void setChest(Inventory chest) {
    if (chest == null) throw new IllegalArgumentException();
    cellChest = chest;
  }

  public void visit() {
    hasVisited = true;
  }
}
