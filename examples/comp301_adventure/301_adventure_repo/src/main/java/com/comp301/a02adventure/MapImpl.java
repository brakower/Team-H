package com.comp301.a02adventure;

public class MapImpl implements Map {
  private int numItems;
  private int w;
  private int h;
  private Cell[][] mapCells;

  public MapImpl(int width, int height, int numItems) {
    if (width <= 0 || height <= 0) throw new IllegalArgumentException();
    this.numItems = numItems;
    w = width;
    h = height;
    mapCells = new Cell[w][h];
  }

  public int getWidth() {
    return w;
  }

  public int getHeight() {
    return h;
  }

  /**
   * Getter method for a specific cell on the map. Throws an IndexOutOfBoundsException for
   * coordinate parameters that are not on the map
   */
  public Cell getCell(int x, int y) {
    if (x < 0 || x > w) throw new IndexOutOfBoundsException();
    else if (y < 0 || y > h) throw new IndexOutOfBoundsException();
    else return mapCells[x][y];
  }

  /**
   * Overloaded getter method for a specific cell on the map. Throws an IndexOutOfBoundsException
   * for coordinate parameters that are not on the map
   */
  public Cell getCell(Position position) {
    int x = position.getX();
    int y = position.getY();
    if (x < 0 || x > w) throw new IndexOutOfBoundsException();
    else if (y < 0 || y > h) throw new IndexOutOfBoundsException();
    else return mapCells[x][y];
  }

  /**
   * Initializes a new CellImpl object at the specified location on the map, overwriting any
   * existing Cell at that location. Throws an IndexOutOfBoundsException for coordinate parameters
   * that are not on the map
   */
  public void initCell(int x, int y) {
    if (x < 0 || x > w) throw new IndexOutOfBoundsException();
    else if (y < 0 || y > h) throw new IndexOutOfBoundsException();
    else mapCells[x][y] = new CellImpl(x, y);
  }

  /**
   * Getter method for the total number of items that need to be collected in order for the player
   * to win. This field is immutable.
   */
  public int getNumItems() {
    return numItems;
  }
}
