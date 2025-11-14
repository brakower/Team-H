package com.comp301.a02adventure;

import java.util.List;

public class GameImpl implements Game {
  private Player readyPlayer;
  private Map readyMap;

  public GameImpl(Map map, Player player) {
    if (map == null || player == null) throw new IllegalArgumentException();
    readyPlayer = player;
    readyMap = map;
  }

  public Position getPlayerPosition() {
    return readyPlayer.getPosition();
  }

  public String getPlayerName() {
    return readyPlayer.getName();
  }

  public List<Item> getPlayerItems() {
    return readyPlayer.getInventory().getItems();
  }

  public boolean getIsWinner() {
    return readyPlayer.getInventory().getNumItems() == readyMap.getNumItems();
  }

  public void printCellInfo() {
    System.out.println("Location: " + readyMap.getCell(readyPlayer.getPosition()).getName());
    System.out.println(readyMap.getCell(readyPlayer.getPosition()).getDescription());
    if (readyMap.getCell(readyPlayer.getPosition()).getIsVisited())
      System.out.println("You have already visited this location.");
    if (readyMap.getCell(readyPlayer.getPosition()).hasChest())
      System.out.println("You found a chest! Type 'open' to see what's inside, or keep moving.");
    readyMap.getCell(readyPlayer.getPosition()).visit();
  }

  public void openChest() {
    if (!readyMap.getCell(readyPlayer.getPosition()).hasChest())
      System.out.println("No chest to open, sorry!");
    else if (readyMap.getCell(readyPlayer.getPosition()).hasChest()
        && readyMap.getCell(readyPlayer.getPosition()).getChest().isEmpty())
      System.out.println("The chest is empty.");
    else if (readyMap.getCell(readyPlayer.getPosition()).hasChest()
        && !readyMap.getCell(readyPlayer.getPosition()).getChest().isEmpty()) {
      System.out.println(
          "You collected these items: "
              + readyMap.getCell(readyPlayer.getPosition()).getChest().getItems());
      readyPlayer
          .getInventory()
          .transferFrom(readyMap.getCell(readyPlayer.getPosition()).getChest());
      /*System.out.println("You collected these items: ");
      List<Item> theItems = readyMap.getCell(readyPlayer.getPosition()).getChest().getItems();
      for (int i=0; i<theItems.size(); i++)
      {
          System.out.print(theItems.get(i).toString()+", ");
      }*/
    }
  }

  public boolean canMove(Direction direction) {
    if (direction == Direction.NORTH) {
      if (readyPlayer.getPosition().getNeighbor(direction).getY() >= readyMap.getHeight()) {
        return false;
      }
      if (readyMap.getCell(readyPlayer.getPosition().getNeighbor(direction)) == null) {
        return false;
      }
    }
    if (direction == Direction.SOUTH) {
      if (readyPlayer.getPosition().getNeighbor(direction).getY() < 0) {
        return false;
      }
      if (readyMap.getCell(readyPlayer.getPosition().getNeighbor(direction)) == null) {
        return false;
      }
    }
    if (direction == Direction.EAST) {
      if (readyPlayer.getPosition().getNeighbor(direction).getX() >= readyMap.getWidth()) {
        return false;
      }
      if (readyMap.getCell(readyPlayer.getPosition().getNeighbor(direction)) == null) {
        return false;
      }
    }
    if (direction == Direction.WEST) {
      if (readyPlayer.getPosition().getNeighbor(direction).getX() < 0) {
        return false;
      }
      if (readyMap.getCell(readyPlayer.getPosition().getNeighbor(direction)) == null) {
        return false;
      }
    }
    return true;
  }

  public void move(Direction direction) {
    if (canMove(direction)) {
      readyPlayer.move(direction);
      printCellInfo();
    } else System.out.println("You can't go that way! Try another direction.");
  }
}
