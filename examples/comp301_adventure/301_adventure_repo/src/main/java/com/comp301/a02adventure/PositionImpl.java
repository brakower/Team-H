package com.comp301.a02adventure;

public class PositionImpl implements Position {
  private int xCoord;
  private int yCoord;

  public PositionImpl(int x, int y) {
    xCoord = x;
    yCoord = y;
  }

  public int getX() {
    return xCoord;
  }

  public int getY() {
    return yCoord;
  }

  public Position getNeighbor(Direction direction) {
    int newX = xCoord;
    int newY = yCoord;

    switch (direction) {
      case NORTH:
        newY++;
        break;
      case SOUTH:
        newY--;
        break;
      case EAST:
        newX++;
        break;
      case WEST:
        newX--;
        break;
    }
    return new PositionImpl(newX, newY);
  }
}
