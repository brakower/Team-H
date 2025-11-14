package com.comp301.a02adventure;

public class PlayerImpl implements Player {
  private String playerName;
  private Position playerPos;
  private Inventory playerIn;

  public PlayerImpl(String name, int startX, int startY) {
    if (name == null) throw new IllegalArgumentException();
    playerName = name;
    playerPos = new PositionImpl(startX, startY);
    playerIn = new InventoryImpl();
  }

  public Position getPosition() {
    return playerPos;
  }

  public Inventory getInventory() {
    return playerIn;
  }

  public String getName() {
    return playerName;
  }

  public void move(Direction direction) {
    playerPos = getPosition().getNeighbor(direction);
  }
}
